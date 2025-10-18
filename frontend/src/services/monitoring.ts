/**
 * Real-time Monitoring Service
 * Phase 2.4.2: 실시간 가격 변동 모니터링 및 자동 알림 시스템
 * Phase 2.4.3: Supabase Realtime 뉴스 구독 + LocalStorage 중복 방지
 */

import { supabase } from '../lib/supabase';
import type { RealtimeChannel } from '@supabase/supabase-js';
import { usePriceStore } from '../stores/priceStore';
import { usePortfolioStore } from '../stores/portfolioStore';
import { useWatchlistStore } from '../stores/watchlistStore';
import type { UserAlertSettings, Alert, PriceChangeData } from '../lib/alertRules';
import {
  evaluatePriceChange,
  createPriceChangeAlert,
  shouldTriggerAlert,
  isDuplicateAlert,
  DEFAULT_ALERT_SETTINGS,
} from '../lib/alertRules';
import { ttsService } from '../lib/tts';
import type { TTSConfig } from '../lib/tts';
import { DEFAULT_TTS_CONFIG } from '../lib/tts';

/**
 * 모니터링 서비스 클래스
 */
class MonitoringService {
  private static instance: MonitoringService;
  private userId: string | null = null;
  private isMonitoring: boolean = false;
  private priceCheckInterval: ReturnType<typeof setInterval> | null = null;
  private newsChannel: RealtimeChannel | null = null; // Supabase Realtime 채널
  private previousPrices: Map<string, number> = new Map(); // symbol → 이전 가격
  private processedNewsIds: Set<string> = new Set(); // 처리된 뉴스 ID (LocalStorage 연동)
  private recentAlerts: Alert[] = []; // 최근 알림 (중복 방지용)
  private alertSettings: UserAlertSettings = DEFAULT_ALERT_SETTINGS;
  private ttsConfig: TTSConfig = DEFAULT_TTS_CONFIG;
  private onAlertCallback: ((alert: Alert) => void) | null = null;

  // LocalStorage 설정
  private readonly PROCESSED_NEWS_KEY = 'jusik_processed_news_ids';
  private readonly NEWS_RETENTION_DAYS = 7;

  private constructor() {
    // LocalStorage에서 처리된 뉴스 ID 로드
    this.processedNewsIds = this.loadProcessedNewsIds();
  }

  /**
   * Singleton 인스턴스 반환
   */
  public static getInstance(): MonitoringService {
    if (!MonitoringService.instance) {
      MonitoringService.instance = new MonitoringService();
    }
    return MonitoringService.instance;
  }

  /**
   * 모니터링 시작
   * @param userId 사용자 ID
   * @param alertSettings 알림 설정
   * @param ttsConfig TTS 설정
   * @param onAlert 알림 발생 시 콜백 함수
   */
  public start(
    userId: string,
    alertSettings: UserAlertSettings = DEFAULT_ALERT_SETTINGS,
    ttsConfig: TTSConfig = DEFAULT_TTS_CONFIG,
    onAlert?: (alert: Alert) => void
  ): void {
    if (this.isMonitoring) {
      console.log('[Monitoring] 이미 모니터링 중입니다.');
      return;
    }

    this.userId = userId;
    this.alertSettings = alertSettings;
    this.ttsConfig = ttsConfig;
    this.onAlertCallback = onAlert || null;
    this.isMonitoring = true;

    console.log('[Monitoring] 모니터링 시작:', {
      userId,
      alertSettings,
      ttsConfig,
    });

    // 현재 가격을 초기 이전 가격으로 설정
    this.initializePreviousPrices();

    // 가격 변동 체크 시작 (5초마다)
    this.priceCheckInterval = setInterval(() => {
      this.checkPriceChanges();
    }, 5000);

    // Supabase Realtime 뉴스 구독 시작 (30초 폴링 대신)
    this.setupNewsRealtimeSubscription();
  }

