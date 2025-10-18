/**
 * TTS (Text-to-Speech) 유틸리티
 * Phase 2.4.2: Web Speech API를 사용한 음성 알림 시스템
 */

import type { Alert } from './alertRules';
import type { PortfolioWithProfit } from './profitCalculator';

export interface TTSOptions {
  lang?: string;
  rate?: number;  // 0.1 ~ 10 (기본 1)
  pitch?: number; // 0 ~ 2 (기본 1)
  volume?: number; // 0 ~ 1 (기본 1)
}

/**
 * TTS 설정 (Phase 2.4)
 */
export interface TTSConfig {
  enabled: boolean;
  rate: number; // 속도 (0.8 ~ 1.2)
  pitch: number; // 음높이 (0.8 ~ 1.2)
  volume: number; // 볼륨 (0.5 ~ 1.0)
  lang: string; // 언어 (기본값: 'ko-KR')
  autoPlayThreshold: number; // 자동 재생 임계값 (0.5/0.7/0.9)
}

export const DEFAULT_TTS_CONFIG: TTSConfig = {
  enabled: true,
  rate: 1.0,
  pitch: 1.0,
  volume: 1.0,
  lang: 'ko-KR',
  autoPlayThreshold: 0.7,
};

/**
 * TTS 메시지 큐 아이템
 */
interface TTSQueueItem {
  id: string;
  text: string;
  config: TTSConfig;
}

class TTSService {
  private synth: SpeechSynthesis;
  private isSpeaking: boolean = false;
  private queue: TTSQueueItem[] = [];
  private isProcessingQueue: boolean = false;

  constructor() {
    if (!('speechSynthesis' in window)) {
      console.warn('Speech Synthesis API not supported');
    }
    this.synth = window.speechSynthesis;
  }

  /**
   * 음성 합성 지원 여부 확인
   */
  public static isSupported(): boolean {
    return 'speechSynthesis' in window;
  }

