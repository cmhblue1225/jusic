"""
target_price_calculator.py 단위 테스트

총 12개 테스트:
1. calculate_target_prices() - 정상 케이스
2. calculate_target_prices() - 재무 데이터 없음
3. calculate_per_based_target() - 정상 케이스
4. calculate_per_based_target() - 데이터 부족
5. calculate_pbr_based_target() - 정상 케이스
6. calculate_pbr_based_target() - 데이터 부족
7. calculate_technical_target() - 정상 케이스
8. calculate_market_adjustment() - 강세장
9. calculate_market_adjustment() - 약세장
10. calculate_conservative_target() - 정상 케이스
11. calculate_neutral_target() - 정상 케이스
12. calculate_aggressive_target() - 정상 케이스
"""
import pytest
from typing import Dict, Any
from target_price_calculator import (
    calculate_target_prices,
    calculate_per_based_target,
    calculate_pbr_based_target,
    calculate_technical_target,
    calculate_market_adjustment,
    calculate_conservative_target,
    calculate_neutral_target,
    calculate_aggressive_target,
    analyze_target_price_gap
)


@pytest.mark.unit
class TestTargetPriceCalculator:
    """목표가 산출 모듈 테스트"""

    def test_calculate_target_prices_normal(
        self,
        sample_indicators,
        sample_financial_data,
        sample_analyst_opinion,
        sample_sector_relative,
        sample_market_context
    ):
        """1. calculate_target_prices() - 정상 케이스"""
        result = calculate_target_prices(
            current_price=sample_indicators["current_price"],
            financial_data=sample_financial_data,
            analyst_opinion=sample_analyst_opinion,
            price_data=sample_indicators,
            sector_relative=sample_sector_relative,
            market_context=sample_market_context
        )

        # 반환 필드 검증
        assert "conservative" in result
        assert "neutral" in result
        assert "aggressive" in result
        assert "current_price" in result
        assert "upside_potential" in result
        assert "methods" in result

        # 값 범위 검증
        assert result["conservative"] < result["neutral"] < result["aggressive"]
        assert result["conservative"] > 0
        assert result["current_price"] == sample_indicators["current_price"]

    def test_calculate_target_prices_without_financial_data(
        self,
        sample_indicators,
        sample_analyst_opinion,
        sample_sector_relative,
        sample_market_context
    ):
        """2. calculate_target_prices() - 재무 데이터 없음"""
        result = calculate_target_prices(
            current_price=sample_indicators["current_price"],
            financial_data={},  # 빈 재무 데이터
            analyst_opinion=sample_analyst_opinion,
            price_data=sample_indicators,
            sector_relative=sample_sector_relative,
            market_context=sample_market_context
        )

        # 기본 필드는 여전히 존재
        assert "conservative" in result
        assert "neutral" in result
        assert "aggressive" in result

        # 재무 기반 목표가는 없거나 기본값
        if "methods" in result and "per_based" in result["methods"]:
            assert result["methods"]["per_based"] is None or isinstance(result["methods"]["per_based"], (int, float))

    def test_calculate_per_based_target_normal(self, sample_financial_data, sample_sector_relative):
        """3. calculate_per_based_target() - 정상 케이스"""
        current_price = 15000
        result = calculate_per_based_target(
            current_price=current_price,
            financial_data=sample_financial_data,
            sector_relative=sample_sector_relative
        )

        # 목표가 반환 검증
        assert result is not None
        assert result > 0

        # PER 기반 계산: EPS * 업종 평균 PER
        expected = sample_financial_data["eps"] * sample_sector_relative["sector_avg_per"]
        assert abs(result - expected) < 100  # 100원 오차 허용

    def test_calculate_per_based_target_missing_data(self, sample_sector_relative):
        """4. calculate_per_based_target() - 데이터 부족"""
        current_price = 15000
        result = calculate_per_based_target(
            current_price=current_price,
            financial_data={},  # EPS 없음
            sector_relative=sample_sector_relative
        )

        # 데이터 부족 시 None 반환
        assert result is None

    def test_calculate_pbr_based_target_normal(self, sample_financial_data, sample_sector_relative):
        """5. calculate_pbr_based_target() - 정상 케이스"""
        current_price = 15000
        result = calculate_pbr_based_target(
            current_price=current_price,
            financial_data=sample_financial_data,
            sector_relative=sample_sector_relative
        )

        # 목표가 반환 검증
        assert result is not None
        assert result > 0

        # PBR 기반 계산: BPS * 업종 평균 PBR
        expected = sample_financial_data["bps"] * sample_sector_relative["sector_avg_pbr"]
        assert abs(result - expected) < 100

    def test_calculate_pbr_based_target_missing_data(self, sample_sector_relative):
        """6. calculate_pbr_based_target() - 데이터 부족"""
        current_price = 15000
        result = calculate_pbr_based_target(
            current_price=current_price,
            financial_data={},  # BPS 없음
            sector_relative=sample_sector_relative
        )

        # 데이터 부족 시 None 반환
        assert result is None

    def test_calculate_technical_target_normal(self, sample_indicators):
        """7. calculate_technical_target() - 정상 케이스"""
        result = calculate_technical_target(
            price_data=sample_indicators
        )

        # 목표가 반환 검증
        assert result is not None
        assert result > 0

        # 기술적 목표가는 볼린저 밴드 상단 기반
        # 일반적으로 현재가보다 높음 (상승 목표)
        assert result > sample_indicators["current_price"] * 0.9

    def test_calculate_market_adjustment_bullish(self):
        """8. calculate_market_adjustment() - 강세장"""
        market_context = {
            "market_trend": "bullish",
            "market_strength": 80,
            "market_sentiment": "긍정적"
        }

        result = calculate_market_adjustment(market_context)

        # 강세장 → 조정 계수 1.0 이상
        assert result >= 1.0
        assert result <= 1.2  # 최대 20% 상향

    def test_calculate_market_adjustment_bearish(self):
        """9. calculate_market_adjustment() - 약세장"""
        market_context = {
            "market_trend": "bearish",
            "market_strength": 30,
            "market_sentiment": "부정적"
        }

        result = calculate_market_adjustment(market_context)

        # 약세장 → 조정 계수 1.0 이하
        assert result <= 1.0
        assert result >= 0.8  # 최대 20% 하향

    def test_calculate_conservative_target(self):
        """10. calculate_conservative_target() - 정상 케이스"""
        methods = {
            "per_based": 17000,
            "pbr_based": 16000,
            "analyst_avg": 18000,
            "technical_resistance": 15000
        }
        market_adj = 1.0

        result = calculate_conservative_target(methods, market_adj)

        # 보수적 목표가 = 최소값 기반
        assert result is not None
        assert result > 0
        assert result <= min([v for v in methods.values() if v is not None])

    def test_calculate_neutral_target(self):
        """11. calculate_neutral_target() - 정상 케이스"""
        methods = {
            "per_based": 17000,
            "pbr_based": 16000,
            "analyst_avg": 18000,
            "technical_resistance": 15000
        }
        market_adj = 1.0

        result = calculate_neutral_target(methods, market_adj)

        # 중립 목표가 = 평균값 기반
        assert result is not None
        assert result > 0

        # 중립값은 보수적과 공격적 사이
        conservative = calculate_conservative_target(methods, market_adj)
        aggressive = calculate_aggressive_target(methods, market_adj)
        assert conservative <= result <= aggressive

    def test_calculate_aggressive_target(self):
        """12. calculate_aggressive_target() - 정상 케이스"""
        methods = {
            "per_based": 17000,
            "pbr_based": 16000,
            "analyst_avg": 18000,
            "technical_resistance": 15000
        }
        market_adj = 1.0

        result = calculate_aggressive_target(methods, market_adj)

        # 공격적 목표가 = 최대값 기반
        assert result is not None
        assert result > 0
        assert result >= max([v for v in methods.values() if v is not None])


@pytest.mark.unit
class TestTargetPriceGapAnalysis:
    """목표가 갭 분석 테스트"""

    def test_analyze_target_price_gap_overvalued(self):
        """현재가 > 목표가 (과대평가)"""
        result = analyze_target_price_gap(
            current_price=20000,
            conservative=16000,
            neutral=18000,
            aggressive=19000
        )

        assert "gap_percent" in result
        assert "warning" in result
        assert result["gap_percent"] > 0
        assert result["warning"]["level"] in ["warning", "danger"]

    def test_analyze_target_price_gap_undervalued(self):
        """현재가 < 목표가 (저평가)"""
        result = analyze_target_price_gap(
            current_price=14000,
            conservative=16000,
            neutral=18000,
            aggressive=20000
        )

        assert "gap_percent" in result
        assert result["gap_percent"] < -10
        assert result["warning"]["level"] == "opportunity"
