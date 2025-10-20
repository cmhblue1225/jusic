"""
AI Ensemble 시스템
- GPT-4 Turbo + Claude 3.5 Sonnet 앙상블
- 두 모델의 분석 결과를 투표(Voting)로 결합
- 신뢰도(Confidence) 점수 계산 (모델 간 합의 정도)
- 폴백 로직: 한 모델 실패 시 다른 모델 결과 사용

🔥 Phase 1.3 개선사항:
- 뉴스 7일 50개 전체 트렌드 분석
- 애널리스트 컨센서스 반영
- 업종/시장 맥락 추가

🔥 Phase 3.2 개선사항:
- 리스크 점수 정량화 (0-100) - 뉴스/변동성/재무/시장/유동성 5개 카테고리

🔥 Phase 3.3 개선사항:
- 신뢰도 계산 개선 - 5개 차원 (권고/평가점수/리스크레벨/리스크점수/타임프레임) 가중 평균
"""
import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from collections import Counter
import numpy as np  # 🔥 Phase 3.3: 표준편차 계산용
from openai import AsyncOpenAI
import anthropic
from risk_score_calculator import calculate_total_risk_score  # 🔥 Phase 3.2

# OpenAI 클라이언트 초기화 (지연 초기화)
_openai_client = None
_anthropic_client = None


def get_openai_client():
    """OpenAI 클라이언트 지연 초기화 및 반환"""
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        _openai_client = AsyncOpenAI(api_key=api_key)
    return _openai_client


def get_anthropic_client():
    """Anthropic 클라이언트 지연 초기화 및 반환"""
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다.")
        _anthropic_client = anthropic.AsyncAnthropic(api_key=api_key)
    return _anthropic_client


