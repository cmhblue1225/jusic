/**
 * Alert Rules Engine
 * Phase 2.4.1: 알림 규칙 정의 및 평가 로직
 */

// ===== 알림 타입 정의 =====
export type AlertType = 'price_change' | 'news' | 'volume';
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';

/**
 * 알림 규칙
 */
export interface AlertRule {
  type: AlertType;
  threshold: number; // 임계값 (가격 변동: %, 뉴스 영향도: 0~1, 거래량: 배수)
  enabled: boolean;
}

/**
 * 사용자 알림 설정
 */
export interface UserAlertSettings {
  priceChangeEnabled: boolean;
  priceChangeThreshold: number; // 기본값: 3 (%)
  newsEnabled: boolean;
  newsThreshold: number; // 기본값: 0.7 (뉴스 영향도)
  volumeEnabled: boolean;
  volumeThreshold: number; // 기본값: 2 (배수)
  marketHoursOnly: boolean; // 장중만 알림
}

/**
 * 알림 데이터
 */
export interface Alert {
  id: string;
  userId: string;
  symbol: string;
  symbolName: string;
  type: AlertType;
  severity: AlertSeverity;
  message: string;
  currentPrice?: number;
  previousPrice?: number;
  priceChange?: number;
  priceChangeRate?: number;
  timestamp: string;
  isRead: boolean;
  isOwned: boolean; // 보유 종목 여부
}

/**
 * 가격 변동 데이터
 */
export interface PriceChangeData {
  symbol: string;
  symbolName: string;
  currentPrice: number;
  previousPrice: number;
  changeRate: number;
}

/**
 * 거래량 변동 데이터
 */
export interface VolumeChangeData {
  symbol: string;
  symbolName: string;
  currentVolume: number;
  avgVolume: number;
  volumeRatio: number;
}

// ===== 기본 설정 =====
export const DEFAULT_ALERT_SETTINGS: UserAlertSettings = {
  priceChangeEnabled: true,
  priceChangeThreshold: 3.0,
  newsEnabled: true,
  newsThreshold: 0.7,
  volumeEnabled: true,
  volumeThreshold: 2.0,
  marketHoursOnly: true,
};

// ===== 장중 시간 확인 =====
/**
 * 현재 시간이 장중인지 확인
 * 평일 09:00 ~ 15:30
 */
export function isMarketHours(): boolean {
  const now = new Date();
  const day = now.getDay(); // 0(일요일) ~ 6(토요일)
  const hours = now.getHours();
  const minutes = now.getMinutes();

  // 주말 체크
  if (day === 0 || day === 6) {
    return false;
  }

  // 평일 09:00 ~ 15:30
  const currentMinutes = hours * 60 + minutes;
  const marketOpen = 9 * 60; // 09:00
  const marketClose = 15 * 60 + 30; // 15:30

  return currentMinutes >= marketOpen && currentMinutes <= marketClose;
}

// ===== 알림 평가 함수 =====

/**
 * 가격 변동 알림 평가
 * @param currentPrice 현재가
 * @param previousPrice 이전가
 * @param threshold 임계값 (%)
 * @returns 알림 발생 여부
 */
export function evaluatePriceChange(
  currentPrice: number,
  previousPrice: number,
  threshold: number
): boolean {
  if (previousPrice === 0) return false;

  const changeRate = ((currentPrice - previousPrice) / previousPrice) * 100;
  return Math.abs(changeRate) >= threshold;
}

/**
 * 거래량 급증 알림 평가
 * @param currentVolume 현재 거래량
 * @param avgVolume 평균 거래량
 * @param threshold 임계값 (배수)
 * @returns 알림 발생 여부
 */
export function evaluateVolume(
  currentVolume: number,
  avgVolume: number,
  threshold: number
): boolean {
  if (avgVolume === 0) return false;

  const volumeRatio = currentVolume / avgVolume;
  return volumeRatio >= threshold;
}

/**
 * 뉴스 영향도 알림 평가
 * @param newsImpact 뉴스 영향도 (0~1)
 * @param threshold 임계값 (0~1)
 * @returns 알림 발생 여부
 */
export function evaluateNewsImpact(newsImpact: number, threshold: number): boolean {
  return newsImpact >= threshold;
}

// ===== 심각도 계산 =====