  /**
   * 모니터링 중지
   */
  public stop(): void {
    if (!this.isMonitoring) {
      console.log('[Monitoring] 모니터링이 실행 중이 아닙니다.');
      return;
    }

    // 가격 체크 인터벌 중지
    if (this.priceCheckInterval) {
      clearInterval(this.priceCheckInterval);
      this.priceCheckInterval = null;
    }

    // Realtime 뉴스 구독 중지
    if (this.newsChannel) {
      supabase.removeChannel(this.newsChannel);
      this.newsChannel = null;
      console.log('[Monitoring] Realtime 뉴스 구독 해제');
    }

    // LocalStorage에 처리된 뉴스 ID 저장
    this.saveProcessedNewsIds();

    this.isMonitoring = false;
    this.userId = null;
    this.previousPrices.clear();
    this.recentAlerts = [];
    this.onAlertCallback = null;

    console.log('[Monitoring] 모니터링 중지');
  }

  /**
   * 모니터링 상태 확인
   */
  public isRunning(): boolean {
    return this.isMonitoring;
  }

  /**
   * 알림 설정 업데이트
   */
  public updateAlertSettings(settings: UserAlertSettings): void {
    this.alertSettings = settings;
    console.log('[Monitoring] 알림 설정 업데이트:', settings);
  }

  /**
   * TTS 설정 업데이트
   */
  public updateTTSConfig(config: TTSConfig): void {
    this.ttsConfig = config;
    console.log('[Monitoring] TTS 설정 업데이트:', config);
  }

  /**
   * 초기 이전 가격 설정
   */
  private initializePreviousPrices(): void {
    const priceStore = usePriceStore.getState();
    const portfolioStore = usePortfolioStore.getState();
    const watchlistStore = useWatchlistStore.getState();

    // 보유 종목 + 관심 종목 심볼 수집
    const portfolioSymbols = portfolioStore.items.map((item: { symbol: string }) => item.symbol);
    const watchlistSymbols = watchlistStore.items.map((item: { symbol: string }) => item.symbol);
    const allSymbols = [...new Set([...portfolioSymbols, ...watchlistSymbols])];

    allSymbols.forEach((symbol) => {
      const priceData = priceStore.getPrice(symbol);
      if (priceData) {
        this.previousPrices.set(symbol, priceData.price);
      }
    });

    console.log(`[Monitoring] 초기 가격 설정 완료: ${this.previousPrices.size}개 종목`);
  }

  /**
   * 가격 변동 체크
   */
  private checkPriceChanges(): void {
    if (!this.isMonitoring || !this.userId) return;

    const priceStore = usePriceStore.getState();
    const portfolioStore = usePortfolioStore.getState();
    const watchlistStore = useWatchlistStore.getState();

    // 보유 종목 체크
    portfolioStore.items.forEach((item: { symbol: string; symbol_name: string; qty: number; avg_price: number }) => {
      const currentPriceData = priceStore.getPrice(item.symbol);
      if (!currentPriceData) return;

      const previousPrice = this.previousPrices.get(item.symbol);
      if (!previousPrice) {
        // 이전 가격이 없으면 현재 가격을 저장하고 넘어감
        this.previousPrices.set(item.symbol, currentPriceData.price);
        return;
      }

      // 가격 변동 평가
      const shouldAlert = evaluatePriceChange(
        currentPriceData.price,
        previousPrice,
        this.alertSettings.priceChangeThreshold
      );

      if (shouldAlert && shouldTriggerAlert('price_change', this.alertSettings)) {
        const changeRate =
          ((currentPriceData.price - previousPrice) / previousPrice) * 100;

        const priceChangeData: PriceChangeData = {
          symbol: item.symbol,
          symbolName: item.symbol_name,
          currentPrice: currentPriceData.price,
          previousPrice,
          changeRate,
        };

        const alert = createPriceChangeAlert(this.userId!, priceChangeData, true);

        // 중복 알림 체크
        if (!isDuplicateAlert(alert, this.recentAlerts)) {
          this.handleAlert(alert);
          this.previousPrices.set(item.symbol, currentPriceData.price);
        }
      }
    });

    // 관심 종목 체크
    watchlistStore.items.forEach((item) => {
      const currentPriceData = priceStore.getPrice(item.symbol);
      if (!currentPriceData) return;

      const previousPrice = this.previousPrices.get(item.symbol);
      if (!previousPrice) {
        this.previousPrices.set(item.symbol, currentPriceData.price);
        return;
      }

      const shouldAlert = evaluatePriceChange(
        currentPriceData.price,
        previousPrice,
        this.alertSettings.priceChangeThreshold
      );

      if (shouldAlert && shouldTriggerAlert('price_change', this.alertSettings)) {
        const changeRate =
          ((currentPriceData.price - previousPrice) / previousPrice) * 100;

        const priceChangeData: PriceChangeData = {
          symbol: item.symbol,
          symbolName: item.symbol_name,
          currentPrice: currentPriceData.price,
          previousPrice,
          changeRate,
        };

        const alert = createPriceChangeAlert(this.userId!, priceChangeData, false);

        if (!isDuplicateAlert(alert, this.recentAlerts)) {
          this.handleAlert(alert);
          this.previousPrices.set(item.symbol, currentPriceData.price);
        }
      }
    });

    // 오래된 알림 제거 (10분 이상)
    this.cleanupOldAlerts();
  }

