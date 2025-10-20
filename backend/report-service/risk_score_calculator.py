"""
🔥 Phase 3.2: 리스크 점수 정량화 시스템 (0-100)

리스크를 여러 차원으로 분해하여 정량적으로 계산:
- 뉴스 감성 리스크 (0-30점)
- 변동성 리스크 (0-25점)
- 재무 리스크 (0-20점)
- 시장 리스크 (0-15점)
- 유동성 리스크 (0-10점)

총점이 낮을수록 안전, 높을수록 위험
"""
from typing import Dict, Any, Optional


def calculate_news_sentiment_risk(news_trend: Dict[str, Any]) -> float:
    """
    뉴스 감성 리스크 계산 (0-30점)

    Args:
        news_trend: 뉴스 트렌드 분석 결과

    Returns:
        float: 뉴스 감성 리스크 점수 (0-30)
    """
    if not news_trend or news_trend.get("total_count", 0) == 0:
        return 15.0  # 데이터 없으면 중립 (50%)

    # 1. 부정 뉴스 비율 (0-15점)
    negative_ratio = news_trend.get("negative_ratio", 0) / 100  # 0~1
    negative_score = negative_ratio * 15

    # 2. 평균 감성 점수 (0-10점) - 부정적일수록 높음
    avg_sentiment = news_trend.get("avg_sentiment_score", 0)  # -1 ~ 1
    # -1 → 10점, 0 → 5점, 1 → 0점
    sentiment_score = (1 - avg_sentiment) / 2 * 10

    # 3. 최근 감성 악화 여부 (0-5점)
    recent_change = news_trend.get("recent_sentiment_change", "불변")
    if recent_change == "악화":
        change_penalty = 5.0
    elif recent_change == "불변":
        change_penalty = 2.5
    else:  # 개선
        change_penalty = 0.0

    total = negative_score + sentiment_score + change_penalty
    return min(30.0, max(0.0, total))


def calculate_volatility_risk(
    current_price: Optional[float],
    week52_high: Optional[float],
    week52_low: Optional[float],
    avg_volume: Optional[int],
    current_volume: Optional[int],
    technical_indicators: Optional[Dict[str, Any]] = None
) -> float:
    """
    변동성 리스크 계산 (0-25점)

    Args:
        current_price: 현재가
        week52_high: 52주 최고가
        week52_low: 52주 최저가
        avg_volume: 평균 거래량
        current_volume: 현재 거래량
        technical_indicators: 기술적 지표 (볼린저밴드, ATR 등)

    Returns:
        float: 변동성 리스크 점수 (0-25)
    """
    score = 0.0

    # 1. 52주 고저 대비 현재가 위치 (0-10점)
    if current_price and week52_high and week52_low and week52_high > week52_low:
        price_range = week52_high - week52_low
        position_from_low = (current_price - week52_low) / price_range  # 0~1

        # 52주 최고가 근처 또는 최저가 근처 = 위험
        if position_from_low > 0.9:  # 고점 근처
            score += 10.0
        elif position_from_low < 0.1:  # 저점 근처
            score += 10.0
        elif 0.4 <= position_from_low <= 0.6:  # 중간 대역
            score += 3.0
        else:  # 중간~고점/저점 사이
            score += 6.0

    # 2. 거래량 급증 (0-8점)
    if avg_volume and current_volume:
        volume_ratio = current_volume / avg_volume
        if volume_ratio >= 3.0:  # 3배 이상 급증
            score += 8.0
        elif volume_ratio >= 2.0:
            score += 5.0
        elif volume_ratio >= 1.5:
            score += 2.0
        # 거래량 감소는 유동성 리스크에서 처리

    # 3. 볼린저 밴드 이탈 (0-7점)
    if technical_indicators and "bollinger_position" in technical_indicators:
        bb_pos = technical_indicators["bollinger_position"]  # 예: "above_upper", "below_lower", "normal"
        if bb_pos in ["above_upper", "below_lower"]:
            score += 7.0
        elif bb_pos == "near_upper" or bb_pos == "near_lower":
            score += 3.0

    return min(25.0, max(0.0, score))


