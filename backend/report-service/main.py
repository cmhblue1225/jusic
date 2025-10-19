"""
Report Service - FastAPI 서버
종목 레포트 생성 및 조회 API
"""
import os
from datetime import datetime, date
from typing import Optional
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

# 로컬 모듈 임포트
from cache import get_cached_report, set_cached_report
from kis_data import get_daily_ohlcv
from technical import calculate_all_indicators
from ai_analyzer import analyze_stock

load_dotenv()

# FastAPI 앱 초기화
app = FastAPI(title="Report Service", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase 클라이언트
supabase: Client = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_SERVICE_KEY", "")
)


# ========== Pydantic 모델 ==========

class ReportRequest(BaseModel):
    symbol: str
    symbol_name: str


class ReportResponse(BaseModel):
    # 기본 정보
    symbol: str
    symbol_name: str
    report_date: str

    # 주가 데이터
    current_price: float
    change_rate: float
    high_price: float
    low_price: float
    avg_price: float
    volume: int

    # 기술적 지표
    ma5: Optional[float]
    ma20: Optional[float]
    ma60: Optional[float]
    volume_ratio: Optional[float]
    volatility: Optional[float]
    bollinger_upper: Optional[float]
    bollinger_lower: Optional[float]

    # AI 분석 결과
    summary: str
    risk_level: str
    recommendation: str
    evaluation_score: float

    # 관련 뉴스
    related_news_count: int

    # 메타데이터
    cached: bool


# ========== 유틸리티 함수 ==========

