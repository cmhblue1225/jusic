"""
AI 분석 서비스
Claude/OpenAI API를 사용한 뉴스 분석
"""
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from anthropic import Anthropic
from openai import OpenAI
import json
from cache import news_cache

load_dotenv()

app = FastAPI(title="AI Analysis Service")

# AI 클라이언트 초기화
claude_client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY", ""))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


class NewsAnalysisRequest(BaseModel):
    title: str
    content: str
    symbols: list[str] = []
    url: str  # 캐싱을 위한 뉴스 URL


class NewsAnalysisResponse(BaseModel):
    summary: str
    sentiment_score: float  # -1 ~ 1
    impact_score: float  # 0 ~ 1
    recommended_action: str  # buy, sell, hold


async def analyze_with_claude(title: str, content: str, symbols: list[str]) -> NewsAnalysisResponse:
    """Claude API로 뉴스 분석"""
    prompt = f"""
다음 뉴스 기사를 분석해주세요.

제목: {title}
내용: {content}
관련 종목: {', '.join(symbols) if symbols else '자동 추출'}

아래 형식의 JSON으로 응답해주세요:
{{
  "summary": "2~3문장 요약",
  "sentiment_score": -1.0 ~ 1.0 (부정 ~ 긍정),
  "impact_score": 0.0 ~ 1.0 (영향도),
  "recommended_action": "buy" | "sell" | "hold",
  "reason": "권고 이유 간단히"
}}
"""

    try:
        message = claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        result = json.loads(message.content[0].text)

        return NewsAnalysisResponse(
            summary=result["summary"],
            sentiment_score=result["sentiment_score"],
            impact_score=result["impact_score"],
            recommended_action=result["recommended_action"]
        )
    except Exception as e:
        print(f"Claude API 오류: {str(e)}")
        # OpenAI로 폴백
        return await analyze_with_openai(title, content, symbols)


async def analyze_with_openai(title: str, content: str, symbols: list[str]) -> NewsAnalysisResponse:
    """OpenAI API로 뉴스 분석 (폴백)"""
    prompt = f"""
다음 뉴스 기사를 분석해주세요.

제목: {title}
내용: {content}
관련 종목: {', '.join(symbols) if symbols else '자동 추출'}

아래 형식의 JSON으로 응답해주세요:
{{
  "summary": "2~3문장 요약",
  "sentiment_score": -1.0 ~ 1.0 (부정 ~ 긍정),
  "impact_score": 0.0 ~ 1.0 (영향도),
  "recommended_action": "buy" | "sell" | "hold"
}}
"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        return NewsAnalysisResponse(
            summary=result["summary"],
            sentiment_score=result["sentiment_score"],
            impact_score=result["impact_score"],
            recommended_action=result["recommended_action"]
        )
    except Exception as e:
        print(f"OpenAI API 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="AI 분석 실패")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-service"}


@app.post("/analyze", response_model=NewsAnalysisResponse)
async def analyze_news(request: NewsAnalysisRequest):
    """뉴스 분석 엔드포인트 (Redis 캐싱 적용)"""

    # 1. 캐시 확인
    cached_result = news_cache.get(request.url)
    if cached_result:
        print(f"✅ 캐시에서 분석 결과 반환: {request.title[:50]}...")
        return NewsAnalysisResponse(**cached_result)

    # 2. 캐시 미스 - AI 분석 수행
    print(f"🤖 AI 분석 시작: {request.title[:50]}...")
    result = await analyze_with_claude(request.title, request.content, request.symbols)

    # 3. 결과를 캐시에 저장 (24시간 TTL)
    news_cache.set(request.url, result.model_dump(), ttl=86400)

    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3003)