/**
 * 가격 변동률에 따른 심각도 계산
 * @param changeRate 가격 변동률 (%)
 * @returns 심각도
 */
export function calculatePriceSeverity(changeRate: number): AlertSeverity {
  const absChangeRate = Math.abs(changeRate);

  if (absChangeRate >= 10) return 'critical';
  if (absChangeRate >= 5) return 'high';
  if (absChangeRate >= 3) return 'medium';
  return 'low';
}

/**
 * 거래량 배수에 따른 심각도 계산
 * @param volumeRatio 거래량 배수
 * @returns 심각도
 */
export function calculateVolumeSeverity(volumeRatio: number): AlertSeverity {
  if (volumeRatio >= 5) return 'critical';
  if (volumeRatio >= 3) return 'high';
  if (volumeRatio >= 2) return 'medium';
  return 'low';
}

/**
 * 뉴스 영향도에 따른 심각도 계산
 * @param newsImpact 뉴스 영향도 (0~1)
 * @returns 심각도
 */
export function calculateNewsSeverity(newsImpact: number): AlertSeverity {
  if (newsImpact >= 0.9) return 'critical';
  if (newsImpact >= 0.8) return 'high';
  if (newsImpact >= 0.7) return 'medium';
  return 'low';
}

// ===== 알림 생성 =====

/**
 * 가격 변동 알림 생성
 */
export function createPriceChangeAlert(
  userId: string,
  data: PriceChangeData,
  isOwned: boolean
): Alert {
  const changeRate = data.changeRate;
  const severity = calculatePriceSeverity(changeRate);
  const direction = changeRate > 0 ? '상승' : '하락';
  const absChangeRate = Math.abs(changeRate).toFixed(2);

  const message = `${data.symbolName} ${absChangeRate}% ${direction}`;

  return {
    id: `${userId}-${data.symbol}-${Date.now()}`,
    userId,
    symbol: data.symbol,
    symbolName: data.symbolName,
    type: 'price_change',
    severity,
    message,
    currentPrice: data.currentPrice,
    previousPrice: data.previousPrice,
    priceChange: data.currentPrice - data.previousPrice,
    priceChangeRate: changeRate,
    timestamp: new Date().toISOString(),
    isRead: false,
    isOwned,
  };
}

/**
 * 거래량 급증 알림 생성
 */
export function createVolumeAlert(
  userId: string,
  data: VolumeChangeData,
  isOwned: boolean
): Alert {
  const severity = calculateVolumeSeverity(data.volumeRatio);
  const message = `${data.symbolName} 거래량 ${data.volumeRatio.toFixed(1)}배 급증`;

  return {
    id: `${userId}-${data.symbol}-${Date.now()}`,
    userId,
    symbol: data.symbol,
    symbolName: data.symbolName,
    type: 'volume',
    severity,
    message,
    timestamp: new Date().toISOString(),
    isRead: false,
    isOwned,
  };
}

// ===== 알림 필터링 =====

/**
 * 사용자 설정에 따라 알림 발생 여부 확인
 */
export function shouldTriggerAlert(
  alertType: AlertType,
  settings: UserAlertSettings
): boolean {
  // 장중만 알림 설정이 켜져 있으면 장중 시간 체크
  if (settings.marketHoursOnly && !isMarketHours()) {
    return false;
  }

  // 알림 타입별 활성화 체크
  switch (alertType) {
    case 'price_change':
      return settings.priceChangeEnabled;
    case 'news':
      return settings.newsEnabled;
    case 'volume':
      return settings.volumeEnabled;
    default:
      return false;
  }
}

/**
 * 중복 알림 방지 (같은 종목, 같은 타입, 5분 이내)
 */
export function isDuplicateAlert(
  newAlert: Alert,
  recentAlerts: Alert[],
  timeWindowMs: number = 5 * 60 * 1000 // 5분
): boolean {
  const newAlertTime = new Date(newAlert.timestamp).getTime();

  return recentAlerts.some((alert) => {
    const alertTime = new Date(alert.timestamp).getTime();
    const timeDiff = newAlertTime - alertTime;

    return (
      alert.symbol === newAlert.symbol &&
      alert.type === newAlert.type &&
      timeDiff < timeWindowMs
    );
  });
}