def calculate_financial_risk(
    per: Optional[float],
    pbr: Optional[float],
    roe: Optional[float],
    debt_ratio: Optional[float],
    operating_margin: Optional[float]
) -> float:
    """
    재무 리스크 계산 (0-20점)

    Args:
        per: 주가수익비율
        pbr: 주가순자산비율
        roe: 자기자본이익률 (%)
        debt_ratio: 부채비율 (%)
        operating_margin: 영업이익률 (%)

    Returns:
        float: 재무 리스크 점수 (0-20)
    """
    score = 0.0

    # 1. PER 위험 (0-5점)
    if per is not None:
        if per < 0:  # 적자
            score += 5.0
        elif per > 50:  # 고평가 (50배 이상)
            score += 4.0
        elif per > 30:
            score += 2.0
        elif per < 5:  # 저평가 (너무 낮으면 오히려 의심)
            score += 1.0

    # 2. ROE 위험 (0-5점)
    if roe is not None:
        if roe < 0:  # 자본잠식
            score += 5.0
        elif roe < 5:  # 낮은 수익성
            score += 3.0
        elif roe < 10:
            score += 1.0
        # ROE >= 10%는 양호 (0점)

    # 3. 부채비율 위험 (0-6점)
    if debt_ratio is not None:
        if debt_ratio > 200:  # 200% 이상
            score += 6.0
        elif debt_ratio > 150:
            score += 4.0
        elif debt_ratio > 100:
            score += 2.0
        # 부채비율 100% 이하는 양호

    # 4. 영업이익률 위험 (0-4점)
    if operating_margin is not None:
        if operating_margin < 0:  # 영업적자
            score += 4.0
        elif operating_margin < 3:  # 낮은 수익성
            score += 2.0
        elif operating_margin < 5:
            score += 1.0

    return min(20.0, max(0.0, score))


def calculate_market_risk(
    kospi_change: Optional[float],
    sector_relative_strength: Optional[float],
    foreign_ownership_change: Optional[float],
    program_trading_net: Optional[int]
) -> float:
    """
    시장 리스크 계산 (0-15점)

    Args:
        kospi_change: 코스피 등락률 (%)
        sector_relative_strength: 업종 대비 상대 강도 (코스피 대비 %)
        foreign_ownership_change: 외국인 지분율 변화 (%)
        program_trading_net: 프로그램매매 순매수 (억원)

    Returns:
        float: 시장 리스크 점수 (0-15)
    """
    score = 0.0

    # 1. 코스피 급락 (0-6점)
    if kospi_change is not None:
        if kospi_change <= -3.0:  # 3% 이상 급락
            score += 6.0
        elif kospi_change <= -2.0:
            score += 4.0
        elif kospi_change <= -1.0:
            score += 2.0

    # 2. 상대 약세 (0-5점)
    if sector_relative_strength is not None:
        # 예: -3.0 = 코스피 대비 3% 약세
        if sector_relative_strength <= -3.0:
            score += 5.0
        elif sector_relative_strength <= -2.0:
            score += 3.0
        elif sector_relative_strength <= -1.0:
            score += 1.0

    # 3. 외국인 이탈 (0-2점)
    if foreign_ownership_change is not None:
        if foreign_ownership_change < -1.0:  # 1%p 이상 감소
            score += 2.0
        elif foreign_ownership_change < -0.5:
            score += 1.0

    # 4. 프로그램매매 순매도 (0-2점)
    if program_trading_net is not None:
        if program_trading_net < -500:  # 500억 이상 순매도
            score += 2.0
        elif program_trading_net < -200:
            score += 1.0

    return min(15.0, max(0.0, score))


def calculate_liquidity_risk(
    current_volume: Optional[int],
    avg_volume: Optional[int],
    market_cap: Optional[int],
    free_float: Optional[float]
) -> float:
    """
    유동성 리스크 계산 (0-10점)

    Args:
        current_volume: 현재 거래량 (주)
        avg_volume: 평균 거래량 (주)
        market_cap: 시가총액 (억원)
        free_float: 유동 주식 비율 (%)

    Returns:
        float: 유동성 리스크 점수 (0-10)
    """
    score = 0.0

    # 1. 거래량 감소 (0-4점)
    if current_volume and avg_volume:
        volume_ratio = current_volume / avg_volume
        if volume_ratio < 0.3:  # 평균의 30% 이하
            score += 4.0
        elif volume_ratio < 0.5:
            score += 2.0

    # 2. 시가총액 (0-3점)
    if market_cap is not None:
        if market_cap < 500:  # 500억 미만 (초소형주)
            score += 3.0
        elif market_cap < 1000:  # 1000억 미만
            score += 2.0
        elif market_cap < 3000:  # 3000억 미만
            score += 1.0

    # 3. 유동 주식 비율 (0-3점)
    if free_float is not None:
        if free_float < 20:  # 20% 미만 (대주주 집중)
            score += 3.0
        elif free_float < 30:
            score += 2.0
        elif free_float < 40:
            score += 1.0

    return min(10.0, max(0.0, score))


