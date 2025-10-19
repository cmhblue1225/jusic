"""
기술적 지표 계산 모듈
- 이동평균선 (5일, 20일, 60일)
- 거래량 비율
- 변동성 (표준편차)
- 볼린저 밴드
"""
import numpy as np
from typing import List, Dict, Any, Optional


def calculate_moving_average(prices: List[float], period: int) -> Optional[float]:
    """
    이동평균선 계산

    Args:
        prices: 종가 리스트 (최신 데이터가 마지막)
        period: 기간 (예: 5일, 20일, 60일)

    Returns:
        float: 이동평균 값 또는 None (데이터 부족 시)
    """
    if len(prices) < period:
        return None

    # 최근 period일 평균
    recent_prices = prices[-period:]
    return float(np.mean(recent_prices))


def calculate_volume_ratio(volumes: List[int], period: int = 20) -> Optional[float]:
    """
    거래량 비율 계산

    Args:
        volumes: 거래량 리스트 (최신 데이터가 마지막)
        period: 평균 계산 기간 (기본: 20일)

    Returns:
        float: 거래량 비율 (당일 거래량 / 평균 거래량) 또는 None
    """
    if len(volumes) < period + 1:
        return None

    # 최근 period일 평균 거래량 (당일 제외)
    avg_volume = np.mean(volumes[-(period + 1):-1])

    if avg_volume == 0:
        return None

    # 당일 거래량 / 평균 거래량
    current_volume = volumes[-1]
    return float(current_volume / avg_volume)


def calculate_volatility(prices: List[float], period: int = 20) -> Optional[float]:
    """
    변동성 계산 (표준편차)

    Args:
        prices: 종가 리스트 (최신 데이터가 마지막)
        period: 계산 기간 (기본: 20일)

    Returns:
        float: 변동성 (표준편차) 또는 None
    """
    if len(prices) < period:
        return None

    # 최근 period일 종가의 표준편차
    recent_prices = prices[-period:]
    return float(np.std(recent_prices))


def calculate_bollinger_bands(prices: List[float], period: int = 20, num_std: float = 2.0) -> Optional[Dict[str, float]]:
    """
    볼린저 밴드 계산

    Args:
        prices: 종가 리스트 (최신 데이터가 마지막)
        period: 이동평균 기간 (기본: 20일)
        num_std: 표준편차 배수 (기본: 2.0)

    Returns:
        Dict: 볼린저 밴드 {'upper': 상단, 'middle': 중간(이동평균), 'lower': 하단} 또는 None
    """
    if len(prices) < period:
        return None

    # 최근 period일 데이터
    recent_prices = prices[-period:]

    middle = np.mean(recent_prices)  # 중간선 (이동평균)
    std = np.std(recent_prices)      # 표준편차

    upper = middle + (num_std * std)  # 상단 밴드
    lower = middle - (num_std * std)  # 하단 밴드

    return {
        "upper": float(upper),
        "middle": float(middle),
        "lower": float(lower)
    }


def calculate_all_indicators(ohlcv_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    모든 기술적 지표 계산

    Args:
        ohlcv_data: OHLCV 데이터 리스트
            - date: 날짜
            - open: 시가
            - high: 고가
            - low: 저가
            - close: 종가
            - volume: 거래량

    Returns:
        Dict: 모든 기술적 지표
            - current_price: 당일 종가
            - change_rate: 등락률 (%)
            - high: 당일 고가
            - low: 당일 저가
            - avg: 당일 평균가
            - volume: 당일 거래량
            - ma5: 5일 이동평균
            - ma20: 20일 이동평균
            - ma60: 60일 이동평균
            - volume_ratio: 거래량 비율
            - volatility: 변동성 (표준편차)
            - bollinger_upper: 볼린저 상단
            - bollinger_lower: 볼린저 하단
    """
    if not ohlcv_data:
        raise ValueError("OHLCV 데이터가 비어 있습니다")

    # 종가 및 거래량 추출
    close_prices = [item["close"] for item in ohlcv_data]
    volumes = [item["volume"] for item in ohlcv_data]

    # 최신(당일) 데이터
    latest = ohlcv_data[-1]

    # 등락률 계산 (전일 대비)
    if len(close_prices) >= 2:
        prev_close = close_prices[-2]
        change_rate = ((latest["close"] - prev_close) / prev_close) * 100
    else:
        change_rate = 0.0

    # 당일 평균가 (고가 + 저가 + 종가) / 3
    avg_price = (latest["high"] + latest["low"] + latest["close"]) / 3

    # 기술적 지표 계산
    indicators = {
        # 기본 주가 데이터
        "current_price": latest["close"],
        "change_rate": round(change_rate, 2),
        "high": latest["high"],
        "low": latest["low"],
        "avg": round(avg_price, 2),
        "volume": latest["volume"],

        # 이동평균선
        "ma5": calculate_moving_average(close_prices, 5),
        "ma20": calculate_moving_average(close_prices, 20),
        "ma60": calculate_moving_average(close_prices, 60),

        # 거래량 비율
        "volume_ratio": calculate_volume_ratio(volumes, 20),

        # 변동성
        "volatility": calculate_volatility(close_prices, 20)
    }

    # 볼린저 밴드
    bollinger = calculate_bollinger_bands(close_prices, 20)
    if bollinger:
        indicators["bollinger_upper"] = bollinger["upper"]
        indicators["bollinger_lower"] = bollinger["lower"]
    else:
        indicators["bollinger_upper"] = None
        indicators["bollinger_lower"] = None

    # None 값을 반올림 (소수점 2자리)
    for key, value in indicators.items():
        if value is not None and key not in ["current_price", "high", "low", "avg", "volume"]:
            if isinstance(value, float):
                indicators[key] = round(value, 2)

    print(f"✅ 기술적 지표 계산 완료:")
    print(f"   - 현재가: {indicators['current_price']:,}원 ({indicators['change_rate']:+.2f}%)")
    print(f"   - MA5: {indicators['ma5']} / MA20: {indicators['ma20']} / MA60: {indicators['ma60']}")
    print(f"   - 거래량 비율: {indicators['volume_ratio']}")
    print(f"   - 변동성: {indicators['volatility']}")

    return indicators
