"""
AI 기반 종목 분석 모듈
- OpenAI GPT-4o-mini 사용
- 주가 데이터 + 뉴스 → 종합 분석
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
    news_data: List[Dict[str, Any]]
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

    # 2. 프롬프트 생성
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

## 최근 뉴스 (최대 5개)
{news_summary_text}

## 분석 요청
다음 JSON 형식으로 응답해주세요:

{{
  "summary": "종합 요약 (3~5문장, 투자자가 꼭 알아야 할 핵심 포인트)",
  "risk_level": "위험도 ('low', 'medium', 'high' 중 하나)",
  "recommendation": "투자 권고 ('buy', 'sell', 'hold' 중 하나)",
  "evaluation_score": "평가 점수 (0~100, 숫자만)",
  "reasoning": "판단 근거 (2~3문장)"
}}

**중요 사항:**
- 위험도는 변동성, 뉴스 부정도, 볼린저 밴드 이탈 여부 등을 종합하여 판단하세요.
- 투자 권고는 이동평균 골든크로스/데드크로스, 볼린저 밴드, 뉴스 감성을 고려하세요.
- 평가 점수는 기술적 지표와 뉴스 감성을 종합한 절대 점수입니다.
- 반드시 JSON 형식으로만 응답하세요. 추가 설명은 "reasoning" 필드에 포함하세요.
"""

    # 3. OpenAI API 호출
    print(f"🤖 OpenAI GPT-4o-mini 분석 시작: {symbol_name} ({symbol})")

    try:
        # OpenAI 클라이언트 가져오기 (환경 변수 체크)
        client = get_openai_client()

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 한국 주식 시장 전문 애널리스트입니다. 항상 JSON 형식으로만 응답합니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # 낮은 온도 → 일관성 있는 분석
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
            "ai_analysis": ai_response  # 원본 JSON 저장
        }

        # 값 검증
        if result["risk_level"] not in ["low", "medium", "high"]:
            result["risk_level"] = "medium"

        if result["recommendation"] not in ["buy", "sell", "hold"]:
            result["recommendation"] = "hold"

        if not (0 <= result["evaluation_score"] <= 100):
            result["evaluation_score"] = 50.0

        print(f"✅ AI 분석 완료:")
        print(f"   - 요약: {result['summary'][:50]}...")
        print(f"   - 위험도: {result['risk_level']}")
        print(f"   - 권고: {result['recommendation']}")
        print(f"   - 평가: {result['evaluation_score']}점")

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