def calculate_total_risk_score(
    news_trend: Dict[str, Any],
    stock_info: Dict[str, Any],
    market_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    전체 리스크 점수 계산 (0-100)

    Args:
        news_trend: 뉴스 트렌드 분석 결과
        stock_info: 종목 정보 (재무, 기술적 지표 등)
        market_data: 시장 데이터 (코스피, 업종 등)

    Returns:
        Dict: 리스크 점수 상세
            - total_score: 총 리스크 점수 (0-100)
            - risk_level: 위험도 레벨 ('low', 'medium', 'high')
            - breakdown: 카테고리별 점수
                - news_sentiment: 뉴스 감성 리스크 (0-30)
                - volatility: 변동성 리스크 (0-25)
                - financial: 재무 리스크 (0-20)
                - market: 시장 리스크 (0-15)
                - liquidity: 유동성 리스크 (0-10)
    """
    # 1. 뉴스 감성 리스크 (0-30)
    news_risk = calculate_news_sentiment_risk(news_trend)

    # 2. 변동성 리스크 (0-25)
    volatility_risk = calculate_volatility_risk(
        current_price=stock_info.get("current_price"),
        week52_high=stock_info.get("week52_high"),
        week52_low=stock_info.get("week52_low"),
        avg_volume=stock_info.get("avg_volume"),
        current_volume=stock_info.get("current_volume"),
        technical_indicators=stock_info.get("technical_indicators")
    )

    # 3. 재무 리스크 (0-20)
    financial_risk = calculate_financial_risk(
        per=stock_info.get("per"),
        pbr=stock_info.get("pbr"),
        roe=stock_info.get("roe"),
        debt_ratio=stock_info.get("debt_ratio"),
        operating_margin=stock_info.get("operating_margin")
    )

    # 4. 시장 리스크 (0-15)
    market_risk = calculate_market_risk(
        kospi_change=market_data.get("kospi_change"),
        sector_relative_strength=market_data.get("sector_relative_strength"),
        foreign_ownership_change=market_data.get("foreign_ownership_change"),
        program_trading_net=market_data.get("program_trading_net")
    )

    # 5. 유동성 리스크 (0-10)
    liquidity_risk = calculate_liquidity_risk(
        current_volume=stock_info.get("current_volume"),
        avg_volume=stock_info.get("avg_volume"),
        market_cap=stock_info.get("market_cap"),
        free_float=stock_info.get("free_float")
    )

    # 총 리스크 점수 계산
    total_score = news_risk + volatility_risk + financial_risk + market_risk + liquidity_risk

    # 리스크 레벨 판정 (0-100 → low/medium/high)
    if total_score < 30:
        risk_level = "low"
    elif total_score < 60:
        risk_level = "medium"
    else:
        risk_level = "high"

    return {
        "total_score": round(total_score, 2),
        "risk_level": risk_level,
        "breakdown": {
            "news_sentiment": round(news_risk, 2),
            "volatility": round(volatility_risk, 2),
            "financial": round(financial_risk, 2),
            "market": round(market_risk, 2),
            "liquidity": round(liquidity_risk, 2)
        },
        "description": get_risk_description(total_score, risk_level)
    }


def get_risk_description(total_score: float, risk_level: str) -> str:
    """
    리스크 점수에 대한 한국어 설명 생성

    Args:
        total_score: 총 리스크 점수 (0-100)
        risk_level: 위험도 레벨

    Returns:
        str: 리스크 설명
    """
    if risk_level == "low":
        return f"리스크 점수 {total_score:.1f}점 - 상대적으로 안정적인 투자 환경입니다. 다만 시장 변동성에 주의하세요."
    elif risk_level == "medium":
        return f"리스크 점수 {total_score:.1f}점 - 중간 수준의 리스크가 존재합니다. 분산 투자와 손절 전략을 권장합니다."
    else:  # high
        return f"리스크 점수 {total_score:.1f}점 - 높은 리스크가 감지되었습니다. 신중한 접근이 필요하며, 소액 투자를 권장합니다."


# 테스트 코드
if __name__ == "__main__":
    # 샘플 데이터로 테스트
    sample_news_trend = {
        "total_count": 20,
        "negative_ratio": 40.0,  # 40% 부정 뉴스
        "avg_sentiment_score": -0.3,  # 약간 부정
        "recent_sentiment_change": "악화"
    }

    sample_stock_info = {
        "current_price": 65000,
        "week52_high": 75000,
        "week52_low": 55000,
        "avg_volume": 1000000,
        "current_volume": 2500000,  # 2.5배 급증
        "per": 12.5,
        "pbr": 1.2,
        "roe": 8.0,  # 낮은 ROE
        "debt_ratio": 180,  # 높은 부채비율
        "operating_margin": 4.5,
        "market_cap": 15000,  # 1.5조
        "free_float": 35.0
    }

    sample_market_data = {
        "kospi_change": -2.5,  # 코스피 2.5% 하락
        "sector_relative_strength": -1.8,  # 업종 대비 약세
        "foreign_ownership_change": -0.7,
        "program_trading_net": -300
    }

    result = calculate_total_risk_score(
        news_trend=sample_news_trend,
        stock_info=sample_stock_info,
        market_data=sample_market_data
    )

    print("\n=== 리스크 점수 테스트 ===")
    print(f"총 리스크 점수: {result['total_score']:.2f}/100")
    print(f"위험도 레벨: {result['risk_level'].upper()}")
    print(f"\n세부 분석:")
    for category, score in result['breakdown'].items():
        print(f"  - {category}: {score:.2f}점")
    print(f"\n설명: {result['description']}")
