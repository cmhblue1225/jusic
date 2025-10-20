"""
AI 기반 종목 분석 모듈
- OpenAI GPT-4 Turbo 사용 (고급 분석)
- 주가 데이터 + 재무비율 + 투자자 동향 + 뉴스 → 종합 분석
"""
import os
import json
from typing import Dict, List, Any
from openai import AsyncOpenAI

# OpenAI 클라이언트 초기화 (지연 초기화)
_client = None

def get_openai_client():
    """OpenAI 클라이언트 지연 초기화 및 반환"""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        _client = AsyncOpenAI(api_key=api_key)
    return _client


async def analyze_stock(
    symbol: str,
    symbol_name: str,
    price_data: Dict[str, Any],
    news_data: List[Dict[str, Any]],
    financial_data: Dict[str, Any] = None,
    investor_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    AI 기반 종목 종합 분석

    Args:
        symbol: 종목 코드 (예: '005930')
        symbol_name: 종목명 (예: '삼성전자')
        price_data: 주가 및 기술적 지표
            - current_price: 현재가
            - change_rate: 등락률
            - ma5, ma20, ma60: 이동평균
            - volume_ratio: 거래량 비율
            - volatility: 변동성
            - bollinger_upper, bollinger_lower: 볼린저 밴드
        news_data: 관련 뉴스 리스트
            - title: 뉴스 제목
            - summary: AI 요약
            - sentiment_score: 감성 점수
            - impact_score: 영향도
            - published_at: 발행 시간

    Returns:
        Dict: AI 분석 결과
            - summary: 종합 요약 (3~5문장)
            - risk_level: 위험도 ('low', 'medium', 'high')
            - recommendation: 투자 권고 ('buy', 'sell', 'hold')
            - evaluation_score: 평가 점수 (0~100)
            - ai_analysis: 원본 JSON 응답
    """
    # 1. 뉴스 요약 텍스트 생성
    news_summary_lines = []
    for i, news in enumerate(news_data[:5], 1):  # 최대 5개 뉴스만 분석
        sentiment_text = "긍정" if news.get("sentiment_score", 0) > 0 else "부정" if news.get("sentiment_score", 0) < 0 else "중립"
        news_summary_lines.append(
            f"{i}. {news['title']}\n"
            f"   - 요약: {news.get('summary', '요약 없음')}\n"
            f"   - 감성: {sentiment_text} ({news.get('sentiment_score', 0):.2f})\n"
            f"   - 영향도: {news.get('impact_score', 0):.2f}\n"
        )

    news_summary_text = "\n".join(news_summary_lines) if news_summary_lines else "관련 뉴스 없음"

    # 2. 재무 데이터 텍스트 생성
    financial_data = financial_data or {}
    financial_text = f"""
- PER (주가수익비율): {financial_data.get('per', 'N/A')}
- PBR (주가순자산비율): {financial_data.get('pbr', 'N/A')}
- ROE (자기자본이익률): {financial_data.get('roe', 'N/A')}%
- 배당수익률: {financial_data.get('dividend_yield', 'N/A')}%
- EPS (주당순이익): {financial_data.get('eps', 'N/A')}원
- BPS (주당순자산): {financial_data.get('bps', 'N/A')}원
- 영업이익률: {financial_data.get('operating_margin', 'N/A')}%
- 순이익률: {financial_data.get('net_margin', 'N/A')}%
- 부채비율: {financial_data.get('debt_ratio', 'N/A')}%
""" if financial_data else "재무 데이터 없음"

    # 3. 투자자 동향 텍스트 생성
    investor_data = investor_data or {}
    investor_text = f"""
- 외국인 순매수: {investor_data.get('foreign_net_buy', 0):+,}주 ({investor_data.get('foreign_net_buy_amt', 0):+,.0f}원)
- 기관 순매수: {investor_data.get('institution_net_buy', 0):+,}주 ({investor_data.get('institution_net_buy_amt', 0):+,.0f}원)
- 개인 순매수: {investor_data.get('individual_net_buy', 0):+,}주 ({investor_data.get('individual_net_buy_amt', 0):+,.0f}원)
""" if investor_data else "투자자 동향 데이터 없음"

    # 4. 프롬프트 생성
    prompt = f"""
당신은 한국 주식 시장 전문 애널리스트입니다. 다음 정보를 바탕으로 종목을 종합 분석해주세요.

## 종목 정보
- 종목명: {symbol_name} ({symbol})

## 주가 데이터 (당일 기준)
- 현재가: {price_data['current_price']:,}원
- 등락률: {price_data['change_rate']:+.2f}%
- 고가: {price_data['high']:,}원
- 저가: {price_data['low']:,}원
- 거래량: {price_data['volume']:,}주

## 기술적 지표
- 5일 이동평균: {price_data.get('ma5', 'N/A')}
- 20일 이동평균: {price_data.get('ma20', 'N/A')}
- 60일 이동평균: {price_data.get('ma60', 'N/A')}
- 거래량 비율: {price_data.get('volume_ratio', 'N/A')} (평균 대비)
- 변동성: {price_data.get('volatility', 'N/A')}
- 볼린저 밴드 상단: {price_data.get('bollinger_upper', 'N/A')}
- 볼린저 밴드 하단: {price_data.get('bollinger_lower', 'N/A')}

## 재무비율
{financial_text}

## 투자자 매매 동향 (당일)
{investor_text}

## 최근 뉴스 (최대 5개)
{news_summary_text}

## 분석 요청
다음 JSON 형식으로 응답해주세요:

{{
  "summary": "종합 요약 (3~5문장, 투자자가 꼭 알아야 할 핵심 포인트)",
  "risk_level": "위험도 ('low', 'medium', 'high' 중 하나)",
  "recommendation": "투자 권고 ('buy', 'sell', 'hold' 중 하나)",
  "evaluation_score": "평가 점수 (0~100, 숫자만)",
  "reasoning": "판단 근거 (2~3문장)",
  "investment_strategy": "투자 전략 제안 (2~3문장, 구체적인 진입/청산 전략)",
  "risk_factors": "주요 리스크 요인 (2~3개 항목, 각 1문장)",
  "catalysts": "긍정적 촉매 (2~3개 항목, 각 1문장)",
  "target_price_range": "목표 주가 범위 (최소~최대, 예: '70000~80000')",
  "time_horizon": "투자 기간 권고 ('short_term': 1~3개월, 'medium_term': 3~6개월, 'long_term': 6개월 이상)",
  "technical_analysis": "기술적 분석 요약 (2문장, 이동평균/볼린저밴드 등)",
  "fundamental_analysis": "기본적 분석 요약 (2문장, PER/PBR/ROE 등 재무비율 해석)",
  "market_sentiment": "시장 심리 분석 (1~2문장, 외국인/기관 매매 동향 해석)"
}}

**중요 사항:**
- 위험도는 변동성, 뉴스 부정도, 볼린저 밴드 이탈 여부, 부채비율 등을 종합하여 판단하세요.
- 투자 권고는 이동평균 골든크로스/데드크로스, 볼린저 밴드, 뉴스 감성, PER/PBR 밸류에이션, 외국인/기관 매매 동향을 고려하세요.
- 평가 점수는 기술적 지표, 재무비율 (PER, PBR, ROE), 투자자 동향, 뉴스 감성을 종합한 절대 점수입니다.
- 재무비율 해석:
  - PER < 10: 저평가 가능성, PER > 30: 고평가 가능성
  - PBR < 1: 저평가, PBR > 3: 고평가
  - ROE > 15%: 우수, ROE < 5%: 저조
  - 부채비율 > 200%: 재무 위험 높음
- 투자자 동향 해석:
  - 외국인/기관 순매수: 긍정적 신호
  - 외국인/기관 순매도: 부정적 신호
- 반드시 JSON 형식으로만 응답하세요. 추가 설명은 "reasoning" 필드에 포함하세요.
"""

    # 3. OpenAI API 호출 (GPT-4 Turbo)
    print(f"🤖 OpenAI GPT-4 Turbo 분석 시작: {symbol_name} ({symbol})")

    try:
        # OpenAI 클라이언트 가져오기 (환경 변수 체크)
        client = get_openai_client()

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",  # GPT-4 Turbo (고급 분석)
            messages=[
                {"role": "system", "content": "당신은 한국 주식 시장 전문 애널리스트입니다. CFA 자격을 보유하고 있으며, 기본적 분석과 기술적 분석을 결합한 종합 분석 전문가입니다. 항상 JSON 형식으로만 응답합니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,  # 낮은 온도 → 일관성 있고 정확한 분석
            response_format={"type": "json_object"}  # JSON 응답 강제
        )

        # 응답 파싱
        ai_response_text = response.choices[0].message.content
        ai_response = json.loads(ai_response_text)

        # 결과 검증 및 정규화
        result = {
            "summary": ai_response.get("summary", "분석 결과 없음"),
            "risk_level": ai_response.get("risk_level", "medium").lower(),
            "recommendation": ai_response.get("recommendation", "hold").lower(),
            "evaluation_score": float(ai_response.get("evaluation_score", 50)),

            # 확장 필드 (신규)
            "investment_strategy": ai_response.get("investment_strategy", ""),
            "risk_factors": ai_response.get("risk_factors", ""),
            "catalysts": ai_response.get("catalysts", ""),
            "target_price_range": ai_response.get("target_price_range", ""),
            "time_horizon": ai_response.get("time_horizon", "medium_term"),
            "technical_analysis": ai_response.get("technical_analysis", ""),
            "fundamental_analysis": ai_response.get("fundamental_analysis", ""),
            "market_sentiment": ai_response.get("market_sentiment", ""),

            "ai_analysis": ai_response  # 원본 JSON 저장
        }

        # 값 검증
        if result["risk_level"] not in ["low", "medium", "high"]:
            result["risk_level"] = "medium"

        if result["recommendation"] not in ["buy", "sell", "hold"]:
            result["recommendation"] = "hold"

        if not (0 <= result["evaluation_score"] <= 100):
            result["evaluation_score"] = 50.0

        if result["time_horizon"] not in ["short_term", "medium_term", "long_term"]:
            result["time_horizon"] = "medium_term"

        print(f"✅ AI 분석 완료 (GPT-4 Turbo):")
        print(f"   - 요약: {result['summary'][:50]}...")
        print(f"   - 위험도: {result['risk_level']}")
        print(f"   - 권고: {result['recommendation']}")
        print(f"   - 평가: {result['evaluation_score']}점")
        print(f"   - 투자기간: {result['time_horizon']}")
        print(f"   - 목표가: {result['target_price_range']}")

        return result

    except json.JSONDecodeError as e:
        print(f"⚠️ JSON 파싱 오류: {str(e)}")
        # 폴백 응답
        return {
            "summary": f"{symbol_name} 종목에 대한 AI 분석 중 오류가 발생했습니다. 수동으로 확인해주세요.",
            "risk_level": "medium",
            "recommendation": "hold",
            "evaluation_score": 50.0,
            "ai_analysis": {"error": str(e)}
        }

    except Exception as e:
        print(f"❌ OpenAI API 오류: {str(e)}")
        # 폴백 응답
        return {
            "summary": f"{symbol_name} 종목에 대한 AI 분석을 수행할 수 없습니다. API 오류가 발생했습니다.",
            "risk_level": "medium",
            "recommendation": "hold",
            "evaluation_score": 50.0,
            "ai_analysis": {"error": str(e)}
        }
