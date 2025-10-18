/**
 * Real-time Monitoring Service
 * Phase 2.4.2: 실시간 가격 변동 모니터링 및 자동 알림 시스템
 */

import { usePriceStore } from '../stores/priceStore';
import { usePortfolioStore } from '../stores/portfolioStore';
import { useWatchlistStore } from '../stores/watchlistStore';
import { useNewsStore } from '../stores/newsStore';
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
  private priceCheckInterval: NodeJS.Timeout | null = null;
  private newsCheckInterval: NodeJS.Timeout | null = null;
  private previousPrices: Map<string, number> = new Map(); // symbol → 이전 가격
  private processedNewsIds: Set<string> = new Set(); // 처리된 뉴스 ID
  private recentAlerts: Alert[] = []; // 최근 알림 (중복 방지용)
  private alertSettings: UserAlertSettings = DEFAULT_ALERT_SETTINGS;
  private ttsConfig: TTSConfig = DEFAULT_TTS_CONFIG;
  private onAlertCallback: ((alert: Alert) => void) | null = null;

  private constructor() {}

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

    // 고영향도 뉴스 체크 시작 (30초마다)
    this.newsCheckInterval = setInterval(() => {
      this.checkHighImpactNews();
    }, 30000);
  }

  /**
   * 모니터링 중지
   */
  public stop(): void {
    if (!this.isMonitoring) {
      console.log('[Monitoring] 모니터링이 실행 중이 아닙니다.');
      return;
    }

    if (this.priceCheckInterval) {
      clearInterval(this.priceCheckInterval);
      this.priceCheckInterval = null;
    }

    if (this.newsCheckInterval) {
      clearInterval(this.newsCheckInterval);
      this.newsCheckInterval = null;
    }

    this.isMonitoring = false;
    this.userId = null;
    this.previousPrices.clear();
    this.processedNewsIds.clear();
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
    const portfolioSymbols = portfolioStore.items.map((item) => item.symbol);
    const watchlistSymbols = watchlistStore.items.map((item) => item.symbol);
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
    portfolioStore.items.forEach((item) => {
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
   * 고영향도 뉴스 체크 (Phase 2.3: News Monitoring)
   */
  private async checkHighImpactNews(): Promise<void> {
    if (!this.isMonitoring || !this.userId) return;

    try {
      const newsStore = useNewsStore.getState();
      const portfolioStore = usePortfolioStore.getState();
      const watchlistStore = useWatchlistStore.getState();

      // 사용자의 관심 종목 코드 수집
      const portfolioSymbols = portfolioStore.items.map((item) => item.symbol);
      const watchlistSymbols = watchlistStore.items.map((item) => item.symbol);
      const userSymbols = new Set([...portfolioSymbols, ...watchlistSymbols]);

      // 모든 뉴스에서 고영향도(impact_score > 0.7) 뉴스 필터링
      const highImpactNews = newsStore.items.filter((news) => {
        // 이미 처리한 뉴스는 제외
        if (this.processedNewsIds.has(news.id)) {
          return false;
        }

        // 영향도가 0.7 이상인 뉴스만
        if (!news.impact_score || news.impact_score < 0.7) {
          return false;
        }

        // 사용자의 관심 종목과 관련된 뉴스인지 확인
        const isRelated = news.related_symbols.some((symbol) => userSymbols.has(symbol));
        return isRelated;
      });

      // 고영향도 뉴스 처리
      for (const news of highImpactNews) {
        console.log('[Monitoring] 고영향도 뉴스 감지:', news.title);

        // 처리된 뉴스로 마킹
        this.processedNewsIds.add(news.id);

        // 알림 생성
        const alert: Alert = {
          id: `news-${news.id}`,
          userId: this.userId,
          type: 'news',
          message: `[중요 뉴스] ${news.title}`,
          symbol: news.related_symbols[0] || '',
          symbolName: news.related_symbols[0] || '',
          timestamp: new Date().toISOString(),
          isPortfolio: portfolioSymbols.includes(news.related_symbols[0] || ''),
          metadata: {
            newsId: news.id,
            impactScore: news.impact_score,
            sentimentScore: news.sentiment_score,
            summary: news.summary,
            recommendedAction: news.recommended_action,
          },
        };

        // 알림 처리
        this.handleAlert(alert);

        // TTS 재생 (뉴스 전용 메시지)
        if (this.ttsConfig.enabled) {
          await this.playNewsTTS(news);
        }
      }
    } catch (error) {
      console.error('[Monitoring] 뉴스 체크 오류:', error);
    }
  }

  /**
   * 뉴스 TTS 재생
   */
  private async playNewsTTS(news: any): Promise<void> {
    try {
      // 뉴스 메시지 생성
      let message = `중요 뉴스입니다. ${news.title}. `;

      if (news.summary) {
        message += news.summary;
      }

      if (news.recommended_action) {
        const actionText =
          news.recommended_action === 'buy' ? '매수' :
          news.recommended_action === 'sell' ? '매도' : '보유';
        message += ` 권고 액션: ${actionText}`;
      }

      // TTS 재생
      await ttsService.speakQueued(message, this.ttsConfig);
    } catch (error) {
      console.error('[Monitoring] 뉴스 TTS 재생 오류:', error);
    }
  }
}

// Singleton 인스턴스 export
export const monitoringService = MonitoringService.getInstance();
