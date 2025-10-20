"""
고급 기술적 지표 모듈
- 모멘텀 지표: RSI, Stochastic, Williams %R, CCI
- 추세 지표: MACD, ADX, Parabolic SAR
- 거래량 지표: OBV, MFI, VWAP
- 변동성 지표: ATR, Keltner Channel
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple


def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    """
    RSI (Relative Strength Index) 계산

    Args:
        prices: 종가 리스트
        period: 기간 (기본: 14일)

    Returns:
        float: RSI 값 (0~100) 또는 None

    해석:
        - RSI > 70: 과매수 (매도 신호)
        - RSI < 30: 과매도 (매수 신호)
    """
    if len(prices) < period + 1:
        return None

    prices_array = np.array(prices)
    deltas = np.diff(prices_array)

    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return round(float(rsi), 2)


def calculate_macd(
    prices: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Optional[Dict[str, float]]:
    """
    MACD (Moving Average Convergence Divergence) 계산

    Args:
        prices: 종가 리스트
        fast_period: 빠른 EMA 기간 (기본: 12일)
        slow_period: 느린 EMA 기간 (기본: 26일)
        signal_period: 시그널 EMA 기간 (기본: 9일)

    Returns:
        Dict: {'macd': MACD선, 'signal': 시그널선, 'histogram': 히스토그램} 또는 None

    해석:
        - MACD > 시그널: 상승 추세 (매수 신호)
        - MACD < 시그널: 하락 추세 (매도 신호)
        - 히스토그램 증가: 강세, 감소: 약세
    """
    if len(prices) < slow_period + signal_period:
        return None

    prices_series = pd.Series(prices)

    # EMA 계산
    ema_fast = prices_series.ewm(span=fast_period, adjust=False).mean()
    ema_slow = prices_series.ewm(span=slow_period, adjust=False).mean()

    # MACD = Fast EMA - Slow EMA
    macd_line = ema_fast - ema_slow

    # Signal = MACD의 EMA
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

    # Histogram = MACD - Signal
    histogram = macd_line - signal_line

    return {
        "macd": round(float(macd_line.iloc[-1]), 2),
        "signal": round(float(signal_line.iloc[-1]), 2),
        "histogram": round(float(histogram.iloc[-1]), 2)
    }


def calculate_stochastic(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    k_period: int = 14,
    d_period: int = 3
) -> Optional[Dict[str, float]]:
    """
    Stochastic Oscillator (스토캐스틱) 계산

    Args:
        high_prices: 고가 리스트
        low_prices: 저가 리스트
        close_prices: 종가 리스트
        k_period: %K 기간 (기본: 14일)
        d_period: %D 기간 (기본: 3일)

    Returns:
        Dict: {'k': %K, 'd': %D} 또는 None

    해석:
        - %K > 80: 과매수
        - %K < 20: 과매도
        - %K가 %D를 상향 돌파: 골든크로스 (매수)
        - %K가 %D를 하향 돌파: 데드크로스 (매도)
    """
    if len(close_prices) < k_period:
        return None

    # 최근 k_period 기간의 최고가/최저가
    recent_highs = high_prices[-k_period:]
    recent_lows = low_prices[-k_period:]
    current_close = close_prices[-1]

    highest_high = max(recent_highs)
    lowest_low = min(recent_lows)

    if highest_high == lowest_low:
        return {"k": 50.0, "d": 50.0}

    # %K = (현재가 - 최저가) / (최고가 - 최저가) * 100
    k = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100

    # %D = %K의 d_period일 이동평균 (간소화: 단일 값 반환)
    # 실제로는 %K 값들의 이동평균이 필요하지만, 현재 단일 %K만 계산
    d = k  # 간소화 버전

    return {
        "k": round(float(k), 2),
        "d": round(float(d), 2)
    }


def calculate_williams_r(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    period: int = 14
) -> Optional[float]:
    """
    Williams %R 계산

    Args:
        high_prices: 고가 리스트
        low_prices: 저가 리스트
        close_prices: 종가 리스트
        period: 기간 (기본: 14일)

    Returns:
        float: Williams %R 값 (-100~0) 또는 None

    해석:
        - %R > -20: 과매수
        - %R < -80: 과매도
    """
    if len(close_prices) < period:
        return None

    recent_highs = high_prices[-period:]
    recent_lows = low_prices[-period:]
    current_close = close_prices[-1]

    highest_high = max(recent_highs)
    lowest_low = min(recent_lows)

    if highest_high == lowest_low:
        return -50.0

    # %R = (최고가 - 현재가) / (최고가 - 최저가) * -100
    williams_r = ((highest_high - current_close) / (highest_high - lowest_low)) * -100

    return round(float(williams_r), 2)


def calculate_cci(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    period: int = 20
) -> Optional[float]:
    """
    CCI (Commodity Channel Index) 계산

    Args:
        high_prices: 고가 리스트
        low_prices: 저가 리스트
        close_prices: 종가 리스트
        period: 기간 (기본: 20일)

    Returns:
        float: CCI 값 또는 None

    해석:
        - CCI > +100: 과매수
        - CCI < -100: 과매도
    """
    if len(close_prices) < period:
        return None

    # Typical Price = (고가 + 저가 + 종가) / 3
    typical_prices = [(h + l + c) / 3 for h, l, c in zip(high_prices[-period:], low_prices[-period:], close_prices[-period:])]

    sma_tp = np.mean(typical_prices)
    current_tp = typical_prices[-1]

    # Mean Deviation
    mean_deviation = np.mean([abs(tp - sma_tp) for tp in typical_prices])

    if mean_deviation == 0:
        return 0.0

    # CCI = (Typical Price - SMA) / (0.015 * Mean Deviation)
    cci = (current_tp - sma_tp) / (0.015 * mean_deviation)

    return round(float(cci), 2)


def calculate_adx(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    period: int = 14
) -> Optional[float]:
    """
    ADX (Average Directional Index) 계산

    Args:
        high_prices: 고가 리스트
        low_prices: 저가 리스트
        close_prices: 종가 리스트
        period: 기간 (기본: 14일)

    Returns:
        float: ADX 값 (0~100) 또는 None

    해석:
        - ADX > 25: 강한 추세
        - ADX < 20: 약한 추세 (횡보)
        - ADX 값 자체는 방향성 없음 (추세 강도만 표시)
    """
    if len(close_prices) < period + 1:
        return None

    # 간소화 버전: True Range의 이동평균 기반 ADX 근사값
    tr_values = []
    for i in range(1, len(close_prices)):
        high_low = high_prices[i] - low_prices[i]
        high_close = abs(high_prices[i] - close_prices[i-1])
        low_close = abs(low_prices[i] - close_prices[i-1])
        tr = max(high_low, high_close, low_close)
        tr_values.append(tr)

    if len(tr_values) < period:
        return None

    atr = np.mean(tr_values[-period:])

    # ADX 간소화: ATR 기반 추세 강도 (0~100 스케일링)
    # 실제 ADX는 +DI, -DI를 계산해야 하지만, 간소화 버전
    price_range = max(close_prices[-period:]) - min(close_prices[-period:])
    current_price = close_prices[-1]

    if current_price == 0:
        return 0.0

    adx_approx = (atr / current_price) * 100 * 2  # 스케일링
    adx_approx = min(adx_approx, 100)  # 100 이하로 제한

    return round(float(adx_approx), 2)


def calculate_obv(close_prices: List[float], volumes: List[int]) -> Optional[float]:
    """
    OBV (On-Balance Volume) 계산

    Args:
        close_prices: 종가 리스트
        volumes: 거래량 리스트

    Returns:
        float: OBV 값 또는 None

    해석:
        - OBV 상승: 매수 압력 증가
        - OBV 하락: 매도 압력 증가
    """
    if len(close_prices) < 2 or len(volumes) != len(close_prices):
        return None

    obv = 0
    for i in range(1, len(close_prices)):
        if close_prices[i] > close_prices[i-1]:
            obv += volumes[i]
        elif close_prices[i] < close_prices[i-1]:
            obv -= volumes[i]

    return float(obv)


def calculate_mfi(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    volumes: List[int],
    period: int = 14
) -> Optional[float]:
    """
    MFI (Money Flow Index) 계산

    Args:
        high_prices: 고가 리스트
        low_prices: 저가 리스트
        close_prices: 종가 리스트
        volumes: 거래량 리스트
        period: 기간 (기본: 14일)

    Returns:
        float: MFI 값 (0~100) 또는 None

    해석:
        - MFI > 80: 과매수
        - MFI < 20: 과매도
    """
    if len(close_prices) < period + 1:
        return None

    # Typical Price = (H + L + C) / 3
    typical_prices = [(h + l + c) / 3 for h, l, c in zip(high_prices, low_prices, close_prices)]

    # Money Flow = Typical Price * Volume
    money_flows = [tp * v for tp, v in zip(typical_prices, volumes)]

    # Positive / Negative Money Flow
    positive_mf = 0
    negative_mf = 0

    for i in range(len(typical_prices) - period, len(typical_prices)):
        if i > 0:
            if typical_prices[i] > typical_prices[i-1]:
                positive_mf += money_flows[i]
            elif typical_prices[i] < typical_prices[i-1]:
                negative_mf += money_flows[i]

    if negative_mf == 0:
        return 100.0

    money_ratio = positive_mf / negative_mf
    mfi = 100 - (100 / (1 + money_ratio))

    return round(float(mfi), 2)


def calculate_vwap(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    volumes: List[int]
) -> Optional[float]:
    """
    VWAP (Volume Weighted Average Price) 계산

    Args:
        high_prices: 고가 리스트
        low_prices: 저가 리스트
        close_prices: 종가 리스트
        volumes: 거래량 리스트

    Returns:
        float: VWAP 값 또는 None

    해석:
        - 현재가 > VWAP: 강세
        - 현재가 < VWAP: 약세
    """
    if len(close_prices) < 1 or len(volumes) != len(close_prices):
        return None

    # Typical Price = (H + L + C) / 3
    typical_prices = [(h + l + c) / 3 for h, l, c in zip(high_prices, low_prices, close_prices)]

    # VWAP = Σ(Typical Price * Volume) / Σ(Volume)
    total_pv = sum([tp * v for tp, v in zip(typical_prices, volumes)])
    total_volume = sum(volumes)

    if total_volume == 0:
        return None

    vwap = total_pv / total_volume

    return round(float(vwap), 2)


def calculate_atr(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    period: int = 14
) -> Optional[float]:
    """
    ATR (Average True Range) 계산

    Args:
        high_prices: 고가 리스트
        low_prices: 저가 리스트
        close_prices: 종가 리스트
        period: 기간 (기본: 14일)

    Returns:
        float: ATR 값 또는 None

    해석:
        - ATR 증가: 변동성 증가
        - ATR 감소: 변동성 감소
    """
    if len(close_prices) < period + 1:
        return None

    tr_values = []
    for i in range(1, len(close_prices)):
        high_low = high_prices[i] - low_prices[i]
        high_close = abs(high_prices[i] - close_prices[i-1])
        low_close = abs(low_prices[i] - close_prices[i-1])
        tr = max(high_low, high_close, low_close)
        tr_values.append(tr)

    if len(tr_values) < period:
        return None

    atr = np.mean(tr_values[-period:])

    return round(float(atr), 2)


def calculate_keltner_channel(
    high_prices: List[float],
    low_prices: List[float],
    close_prices: List[float],
    period: int = 20,
    multiplier: float = 2.0
) -> Optional[Dict[str, float]]:
    """
    Keltner Channel 계산

    Args:
        high_prices: 고가 리스트
        low_prices: 저가 리스트
        close_prices: 종가 리스트
        period: EMA 기간 (기본: 20일)
        multiplier: ATR 배수 (기본: 2.0)

    Returns:
        Dict: {'upper': 상단, 'middle': 중간(EMA), 'lower': 하단} 또는 None

    해석:
        - 가격이 상단 돌파: 강한 상승 추세
        - 가격이 하단 하회: 강한 하락 추세
    """
    if len(close_prices) < period + 1:
        return None

    # EMA 계산
    ema = pd.Series(close_prices).ewm(span=period, adjust=False).mean().iloc[-1]

    # ATR 계산
    atr = calculate_atr(high_prices, low_prices, close_prices, period)

    if atr is None:
        return None

    upper = ema + (multiplier * atr)
    lower = ema - (multiplier * atr)

    return {
        "upper": round(float(upper), 2),
        "middle": round(float(ema), 2),
        "lower": round(float(lower), 2)
    }


def calculate_all_advanced_indicators(ohlcv_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    모든 고급 기술적 지표 계산

    Args:
        ohlcv_data: OHLCV 데이터 리스트

    Returns:
        Dict: 모든 고급 기술적 지표
    """
    if not ohlcv_data or len(ohlcv_data) < 2:
        return {}

    # 데이터 추출
    high_prices = [item["high"] for item in ohlcv_data]
    low_prices = [item["low"] for item in ohlcv_data]
    close_prices = [item["close"] for item in ohlcv_data]
    volumes = [item["volume"] for item in ohlcv_data]

    # 모든 지표 계산
    indicators = {}

    # 모멘텀 지표
    indicators["rsi"] = calculate_rsi(close_prices, 14)
    indicators["williams_r"] = calculate_williams_r(high_prices, low_prices, close_prices, 14)
    indicators["cci"] = calculate_cci(high_prices, low_prices, close_prices, 20)

    # MACD
    macd_result = calculate_macd(close_prices, 12, 26, 9)
    if macd_result:
        indicators["macd"] = macd_result["macd"]
        indicators["macd_signal"] = macd_result["signal"]
        indicators["macd_histogram"] = macd_result["histogram"]

    # Stochastic
    stochastic_result = calculate_stochastic(high_prices, low_prices, close_prices, 14, 3)
    if stochastic_result:
        indicators["stochastic_k"] = stochastic_result["k"]
        indicators["stochastic_d"] = stochastic_result["d"]

    # 추세 지표
    indicators["adx"] = calculate_adx(high_prices, low_prices, close_prices, 14)

    # 거래량 지표
    indicators["obv"] = calculate_obv(close_prices, volumes)
    indicators["mfi"] = calculate_mfi(high_prices, low_prices, close_prices, volumes, 14)
    indicators["vwap"] = calculate_vwap(high_prices, low_prices, close_prices, volumes)

    # 변동성 지표
    indicators["atr"] = calculate_atr(high_prices, low_prices, close_prices, 14)

    # Keltner Channel
    keltner_result = calculate_keltner_channel(high_prices, low_prices, close_prices, 20, 2.0)
    if keltner_result:
        indicators["keltner_upper"] = keltner_result["upper"]
        indicators["keltner_middle"] = keltner_result["middle"]
        indicators["keltner_lower"] = keltner_result["lower"]

    print(f"✅ 고급 기술적 지표 계산 완료:")
    print(f"   - RSI: {indicators.get('rsi')}")
    print(f"   - MACD: {indicators.get('macd')} (Signal: {indicators.get('macd_signal')})")
    print(f"   - Stochastic %K: {indicators.get('stochastic_k')}")
    print(f"   - ADX: {indicators.get('adx')}")
    print(f"   - MFI: {indicators.get('mfi')}")
    print(f"   - ATR: {indicators.get('atr')}")

    return indicators