def analyze_news_trend(news_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    🔥 Phase 1.3: 뉴스 트렌드 분석 (7일 50개 전체 분석)

    Args:
        news_data: 뉴스 데이터 리스트 (최대 50개)

    Returns:
        Dict: 뉴스 트렌드 분석 결과
            - total_count: 총 뉴스 수
            - positive_count/negative_count/neutral_count: 감성별 뉴스 수
            - positive_ratio/negative_ratio: 긍정/부정 비율
            - avg_sentiment_score: 평균 감성 점수
            - avg_impact_score: 평균 영향도
            - high_impact_news: 고영향도 뉴스 (impact >= 0.7)
            - trending_keywords: 자주 등장하는 키워드 (상위 5개)
            - recent_sentiment_change: 최근 3일 vs 이전 4일 감성 변화
    """
    if not news_data:
        return {
            "total_count": 0,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "positive_ratio": 0.0,
            "negative_ratio": 0.0,
            "avg_sentiment_score": 0.0,
            "avg_impact_score": 0.0,
            "high_impact_news": [],
            "trending_keywords": [],
            "recent_sentiment_change": "불변"
        }

    total_count = len(news_data)
    positive_count = sum(1 for n in news_data if n.get("sentiment_score", 0) > 0)
    negative_count = sum(1 for n in news_data if n.get("sentiment_score", 0) < 0)
    neutral_count = total_count - positive_count - negative_count

    positive_ratio = (positive_count / total_count * 100) if total_count > 0 else 0.0
    negative_ratio = (negative_count / total_count * 100) if total_count > 0 else 0.0

    avg_sentiment = sum(n.get("sentiment_score", 0) for n in news_data) / total_count
    avg_impact = sum(n.get("impact_score", 0) for n in news_data) / total_count

    # 고영향도 뉴스 추출 (impact_score >= 0.7)
    high_impact_news = [
        {
            "title": n["title"],
            "sentiment_score": n.get("sentiment_score", 0),
            "impact_score": n.get("impact_score", 0)
        }
        for n in news_data if n.get("impact_score", 0) >= 0.7
    ][:5]  # 상위 5개만

    # 키워드 추출 (제목에서 자주 등장하는 단어, 2글자 이상)
    all_words = []
    for n in news_data:
        title = n.get("title", "")
        # 간단한 한글 단어 추출 (2글자 이상)
        words = [word.strip() for word in title.split() if len(word) >= 2 and word.isalpha()]
        all_words.extend(words)

    # 불용어 제거 (조사, 접속사 등)
    stopwords = {"있는", "있다", "하는", "그리고", "이번", "올해", "작년", "지난", "최근"}
    filtered_words = [w for w in all_words if w not in stopwords]

    # 상위 5개 키워드
    word_counts = Counter(filtered_words)
    trending_keywords = [word for word, count in word_counts.most_common(5)]

    # 최근 감성 변화 (최근 3일 vs 이전 4일)
    # published_at 기준 정렬 (이미 정렬되어 있다고 가정)
    recent_news = news_data[:int(total_count * 0.4)]  # 최근 40%
    older_news = news_data[int(total_count * 0.4):]   # 이전 60%

    if recent_news and older_news:
        recent_avg = sum(n.get("sentiment_score", 0) for n in recent_news) / len(recent_news)
        older_avg = sum(n.get("sentiment_score", 0) for n in older_news) / len(older_news)

        if recent_avg > older_avg + 0.1:
            sentiment_change = "개선"
        elif recent_avg < older_avg - 0.1:
            sentiment_change = "악화"
        else:
            sentiment_change = "불변"
    else:
        sentiment_change = "불변"

    return {
        "total_count": total_count,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "positive_ratio": round(positive_ratio, 1),
        "negative_ratio": round(negative_ratio, 1),
        "avg_sentiment_score": round(avg_sentiment, 2),
        "avg_impact_score": round(avg_impact, 2),
        "high_impact_news": high_impact_news,
        "trending_keywords": trending_keywords,
        "recent_sentiment_change": sentiment_change
    }


async def analyze_with_gpt4(
    symbol: str,
    symbol_name: str,
    price_data: Dict[str, Any],
    news_data: List[Dict[str, Any]],
    financial_data: Dict[str, Any] = None,
    investor_data: Dict[str, Any] = None,
    analyst_opinion: Dict[str, Any] = None,  # 🔥 Phase 1.3
    sector_info: Dict[str, Any] = None,      # 🔥 Phase 1.3
    market_index: Dict[str, Any] = None,     # 🔥 Phase 1.3
    credit_balance: List[Dict] = None,       # 🔥 Phase 1.3
    short_selling: List[Dict] = None,        # 🔥 Phase 1.3
    program_trading: List[Dict] = None,      # 🔥 Phase 1.3
    institutional_flow: Dict[str, Any] = None  # 🔥 Phase 1.3
) -> Optional[Dict[str, Any]]:
    """
    🔥 Phase 1.3 개선: GPT-4 Turbo 기반 종목 분석 (뉴스 트렌드, 애널리스트 의견, 업종/시장 맥락 추가)
    🔥 Phase 3.2 개선: 리스크 점수 정량화 (0-100) 추가

    Returns:
        Dict: AI 분석 결과 또는 None (실패 시)
    """
    # 🔥 Phase 1.3: 뉴스 트렌드 분석 (7일 50개 전체 분석)
    news_trend = analyze_news_trend(news_data)

    # 🔥 Phase 3.2: 리스크 점수 계산 (0-100 정량화)
    stock_info = {
        "current_price": price_data.get("current_price"),
        "week52_high": price_data.get("week52_high"),
        "week52_low": price_data.get("week52_low"),
        "avg_volume": price_data.get("avg_volume"),
        "current_volume": price_data.get("volume"),
        "per": financial_data.get("per") if financial_data else None,
        "pbr": financial_data.get("pbr") if financial_data else None,
        "roe": financial_data.get("roe") if financial_data else None,
        "debt_ratio": financial_data.get("debt_ratio") if financial_data else None,
        "operating_margin": financial_data.get("operating_margin") if financial_data else None,
        "market_cap": price_data.get("market_cap"),
        "free_float": None,  # TODO: 추후 KIS API에서 추가
        "technical_indicators": {
            "rsi": price_data.get("rsi"),
            "bollinger_position": None  # TODO: 추후 계산 추가
        }
    }

    market_data_dict = {
        "kospi_change": market_index.get("kospi_change_rate") if market_index else None,
        "sector_relative_strength": None,  # TODO: 추후 계산 추가
        "foreign_ownership_change": None,  # TODO: 추후 추가
        "program_trading_net": program_trading[0].get("program_net_buy") if program_trading else None
    }

    risk_score_result = calculate_total_risk_score(
        news_trend=news_trend,
        stock_info=stock_info,
        market_data=market_data_dict
    )

    # 고영향도 뉴스 텍스트 생성
    high_impact_lines = []
    for i, news in enumerate(news_trend["high_impact_news"], 1):
        sentiment_text = "긍정" if news["sentiment_score"] > 0 else "부정" if news["sentiment_score"] < 0 else "중립"
        high_impact_lines.append(
            f"{i}. {news['title']}\n"
            f"   감성: {sentiment_text} ({news['sentiment_score']:.2f}), 영향도: {news['impact_score']:.2f}"
        )

    high_impact_text = "\n".join(high_impact_lines) if high_impact_lines else "고영향도 뉴스 없음"

    # 뉴스 트렌드 요약 텍스트
    news_trend_text = f"""
📊 뉴스 트렌드 분석 (7일, 총 {news_trend['total_count']}개)
- 긍정: {news_trend['positive_count']}개 ({news_trend['positive_ratio']}%)
- 부정: {news_trend['negative_count']}개 ({news_trend['negative_ratio']}%)
- 중립: {news_trend['neutral_count']}개
- 평균 감성 점수: {news_trend['avg_sentiment_score']:.2f}
- 평균 영향도: {news_trend['avg_impact_score']:.2f}
- 최근 감성 변화: {news_trend['recent_sentiment_change']}
- 트렌딩 키워드: {', '.join(news_trend['trending_keywords']) if news_trend['trending_keywords'] else '없음'}

🔥 고영향도 뉴스 (impact ≥ 0.7):
{high_impact_text}

🔥 Phase 3.2: 정량적 리스크 점수 (0-100)
총 리스크 점수: {risk_score_result['total_score']:.1f}/100 (위험도: {risk_score_result['risk_level'].upper()})
세부 분석:
  - 뉴스 감성 리스크: {risk_score_result['breakdown']['news_sentiment']:.1f}/30
  - 변동성 리스크: {risk_score_result['breakdown']['volatility']:.1f}/25
  - 재무 리스크: {risk_score_result['breakdown']['financial']:.1f}/20
  - 시장 리스크: {risk_score_result['breakdown']['market']:.1f}/15
  - 유동성 리스크: {risk_score_result['breakdown']['liquidity']:.1f}/10
설명: {risk_score_result['description']}
"""

    # 2. 재무 데이터 텍스트 생성
    financial_data = financial_data or {}
    financial_text = f"""
- PER: {financial_data.get('per', 'N/A')}, PBR: {financial_data.get('pbr', 'N/A')}, ROE: {financial_data.get('roe', 'N/A')}%
- 배당수익률: {financial_data.get('dividend_yield', 'N/A')}%, EPS: {financial_data.get('eps', 'N/A')}원
- 영업이익률: {financial_data.get('operating_margin', 'N/A')}%, 부채비율: {financial_data.get('debt_ratio', 'N/A')}%
""" if financial_data else "재무 데이터 없음"

    # 3. 투자자 동향 텍스트 생성
    investor_data = investor_data or {}
    investor_text = f"""
- 외국인: {investor_data.get('foreign_net_buy', 0):+,}주, 기관: {investor_data.get('institution_net_buy', 0):+,}주
""" if investor_data else "투자자 동향 데이터 없음"

    # 🔥 Phase 1.3: 애널리스트 컨센서스 텍스트 생성
    analyst_opinion = analyst_opinion or {}
    analyst_text = ""
    if analyst_opinion.get("total_count", 0) > 0:
        analyst_text = f"""
📈 애널리스트 컨센서스 (총 {analyst_opinion['total_count']}명)
- 매수: {analyst_opinion.get('buy_count', 0)}명
- 중립: {analyst_opinion.get('hold_count', 0)}명
- 매도: {analyst_opinion.get('sell_count', 0)}명
- 평균 목표가: {analyst_opinion.get('avg_target_price', 'N/A')}원
"""
    else:
        analyst_text = "애널리스트 의견 없음"

    # 🔥 Phase 1.3: 업종 정보 텍스트 생성
    sector_info = sector_info or {}
    sector_text = f"""
🏢 업종: {sector_info.get('sector_name', 'N/A')} (코드: {sector_info.get('sector_code', 'N/A')})
""" if sector_info.get("sector_name") else "업종 정보 없음"

    # 🔥 Phase 1.3: 시장 지수 비교 텍스트 생성
    market_index = market_index or {}
    market_text = ""
    if market_index.get("kospi_value"):
        kospi_change = market_index.get('kospi_change_rate', 0)
        stock_change = price_data.get('change_rate', 0)
        relative_strength = "강세" if stock_change > kospi_change else "약세" if stock_change < kospi_change else "동조"

        market_text = f"""
📊 시장 대비 상대 강도
- 코스피: {market_index['kospi_value']:.2f} ({kospi_change:+.2f}%)
- 종목: {stock_change:+.2f}%
- 상대 강도: {relative_strength} ({stock_change - kospi_change:+.2f}%p 차이)
"""
    else:
        market_text = "시장 지수 데이터 없음"

    # 🔥 Phase 1.3: 신용/공매도 트렌드 텍스트 생성
    advanced_flow_text = ""
    if credit_balance or short_selling or program_trading:
        advanced_flow_text = "\n## 고급 매매 동향\n"

        if credit_balance:
            latest_credit = credit_balance[0] if credit_balance else {}
            advanced_flow_text += f"- 신용잔고: {latest_credit.get('credit_balance', 'N/A')}\n"

        if short_selling:
            latest_short = short_selling[0] if short_selling else {}
            advanced_flow_text += f"- 공매도 잔고: {latest_short.get('short_balance', 'N/A')}\n"

        if program_trading:
            latest_program = program_trading[0] if program_trading else {}
            advanced_flow_text += f"- 프로그램 순매수: {latest_program.get('program_net_buy', 'N/A')}\n"

        if institutional_flow:
            advanced_flow_text += f"- 당일 외국인 순매수액: {institutional_flow.get('foreign_net_buy_amt', 0):+,}원\n"
            advanced_flow_text += f"- 당일 기관 순매수액: {institutional_flow.get('institution_net_buy_amt', 0):+,}원\n"

    # 4. 고급 기술적 지표 텍스트 생성
    advanced_indicators = ""
    if price_data.get('rsi'):
        advanced_indicators = f"""
## 고급 기술적 지표
- RSI: {price_data.get('rsi', 'N/A')} (과매수 >70, 과매도 <30)
- MACD: {price_data.get('macd', 'N/A')}, Signal: {price_data.get('macd_signal', 'N/A')}
- Stochastic %K: {price_data.get('stochastic_k', 'N/A')}, %D: {price_data.get('stochastic_d', 'N/A')}
- ADX: {price_data.get('adx', 'N/A')} (추세 강도, >25 강한 추세)
- OBV: {price_data.get('obv', 'N/A')} (거래량 추세)
- MFI: {price_data.get('mfi', 'N/A')} (거래량 가중 RSI)
"""

    # 5. 프롬프트 생성
    prompt = f"""
당신은 한국 주식 시장 전문 애널리스트입니다. 다음 **확장된 정보**를 바탕으로 종목을 종합 분석해주세요.

## 종목 정보
- 종목명: {symbol_name} ({symbol})
{sector_text}

## 주가 데이터
- 현재가: {price_data['current_price']:,}원 ({price_data['change_rate']:+.2f}%)
- 거래량: {price_data['volume']:,}주

{market_text}

## 기술적 지표
- MA5: {price_data.get('ma5', 'N/A')}, MA20: {price_data.get('ma20', 'N/A')}, MA60: {price_data.get('ma60', 'N/A')}
- 볼린저 밴드: {price_data.get('bollinger_upper', 'N/A')} / {price_data.get('bollinger_lower', 'N/A')}
- 거래량 비율: {price_data.get('volume_ratio', 'N/A')}
{advanced_indicators}

## 재무비율
{financial_text}

## 투자자 매매 동향
{investor_text}

{analyst_text}

{advanced_flow_text}

## 🔥 뉴스 트렌드 분석 (7일)
{news_trend_text}

## 분석 요청
다음 JSON 형식으로 응답해주세요:

{{
  "summary": "종합 요약 (3~5문장)",
  "risk_level": "위험도 ('low', 'medium', 'high')",
  "risk_score": "리스크 점수 (0~100, 숫자만, 위 정량적 리스크 점수를 참고하되 독립적 판단)",
  "recommendation": "투자 권고 ('buy', 'sell', 'hold')",
  "evaluation_score": "평가 점수 (0~100, 숫자만)",
  "reasoning": "판단 근거 (2~3문장)",
  "target_price_range": "목표 주가 범위 (예: '70000~80000')",
  "time_horizon": "투자 기간 ('short_term', 'medium_term', 'long_term')",
  "investment_strategy": "구체적인 투자 전략 (2~3문장, 진입/청산 시점 포함)",
  "technical_analysis": "기술적 분석 상세 (3~4문장, 이평선/RSI/MACD 등 해석)",
  "fundamental_analysis": "기본적 분석 상세 (3~4문장, PER/PBR/ROE 등 해석)",
  "market_sentiment": "시장 심리 분석 (2~3문장, 투자자 동향 포함)",
  "catalysts": "긍정적 촉매 요인 (3~5개 항목, 줄바꿈으로 구분)",
  "risk_factors": "주요 리스크 요인 (3~5개 항목, 줄바꿈으로 구분)",
  "timeframe_analysis": {{
    "short_term": {{
      "outlook": "단기 전망 (1주~1개월, 'bullish'/'bearish'/'neutral')",
      "key_factors": "단기 핵심 요인 (2~3문장, 기술적 지표 및 단기 뉴스 중심)",
      "entry_price": "단기 진입가 (숫자, 예: 65000)",
      "target_price": "단기 목표가 (숫자, 예: 72000)",
      "stop_loss": "단기 손절가 (숫자, 예: 62000)"
    }},
    "medium_term": {{
      "outlook": "중기 전망 (1~3개월, 'bullish'/'bearish'/'neutral')",
      "key_factors": "중기 핵심 요인 (2~3문장, 재무 및 업종 트렌드 중심)",
      "target_price": "중기 목표가 (숫자, 예: 80000)"
    }},
    "long_term": {{
      "outlook": "장기 전망 (6개월~1년, 'bullish'/'bearish'/'neutral')",
      "key_factors": "장기 핵심 요인 (2~3문장, 펀더멘털 및 성장성 중심)",
      "target_price": "장기 목표가 (숫자, 예: 95000)"
    }}
  }}
}}

**🔥 Phase 1.3 + 3.1 + 3.2 개선된 분석 가이드라인:**
1. **뉴스 트렌드 반영**: 7일간의 뉴스 감성 변화(개선/악화/불변), 고영향도 뉴스, 트렌딩 키워드를 종합 판단에 반드시 포함하세요.
2. **애널리스트 컨센서스**: 증권사 애널리스트들의 의견 분포와 평균 목표가를 참고하세요. 다만 이것은 참고사항이며, 당신의 독립적 판단이 우선입니다.
3. **업종/시장 맥락**: 코스피 대비 상대 강도를 분석하고, 시장 흐름 대비 종목의 강약을 평가하세요.
4. **고급 매매 동향**: 신용잔고, 공매도, 프로그램매매, 당일 외국인/기관 순매수액을 종합하여 단기 수급을 판단하세요.
5. **🆕 정량적 리스크 점수 활용** (Phase 3.2):
   - 위에 제공된 **정량적 리스크 점수**는 5개 카테고리(뉴스/변동성/재무/시장/유동성)로 세분화된 객관적 지표입니다.
   - 이를 참고하되, AI 자체 판단으로 risk_score (0~100)를 산출하세요. 시스템 점수와 다를 수 있습니다.
   - 예: 시스템 점수가 45점이지만, 최근 대형 호재가 있다면 AI는 35점으로 낮출 수 있습니다.
6. **위험도 평가**: 변동성, 뉴스 부정도(negative_ratio), 볼린저 밴드 이탈, 부채비율, 공매도 잔고 증가 여부를 고려하세요.
7. **투자 권고**: 기술적 지표, 뉴스 트렌드, 애널리스트 컨센서스, 투자자 동향을 종합하여 결정하세요.
8. **평가 점수**: 모든 데이터를 종합한 절대 점수(0~100)입니다. 데이터가 많을수록 더 정확하게 평가할 수 있습니다.
9. **멀티 타임프레임 분석** (Phase 3.1):
   - **단기 (1주~1개월)**: RSI, MACD, 볼린저밴드 등 기술적 지표 중심. 진입가/목표가/손절가를 구체적 숫자로 제시.
   - **중기 (1~3개월)**: 실적 발표, 업종 트렌드, 애널리스트 컨센서스 반영. 목표가 제시.
   - **장기 (6개월~1년)**: 펀더멘털(PER/PBR/ROE), 성장성, 경쟁력 분석. 장기 목표가 제시.
10. **심화 분석 필드는 필수**입니다. 데이터가 부족해도 현재 정보 기반으로 작성하세요.
11. 반드시 JSON 형식으로만 응답하세요.
"""

    try:
        print(f"🤖 [GPT-4] 분석 시작: {symbol_name}")
        client = get_openai_client()

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "당신은 한국 주식 시장 전문 애널리스트입니다. 기본적 분석과 기술적 분석을 결합한 종합 분석 전문가입니다. 항상 JSON 형식으로만 응답합니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        ai_response_text = response.choices[0].message.content
        ai_response = json.loads(ai_response_text)

        # 결과 정규화
        result = {
            "model": "gpt-4-turbo",
            "summary": ai_response.get("summary", ""),
            "risk_level": ai_response.get("risk_level", "medium").lower(),
            "risk_score": float(ai_response.get("risk_score", risk_score_result['total_score'])),  # 🔥 Phase 3.2
            "recommendation": ai_response.get("recommendation", "hold").lower(),
            "evaluation_score": float(ai_response.get("evaluation_score", 50)),
            "reasoning": ai_response.get("reasoning", ""),
            "target_price_range": ai_response.get("target_price_range", ""),
            "time_horizon": ai_response.get("time_horizon", "medium_term"),
            # 🔥 심화 분석 필드 추가
            "investment_strategy": ai_response.get("investment_strategy", ""),
            "technical_analysis": ai_response.get("technical_analysis", ""),
            "fundamental_analysis": ai_response.get("fundamental_analysis", ""),
            "market_sentiment": ai_response.get("market_sentiment", ""),
            "catalysts": ai_response.get("catalysts", ""),
            "risk_factors": ai_response.get("risk_factors", ""),
            # 🔥 Phase 3.1: 멀티 타임프레임 분석 추가
            "timeframe_analysis": ai_response.get("timeframe_analysis", {}),
            # 🔥 Phase 3.2: 정량적 리스크 점수 세부 정보 추가
            "risk_score_breakdown": risk_score_result['breakdown'],
            "risk_score_description": risk_score_result['description'],
            "raw_response": ai_response
        }

        # 값 검증
        if result["risk_level"] not in ["low", "medium", "high"]:
            result["risk_level"] = "medium"
        if result["recommendation"] not in ["buy", "sell", "hold"]:
            result["recommendation"] = "hold"
        if not (0 <= result["evaluation_score"] <= 100):
            result["evaluation_score"] = 50.0
        # 🔥 Phase 3.2: risk_score 검증
        if not (0 <= result["risk_score"] <= 100):
            result["risk_score"] = risk_score_result['total_score']

        print(f"✅ [GPT-4] 분석 완료: {result['recommendation']} (점수: {result['evaluation_score']})")
        return result

    except Exception as e:
        print(f"❌ [GPT-4] 오류: {str(e)}")
        return None


async def analyze_with_claude(
    symbol: str,
    symbol_name: str,
    price_data: Dict[str, Any],
    news_data: List[Dict[str, Any]],
    financial_data: Dict[str, Any] = None,
    investor_data: Dict[str, Any] = None,
    analyst_opinion: Dict[str, Any] = None,  # 🔥 Phase 1.3
    sector_info: Dict[str, Any] = None,      # 🔥 Phase 1.3
    market_index: Dict[str, Any] = None,     # 🔥 Phase 1.3
    credit_balance: List[Dict] = None,       # 🔥 Phase 1.3
    short_selling: List[Dict] = None,        # 🔥 Phase 1.3
    program_trading: List[Dict] = None,      # 🔥 Phase 1.3
    institutional_flow: Dict[str, Any] = None  # 🔥 Phase 1.3
) -> Optional[Dict[str, Any]]:
    """
    🔥 Phase 1.3 개선: Claude 3.5 Sonnet 기반 종목 분석 (리스크 분석 전문가, 뉴스 트렌드, 애널리스트 의견, 업종/시장 맥락 추가)
    🔥 Phase 3.2 개선: 리스크 점수 정량화 (0-100) 추가

    Returns:
        Dict: AI 분석 결과 또는 None (실패 시)
    """
    # 🔥 Phase 1.3: 뉴스 트렌드 분석 (7일 50개 전체 분석)
    news_trend = analyze_news_trend(news_data)

    # 🔥 Phase 3.2: 리스크 점수 계산 (0-100 정량화)
    stock_info = {
        "current_price": price_data.get("current_price"),
        "week52_high": price_data.get("week52_high"),
        "week52_low": price_data.get("week52_low"),
        "avg_volume": price_data.get("avg_volume"),
        "current_volume": price_data.get("volume"),
        "per": financial_data.get("per") if financial_data else None,
        "pbr": financial_data.get("pbr") if financial_data else None,
        "roe": financial_data.get("roe") if financial_data else None,
        "debt_ratio": financial_data.get("debt_ratio") if financial_data else None,
        "operating_margin": financial_data.get("operating_margin") if financial_data else None,
        "market_cap": price_data.get("market_cap"),
        "free_float": None,  # TODO: 추후 KIS API에서 추가
        "technical_indicators": {
            "rsi": price_data.get("rsi"),
            "bollinger_position": None  # TODO: 추후 계산 추가
        }
    }

    market_data_dict = {
        "kospi_change": market_index.get("kospi_change_rate") if market_index else None,
        "sector_relative_strength": None,  # TODO: 추후 계산 추가
        "foreign_ownership_change": None,  # TODO: 추후 추가
        "program_trading_net": program_trading[0].get("program_net_buy") if program_trading else None
    }

    risk_score_result = calculate_total_risk_score(
        news_trend=news_trend,
        stock_info=stock_info,
        market_data=market_data_dict
    )

    # 고영향도 뉴스 텍스트 생성
    high_impact_lines = []
    for i, news in enumerate(news_trend["high_impact_news"], 1):
        sentiment_text = "긍정" if news["sentiment_score"] > 0 else "부정" if news["sentiment_score"] < 0 else "중립"
        high_impact_lines.append(
            f"{i}. {news['title']}\n"
            f"   감성: {sentiment_text} ({news['sentiment_score']:.2f}), 영향도: {news['impact_score']:.2f}"
        )

    high_impact_text = "\n".join(high_impact_lines) if high_impact_lines else "고영향도 뉴스 없음"

    # 뉴스 트렌드 요약 텍스트
    news_trend_text = f"""
📊 뉴스 트렌드 분석 (7일, 총 {news_trend['total_count']}개)
- 긍정: {news_trend['positive_count']}개 ({news_trend['positive_ratio']}%)
- 부정: {news_trend['negative_count']}개 ({news_trend['negative_ratio']}%)
- 중립: {news_trend['neutral_count']}개
- 평균 감성 점수: {news_trend['avg_sentiment_score']:.2f}
- 평균 영향도: {news_trend['avg_impact_score']:.2f}
- 최근 감성 변화: {news_trend['recent_sentiment_change']}
- 트렌딩 키워드: {', '.join(news_trend['trending_keywords']) if news_trend['trending_keywords'] else '없음'}

🔥 고영향도 뉴스 (impact ≥ 0.7):
{high_impact_text}

🔥 Phase 3.2: 정량적 리스크 점수 (0-100)
총 리스크 점수: {risk_score_result['total_score']:.1f}/100 (위험도: {risk_score_result['risk_level'].upper()})
세부 분석:
  - 뉴스 감성 리스크: {risk_score_result['breakdown']['news_sentiment']:.1f}/30
  - 변동성 리스크: {risk_score_result['breakdown']['volatility']:.1f}/25
  - 재무 리스크: {risk_score_result['breakdown']['financial']:.1f}/20
  - 시장 리스크: {risk_score_result['breakdown']['market']:.1f}/15
  - 유동성 리스크: {risk_score_result['breakdown']['liquidity']:.1f}/10
설명: {risk_score_result['description']}
"""

    # 2. 재무 데이터 텍스트 생성
    financial_data = financial_data or {}
    financial_text = f"""
- PER: {financial_data.get('per', 'N/A')}, PBR: {financial_data.get('pbr', 'N/A')}, ROE: {financial_data.get('roe', 'N/A')}%
- 배당수익률: {financial_data.get('dividend_yield', 'N/A')}%, 부채비율: {financial_data.get('debt_ratio', 'N/A')}%
""" if financial_data else "재무 데이터 없음"

    # 3. 투자자 동향 텍스트 생성
    investor_data = investor_data or {}
    investor_text = f"""
- 외국인: {investor_data.get('foreign_net_buy', 0):+,}주, 기관: {investor_data.get('institution_net_buy', 0):+,}주
""" if investor_data else "투자자 동향 데이터 없음"

    # 🔥 Phase 1.3: 애널리스트 컨센서스 텍스트 생성
    analyst_opinion = analyst_opinion or {}
    analyst_text = ""
    if analyst_opinion.get("total_count", 0) > 0:
        analyst_text = f"""
📈 애널리스트 컨센서스 (총 {analyst_opinion['total_count']}명)
- 매수: {analyst_opinion.get('buy_count', 0)}명
- 중립: {analyst_opinion.get('hold_count', 0)}명
- 매도: {analyst_opinion.get('sell_count', 0)}명
- 평균 목표가: {analyst_opinion.get('avg_target_price', 'N/A')}원
"""
    else:
        analyst_text = "애널리스트 의견 없음"

    # 🔥 Phase 1.3: 업종 정보 텍스트 생성
    sector_info = sector_info or {}
    sector_text = f"""
🏢 업종: {sector_info.get('sector_name', 'N/A')} (코드: {sector_info.get('sector_code', 'N/A')})
""" if sector_info.get("sector_name") else "업종 정보 없음"

    # 🔥 Phase 1.3: 시장 지수 비교 텍스트 생성
    market_index = market_index or {}
    market_text = ""
    if market_index.get("kospi_value"):
        kospi_change = market_index.get('kospi_change_rate', 0)
        stock_change = price_data.get('change_rate', 0)
        relative_strength = "강세" if stock_change > kospi_change else "약세" if stock_change < kospi_change else "동조"

        market_text = f"""
📊 시장 대비 상대 강도
- 코스피: {market_index['kospi_value']:.2f} ({kospi_change:+.2f}%)
- 종목: {stock_change:+.2f}%
- 상대 강도: {relative_strength} ({stock_change - kospi_change:+.2f}%p 차이)
"""
    else:
        market_text = "시장 지수 데이터 없음"

    # 🔥 Phase 1.3: 신용/공매도 트렌드 텍스트 생성
    advanced_flow_text = ""
    if credit_balance or short_selling or program_trading:
        advanced_flow_text = "\n## 🚨 고급 매매 동향 (리스크 지표)\n"

        if credit_balance:
            latest_credit = credit_balance[0] if credit_balance else {}
            advanced_flow_text += f"- 신용잔고: {latest_credit.get('credit_balance', 'N/A')}\n"

        if short_selling:
            latest_short = short_selling[0] if short_selling else {}
            advanced_flow_text += f"- 공매도 잔고: {latest_short.get('short_balance', 'N/A')} (⚠️ 공매도 증가 시 하방 압력)\n"

        if program_trading:
            latest_program = program_trading[0] if program_trading else {}
            advanced_flow_text += f"- 프로그램 순매수: {latest_program.get('program_net_buy', 'N/A')}\n"

        if institutional_flow:
            advanced_flow_text += f"- 당일 외국인 순매수액: {institutional_flow.get('foreign_net_buy_amt', 0):+,}원\n"
            advanced_flow_text += f"- 당일 기관 순매수액: {institutional_flow.get('institution_net_buy_amt', 0):+,}원\n"

    # 4. 고급 기술적 지표 텍스트 생성
    advanced_indicators = ""
    if price_data.get('rsi'):
        advanced_indicators = f"""
## 고급 기술적 지표
- RSI: {price_data.get('rsi', 'N/A')}, MACD: {price_data.get('macd', 'N/A')}
- ADX: {price_data.get('adx', 'N/A')}, ATR: {price_data.get('atr', 'N/A')} (변동성 지표)
- Williams %R: {price_data.get('williams_r', 'N/A')} (과매수/과매도)
"""

    # 5. 프롬프트 생성
    prompt = f"""
당신은 한국 주식 시장 리스크 분석 전문가입니다. 다음 **확장된 정보**를 바탕으로 종목을 분석하되, **리스크 요인**과 **변동성**에 특히 집중해주세요.

## 종목 정보
- 종목명: {symbol_name} ({symbol})
{sector_text}

## 주가 데이터
- 현재가: {price_data['current_price']:,}원 ({price_data['change_rate']:+.2f}%)
- 거래량: {price_data['volume']:,}주

{market_text}

## 기술적 지표
- MA5: {price_data.get('ma5', 'N/A')}, MA20: {price_data.get('ma20', 'N/A')}
- 볼린저 밴드: {price_data.get('bollinger_upper', 'N/A')} / {price_data.get('bollinger_lower', 'N/A')}
- 변동성: {price_data.get('volatility', 'N/A')}
{advanced_indicators}

## 재무비율
{financial_text}

## 투자자 매매 동향
{investor_text}

{analyst_text}

{advanced_flow_text}

## 🔥 뉴스 트렌드 분석 (7일)
{news_trend_text}

## 분석 요청
다음 JSON 형식으로 응답해주세요:

{{
  "summary": "종합 요약 (3~5문장, 리스크 중심)",
  "risk_level": "위험도 ('low', 'medium', 'high')",
  "risk_score": "리스크 점수 (0~100, 숫자만, 위 정량적 리스크 점수를 참고하되 독립적 판단)",
  "recommendation": "투자 권고 ('buy', 'sell', 'hold')",
  "evaluation_score": "평가 점수 (0~100, 숫자만)",
  "reasoning": "판단 근거 (2~3문장, 리스크 요인 강조)",
  "target_price_range": "목표 주가 범위 (예: '70000~80000')",
  "time_horizon": "투자 기간 ('short_term', 'medium_term', 'long_term')",
  "investment_strategy": "구체적인 투자 전략 (2~3문장, 진입/청산 시점 포함)",
  "technical_analysis": "기술적 분석 상세 (3~4문장, 이평선/RSI/MACD 등 해석)",
  "fundamental_analysis": "기본적 분석 상세 (3~4문장, PER/PBR/ROE 등 해석)",
  "market_sentiment": "시장 심리 분석 (2~3문장, 투자자 동향 포함)",
  "catalysts": "긍정적 촉매 요인 (3~5개 항목, 줄바꿈으로 구분)",
  "risk_factors": "주요 리스크 요인 (3~5개 항목, 줄바꿈으로 구분)",
  "timeframe_analysis": {{
    "short_term": {{
      "outlook": "단기 전망 (1주~1개월, 'bullish'/'bearish'/'neutral')",
      "key_factors": "단기 핵심 요인 (2~3문장, 기술적 지표 및 단기 뉴스 중심)",
      "entry_price": "단기 진입가 (숫자, 예: 65000)",
      "target_price": "단기 목표가 (숫자, 예: 72000)",
      "stop_loss": "단기 손절가 (숫자, 예: 62000)"
    }},
    "medium_term": {{
      "outlook": "중기 전망 (1~3개월, 'bullish'/'bearish'/'neutral')",
      "key_factors": "중기 핵심 요인 (2~3문장, 재무 및 업종 트렌드 중심)",
      "target_price": "중기 목표가 (숫자, 예: 80000)"
    }},
    "long_term": {{
      "outlook": "장기 전망 (6개월~1년, 'bullish'/'bearish'/'neutral')",
      "key_factors": "장기 핵심 요인 (2~3문장, 펀더멘털 및 성장성 중심)",
      "target_price": "장기 목표가 (숫자, 예: 95000)"
    }}
  }}
}}

**🔥 Phase 1.3 + 3.2 개선된 리스크 중심 분석 가이드라인:**
1. **🆕 정량적 리스크 점수 활용** (Phase 3.2):
   - 위에 제공된 **정량적 리스크 점수**는 5개 카테고리(뉴스/변동성/재무/시장/유동성)로 세분화된 객관적 지표입니다.
   - 이를 참고하되, AI 자체 판단으로 risk_score (0~100)를 산출하세요. 시스템 점수와 다를 수 있습니다.
   - 예: 시스템 점수가 45점이지만, 최근 대형 호재가 있다면 AI는 35점으로 낮출 수 있습니다.
2. **뉴스 리스크 평가**: 7일간 뉴스 부정 비율이 높거나(>50%), 고영향도 부정 뉴스가 많으면 위험도를 높이세요. 최근 감성이 악화되었다면 더욱 주의하세요.
3. **공매도/신용 리스크**: 공매도 잔고 증가는 하방 압력 신호입니다. 신용잔고 급증은 변동성 확대 가능성을 의미합니다.
4. **변동성 지표**: ATR, 볼린저 밴드 이탈, Williams %R을 종합하여 변동성을 평가하세요.
5. **애널리스트 vs 실제**: 애널리스트 컨센서스가 낙관적이어도, 실제 매매 동향(외국인/기관 순매도)이 부정적이면 리스크를 강조하세요.
6. **시장 대비 약세**: 코스피가 상승하는데 종목이 하락하면 상대적 약세로 판단하고 원인을 분석하세요.
7. **부채비율 경고**: 부채비율이 200% 이상이면 재무 리스크를 명시적으로 언급하세요.
8. **평가 점수**: 리스크가 클수록 보수적으로 책정하세요. 데이터가 풍부할수록 정확도가 높아집니다.
9. **심화 분석 필드는 필수**입니다. 리스크 요인을 구체적으로 나열하세요.
10. 반드시 JSON 형식으로만 응답하세요.
"""

    try:
        print(f"🤖 [Claude] 분석 시작: {symbol_name}")
        client = get_anthropic_client()

        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            temperature=0.2,
            system="당신은 한국 주식 시장 리스크 분석 전문가입니다. 변동성과 위험 요인을 중점적으로 평가하며, 항상 JSON 형식으로만 응답합니다.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Claude 응답 파싱
        ai_response_text = response.content[0].text

        # JSON 추출 (Claude는 때때로 마크다운 코드블록으로 감싸므로 처리)
        if "```json" in ai_response_text:
            ai_response_text = ai_response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in ai_response_text:
            ai_response_text = ai_response_text.split("```")[1].strip()

        ai_response = json.loads(ai_response_text)

        # 결과 정규화
        result = {
            "model": "claude-3.5-sonnet",
            "summary": ai_response.get("summary", ""),
            "risk_level": ai_response.get("risk_level", "medium").lower(),
            "risk_score": float(ai_response.get("risk_score", risk_score_result['total_score'])),  # 🔥 Phase 3.2
            "recommendation": ai_response.get("recommendation", "hold").lower(),
            "evaluation_score": float(ai_response.get("evaluation_score", 50)),
            "reasoning": ai_response.get("reasoning", ""),
            "target_price_range": ai_response.get("target_price_range", ""),
            "time_horizon": ai_response.get("time_horizon", "medium_term"),
            # 🔥 심화 분석 필드 추가
            "investment_strategy": ai_response.get("investment_strategy", ""),
            "technical_analysis": ai_response.get("technical_analysis", ""),
            "fundamental_analysis": ai_response.get("fundamental_analysis", ""),
            "market_sentiment": ai_response.get("market_sentiment", ""),
            "catalysts": ai_response.get("catalysts", ""),
            "risk_factors": ai_response.get("risk_factors", ""),
            # 🔥 Phase 3.1: 멀티 타임프레임 분석 추가
            "timeframe_analysis": ai_response.get("timeframe_analysis", {}),
            # 🔥 Phase 3.2: 정량적 리스크 점수 세부 정보 추가
            "risk_score_breakdown": risk_score_result['breakdown'],
            "risk_score_description": risk_score_result['description'],
            "raw_response": ai_response
        }

        # 값 검증
        if result["risk_level"] not in ["low", "medium", "high"]:
            result["risk_level"] = "medium"
        if result["recommendation"] not in ["buy", "sell", "hold"]:
            result["recommendation"] = "hold"
        if not (0 <= result["evaluation_score"] <= 100):
            result["evaluation_score"] = 50.0
        # 🔥 Phase 3.2: risk_score 검증
        if not (0 <= result["risk_score"] <= 100):
            result["risk_score"] = risk_score_result['total_score']

        print(f"✅ [Claude] 분석 완료: {result['recommendation']} (점수: {result['evaluation_score']})")
        return result

    except Exception as e:
        print(f"❌ [Claude] 오류: {str(e)}")
        return None


def ensemble_vote(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    앙상블 투표 - 여러 모델의 분석 결과를 결합

    Args:
        results: 각 모델의 분석 결과 리스트

    Returns:
        Dict: 최종 앙상블 결과
            - summary: 종합 요약
            - risk_level: 위험도 (다수결)
            - recommendation: 투자 권고 (다수결)
            - evaluation_score: 평가 점수 (평균)
            - confidence_score: 신뢰도 (0~100, 모델 간 합의 정도)
            - model_agreement: 모델별 결과 비교
    """
    if not results:
        return {
            "summary": "AI 분석 결과 없음",
            "risk_level": "medium",
            "recommendation": "hold",
            "evaluation_score": 50.0,
            "confidence_score": 0.0,
            "model_agreement": {}
        }

    # 1. 투자 권고 다수결
    recommendations = [r["recommendation"] for r in results]
    recommendation_counts = {rec: recommendations.count(rec) for rec in set(recommendations)}
    final_recommendation = max(recommendation_counts, key=recommendation_counts.get)

    # 2. 위험도 다수결
    risk_levels = [r["risk_level"] for r in results]
    risk_counts = {risk: risk_levels.count(risk) for risk in set(risk_levels)}
    final_risk_level = max(risk_counts, key=risk_counts.get)

    # 3. 평가 점수 가중 평균 (GPT-4: 60%, Claude: 40%)
    weights = {"gpt-4-turbo": 0.6, "claude-3.5-sonnet": 0.4}
    weighted_scores = []
    for r in results:
        weight = weights.get(r["model"], 0.5)
        weighted_scores.append(r["evaluation_score"] * weight)

    final_score = sum(weighted_scores) / sum(weights.get(r["model"], 0.5) for r in results)

    # 4. 🔥 Phase 3.3: 개선된 신뢰도 계산 (모델 간 합의 정도)
    # - 투자 권고 일치율 (30%)
    rec_agreement = recommendation_counts[final_recommendation] / len(results) * 100

    # - 평가 점수 표준편차 (25%, 낮을수록 합의 높음)
    score_std = np.std([r["evaluation_score"] for r in results])
    score_agreement = max(0, 100 - score_std)  # 표준편차가 클수록 합의 낮음

    # - 🆕 리스크 레벨 일치율 (20%)
    risk_agreement = risk_counts[final_risk_level] / len(results) * 100

    # - 🆕 리스크 점수 일치도 (15%, Phase 3.2에서 추가된 필드 활용)
    risk_scores = [r.get("risk_score", 50) for r in results]
    risk_score_std = np.std(risk_scores) if len(risk_scores) > 1 else 0
    risk_score_agreement = max(0, 100 - risk_score_std)  # 표준편차가 클수록 합의 낮음

    # - 🆕 타임프레임 분석 일치도 (10%, Phase 3.1에서 추가된 필드 활용)
    # 단기/중기/장기 전망(outlook)이 일치하는지 확인
    timeframe_agreement = 0
    if all("timeframe_analysis" in r for r in results):
        short_outlooks = [r["timeframe_analysis"].get("short_term", {}).get("outlook", "neutral") for r in results]
        medium_outlooks = [r["timeframe_analysis"].get("medium_term", {}).get("outlook", "neutral") for r in results]
        long_outlooks = [r["timeframe_analysis"].get("long_term", {}).get("outlook", "neutral") for r in results]

        short_agreement = len([o for o in short_outlooks if o == max(set(short_outlooks), key=short_outlooks.count)]) / len(short_outlooks) * 100
        medium_agreement = len([o for o in medium_outlooks if o == max(set(medium_outlooks), key=medium_outlooks.count)]) / len(medium_outlooks) * 100
        long_agreement = len([o for o in long_outlooks if o == max(set(long_outlooks), key=long_outlooks.count)]) / len(long_outlooks) * 100

        timeframe_agreement = (short_agreement + medium_agreement + long_agreement) / 3
    else:
        timeframe_agreement = 50  # 데이터 없으면 중립

    # 가중 평균으로 최종 신뢰도 계산
    confidence_score = (
        rec_agreement * 0.30 +
        score_agreement * 0.25 +
        risk_agreement * 0.20 +
        risk_score_agreement * 0.15 +
        timeframe_agreement * 0.10
    )

    # 5. 종합 요약 생성
    summary_parts = []
    for r in results:
        summary_parts.append(f"[{r['model']}] {r['summary']}")

    final_summary = "\n\n".join(summary_parts)

    # 6. 모델별 결과 비교
    model_agreement = {}
    for r in results:
        model_agreement[r["model"]] = {
            "recommendation": r["recommendation"],
            "evaluation_score": r["evaluation_score"],
            "risk_level": r["risk_level"]
        }

    # 7. 심화 분석 필드 병합 (우선순위: GPT-4 > Claude)
    # GPT-4 결과 우선 사용, 없으면 Claude 결과 사용
    gpt4_result = next((r for r in results if "gpt-4" in r["model"]), None)
    claude_result = next((r for r in results if "claude" in r["model"]), None)
    primary_result = gpt4_result or claude_result or results[0]

    # 🔥 Phase 3.2 + 3.3: 리스크 점수 평균 계산
    final_risk_score = sum(r.get("risk_score", 50) for r in results) / len(results)

    result = {
        "summary": final_summary,
        "risk_level": final_risk_level,
        "risk_score": round(final_risk_score, 2),  # 🔥 Phase 3.2: 리스크 점수 평균
        "recommendation": final_recommendation,
        "evaluation_score": round(final_score, 2),
        "confidence_score": round(confidence_score, 2),
        "model_agreement": model_agreement,
        # 🔥 심화 분석 필드 추가 (primary_result에서 가져오기)
        "investment_strategy": primary_result.get("investment_strategy", ""),
        "technical_analysis": primary_result.get("technical_analysis", ""),
        "fundamental_analysis": primary_result.get("fundamental_analysis", ""),
        "market_sentiment": primary_result.get("market_sentiment", ""),
        "catalysts": primary_result.get("catalysts", ""),
        "risk_factors": primary_result.get("risk_factors", ""),
        "target_price_range": primary_result.get("target_price_range", ""),
        "time_horizon": primary_result.get("time_horizon", "medium_term"),
        # 🔥 Phase 3.1: 멀티 타임프레임 분석 (primary_result에서 가져오기)
        "timeframe_analysis": primary_result.get("timeframe_analysis", {}),
        # 🔥 Phase 3.2: 리스크 점수 세부 정보 (primary_result에서 가져오기)
        "risk_score_breakdown": primary_result.get("risk_score_breakdown", {}),
        "risk_score_description": primary_result.get("risk_score_description", ""),
        "ensemble_metadata": {
            "models_used": [r["model"] for r in results],
            "recommendation_counts": recommendation_counts,
            "risk_counts": risk_counts,
            "score_std": round(score_std, 2),
            "rec_agreement_pct": round(rec_agreement, 2),
            "score_agreement_pct": round(score_agreement, 2),
            # 🔥 Phase 3.3: 새로운 일치도 메트릭 추가
            "risk_agreement_pct": round(risk_agreement, 2),
            "risk_score_std": round(risk_score_std, 2),
            "risk_score_agreement_pct": round(risk_score_agreement, 2),
            "timeframe_agreement_pct": round(timeframe_agreement, 2)
        }
    }

    print(f"\n🔮 [Ensemble] 최종 결과:")
    print(f"   - 권고: {final_recommendation} (합의율: {rec_agreement:.1f}%)")
    print(f"   - 점수: {final_score:.2f} (표준편차: {score_std:.2f})")
    print(f"   - 리스크: {final_risk_level} (합의율: {risk_agreement:.1f}%)")
    print(f"   - 리스크 점수 표준편차: {risk_score_std:.2f}")
    print(f"   - 타임프레임 합의율: {timeframe_agreement:.1f}%")
    print(f"   - 🔥 신뢰도: {confidence_score:.2f}점 (5개 차원 가중 평균)")

    return result


async def analyze_with_ensemble(
    symbol: str,
    symbol_name: str,
    price_data: Dict[str, Any],
    news_data: List[Dict[str, Any]],
    financial_data: Dict[str, Any] = None,
    investor_data: Dict[str, Any] = None,
    analyst_opinion: Dict[str, Any] = None,  # 🔥 Phase 1.3
    sector_info: Dict[str, Any] = None,      # 🔥 Phase 1.3
    market_index: Dict[str, Any] = None,     # 🔥 Phase 1.3
    credit_balance: List[Dict] = None,       # 🔥 Phase 1.3
    short_selling: List[Dict] = None,        # 🔥 Phase 1.3
    program_trading: List[Dict] = None,      # 🔥 Phase 1.3
    institutional_flow: Dict[str, Any] = None  # 🔥 Phase 1.3
) -> Dict[str, Any]:
    """
    🔥 Phase 1.3 개선: AI Ensemble 종목 분석 - GPT-4 + Claude 병렬 실행 후 투표 (확장 데이터 반영)
    🔥 Phase 3.1 개선: 멀티 타임프레임 분석 (단기/중기/장기) 추가
    🔥 Phase 3.2 개선: 리스크 점수 정량화 (0-100) 추가
    🔥 Phase 3.3 개선: 신뢰도 계산 개선 - 5개 차원 가중 평균 (권고 30%, 평가점수 25%, 리스크레벨 20%, 리스크점수 15%, 타임프레임 10%)

    Args:
        symbol: 종목 코드
        symbol_name: 종목명
        price_data: 주가 데이터 (기술적 지표 포함)
        news_data: 뉴스 데이터 리스트 (7일 최대 50개)
        financial_data: 재무 데이터 (선택)
        investor_data: 투자자 동향 (선택)
        analyst_opinion: 애널리스트 의견 (선택)
        sector_info: 업종 정보 (선택)
        market_index: 시장 지수 (선택)
        credit_balance: 신용잔고 추이 (선택)
        short_selling: 공매도 추이 (선택)
        program_trading: 프로그램매매 추이 (선택)
        institutional_flow: 당일 외국인/기관 매매 (선택)

    Returns:
        Dict: 앙상블 분석 결과
            - summary: 종합 요약
            - risk_level: 위험도
            - recommendation: 투자 권고
            - evaluation_score: 평가 점수
            - confidence_score: 신뢰도 (0~100)
            - model_agreement: 모델별 결과
    """
    print(f"\n{'='*60}")
    print(f"🤖 AI Ensemble 분석 시작: {symbol_name} ({symbol})")
    print(f"{'='*60}")

    # 🔥 Phase 1.3: GPT-4와 Claude를 병렬 실행 (확장 데이터 전달)
    try:
        gpt4_task = analyze_with_gpt4(
            symbol, symbol_name, price_data, news_data, financial_data, investor_data,
            analyst_opinion, sector_info, market_index, credit_balance, short_selling,
            program_trading, institutional_flow
        )
        claude_task = analyze_with_claude(
            symbol, symbol_name, price_data, news_data, financial_data, investor_data,
            analyst_opinion, sector_info, market_index, credit_balance, short_selling,
            program_trading, institutional_flow
        )

        gpt4_result, claude_result = await asyncio.gather(gpt4_task, claude_task)

    except Exception as e:
        print(f"❌ Ensemble 병렬 실행 오류: {str(e)}")
        gpt4_result, claude_result = None, None

    # 2. 결과 수집
    valid_results = []
    if gpt4_result:
        valid_results.append(gpt4_result)
    if claude_result:
        valid_results.append(claude_result)

    # 3. 폴백 로직: 모든 모델 실패 시
    if not valid_results:
        print("❌ 모든 AI 모델 실패 → 기본 분석 반환")
        return {
            "summary": f"{symbol_name} 종목에 대한 AI 분석을 수행할 수 없습니다. 모든 모델에서 오류가 발생했습니다.",
            "risk_level": "medium",
            "recommendation": "hold",
            "evaluation_score": 50.0,
            "confidence_score": 0.0,
            "model_agreement": {},
            "error": "All AI models failed"
        }

    # 4. 한 모델만 성공한 경우 → 해당 모델 결과 반환 (신뢰도 50%)
    if len(valid_results) == 1:
        single_result = valid_results[0]
        print(f"⚠️ 단일 모델 결과 사용: {single_result['model']}")
        return {
            "summary": single_result["summary"],
            "risk_level": single_result["risk_level"],
            "recommendation": single_result["recommendation"],
            "evaluation_score": single_result["evaluation_score"],
            "confidence_score": 50.0,  # 단일 모델이므로 중간 신뢰도
            # 🔥 심화 분석 필드 추가
            "investment_strategy": single_result.get("investment_strategy", ""),
            "technical_analysis": single_result.get("technical_analysis", ""),
            "fundamental_analysis": single_result.get("fundamental_analysis", ""),
            "market_sentiment": single_result.get("market_sentiment", ""),
            "catalysts": single_result.get("catalysts", ""),
            "risk_factors": single_result.get("risk_factors", ""),
            "target_price_range": single_result.get("target_price_range", ""),
            "time_horizon": single_result.get("time_horizon", "medium_term"),
            "model_agreement": {single_result["model"]: {
                "recommendation": single_result["recommendation"],
                "evaluation_score": single_result["evaluation_score"],
                "risk_level": single_result["risk_level"]
            }},
            "ensemble_metadata": {
                "models_used": [single_result["model"]],
                "note": "Only one model succeeded"
            }
        }

    # 5. 앙상블 투표 실행
    ensemble_result = ensemble_vote(valid_results)

    print(f"{'='*60}")
    print(f"✅ AI Ensemble 분석 완료!")
    print(f"{'='*60}\n")

    return ensemble_result


# NumPy 임포트 (신뢰도 계산용)
import numpy as np
