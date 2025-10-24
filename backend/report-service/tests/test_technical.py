"""
technical.py 단위 테스트

총 10개 테스트:
1. calculate_moving_average() - 정상 케이스
2. calculate_moving_average() - 데이터 부족
3. calculate_volume_ratio() - 정상 케이스
4. calculate_volume_ratio() - 데이터 부족
5. calculate_volatility() - 정상 케이스
6. calculate_volatility() - 데이터 부족
7. calculate_bollinger_bands() - 정상 케이스
8. calculate_bollinger_bands() - 데이터 부족
9. calculate_all_indicators() - 기본 지표만
10. calculate_all_indicators() - 고급 지표 포함
"""
import pytest
from typing import List, Dict, Any, Optional
from technical import (
    calculate_moving_average,
    calculate_volume_ratio,
    calculate_volatility,
    calculate_bollinger_bands,
    calculate_all_indicators
)


@pytest.mark.unit
class TestTechnicalIndicators:
    """기술적 지표 계산 모듈 테스트"""

    def test_calculate_moving_average_normal(self):
        """1. calculate_moving_average() - 정상 케이스"""
        prices = [10, 20, 30, 40, 50]  # 5개 가격
        period = 3

        result = calculate_moving_average(prices, period)

        # MA3 = (30 + 40 + 50) / 3 = 40.0
        assert result is not None
        assert isinstance(result, float)
        assert result == pytest.approx(40.0, rel=1e-2)

    def test_calculate_moving_average_insufficient_data(self):
        """2. calculate_moving_average() - 데이터 부족"""
        prices = [10, 20]  # 2개 (3개 필요)
        period = 3

        result = calculate_moving_average(prices, period)

        # 데이터 부족 시 None 반환
        assert result is None

    def test_calculate_volume_ratio_normal(self):
        """3. calculate_volume_ratio() - 정상 케이스"""
        volumes = [100000 + (i * 10000) for i in range(30)]  # 30일치
        period = 20

        result = calculate_volume_ratio(volumes, period)

        # 최근 거래량 / 평균 거래량
        assert result is not None
        assert isinstance(result, float)
        assert result > 0

        # 증가 추세 → 비율 > 1
        assert result > 1.0

    def test_calculate_volume_ratio_insufficient_data(self):
        """4. calculate_volume_ratio() - 데이터 부족"""
        volumes = [100000, 200000]  # 2개 (20개 필요)
        period = 20

        result = calculate_volume_ratio(volumes, period)

        # 데이터 부족 시 None 반환
        assert result is None

    def test_calculate_volatility_normal(self):
        """5. calculate_volatility() - 정상 케이스"""
        # 변동성 있는 가격 데이터
        prices = [100, 105, 98, 110, 95, 115, 90, 120, 85, 125] * 3  # 30개
        period = 20

        result = calculate_volatility(prices, period)

        # 표준편차 기반 변동성
        assert result is not None
        assert isinstance(result, float)
        assert result > 0
        assert result < 50  # 변동성은 일반적으로 50% 미만

    def test_calculate_volatility_insufficient_data(self):
        """6. calculate_volatility() - 데이터 부족"""
        prices = [100, 105, 98]  # 3개 (20개 필요)
        period = 20

        result = calculate_volatility(prices, period)

        # 데이터 부족 시 None 반환
        assert result is None

    def test_calculate_bollinger_bands_normal(self):
        """7. calculate_bollinger_bands() - 정상 케이스"""
        # 일정한 가격 데이터
        prices = [100 + (i % 10) for i in range(30)]  # 30개
        period = 20
        num_std = 2.0

        result = calculate_bollinger_bands(prices, period, num_std)

        # 볼린저 밴드: {upper, middle, lower}
        assert result is not None
        assert "upper" in result
        assert "middle" in result
        assert "lower" in result

        # 상단 > 중간 > 하단
        assert result["upper"] > result["middle"] > result["lower"]

        # 중간값은 MA20과 동일
        ma20 = calculate_moving_average(prices, period)
        assert result["middle"] == pytest.approx(ma20, rel=1e-2)

    def test_calculate_bollinger_bands_insufficient_data(self):
        """8. calculate_bollinger_bands() - 데이터 부족"""
        prices = [100, 105, 98]  # 3개 (20개 필요)
        period = 20

        result = calculate_bollinger_bands(prices, period)

        # 데이터 부족 시 None 반환
        assert result is None

    def test_calculate_all_indicators_basic_only(self, sample_ohlcv_data):
        """9. calculate_all_indicators() - 기본 지표만"""
        result = calculate_all_indicators(sample_ohlcv_data, include_advanced=False)

        # 기본 지표 (7개) 확인
        assert "current_price" in result
        assert "change_rate" in result
        assert "high" in result
        assert "low" in result
        assert "avg" in result
        assert "volume" in result
        assert "ma5" in result
        assert "ma20" in result
        assert "ma60" in result
        assert "volume_ratio" in result
        assert "volatility" in result
        assert "bollinger_upper" in result
        assert "bollinger_lower" in result

        # 고급 지표는 없음
        assert "rsi" not in result
        assert "macd" not in result

    def test_calculate_all_indicators_with_advanced(self, sample_ohlcv_data):
        """10. calculate_all_indicators() - 고급 지표 포함"""
        result = calculate_all_indicators(sample_ohlcv_data, include_advanced=True)

        # 기본 지표
        assert "current_price" in result
        assert "ma5" in result
        assert "ma20" in result

        # 고급 지표 (15개) 확인
        assert "rsi" in result
        assert "macd" in result
        assert "macd_signal" in result
        assert "macd_histogram" in result
        assert "stochastic_k" in result
        assert "stochastic_d" in result
        assert "williams_r" in result
        assert "cci" in result
        assert "adx" in result
        assert "obv" in result
        assert "mfi" in result
        assert "vwap" in result
        assert "atr" in result
        assert "keltner_upper" in result
        assert "keltner_middle" in result
        assert "keltner_lower" in result

        # 타입 검증
        assert isinstance(result["current_price"], (int, float))
        assert isinstance(result["change_rate"], float)
        if result["rsi"] is not None:
            assert 0 <= result["rsi"] <= 100  # RSI 범위