def get_user_id_from_token(authorization: Optional[str]) -> Optional[str]:
    """
    JWT 토큰에서 user_id 추출

    Args:
        authorization: Authorization 헤더 값 (Bearer <token>)

    Returns:
        str: user_id 또는 None
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.replace("Bearer ", "")

    try:
        # Supabase Auth를 통한 토큰 검증
        user = supabase.auth.get_user(token)
        return user.user.id if user and user.user else None
    except Exception as e:
        print(f"⚠️ 토큰 검증 실패: {str(e)}")
        return None


# ========== API 엔드포인트 ==========

@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "ok", "service": "report-service"}


@app.post("/api/reports/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    authorization: Optional[str] = Header(None)
):
    """
    종목 레포트 생성

    Args:
        request: 종목 코드 및 종목명
        authorization: JWT 토큰 (옵션)

    Returns:
        ReportResponse: 생성된 레포트
    """
    symbol = request.symbol
    symbol_name = request.symbol_name
    report_date_str = date.today().isoformat()

    print(f"\n📊 레포트 생성 요청: {symbol_name} ({symbol}) - {report_date_str}")

    # 1. 캐시 확인
    cached_report = get_cached_report(symbol, report_date_str)
    if cached_report:
        print(f"✅ 캐시에서 레포트 반환")
        return {**cached_report, "cached": True}

    try:
        # 2. 주가 데이터 조회 (60일 - 이평선 60일 계산용)
        print(f"📈 주가 데이터 조회 중...")
        ohlcv_data = await get_daily_ohlcv(symbol, days=60)

        if not ohlcv_data or len(ohlcv_data) < 20:
            raise HTTPException(
                status_code=400,
                detail=f"주가 데이터가 부족합니다. (최소 20일 필요, 현재: {len(ohlcv_data)}일)"
            )

        # 3. 기술적 지표 계산
        print(f"📊 기술적 지표 계산 중...")
        indicators = calculate_all_indicators(ohlcv_data)

        # 4. 관련 뉴스 조회 (최근 1일)
        print(f"📰 관련 뉴스 조회 중...")
        news_result = supabase.table("news") \
            .select("id, title, summary, sentiment_score, impact_score, published_at") \
            .contains("related_symbols", [symbol]) \
            .gte("published_at", datetime.now().replace(hour=0, minute=0, second=0).isoformat()) \
            .order("published_at", desc=True) \
            .limit(10) \
            .execute()

        news_data = news_result.data or []
        print(f"   → {len(news_data)}개 뉴스 발견")

        # 5. AI 분석
        print(f"🤖 AI 분석 시작...")
        ai_result = await analyze_stock(symbol, symbol_name, indicators, news_data)

        # 6. 레포트 데이터 구성
        report = {
            # 기본 정보
            "symbol": symbol,
            "symbol_name": symbol_name,
            "report_date": report_date_str,

            # 주가 데이터
            "current_price": indicators["current_price"],
            "change_rate": indicators["change_rate"],
            "high_price": indicators["high"],
            "low_price": indicators["low"],
            "avg_price": indicators["avg"],
            "volume": indicators["volume"],

            # 기술적 지표
            "ma5": indicators.get("ma5"),
            "ma20": indicators.get("ma20"),
            "ma60": indicators.get("ma60"),
            "volume_ratio": indicators.get("volume_ratio"),
            "volatility": indicators.get("volatility"),
            "bollinger_upper": indicators.get("bollinger_upper"),
            "bollinger_lower": indicators.get("bollinger_lower"),

            # AI 분석 결과
            "summary": ai_result["summary"],
            "risk_level": ai_result["risk_level"],
            "recommendation": ai_result["recommendation"],
            "evaluation_score": ai_result["evaluation_score"],

            # 관련 뉴스
            "related_news_count": len(news_data),

            # 메타데이터
            "cached": False
        }

        # 7. Redis 캐싱
        set_cached_report(symbol, report_date_str, report)

        # 8. (옵션) 사용자 인증 시 Supabase에 북마크 저장
        user_id = get_user_id_from_token(authorization)
        if user_id:
            try:
                # 뉴스 ID 추출
                related_news_ids = [news["id"] for news in news_data]

                supabase.table("stock_reports").upsert({
                    "user_id": user_id,
                    "symbol": symbol,
                    "symbol_name": symbol_name,
                    "report_date": report_date_str,
                    **{k: v for k, v in report.items() if k not in ["symbol", "symbol_name", "report_date", "cached", "related_news_count"]},
                    "ai_analysis": ai_result["ai_analysis"],
                    "related_news_ids": related_news_ids,
                    "is_bookmarked": True
                }, on_conflict="user_id,symbol,report_date").execute()

                print(f"✅ 레포트를 Supabase에 저장 (user_id: {user_id})")

            except Exception as e:
                print(f"⚠️ Supabase 저장 실패 (레포트는 정상 반환됨): {str(e)}")

        print(f"✅ 레포트 생성 완료: {symbol_name} ({symbol})\n")
        return report

    except Exception as e:
        print(f"❌ 레포트 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"레포트 생성 중 오류 발생: {str(e)}")


@app.get("/api/reports/bookmarks")
async def get_bookmarks(authorization: Optional[str] = Header(None)):
    """
    사용자의 북마크된 레포트 목록 조회

    Args:
        authorization: JWT 토큰

    Returns:
        List[Dict]: 북마크된 레포트 목록
    """
    user_id = get_user_id_from_token(authorization)

    if not user_id:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")

    try:
        result = supabase.table("stock_reports") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("is_bookmarked", True) \
            .order("created_at", desc=True) \
            .execute()

        return {"bookmarks": result.data or []}

    except Exception as e:
        print(f"❌ 북마크 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"북마크 조회 중 오류 발생: {str(e)}")


@app.delete("/api/reports/bookmarks/{symbol}")
async def delete_bookmark(symbol: str, authorization: Optional[str] = Header(None)):
    """
    북마크 삭제

    Args:
        symbol: 종목 코드
        authorization: JWT 토큰

    Returns:
        Dict: 삭제 결과
    """
    user_id = get_user_id_from_token(authorization)

    if not user_id:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")

    try:
        report_date_str = date.today().isoformat()

        result = supabase.table("stock_reports") \
            .delete() \
            .eq("user_id", user_id) \
            .eq("symbol", symbol) \
            .eq("report_date", report_date_str) \
            .execute()

        return {"message": f"{symbol} 북마크가 삭제되었습니다"}

    except Exception as e:
        print(f"❌ 북마크 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"북마크 삭제 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    # Railway/Render에서 제공하는 PORT 환경 변수 사용
    port = int(os.getenv("PORT", "3004"))
    print(f"🚀 Report Service starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
