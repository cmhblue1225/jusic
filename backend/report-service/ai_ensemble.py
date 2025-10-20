"""
AI Ensemble 시스템
- GPT-4 Turbo + Claude 3.5 Sonnet 앙상블
- 두 모델의 분석 결과를 투표(Voting)로 결합
- 신뢰도(Confidence) 점수 계산 (모델 간 합의 정도)
- 폴백 로직: 한 모델 실패 시 다른 모델 결과 사용
"""
import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI
import anthropic

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


async def analyze_with_gpt4(
    symbol: str,
    symbol_name: str,
    price_data: Dict[str, Any],
    news_data: List[Dict[str, Any]],
    financial_data: Dict[str, Any] = None,
    investor_data: Dict[str, Any] = None
) -> Optional[Dict[str, Any]]:
    """
    GPT-4 Turbo 기반 종목 분석

    Returns:
        Dict: AI 분석 결과 또는 None (실패 시)
    """
    # 1. 뉴스 요약 텍스트 생성
    news_summary_lines = []
    for i, news in enumerate(news_data[:5], 1):
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
- PER: {financial_data.get('per', 'N/A')}, PBR: {financial_data.get('pbr', 'N/A')}, ROE: {financial_data.get('roe', 'N/A')}%
- 배당수익률: {financial_data.get('dividend_yield', 'N/A')}%, EPS: {financial_data.get('eps', 'N/A')}원
- 영업이익률: {financial_data.get('operating_margin', 'N/A')}%, 부채비율: {financial_data.get('debt_ratio', 'N/A')}%
""" if financial_data else "재무 데이터 없음"

    # 3. 투자자 동향 텍스트 생성
    investor_data = investor_data or {}
    investor_text = f"""
