"""
🔥 Phase 5.2: 매매 타이밍 신호 생성 모듈
기술적 지표 + 목표가 + 리스크 + 시장 맥락 + AI 추천을 종합하여
구체적인 매수/매도/관망 신호 생성
"""
from typing import Dict, Any, Optional, List


def generate_trading_signals(
    current_price: float,
    target_prices: Dict[str, Any],
    technical_indicators: Dict[str, Any],
    risk_scores: Dict[str, Any],
    market_context: Dict[str, Any],
    ai_recommendations: Dict[str, Any],
    analyst_opinion: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    매매 타이밍 신호 생성

    Args:
        current_price: 현재가
        target_prices: 목표가 (보수적/중립적/공격적)
        technical_indicators: 기술적 지표 (RSI, MACD, Bollinger Bands 등)
        risk_scores: 리스크 점수 (단기/중기/장기)
        market_context: 시장 전체 맥락
        ai_recommendations: AI 앙상블 추천
        analyst_opinion: 애널리스트 의견

    Returns:
        Dict: 매매 신호
            - signal: buy/sell/hold
            - confidence: 신호 신뢰도 (0-100)
            - entry_timing: 진입 타이밍 (immediate/wait/gradual)
            - position_size: 권장 포지션 크기 (small/medium/large)
            - stop_loss: 손절 가격
            - take_profit: 목표 수익 가격 (단계별)
            - reasoning: 신호 근거
    """
    # 1. 가격 포지션 분석
    price_position = analyze_price_position(current_price, target_prices, analyst_opinion)

    # 2. 기술적 신호 분석
    technical_signal = analyze_technical_signals(technical_indicators)

    # 3. 리스크 평가
    risk_assessment = assess_risk_level(risk_scores, market_context)

    # 4. 시장 환경 평가
    market_favorability = assess_market_favorability(market_context)

    # 5. AI 추천 통합
    ai_signal = integrate_ai_recommendations(ai_recommendations)

    # 6. 종합 신호 생성
    final_signal = synthesize_signals(
        price_position,
        technical_signal,
        risk_assessment,
        market_favorability,
        ai_signal
    )

    # 7. 진입/청산 전략 수립
    entry_strategy = determine_entry_strategy(
        final_signal,
        technical_indicators,
        risk_assessment,
        market_context
    )

    # 8. 손절/익절 라인 설정
    stop_loss, take_profit_levels = calculate_exit_points(
        current_price,
        target_prices,
        technical_indicators,
        risk_scores
    )

    result = {
        "signal": final_signal["action"],  # buy/sell/hold
        "confidence": final_signal["confidence"],  # 0-100
        "strength": final_signal["strength"],  # weak/moderate/strong

        "entry_timing": entry_strategy["timing"],  # immediate/wait/gradual
        "position_size": entry_strategy["position_size"],  # small/medium/large
        "entry_price_range": entry_strategy["price_range"],

        "stop_loss": round(stop_loss, 0) if stop_loss > 0 else None,
        "take_profit": {
            "target_1": take_profit_levels.get("conservative"),
            "target_2": take_profit_levels.get("neutral"),
            "target_3": take_profit_levels.get("aggressive")
        },

        "reasoning": final_signal["reasoning"],
        "risks": risk_assessment["key_risks"],
        "favorable_factors": final_signal["favorable_factors"],
        "unfavorable_factors": final_signal["unfavorable_factors"],

        # 세부 분석 결과
        "analysis_breakdown": {
            "price_position": price_position,
            "technical_signal": technical_signal,
            "risk_level": risk_assessment["overall_risk"],
            "market_favorability": market_favorability,
            "ai_consensus": ai_signal
        }
    }

    print(f"✅ 매매 신호: {result['signal'].upper()} (신뢰도: {result['confidence']}%, 강도: {result['strength']})")
    return result


def analyze_price_position(
    current_price: float,
    target_prices: Dict[str, Any],
    analyst_opinion: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """현재가의 목표가 대비 위치 분석"""
    conservative = target_prices.get("conservative") or 0
    neutral = target_prices.get("neutral") or 0
    aggressive = target_prices.get("aggressive") or 0

    # 상승 여력 계산
    upside_conservative = ((conservative / current_price) - 1) * 100 if conservative > 0 else 0
    upside_neutral = ((neutral / current_price) - 1) * 100 if neutral > 0 else 0
    upside_aggressive = ((aggressive / current_price) - 1) * 100 if aggressive > 0 else 0

    # 가격 매력도 판단
    if upside_neutral >= 20:
        attractiveness = "high"  # 20% 이상 상승 여력
    elif upside_neutral >= 10:
        attractiveness = "moderate"  # 10~20% 상승 여력
    elif upside_neutral >= 0:
        attractiveness = "low"  # 0~10% 상승 여력
    else:
        attractiveness = "overvalued"  # 현재가가 목표가 초과

    # 애널리스트 컨센서스 비교
    analyst_signal = "neutral"
    if analyst_opinion and analyst_opinion.get("avg_target_price"):
        analyst_target = analyst_opinion["avg_target_price"]
        analyst_upside = ((analyst_target / current_price) - 1) * 100

        if analyst_upside >= 15:
            analyst_signal = "bullish"
        elif analyst_upside <= -5:
            analyst_signal = "bearish"

    return {
        "upside_potential": {
            "conservative": round(upside_conservative, 2),
            "neutral": round(upside_neutral, 2),
            "aggressive": round(upside_aggressive, 2)
        },
        "attractiveness": attractiveness,
        "analyst_signal": analyst_signal,
        "current_vs_target": {
            "conservative": round((current_price / conservative * 100), 1) if conservative > 0 else 100,
            "neutral": round((current_price / neutral * 100), 1) if neutral > 0 else 100,
            "aggressive": round((current_price / aggressive * 100), 1) if aggressive > 0 else 100
        }
    }


def analyze_technical_signals(indicators: Dict[str, Any]) -> Dict[str, Any]:
    """기술적 지표 종합 분석"""
    signals = []
    scores = []

    # 1. RSI 신호
    rsi = indicators.get("rsi") or 50
    if rsi < 30:
        signals.append("RSI 과매도 (매수 신호)")
        scores.append(70)
    elif rsi > 70:
        signals.append("RSI 과매수 (매도 신호)")
        scores.append(-70)
    elif 40 <= rsi <= 60:
        signals.append("RSI 중립")
        scores.append(0)
    else:
        signals.append("RSI 보통")
        scores.append(0)

    # 2. MACD 신호
    macd = indicators.get("macd") or {}
    macd_value = macd.get("value") or 0
    macd_signal = macd.get("signal") or 0
    macd_histogram = macd.get("histogram") or 0

    if macd_histogram > 0 and macd_value > macd_signal:
        signals.append("MACD 골든크로스 (매수 신호)")
        scores.append(60)
    elif macd_histogram < 0 and macd_value < macd_signal:
        signals.append("MACD 데드크로스 (매도 신호)")
        scores.append(-60)
    else:
        signals.append("MACD 중립")
        scores.append(0)

    # 3. Bollinger Bands 신호
    bollinger = indicators.get("bollinger_bands") or {}
    bb_position = bollinger.get("position") or "middle"

    if bb_position == "below_lower":
        signals.append("볼린저 밴드 하단 이탈 (매수 신호)")
        scores.append(50)
    elif bb_position == "above_upper":
        signals.append("볼린저 밴드 상단 이탈 (매도 신호)")
        scores.append(-50)
    elif bb_position == "near_lower":
        signals.append("볼린저 밴드 하단 근접")
        scores.append(30)
    elif bb_position == "near_upper":
        signals.append("볼린저 밴드 상단 근접")
        scores.append(-30)
    else:
        signals.append("볼린저 밴드 중간")
        scores.append(0)

    # 4. 이동평균선 신호
    ma_trend = indicators.get("moving_average_trend") or "neutral"
    if ma_trend == "golden_cross":
        signals.append("이동평균 골든크로스")
        scores.append(50)
    elif ma_trend == "dead_cross":
        signals.append("이동평균 데드크로스")
        scores.append(-50)

    # 종합 점수 계산 (-100 ~ 100)
    avg_score = sum(scores) / len(scores) if scores else 0

    if avg_score >= 40:
        overall_signal = "strong_buy"
    elif avg_score >= 20:
        overall_signal = "buy"
    elif avg_score >= -20:
        overall_signal = "neutral"
    elif avg_score >= -40:
        overall_signal = "sell"
    else:
        overall_signal = "strong_sell"

    return {
        "signal": overall_signal,
        "score": round(avg_score, 1),
        "indicators": signals,
        "rsi": rsi,
        "macd_histogram": macd_histogram,
        "bollinger_position": bb_position
    }


def assess_risk_level(
    risk_scores: Dict[str, Any],
    market_context: Dict[str, Any]
) -> Dict[str, Any]:
    """리스크 수준 종합 평가"""
    # Phase 3.2의 리스크 점수 활용
    short_term_risk = (risk_scores.get("short_term") or {}).get("score") or 50
    mid_term_risk = (risk_scores.get("mid_term") or {}).get("score") or 50
    long_term_risk = (risk_scores.get("long_term") or {}).get("score") or 50

    # 가중 평균 (단기 40%, 중기 35%, 장기 25%)
    overall_risk = (
        short_term_risk * 0.4 +
        mid_term_risk * 0.35 +
        long_term_risk * 0.25
    )

    # 시장 변동성 반영
    volatility_level = market_context.get("volatility_level") or "medium"
    if volatility_level == "high":
        overall_risk += 10  # 변동성 높으면 리스크 증가
    elif volatility_level == "low":
        overall_risk -= 5  # 변동성 낮으면 리스크 감소

    overall_risk = max(0, min(100, overall_risk))

    # 리스크 등급 분류
    if overall_risk >= 70:
        risk_grade = "high"
    elif overall_risk >= 40:
        risk_grade = "moderate"
    else:
        risk_grade = "low"

    # 주요 리스크 요인 수집
    key_risks = []
    if short_term_risk >= 70:
        key_risks.append("단기 리스크 높음")
    if volatility_level == "high":
        key_risks.append("시장 변동성 높음")
    if market_context.get("market_trend") == "bearish":
        key_risks.append("시장 전체 하락세")

    return {
        "overall_risk": overall_risk,
        "risk_grade": risk_grade,
        "key_risks": key_risks,
        "details": {
            "short_term": short_term_risk,
            "mid_term": mid_term_risk,
            "long_term": long_term_risk
        }
    }


def assess_market_favorability(market_context: Dict[str, Any]) -> Dict[str, Any]:
    """시장 환경의 호의성 평가"""
    market_trend = market_context.get("market_trend") or "neutral"
    market_strength = market_context.get("market_strength") or 50
    volatility_level = market_context.get("volatility_level") or "medium"
    market_breadth_pct = market_context.get("market_breadth_pct") or 50

    # 호의성 점수 계산 (0-100)
    favorability_score = 50  # 기본값

    # 시장 추세 반영
    if market_trend == "bullish":
        favorability_score += 20
    elif market_trend == "bearish":
        favorability_score -= 20

    # 시장 강도 반영
    favorability_score += (market_strength - 50) * 0.3

    # 변동성 반영 (낮을수록 유리)
    if volatility_level == "low":
        favorability_score += 10
    elif volatility_level == "high":
        favorability_score -= 15

    # 시장 폭 반영
    favorability_score += (market_breadth_pct - 50) * 0.2

    favorability_score = max(0, min(100, favorability_score))

    if favorability_score >= 70:
        favorability = "very_favorable"
    elif favorability_score >= 55:
        favorability = "favorable"
    elif favorability_score >= 45:
        favorability = "neutral"
    elif favorability_score >= 30:
        favorability = "unfavorable"
    else:
        favorability = "very_unfavorable"

    return {
        "favorability": favorability,
        "score": round(favorability_score, 1),
        "market_trend": market_trend,
        "market_strength": market_strength
    }


def integrate_ai_recommendations(ai_recommendations: Dict[str, Any]) -> Dict[str, Any]:
    """AI 앙상블 추천 통합"""
    # Phase 3.3의 AI 앙상블 결과 활용
    # ai_ensemble에서 반환하는 키: recommendation, confidence_score
    consensus = ai_recommendations.get("recommendation") or ai_recommendations.get("consensus") or "hold"
    confidence = ai_recommendations.get("confidence_score") or ai_recommendations.get("confidence") or 50

    # 컨센서스를 신호로 변환
    if consensus in ["strong_buy", "buy"]:
        signal = "buy"
        signal_strength = 80 if consensus == "strong_buy" else 60
    elif consensus in ["strong_sell", "sell"]:
        signal = "sell"
        signal_strength = 80 if consensus == "strong_sell" else 60
    else:
        signal = "hold"
        signal_strength = 50

    return {
        "signal": signal,
        "consensus": consensus,
        "confidence": confidence,
        "signal_strength": signal_strength
    }


def synthesize_signals(
    price_position: Dict[str, Any],
    technical_signal: Dict[str, Any],
    risk_assessment: Dict[str, Any],
    market_favorability: Dict[str, Any],
    ai_signal: Dict[str, Any]
) -> Dict[str, Any]:
    """모든 신호를 종합하여 최종 매매 신호 생성"""

    # 각 요소별 점수 (0-100 스케일)
    scores = []
    weights = []

    # 1. 가격 포지션 (가중치 25%)
    attractiveness = price_position["attractiveness"]
    if attractiveness == "high":
        scores.append(80)
    elif attractiveness == "moderate":
        scores.append(60)
    elif attractiveness == "low":
        scores.append(40)
    else:  # overvalued
        scores.append(20)
    weights.append(0.25)

    # 2. 기술적 신호 (가중치 30%)
    tech_score = technical_signal["score"]  # -100 ~ 100
    tech_normalized = (tech_score + 100) / 2  # 0 ~ 100으로 정규화
    scores.append(tech_normalized)
    weights.append(0.30)

    # 3. 리스크 평가 (가중치 20%, 리스크 낮을수록 높은 점수)
    risk_score = 100 - risk_assessment["overall_risk"]
    scores.append(risk_score)
    weights.append(0.20)

    # 4. 시장 호의성 (가중치 15%)
    scores.append(market_favorability["score"])
    weights.append(0.15)

    # 5. AI 추천 (가중치 10%)
    ai_score = ai_signal["signal_strength"]
    scores.append(ai_score)
    weights.append(0.10)

    # 가중 평균 계산
    total_score = sum(s * w for s, w in zip(scores, weights))

    # 최종 신호 결정
    if total_score >= 70:
        action = "buy"
        strength = "strong"
        confidence = min(95, total_score)
    elif total_score >= 55:
        action = "buy"
        strength = "moderate"
        confidence = total_score
    elif total_score >= 45:
        action = "hold"
        strength = "neutral"
        confidence = 100 - abs(total_score - 50) * 2
    elif total_score >= 30:
        action = "sell"
        strength = "moderate"
        confidence = 100 - total_score
    else:
        action = "sell"
        strength = "strong"
        confidence = min(95, 100 - total_score)

    # 긍정/부정 요인 정리
    favorable_factors = []
    unfavorable_factors = []

    if attractiveness in ["high", "moderate"]:
        favorable_factors.append(f"목표가 대비 {price_position['upside_potential']['neutral']:.1f}% 상승 여력")

    if technical_signal["score"] >= 20:
        favorable_factors.append("기술적 지표 긍정적")
    elif technical_signal["score"] <= -20:
        unfavorable_factors.append("기술적 지표 부정적")

    if risk_assessment["risk_grade"] == "low":
        favorable_factors.append("리스크 수준 낮음")
    elif risk_assessment["risk_grade"] == "high":
        unfavorable_factors.append("리스크 수준 높음")

    if market_favorability["favorability"] in ["favorable", "very_favorable"]:
        favorable_factors.append("시장 환경 우호적")
    elif market_favorability["favorability"] in ["unfavorable", "very_unfavorable"]:
        unfavorable_factors.append("시장 환경 불리함")

    if ai_signal["signal"] == "buy":
        favorable_factors.append("AI 분석 매수 추천")
    elif ai_signal["signal"] == "sell":
        unfavorable_factors.append("AI 분석 매도 추천")

    # 신호 근거 생성
    reasoning = f"종합 점수 {total_score:.1f}/100 기준 {action.upper()} 신호. "
    if favorable_factors:
        reasoning += f"긍정 요인: {', '.join(favorable_factors[:3])}. "
    if unfavorable_factors:
        reasoning += f"부정 요인: {', '.join(unfavorable_factors[:2])}."

    return {
        "action": action,
        "strength": strength,
        "confidence": round(confidence, 1),
        "total_score": round(total_score, 1),
        "reasoning": reasoning,
        "favorable_factors": favorable_factors,
        "unfavorable_factors": unfavorable_factors
    }


def determine_entry_strategy(
    final_signal: Dict[str, Any],
    technical_indicators: Dict[str, Any],
    risk_assessment: Dict[str, Any],
    market_context: Dict[str, Any]
) -> Dict[str, Any]:
    """진입 타이밍 및 포지션 크기 결정"""
    action = final_signal["action"]
    strength = final_signal["strength"]
    confidence = final_signal["confidence"]

    current_price = technical_indicators.get("current_price") or 0

    # 진입 타이밍 결정
    if action == "buy":
        if strength == "strong" and confidence >= 80:
            timing = "immediate"  # 즉시 진입
        elif strength == "moderate" or confidence >= 60:
            timing = "gradual"  # 분할 매수
        else:
            timing = "wait"  # 추가 확인 후 진입
    elif action == "sell":
        if strength == "strong":
            timing = "immediate"
        else:
            timing = "gradual"
    else:  # hold
        timing = "wait"

    # 포지션 크기 결정
    risk_grade = risk_assessment["risk_grade"]

    if action == "buy":
        if risk_grade == "low" and confidence >= 75:
            position_size = "large"  # 70-100%
        elif risk_grade == "moderate" or confidence >= 60:
            position_size = "medium"  # 40-70%
        else:
            position_size = "small"  # 20-40%
    elif action == "sell":
        if risk_grade == "high" or strength == "strong":
            position_size = "large"  # 전량 매도
        else:
            position_size = "medium"  # 부분 매도
    else:
        position_size = "none"

    # 진입 가격 범위
    if timing == "gradual":
        price_range = {
            "lower": round(current_price * 0.97, 0),
            "upper": round(current_price * 1.03, 0)
        }
    else:
        price_range = {
            "lower": current_price,
            "upper": current_price
        }

    return {
        "timing": timing,
        "position_size": position_size,
        "price_range": price_range
    }


def calculate_exit_points(
    current_price: float,
    target_prices: Dict[str, Any],
    technical_indicators: Dict[str, Any],
    risk_scores: Dict[str, Any]
) -> tuple:
    """손절가 및 목표가 설정"""

    # 손절가 계산 (기술적 지표 + 리스크 기반)
    bollinger = technical_indicators.get("bollinger_bands") or {}
    lower_band = bollinger.get("lower") or (current_price * 0.95)

    # 단기 리스크에 따라 손절폭 조정
    short_term_risk = (risk_scores.get("short_term") or {}).get("score") or 50

    if short_term_risk >= 70:
        # 리스크 높으면 손절폭 작게 (5%)
        stop_loss = current_price * 0.95
    elif short_term_risk >= 40:
        # 리스크 중간이면 7%
        stop_loss = current_price * 0.93
    else:
        # 리스크 낮으면 10%
        stop_loss = current_price * 0.90

    # 볼린저 밴드 하단과 비교하여 더 가까운 쪽 선택
    stop_loss = max(stop_loss, lower_band * 0.98)

    # 목표가 (Phase 5.1의 목표가 활용)
    take_profit_levels = {
        "conservative": target_prices.get("conservative"),
        "neutral": target_prices.get("neutral"),
        "aggressive": target_prices.get("aggressive")
    }

    return stop_loss, take_profit_levels