  /**
   * 알림 처리
   */
  private handleAlert(alert: Alert): void {
    console.log('[Monitoring] 알림 발생:', alert);

    // 최근 알림에 추가
    this.recentAlerts.push(alert);

    // 콜백 호출 (alertStore에 추가 등)
    if (this.onAlertCallback) {
      this.onAlertCallback(alert);
    }

    // TTS 재생
    if (this.ttsConfig.enabled) {
      this.playTTSAlert(alert);
    }
  }

  /**
   * TTS 알림 재생
   */
  private async playTTSAlert(alert: Alert): Promise<void> {
    try {
      // 포트폴리오 데이터 가져오기 (수익률 계산용)
      const portfolioStore = usePortfolioStore.getState();
      const portfolio = portfolioStore.getPortfolioWithProfit();

      // TTS 메시지 생성
      const message = ttsService.generateAlertMessage(alert, portfolio);

      // TTS 재생
      await ttsService.speakQueued(message, this.ttsConfig);
    } catch (error) {
      console.error('[Monitoring] TTS 재생 오류:', error);
    }
  }

  /**
   * 오래된 알림 제거 (10분 이상)
   */
  private cleanupOldAlerts(): void {
    const tenMinutesAgo = new Date(Date.now() - 10 * 60 * 1000);
    this.recentAlerts = this.recentAlerts.filter((alert) => {
      return new Date(alert.timestamp) > tenMinutesAgo;
    });
  }

  /**
   * LocalStorage에서 처리된 뉴스 ID 로드
   */
  private loadProcessedNewsIds(): Set<string> {
    try {
      const stored = localStorage.getItem(this.PROCESSED_NEWS_KEY);
      if (!stored) {
        console.log('[Monitoring] LocalStorage: 저장된 데이터 없음');
        return new Set();
      }

      const data: { ids: string[]; timestamp: number } = JSON.parse(stored);

      // 7일 이상 지난 데이터는 삭제
      const retentionMs = this.NEWS_RETENTION_DAYS * 24 * 60 * 60 * 1000;
      const isExpired = Date.now() - data.timestamp > retentionMs;

      if (isExpired) {
        console.log('[Monitoring] LocalStorage: 만료된 데이터 삭제');
        localStorage.removeItem(this.PROCESSED_NEWS_KEY);
        return new Set();
      }

      console.log(`[Monitoring] LocalStorage: ${data.ids.length}개 뉴스 ID 로드`);
      return new Set(data.ids);
    } catch (error) {
      console.error('[Monitoring] LocalStorage 로드 오류:', error);
      return new Set();
    }
  }

  /**
   * LocalStorage에 처리된 뉴스 ID 저장
   */
  private saveProcessedNewsIds(): void {
    try {
      const data = {
        ids: Array.from(this.processedNewsIds),
        timestamp: Date.now(),
      };

      localStorage.setItem(this.PROCESSED_NEWS_KEY, JSON.stringify(data));
      console.log(`[Monitoring] LocalStorage: ${data.ids.length}개 뉴스 ID 저장`);
    } catch (error) {
      console.error('[Monitoring] LocalStorage 저장 오류:', error);
    }
  }

