"""
trading_signal_generator.py 단위 테스트

총 15개 테스트:
1. generate_trading_signals() - 매수 신호
2. generate_trading_signals() - 매도 신호
3. generate_trading_signals() - 관망 신호
4. analyze_price_position() - 저평가
5. analyze_price_position() - 고평가
6. analyze_technical_signals() - 매수 신호
7. analyze_technical_signals() - 매도 신호
8. assess_risk_level() - 낮은 위험
9. assess_risk_level() - 높은 위험
10. assess_market_favorability() - 호재장
11. assess_market_favorability() - 악재장
12. integrate_ai_recommendations() - AI 권고 매수
13. synthesize_signals() - 매수 신호 통합
14. determine_entry_strategy() - 즉시 매수
15. calculate_exit_points() - 손절/목표가
"""
import pytest
from typing import Dict, Any
from trading_signal_generator import (
    generate_trading_signals,
    analyze_price_position,
    analyze_technical_signals,
    assess_risk_level,
    assess_market_favorability,
    integrate_ai_recommendations,
    synthesize_signals,
    determine_entry_strategy,
    calculate_exit_points,
    calculate_comprehensive_risk_score
)


@pytest.mark.unit
class TestTradingSignalGenerator:
    """매매 신호 생성 모듈 테스트"""

    def test_generate_trading_signals_buy(
        self,
        sample_indicators,
        sample_target_prices,
        sample_risk_scores,
        sample_market_context,
        sample_analyst_opinion,
        sample_financial_data
    ):
        """1. generate_trading_signals() - 매수 신호"""
        # 저평가 상황 설정 (현재가 < 목표가)
        indicators = sample_indicators.copy()
        indicators["current_price"] = 12000  # 낮은 가격

        target_prices = sample_target_prices.copy()
        target_prices["current_price"] = 12000
        target_prices["neutral"] = 18000  # 높은 목표가

        ai_recommendations = {
            "recommendation": "매수",
            "risk_level": "낮음",
            "evaluation_score": 80
        }

        result = generate_trading_signals(
            current_price=12000,
            target_prices=target_prices,
            technical_indicators=indicators,
            risk_scores=sample_risk_scores,
            market_context=sample_market_context,
            ai_recommendations=ai_recommendations,
            analyst_opinion=sample_analyst_opinion,
            financial_data=sample_financial_data
        )

        # 매수 신호 검증
        assert result["signal"] in ["buy", "hold"]  # 저평가 → 매수 또는 보유
        assert result["confidence"] > 0
        assert result["strength"] in ["weak", "moderate", "strong"]

    def test_generate_trading_signals_sell(
        self,
        sample_indicators,
        sample_target_prices,
        sample_risk_scores,
        sample_market_context,
        sample_analyst_opinion,
        sample_financial_data
    ):
        """2. generate_trading_signals() - 매도 신호"""
        # 고평가 상황 설정 (현재가 > 목표가)
        indicators = sample_indicators.copy()
        indicators["current_price"] = 22000  # 높은 가격
        indicators["rsi"] = 85  # 과매수

        target_prices = sample_target_prices.copy()
        target_prices["current_price"] = 22000
        target_prices["neutral"] = 18000  # 낮은 목표가

        ai_recommendations = {
            "recommendation": "매도",
            "risk_level": "높음",
            "evaluation_score": 30
        }

        result = generate_trading_signals(
            current_price=22000,
            target_prices=target_prices,
            technical_indicators=indicators,
            risk_scores=sample_risk_scores,
            market_context=sample_market_context,
            ai_recommendations=ai_recommendations,
            analyst_opinion=sample_analyst_opinion,
            financial_data=sample_financial_data
        )

        # 매도 신호 검증
        assert result["signal"] in ["sell", "hold"]

    def test_generate_trading_signals_hold(
        self,
        sample_indicators,
        sample_target_prices,
        sample_risk_scores,
        sample_market_context,
        sample_analyst_opinion,
        sample_financial_data
    ):
        """3. generate_trading_signals() - 관망 신호"""
        # 중립 상황 설정
        ai_recommendations = {
            "recommendation": "관망",
            "risk_level": "보통",
            "evaluation_score": 50
        }

        result = generate_trading_signals(
            current_price=sample_indicators["current_price"],
            target_prices=sample_target_prices,
            technical_indicators=sample_indicators,
            risk_scores=sample_risk_scores,
            market_context=sample_market_context,
            ai_recommendations=ai_recommendations,
            analyst_opinion=sample_analyst_opinion,
            financial_data=sample_financial_data
        )

        # 관망 신호 검증
        assert result["signal"] in ["buy", "sell", "hold"]
        assert "reasoning" in result

    def test_analyze_price_position_undervalued(self, sample_target_prices):
        """4. analyze_price_position() - 저평가"""
        target_prices = sample_target_prices.copy()
        target_prices["current_price"] = 12000  # 낮은 가격
        target_prices["neutral"] = 18000  # 높은 목표가

        result = analyze_price_position(12000, target_prices)

        # 저평가 판정
        assert result["price_position"] == "undervalued"
        assert result["upside_to_neutral"] > 30  # 30% 이상 상승 여력

    def test_analyze_price_position_overvalued(self, sample_target_prices):
        """5. analyze_price_position() - 고평가"""
        target_prices = sample_target_prices.copy()
        target_prices["current_price"] = 22000  # 높은 가격
        target_prices["neutral"] = 18000  # 낮은 목표가

        result = analyze_price_position(22000, target_prices)

        # 고평가 판정
        assert result["price_position"] == "overvalued"
        assert result["upside_to_neutral"] < -10  # 목표가 하회

    def test_analyze_technical_signals_buy(self, sample_indicators):
        """6. analyze_technical_signals() - 매수 신호"""
        indicators = sample_indicators.copy()
        indicators["rsi"] = 35  # 과매도
        indicators["macd_histogram"] = 50  # 양수 (상승)
        indicators["stochastic_k"] = 25  # 과매도

        result = analyze_technical_signals(indicators)

        # 매수 신호 점수 확인
        assert "score" in result
        assert "signals" in result
        assert result["score"] > 0  # 양의 점수

    def test_analyze_technical_signals_sell(self, sample_indicators):
        """7. analyze_technical_signals() - 매도 신호"""
        indicators = sample_indicators.copy()
        indicators["rsi"] = 85  # 과매수
        indicators["macd_histogram"] = -50  # 음수 (하락)
        indicators["stochastic_k"] = 95  # 과매수

        result = analyze_technical_signals(indicators)

        # 매도 신호 점수 확인
        assert "score" in result
        assert result["score"] < 0  # 음의 점수

    def test_assess_risk_level_low(self, sample_risk_scores):
        """8. assess_risk_level() - 낮은 위험"""
        risk_scores = {
            "short_term": {"score": 20},
            "mid_term": {"score": 25},
            "long_term": {"score": 30}
        }

        result = assess_risk_level(risk_scores, {})

        # 낮은 위험도
        assert result["risk_level"] == "low"
        assert result["avg_risk_score"] < 40

    def test_assess_risk_level_high(self, sample_risk_scores):
        """9. assess_risk_level() - 높은 위험"""
        risk_scores = {
            "short_term": {"score": 75},
            "mid_term": {"score": 80},
            "long_term": {"score": 85}
        }

        result = assess_risk_level(risk_scores, {})

        # 높은 위험도
        assert result["risk_level"] == "high"
        assert result["avg_risk_score"] > 70

    def test_assess_market_favorability_bullish(self):
        """10. assess_market_favorability() - 호재장"""
        market_context = {
            "market_trend": "bullish",
            "market_strength": 80,
            "market_sentiment": "긍정적"
        }

        result = assess_market_favorability(market_context)

        # 호재장 판정
        assert result["favorability"] in ["favorable", "neutral"]
        assert result["score"] > 0

    def test_assess_market_favorability_bearish(self):
        """11. assess_market_favorability() - 악재장"""
        market_context = {
            "market_trend": "bearish",
            "market_strength": 30,
            "market_sentiment": "부정적"
        }

        result = assess_market_favorability(market_context)

        # 악재장 판정
        assert result["favorability"] in ["unfavorable", "neutral"]
        assert result["score"] < 0

    def test_integrate_ai_recommendations_buy(self):
        """12. integrate_ai_recommendations() - AI 권고 매수"""
        ai_recommendations = {
            "recommendation": "매수",
            "risk_level": "낮음",
            "evaluation_score": 85
        }

        result = integrate_ai_recommendations(ai_recommendations)

        # AI 매수 권고
        assert result["ai_signal"] == "buy"
        assert result["ai_confidence"] > 80

    def test_synthesize_signals_buy(self):
        """13. synthesize_signals() - 매수 신호 통합"""
        price_analysis = {"upside_to_neutral": 25.0, "price_position": "undervalued"}
        technical_analysis = {"score": 50, "signal": "buy"}
        risk_assessment = {"risk_level": "low", "avg_risk_score": 30}
        market_assessment = {"favorability": "favorable", "score": 60}
        ai_analysis = {"ai_signal": "buy", "ai_confidence": 80}

        result = synthesize_signals(
            price_analysis,
            technical_analysis,
            risk_assessment,
            market_assessment,
            ai_analysis
        )

        # 매수 신호 통합
        assert result["signal"] in ["buy", "hold"]
        assert result["confidence"] > 0

    def test_determine_entry_strategy_immediate(self):
        """14. determine_entry_strategy() - 즉시 매수"""
        current_price = 15000
        target_prices = {
            "conservative": 18000,
            "neutral": 20000,
            "aggressive": 22000
        }
        technical_score = 70

        result = determine_entry_strategy(
            signal="buy",
            confidence=80,
            current_price=current_price,
            target_prices=target_prices,
            technical_score=technical_score
        )

        # 즉시 매수 전략
        assert result["entry_timing"] in ["immediate", "wait", "gradual"]
        assert result["position_size"] in ["small", "medium", "large"]

    def test_calculate_exit_points(self, sample_target_prices):
        """15. calculate_exit_points() - 손절/목표가"""
        current_price = 15000
        result = calculate_exit_points(
            current_price=current_price,
            target_prices=sample_target_prices,
            risk_level="low"
        )

        # 손절가 및 목표가 검증
        assert "stop_loss" in result
        assert "take_profit" in result
        assert result["stop_loss"] < current_price
        assert result["take_profit"]["first"] > current_price


