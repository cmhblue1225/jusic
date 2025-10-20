"""
🔥 Phase 5.1: 목표가 산출 모듈
보수적/중립적/공격적 3가지 시나리오 목표가 계산
"""
from typing import Dict, Any, Optional


def calculate_target_prices(
    current_price: float,
    financial_data: Optional[Dict[str, Any]] = None,
    analyst_opinion: Optional[Dict[str, Any]] = None,
    price_data: Optional[Dict[str, Any]] = None,
    sector_relative: Optional[Dict[str, Any]] = None,
    market_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    3가지 시나리오 목표가 산출 (보수적/중립적/공격적)

    Args:
        current_price: 현재가
        financial_data: 재무 데이터 (PER, PBR, EPS, BPS 등)
        analyst_opinion: 애널리스트 의견 (평균 목표가)
        price_data: 주가 데이터 (52주 고가/저가, 기술적 지표)
        sector_relative: 업종 상대 평가
        market_context: 시장 전체 맥락

    Returns:
        Dict: 목표가 정보
            - conservative: 보수적 목표가
            - neutral: 중립적 목표가
            - aggressive: 공격적 목표가
            - methods: 각 방법론별 목표가
            - upside_potential: 각 시나리오별 상승 여력 (%)
    """
    financial_data = financial_data or {}
    analyst_opinion = analyst_opinion or {}
    price_data = price_data or {}
    sector_relative = sector_relative or {}
    market_context = market_context or {}

    # 1. PER 기반 목표가 계산
    per_based_targets = calculate_per_based_target(current_price, financial_data, sector_relative)

    # 2. PBR 기반 목표가 계산
    pbr_based_targets = calculate_pbr_based_target(current_price, financial_data)

    # 3. 기술적 분석 기반 목표가
    technical_targets = calculate_technical_target(current_price, price_data)

    # 4. 애널리스트 목표가 (있는 경우)
    analyst_target = analyst_opinion.get("avg_target_price", 0)

    # 5. 시장 맥락 반영 조정 계수
    market_adjustment = calculate_market_adjustment(market_context)

    # 6. 각 방법론 종합
    methods = {
        "per_based": per_based_targets,
        "pbr_based": pbr_based_targets,
        "technical": technical_targets,
        "analyst_consensus": analyst_target if analyst_target else None
    }

    # 7. 보수적 목표가 (가중 평균 - 낮은 쪽에 가중치)
    conservative = calculate_conservative_target(
        current_price, per_based_targets, pbr_based_targets,
        technical_targets, analyst_target, market_adjustment
    )

    # 8. 중립적 목표가 (균형 잡힌 가중 평균)
    neutral = calculate_neutral_target(
        current_price, per_based_targets, pbr_based_targets,
        technical_targets, analyst_target, market_adjustment
    )

    # 9. 공격적 목표가 (가중 평균 - 높은 쪽에 가중치)
    aggressive = calculate_aggressive_target(
        current_price, per_based_targets, pbr_based_targets,
        technical_targets, analyst_target, market_adjustment
    )

    # 10. 상승 여력 계산
    upside_potential = {
        "conservative": round((conservative / current_price - 1) * 100, 2) if conservative > 0 else 0,
        "neutral": round((neutral / current_price - 1) * 100, 2) if neutral > 0 else 0,
        "aggressive": round((aggressive / current_price - 1) * 100, 2) if aggressive > 0 else 0
    }

    result = {
        "conservative": round(conservative, 0) if conservative > 0 else None,
        "neutral": round(neutral, 0) if neutral > 0 else None,
        "aggressive": round(aggressive, 0) if aggressive > 0 else None,
        "current_price": round(current_price, 0),
        "upside_potential": upside_potential,
        "methods": methods,
        "market_adjustment_factor": round(market_adjustment, 2)
    }

    print(f"✅ 목표가 산출: 보수 {result['conservative']:,}원 / 중립 {result['neutral']:,}원 / 공격 {result['aggressive']:,}원")
    return result


def calculate_per_based_target(
    current_price: float,
    financial_data: Dict[str, Any],
    sector_relative: Dict[str, Any]
) -> Dict[str, float]:
    """PER 기반 목표가 계산"""
    per = financial_data.get("per", 0)
    eps = financial_data.get("eps", 0)

    if per <= 0 or eps <= 0:
        return {"conservative": 0, "neutral": 0, "aggressive": 0}

    # 적정 PER 산출 (현재 PER 기준)
    # 보수적: 현재 PER의 90%
    # 중립적: 현재 PER의 100%
    # 공격적: 현재 PER의 120%

    # 업종 상대 강도 반영
    relative_strength = sector_relative.get("relative_strength", 1.0)
    adjustment = 1.0 + (relative_strength - 1.0) * 0.3  # 30% 반영

    conservative = eps * per * 0.9 * adjustment
    neutral = eps * per * 1.0 * adjustment
    aggressive = eps * per * 1.2 * adjustment

    return {
        "conservative": conservative,
        "neutral": neutral,
        "aggressive": aggressive
    }


def calculate_pbr_based_target(
    current_price: float,
    financial_data: Dict[str, Any]
) -> Dict[str, float]:
    """PBR 기반 목표가 계산"""
    pbr = financial_data.get("pbr", 0)
    bps = financial_data.get("bps", 0)

    if pbr <= 0 or bps <= 0:
        return {"conservative": 0, "neutral": 0, "aggressive": 0}

    # 적정 PBR 산출
    # 보수적: 현재 PBR의 85%
    # 중립적: 현재 PBR의 100%
    # 공격적: 현재 PBR의 115%

    conservative = bps * pbr * 0.85
    neutral = bps * pbr * 1.0
    aggressive = bps * pbr * 1.15

    return {
        "conservative": conservative,
        "neutral": neutral,
        "aggressive": aggressive
    }


def calculate_technical_target(
    current_price: float,
    price_data: Dict[str, Any]
) -> Dict[str, float]:
    """기술적 분석 기반 목표가 (52주 고가/저가 활용)"""
    week52_high = price_data.get("week52_high", 0)
    week52_low = price_data.get("week52_low", 0)

    if week52_high <= 0 or week52_low <= 0:
        return {"conservative": 0, "neutral": 0, "aggressive": 0}

    # 현재가 위치 기반 목표가
    # 보수적: 현재가 + (52주 고가 - 현재가) * 0.3
    # 중립적: 현재가 + (52주 고가 - 현재가) * 0.5
    # 공격적: 52주 고가 돌파 (52주 고가 * 1.05)

    conservative = current_price + (week52_high - current_price) * 0.3
    neutral = current_price + (week52_high - current_price) * 0.5
    aggressive = week52_high * 1.05

    return {
        "conservative": conservative,
        "neutral": neutral,
        "aggressive": aggressive
    }


def calculate_market_adjustment(market_context: Dict[str, Any]) -> float:
    """
    시장 맥락 기반 조정 계수 계산

    Returns:
        float: 조정 계수 (0.9 ~ 1.1)
    """
    market_trend = market_context.get("market_trend", "neutral")
    market_strength = market_context.get("market_strength", 50)
    volatility_level = market_context.get("volatility_level", "medium")

    # 기본 계수 1.0
    adjustment = 1.0

    # 시장 추세 반영
    if market_trend == "bullish":
        adjustment += 0.05
    elif market_trend == "bearish":
        adjustment -= 0.05

    # 시장 강도 반영 (50 기준)
    strength_adjustment = (market_strength - 50) / 1000  # -0.05 ~ +0.05
    adjustment += strength_adjustment

    # 변동성 반영 (높은 변동성은 할인)
    if volatility_level == "high":
        adjustment -= 0.03
    elif volatility_level == "low":
        adjustment += 0.02

    # 0.9 ~ 1.1 범위로 제한
    adjustment = max(0.9, min(1.1, adjustment))

    return adjustment


def calculate_conservative_target(
    current_price: float,
    per_targets: Dict[str, float],
    pbr_targets: Dict[str, float],
    technical_targets: Dict[str, float],
    analyst_target: float,
    market_adjustment: float
) -> float:
    """보수적 목표가 계산 (낮은 값에 가중치)"""
    targets = []
    weights = []

    # PER 기반 (가중치 30%)
    if per_targets["conservative"] > 0:
        targets.append(per_targets["conservative"])
        weights.append(0.30)

    # PBR 기반 (가중치 25%)
    if pbr_targets["conservative"] > 0:
        targets.append(pbr_targets["conservative"])
        weights.append(0.25)

    # 기술적 분석 (가중치 20%)
    if technical_targets["conservative"] > 0:
        targets.append(technical_targets["conservative"])
        weights.append(0.20)

    # 애널리스트 목표가 (가중치 25%, 있는 경우)
    if analyst_target > 0:
        # 보수적이므로 애널리스트 목표가의 90%만 반영
        targets.append(analyst_target * 0.9)
        weights.append(0.25)

    if not targets:
        return current_price * 1.05  # 최소 5% 상승 가정

    # 가중 평균
    total_weight = sum(weights)
    weighted_sum = sum(t * w for t, w in zip(targets, weights))
    target = (weighted_sum / total_weight) * market_adjustment

    # 현재가보다 낮으면 현재가의 95%로 설정
    return max(target, current_price * 0.95)


def calculate_neutral_target(
    current_price: float,
    per_targets: Dict[str, float],
    pbr_targets: Dict[str, float],
    technical_targets: Dict[str, float],
    analyst_target: float,
    market_adjustment: float
) -> float:
    """중립적 목표가 계산 (균형 잡힌 가중치)"""
    targets = []
    weights = []

    # PER 기반 (가중치 30%)
    if per_targets["neutral"] > 0:
        targets.append(per_targets["neutral"])
        weights.append(0.30)

    # PBR 기반 (가중치 25%)
    if pbr_targets["neutral"] > 0:
        targets.append(pbr_targets["neutral"])
        weights.append(0.25)

    # 기술적 분석 (가중치 20%)
    if technical_targets["neutral"] > 0:
        targets.append(technical_targets["neutral"])
        weights.append(0.20)

    # 애널리스트 목표가 (가중치 25%, 있는 경우)
    if analyst_target > 0:
        targets.append(analyst_target)
        weights.append(0.25)

    if not targets:
        return current_price * 1.10  # 최소 10% 상승 가정

    # 가중 평균
    total_weight = sum(weights)
    weighted_sum = sum(t * w for t, w in zip(targets, weights))
    target = (weighted_sum / total_weight) * market_adjustment

    return max(target, current_price)


def calculate_aggressive_target(
    current_price: float,
    per_targets: Dict[str, float],
    pbr_targets: Dict[str, float],
    technical_targets: Dict[str, float],
    analyst_target: float,
    market_adjustment: float
) -> float:
    """공격적 목표가 계산 (높은 값에 가중치)"""
    targets = []
    weights = []

    # PER 기반 (가중치 35%)
    if per_targets["aggressive"] > 0:
        targets.append(per_targets["aggressive"])
        weights.append(0.35)

    # PBR 기반 (가중치 20%)
    if pbr_targets["aggressive"] > 0:
        targets.append(pbr_targets["aggressive"])
        weights.append(0.20)

    # 기술적 분석 (가중치 25%)
    if technical_targets["aggressive"] > 0:
        targets.append(technical_targets["aggressive"])
        weights.append(0.25)

    # 애널리스트 목표가 (가중치 20%, 있는 경우)
    if analyst_target > 0:
        # 공격적이므로 애널리스트 목표가의 110% 반영
        targets.append(analyst_target * 1.1)
        weights.append(0.20)

    if not targets:
        return current_price * 1.20  # 최소 20% 상승 가정

    # 가중 평균
    total_weight = sum(weights)
    weighted_sum = sum(t * w for t, w in zip(targets, weights))
    target = (weighted_sum / total_weight) * market_adjustment

    return max(target, current_price * 1.05)