@pytest.mark.unit
class TestTechnicalCalculations:
    """기술적 지표 계산 정확도 테스트"""

    def test_moving_average_accuracy(self):
        """이동평균 계산 정확도"""
        prices = [100, 110, 120, 130, 140]
        ma5 = calculate_moving_average(prices, 5)

        # 수동 계산: (100 + 110 + 120 + 130 + 140) / 5 = 120
        assert ma5 == pytest.approx(120.0, rel=1e-6)

    def test_volume_ratio_accuracy(self):
        """거래량 비율 계산 정확도"""
        # 최근 거래량이 평균보다 2배
        volumes = [100] * 19 + [200]  # 19개는 100, 마지막 1개는 200
        ratio = calculate_volume_ratio(volumes, 20)

        # 비율: 200 / ((19*100 + 200)/20) = 200 / 105 ≈ 1.90
        assert ratio == pytest.approx(1.90, rel=0.1)

    def test_volatility_zero_for_constant_prices(self):
        """변동성 = 0 (가격 일정)"""
        prices = [100] * 30  # 모두 동일
        volatility = calculate_volatility(prices, 20)

        # 가격 변동 없음 → 변동성 0
        assert volatility == pytest.approx(0.0, abs=1e-6)

    def test_bollinger_bands_width_with_volatility(self):
        """변동성 증가 → 볼린저 밴드 폭 증가"""
        # 변동성 낮은 데이터
        prices_low_vol = [100, 101, 99, 100, 101] * 6  # 30개
        bb_low = calculate_bollinger_bands(prices_low_vol, 20)

        # 변동성 높은 데이터
        prices_high_vol = [100, 120, 80, 110, 90] * 6  # 30개
        bb_high = calculate_bollinger_bands(prices_high_vol, 20)

        # 변동성 높을수록 밴드 폭 증가
        width_low = bb_low["upper"] - bb_low["lower"]
        width_high = bb_high["upper"] - bb_high["lower"]

        assert width_high > width_low