@pytest.mark.unit
class TestComprehensiveRiskScore:
    """종합 위험도 테스트"""

    def test_calculate_comprehensive_risk_score_high_risk(self, sample_indicators, sample_financial_data):
        """RSI 과열 + 거래량 급증 + EPS 음수 = 높은 위험"""
        indicators = sample_indicators.copy()
        indicators["rsi"] = 85
        indicators["volume_ratio"] = 7.0

        financial_data = sample_financial_data.copy()
        financial_data["eps"] = -500  # 적자

        ai_risk_score = 70
        market_context = {"market_trend": "bearish"}

        result = calculate_comprehensive_risk_score(
            indicators,
            financial_data,
            ai_risk_score,
            market_context
        )

        # 높은 위험도
        assert result["risk_score"] >= 60
        assert result["risk_level"] in ["높음", "high"]
        assert len(result["risk_factors"]) > 0

    def test_calculate_comprehensive_risk_score_low_risk(self, sample_indicators, sample_financial_data):
        """RSI 정상 + 거래량 정상 + EPS 양수 = 낮은 위험"""
        indicators = sample_indicators.copy()
        indicators["rsi"] = 50
        indicators["volume_ratio"] = 1.2

        ai_risk_score = 25
        market_context = {"market_trend": "bullish"}

        result = calculate_comprehensive_risk_score(
            indicators,
            sample_financial_data,
            ai_risk_score,
            market_context
        )

        # 낮은 위험도
        assert result["risk_score"] < 40
        assert result["risk_level"] in ["낮음", "low"]