- 외국인: {investor_data.get('foreign_net_buy', 0):+,}주, 기관: {investor_data.get('institution_net_buy', 0):+,}주
""" if investor_data else "투자자 동향 데이터 없음"

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
당신은 한국 주식 시장 전문 애널리스트입니다. 다음 정보를 바탕으로 종목을 종합 분석해주세요.

## 종목 정보
- 종목명: {symbol_name} ({symbol})

## 주가 데이터
- 현재가: {price_data['current_price']:,}원 ({price_data['change_rate']:+.2f}%)
- 거래량: {price_data['volume']:,}주

## 기술적 지표
- MA5: {price_data.get('ma5', 'N/A')}, MA20: {price_data.get('ma20', 'N/A')}, MA60: {price_data.get('ma60', 'N/A')}
- 볼린저 밴드: {price_data.get('bollinger_upper', 'N/A')} / {price_data.get('bollinger_lower', 'N/A')}
- 거래량 비율: {price_data.get('volume_ratio', 'N/A')}
{advanced_indicators}

## 재무비율
{financial_text}

## 투자자 매매 동향
{investor_text}

## 최근 뉴스
{news_summary_text}

## 분석 요청
다음 JSON 형식으로 응답해주세요:

{{
  "summary": "종합 요약 (3~5문장)",
  "risk_level": "위험도 ('low', 'medium', 'high')",
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
  "risk_factors": "주요 리스크 요인 (3~5개 항목, 줄바꿈으로 구분)"
}}

**중요 사항:**
- 위험도는 변동성, 뉴스 부정도, 볼린저 밴드 이탈 여부를 고려하세요.
- 투자 권고는 이동평균, RSI, MACD, 뉴스 감성, 외국인/기관 매매를 고려하세요.
- 평가 점수는 기술적 지표, 재무비율, 투자자 동향, 뉴스 감성을 종합한 절대 점수입니다.
- **심화 분석 필드는 필수**입니다. 데이터가 부족해도 현재 정보 기반으로 작성하세요.
- 반드시 JSON 형식으로만 응답하세요.
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
            "raw_response": ai_response
        }

        # 값 검증
        if result["risk_level"] not in ["low", "medium", "high"]:
            result["risk_level"] = "medium"
        if result["recommendation"] not in ["buy", "sell", "hold"]:
            result["recommendation"] = "hold"
        if not (0 <= result["evaluation_score"] <= 100):
            result["evaluation_score"] = 50.0

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
    investor_data: Dict[str, Any] = None
) -> Optional[Dict[str, Any]]:
    """
    Claude 3.5 Sonnet 기반 종목 분석 (리스크 분석 전문가)

    Returns:
        Dict: AI 분석 결과 또는 None (실패 시)
    """
    # 1. 뉴스 요약 텍스트 생성
    news_summary_lines = []
    for i, news in enumerate(news_data[:5], 1):
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
- PER: {financial_data.get('per', 'N/A')}, PBR: {financial_data.get('pbr', 'N/A')}, ROE: {financial_data.get('roe', 'N/A')}%
- 배당수익률: {financial_data.get('dividend_yield', 'N/A')}%, 부채비율: {financial_data.get('debt_ratio', 'N/A')}%
""" if financial_data else "재무 데이터 없음"

    # 3. 투자자 동향 텍스트 생성
    investor_data = investor_data or {}
    investor_text = f"""
- 외국인: {investor_data.get('foreign_net_buy', 0):+,}주, 기관: {investor_data.get('institution_net_buy', 0):+,}주
""" if investor_data else "투자자 동향 데이터 없음"

    # 4. 고급 기술적 지표 텍스트 생성
    advanced_indicators = ""
    if price_data.get('rsi'):
        advanced_indicators = f"""
## 고급 기술적 지표
- RSI: {price_data.get('rsi', 'N/A')}, MACD: {price_data.get('macd', 'N/A')}
- ADX: {price_data.get('adx', 'N/A')}, ATR: {price_data.get('atr', 'N/A')} (변동성)
- Williams %R: {price_data.get('williams_r', 'N/A')} (과매수/과매도)
"""

    # 5. 프롬프트 생성
    prompt = f"""
당신은 한국 주식 시장 리스크 분석 전문가입니다. 다음 정보를 바탕으로 종목을 분석하되, **리스크 요인**과 **변동성**에 특히 집중해주세요.

## 종목 정보
- 종목명: {symbol_name} ({symbol})

## 주가 데이터
- 현재가: {price_data['current_price']:,}원 ({price_data['change_rate']:+.2f}%)
- 거래량: {price_data['volume']:,}주

## 기술적 지표
- MA5: {price_data.get('ma5', 'N/A')}, MA20: {price_data.get('ma20', 'N/A')}
- 볼린저 밴드: {price_data.get('bollinger_upper', 'N/A')} / {price_data.get('bollinger_lower', 'N/A')}
- 변동성: {price_data.get('volatility', 'N/A')}
{advanced_indicators}

## 재무비율
{financial_text}

## 투자자 매매 동향
{investor_text}

## 최근 뉴스
{news_summary_text}

## 분석 요청
다음 JSON 형식으로 응답해주세요:

{{
  "summary": "종합 요약 (3~5문장, 리스크 중심)",
  "risk_level": "위험도 ('low', 'medium', 'high')",
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
  "risk_factors": "주요 리스크 요인 (3~5개 항목, 줄바꿈으로 구분)"
}}

**중요 사항:**
- 위험도는 변동성(ATR), 부채비율, 뉴스 부정도, 볼린저 밴드 이탈을 중점적으로 평가하세요.
- 투자 권고는 리스크-리워드 비율을 고려하세요.
- 평가 점수는 보수적으로 책정하세요 (리스크가 크면 점수 낮춤).
- **심화 분석 필드는 필수**입니다. 데이터가 부족해도 현재 정보 기반으로 작성하세요.
- 반드시 JSON 형식으로만 응답하세요.
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
            "raw_response": ai_response
        }

        # 값 검증
        if result["risk_level"] not in ["low", "medium", "high"]:
            result["risk_level"] = "medium"
        if result["recommendation"] not in ["buy", "sell", "hold"]:
            result["recommendation"] = "hold"
        if not (0 <= result["evaluation_score"] <= 100):
            result["evaluation_score"] = 50.0

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

    # 4. 신뢰도 계산 (모델 간 합의 정도)
    # - 투자 권고 일치율 (50%)
    rec_agreement = recommendation_counts[final_recommendation] / len(results) * 100
    # - 평가 점수 표준편차 (50%, 낮을수록 합의 높음)
    score_std = np.std([r["evaluation_score"] for r in results])
    score_agreement = max(0, 100 - score_std)  # 표준편차가 클수록 합의 낮음

    confidence_score = (rec_agreement * 0.5 + score_agreement * 0.5)

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

    result = {
        "summary": final_summary,
        "risk_level": final_risk_level,
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
        "ensemble_metadata": {
            "models_used": [r["model"] for r in results],
            "recommendation_counts": recommendation_counts,
            "risk_counts": risk_counts,
            "score_std": round(score_std, 2),
            "rec_agreement_pct": round(rec_agreement, 2),
            "score_agreement_pct": round(score_agreement, 2)
        }
    }

    print(f"\n🔮 [Ensemble] 최종 결과:")
    print(f"   - 권고: {final_recommendation} (합의율: {rec_agreement:.1f}%)")
    print(f"   - 점수: {final_score:.2f} (표준편차: {score_std:.2f})")
    print(f"   - 신뢰도: {confidence_score:.2f}점")

    return result


async def analyze_with_ensemble(
    symbol: str,
    symbol_name: str,
    price_data: Dict[str, Any],
    news_data: List[Dict[str, Any]],
    financial_data: Dict[str, Any] = None,
    investor_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    AI Ensemble 종목 분석 - GPT-4 + Claude 병렬 실행 후 투표

    Args:
        symbol: 종목 코드
        symbol_name: 종목명
        price_data: 주가 데이터 (기술적 지표 포함)
        news_data: 뉴스 데이터 리스트
        financial_data: 재무 데이터 (선택)
        investor_data: 투자자 동향 (선택)

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

    # 1. GPT-4와 Claude를 병렬 실행
    try:
        gpt4_task = analyze_with_gpt4(symbol, symbol_name, price_data, news_data, financial_data, investor_data)
        claude_task = analyze_with_claude(symbol, symbol_name, price_data, news_data, financial_data, investor_data)

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