  /**
   * 종목 코드에서 종목명 해석
   */
  private getStockName(symbol: string): string {
    const portfolioStore = usePortfolioStore.getState();
    const watchlistStore = useWatchlistStore.getState();

    // 보유 종목에서 먼저 찾기
    const portfolioItem = portfolioStore.items.find((item: any) => item.symbol === symbol);
    if (portfolioItem) {
      return portfolioItem.symbol_name;
    }

    // 관심 종목에서 찾기
    const watchlistItem = watchlistStore.items.find((item: any) => item.symbol === symbol);
    if (watchlistItem) {
      return watchlistItem.symbol_name;
    }

    // 종목명을 찾지 못하면 종목코드 반환
    console.warn(`[Monitoring] 종목명을 찾을 수 없음: ${symbol}`);
    return symbol;
  }

  /**
   * Supabase Realtime 뉴스 구독 설정
   */
  private setupNewsRealtimeSubscription(): void {
    console.log('[Monitoring] Realtime 뉴스 구독 시작');

    this.newsChannel = supabase
      .channel('news-monitoring')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'news',
        },
        (payload) => {
          console.log('[Monitoring] 새 뉴스 INSERT 감지:', payload.new);
          this.handleNewNews(payload.new as any);
        }
      )
      .subscribe((status) => {
        console.log('[Monitoring] Realtime 구독 상태:', status);
      });
  }

  /**
   * 새로운 뉴스 처리 (Realtime 콜백)
   */
  private async handleNewNews(news: any): Promise<void> {
    if (!this.isMonitoring || !this.userId) return;

    try {
      // 중복 체크 (LocalStorage 기반)
      if (this.processedNewsIds.has(news.id)) {
        console.log('[Monitoring] 이미 처리된 뉴스:', news.id);
        return;
      }

      // 영향도 임계값 체크
      if (!news.impact_score || news.impact_score < this.alertSettings.newsThreshold) {
        console.log('[Monitoring] 낮은 영향도 뉴스 무시:', news.impact_score);
        return;
      }

      // 사용자의 관심 종목 확인
      const portfolioStore = usePortfolioStore.getState();
      const watchlistStore = useWatchlistStore.getState();
      const portfolioSymbols = portfolioStore.items.map((item: any) => item.symbol);
      const watchlistSymbols = watchlistStore.items.map((item: any) => item.symbol);
      const userSymbols = new Set([...portfolioSymbols, ...watchlistSymbols]);

      // 관련 종목 체크
      const isRelated = news.related_symbols.some((symbol: string) => userSymbols.has(symbol));
      if (!isRelated) {
        console.log('[Monitoring] 사용자와 무관한 뉴스 무시');
        return;
      }

      console.log('[Monitoring] 고영향도 뉴스 감지:', news.title);

      // 처리된 뉴스로 마킹 (LocalStorage에 저장)
      this.processedNewsIds.add(news.id);
      this.saveProcessedNewsIds();

      // 종목명 해석 (종목코드 대신 종목명 사용!)
      const primarySymbol = news.related_symbols[0] || '';
      const symbolName = this.getStockName(primarySymbol);
      const isOwned = portfolioSymbols.includes(primarySymbol);

      // 알림 생성 (모든 메타데이터 포함)
      const alert: Alert = {
        id: `news-${news.id}`,
        userId: this.userId,
        type: 'news',
        severity: 'high',
        message: `[중요 뉴스] ${news.title}`,
        symbol: primarySymbol,
        symbolName: symbolName, // 종목명 사용!
        timestamp: new Date().toISOString(),
        isRead: false,
        isOwned,
        // 뉴스 메타데이터 (Phase 2.3.3)
        newsId: news.id,
        sentimentScore: news.sentiment_score,
        impactScore: news.impact_score,
        recommendedAction: news.recommended_action,
        summary: news.summary,
      };

      // 알림 처리 (콜백 호출 + TTS 재생)
      this.handleAlert(alert);
    } catch (error) {
      console.error('[Monitoring] 뉴스 처리 오류:', error);
    }
  }
}

// Singleton 인스턴스 export
export const monitoringService = MonitoringService.getInstance();