  /**
   * 텍스트 음성 변환 (기존 호환성 유지)
   */
  speak(text: string, options: TTSOptions = {}) {
    // 기존 음성 중지
    this.stop();

    if (!this.synth) {
      console.warn('Speech Synthesis API not supported');
      return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = options.lang || 'ko-KR';
    utterance.rate = options.rate || 0.9;
    utterance.pitch = options.pitch || 1.0;
    utterance.volume = options.volume || 1.0;

    utterance.onstart = () => {
      this.isSpeaking = true;
    };

    utterance.onend = () => {
      this.isSpeaking = false;
    };

    utterance.onerror = (error) => {
      console.error('TTS Error:', error);
      this.isSpeaking = false;
    };

    this.synth.speak(utterance);
  }

  /**
   * 텍스트를 음성으로 변환하여 큐에 추가 (Phase 2.4)
   * @param text 재생할 텍스트
   * @param config TTS 설정
   * @returns Promise<void>
   */
  public async speakQueued(text: string, config: TTSConfig = DEFAULT_TTS_CONFIG): Promise<void> {
    if (!config.enabled) {
      console.log('[TTS] TTS가 비활성화되어 있습니다.');
      return;
    }

    if (!this.synth) {
      console.warn('[TTS] Speech Synthesis API가 지원되지 않습니다.');
      return;
    }

    // 큐에 추가
    const queueItem: TTSQueueItem = {
      id: `${Date.now()}-${Math.random()}`,
      text,
      config,
    };

    this.queue.push(queueItem);
    console.log(`[TTS] 큐에 추가: "${text}" (큐 길이: ${this.queue.length})`);

    // 재생 중이 아니면 재생 시작
    if (!this.isProcessingQueue) {
      await this.processQueue();
    }
  }

  /**
   * 큐를 순차적으로 처리
   */
  private async processQueue(): Promise<void> {
    if (this.queue.length === 0) {
      this.isProcessingQueue = false;
      return;
    }

    this.isProcessingQueue = true;
    const item = this.queue.shift()!;

    console.log(`[TTS] 재생 시작: "${item.text}"`);

    try {
      await this.speakSingle(item.text, item.config);
    } catch (error) {
      console.error('[TTS] 재생 오류:', error);
    }

    // 다음 항목 처리
    await this.processQueue();
  }

  /**
   * 단일 텍스트 재생
   */
  private speakSingle(text: string, config: TTSConfig): Promise<void> {
    return new Promise((resolve, reject) => {
      const utterance = new SpeechSynthesisUtterance(text);

      utterance.lang = config.lang;
      utterance.rate = config.rate;
      utterance.pitch = config.pitch;
      utterance.volume = config.volume;

      utterance.onstart = () => {
        this.isSpeaking = true;
        console.log(`[TTS] 재생 중: "${text}"`);
      };

      utterance.onend = () => {
        this.isSpeaking = false;
        console.log(`[TTS] 재생 완료: "${text}"`);
        resolve();
      };

      utterance.onerror = (event) => {
        this.isSpeaking = false;
        console.error(`[TTS] 재생 오류:`, event);
        reject(event);
      };

      this.synth.speak(utterance);
    });
  }

  /**
   * 음성 중지
   */
  stop() {
    if (this.synth && this.synth.speaking) {
      this.synth.cancel();
      this.queue = [];
      this.isSpeaking = false;
      this.isProcessingQueue = false;
      console.log('[TTS] 재생 중지 및 큐 초기화');
    }
  }

  /**
   * 일시 정지
   */
  pause() {
    if (this.synth && this.isSpeaking) {
      this.synth.pause();
      console.log('[TTS] 일시 정지');
    }
  }

  /**
   * 재개
   */
  resume() {
    if (this.synth && this.synth.paused) {
      this.synth.resume();
      console.log('[TTS] 재개');
    }
  }

  /**
   * 현재 말하고 있는지 확인
   */
  get speaking(): boolean {
    return this.isSpeaking;
  }

  /**
   * 큐 길이 반환
   */
  public getQueueLength(): number {
    return this.queue.length;
  }

  /**
   * 큐 초기화
   */
  public clearQueue(): void {
    this.queue = [];
    console.log('[TTS] 큐 초기화');
  }

  // ===== Alert 메시지 생성 (Phase 2.4) =====

  /**
   * Alert 객체에서 TTS 메시지 생성
   * @param alert 알림 데이터
   * @param portfolio 포트폴리오 데이터 (수익률 계산용)
   * @returns TTS 메시지
   */
  public generateAlertMessage(
    alert: Alert,
    portfolio?: PortfolioWithProfit[]
  ): string {
    const { symbolName, type, isOwned, currentPrice, priceChangeRate } = alert;

    // 보유 종목인지 확인
    const ownedStock = portfolio?.find((item) => item.symbol === alert.symbol);

    switch (type) {
      case 'price_change':
        return this.generatePriceChangeMessage(
          symbolName,
          isOwned,
          currentPrice,
          priceChangeRate,
          ownedStock
        );

      case 'volume':
        return this.generateVolumeMessage(symbolName, isOwned);

      case 'news':
        return this.generateNewsMessage(alert, portfolio);

      default:
        return `${symbolName} 알림이 발생했습니다.`;
    }
  }

  /**
   * 가격 변동 메시지 생성
   */
  private generatePriceChangeMessage(
    symbolName: string,
    isOwned: boolean,
    currentPrice: number | undefined,
    priceChangeRate: number | undefined,
    ownedStock?: PortfolioWithProfit
  ): string {
    if (!currentPrice || priceChangeRate === undefined) {
      return `${symbolName} 가격이 변동했습니다.`;
    }

    const direction = priceChangeRate > 0 ? '상승' : '하락';
    const absChangeRate = Math.abs(priceChangeRate).toFixed(2);
    const priceStr = this.formatPrice(currentPrice);

    if (isOwned && ownedStock) {
      // 보유 종목: 수익률 포함
      const profitDirection = ownedStock.profitRate > 0 ? '수익' : '손실';

      return `보유 종목 알림. ${symbolName}이 ${absChangeRate} 퍼센트 ${direction}했습니다. 현재가 ${priceStr}원, ${profitDirection}률 ${Math.abs(
        ownedStock.profitRate
      ).toFixed(2)} 퍼센트입니다.`;
    } else {
      // 관심 종목: 가격만 표시
      return `관심 종목 알림. ${symbolName}이 ${absChangeRate} 퍼센트 ${direction}했습니다. 현재가 ${priceStr}원입니다.`;
    }
  }

  /**
   * 거래량 급증 메시지 생성
   */
  private generateVolumeMessage(symbolName: string, isOwned: boolean): string {
    const prefix = isOwned ? '보유 종목' : '관심 종목';
    return `${prefix} 알림. ${symbolName}의 거래량이 급증했습니다.`;
  }

  /**
   * 뉴스 메시지 생성 (Phase 2.3.3 고도화)
   * @param alert 알림 데이터 (뉴스 메타데이터 포함)
   * @param portfolio 포트폴리오 데이터
   */
  private generateNewsMessage(alert: Alert, portfolio?: PortfolioWithProfit[]): string {
    const { symbolName, isOwned, sentimentScore, impactScore, recommendedAction, summary } = alert;

    const prefix = isOwned ? '보유 종목' : '관심 종목';
    let message = `${prefix} 중요 뉴스입니다. ${symbolName}에 대한 뉴스입니다. `;

    // 감성 점수 텍스트 변환
    if (sentimentScore !== undefined && sentimentScore !== null) {
      const sentimentText = this.getSentimentText(sentimentScore);
      message += `${sentimentText} 감정, `;
    }

    // 영향도
    if (impactScore !== undefined && impactScore !== null) {
      const impactPercent = Math.round(impactScore * 100);
      message += `영향도 ${impactPercent}%, `;
    }

    // 권고 액션
    if (recommendedAction) {
      const actionText = this.getActionText(recommendedAction);
      message += `${actionText}. `;
    }

    // 요약 (있으면 추가)
    if (summary) {
      message += summary;
    }

    return message;
  }

  /**
   * 감성 점수를 텍스트로 변환
   */
  private getSentimentText(score: number): string {
    if (score > 0.5) return '매우 긍정적';
    if (score > 0.2) return '긍정적';
    if (score > -0.2) return '중립';
    if (score > -0.5) return '부정적';
    return '매우 부정적';
  }

  /**
   * 권고 액션을 텍스트로 변환
   */
  private getActionText(action: string): string {
    if (action === 'buy') return '매수 권고';
    if (action === 'sell') return '매도 권고';
    if (action === 'hold') return '보유 권고';
    return '대기';
  }

  /**
   * 가격 포맷팅 (천단위 콤마)
   */
  private formatPrice(price: number): string {
    return price.toLocaleString('ko-KR');
  }

  /**
   * 테스트 메시지 재생
   */
  public async speakTestMessage(config: TTSConfig = DEFAULT_TTS_CONFIG): Promise<void> {
    const testMessage = '음성 알림 테스트입니다. 삼성전자가 3.5 퍼센트 상승했습니다.';
    await this.speakQueued(testMessage, config);
  }
}

export const ttsService = new TTSService();

// 편의 함수 export
export const speak = (text: string, options?: TTSOptions) => ttsService.speak(text, options);
export const cancel = () => ttsService.stop();
export const pause = () => ttsService.pause();
export const resume = () => ttsService.resume();
