"""
Report Service - FastAPI 서버
종목 레포트 생성 및 조회 API
"""
import os
import sys
import traceback
from datetime import datetime, date
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

print("=" * 60)
print("🚀 Report Service 초기화 시작...")
print("=" * 60)

# 환경 변수 로드
load_dotenv()
print("✅ .env 로드 완료")

# 로컬 모듈 임포트 (에러 발생 시 상세 로그)
try:
    print("📦 모듈 임포트 시작...")
    from cache import get_cached_report, set_cached_report
    print("  ✅ cache 모듈")
    from kis_data import get_daily_ohlcv, get_financial_ratio, get_investor_trend
    print("  ✅ kis_data 모듈")
    from technical import calculate_all_indicators
    print("  ✅ technical 모듈")
    from ai_analyzer import analyze_stock
    print("  ✅ ai_analyzer 모듈")
    print("✅ 모든 모듈 임포트 완료")
except Exception as e:
    print(f"❌ 모듈 임포트 실패: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

# FastAPI 앱 초기화
print("📦 FastAPI 앱 초기화 중...")
app = FastAPI(
    title="Report Service",
    version="1.0.1",
    docs_url="/docs",
    redoc_url="/redoc"
)
print("✅ FastAPI 앱 생성 완료")

# CORS 설정 (프로덕션 도메인 명시)
# 🔥 중요: 미들웨어는 앱 초기화 직후에 추가해야 함
print("🔐 CORS 미들웨어 설정 중...")
print(f"📍 환경: {os.getenv('RAILWAY_ENVIRONMENT', 'local')}")

# 환경 변수 ALLOWED_ORIGINS가 설정되어 있으면 사용, 아니면 기본값
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    ALLOWED_ORIGINS = [origin.strip() for origin in allowed_origins_env.split(",")]
else:
    ALLOWED_ORIGINS = ["*"]  # 기본값: 모든 도메인 허용

print(f"🔐 CORS 설정:")
print(f"   - allow_origins: {ALLOWED_ORIGINS}")
print(f"   - allow_credentials: True")
print(f"   - allow_methods: ['*']")
print(f"   - allow_headers: ['*']")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
print("✅ CORS 미들웨어 추가 완료")

# Supabase 클라이언트
print("📊 Supabase 클라이언트 초기화 중...")
try:
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL", ""),
        os.getenv("SUPABASE_SERVICE_KEY", "")
    )
    print("✅ Supabase 클라이언트 생성 완료")
except Exception as e:
    print(f"❌ Supabase 초기화 실패: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

print("=" * 60)
print("✅ Report Service 초기화 완료!")
print("=" * 60)


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
    return {
        "status": "ok",
        "service": "report-service",
        "cors": "enabled",
        "version": "1.0.1"
    }


@app.options("/api/reports/generate")
async def options_generate_report():
    """CORS preflight 요청 처리"""
    from fastapi.responses import Response
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "3600",
        }
    )


@app.post("/api/reports/generate")
async def generate_report(
    request: ReportRequest,
    response: Response,
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
    # CORS 헤더 명시적 추가
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"

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

        # 3-1. 재무비율 조회 (PER, PBR, ROE 등)
        print(f"💰 재무비율 조회 중...")
        try:
            financial_data = await get_financial_ratio(symbol)
        except Exception as e:
            print(f"⚠️ 재무비율 조회 실패 (계속 진행): {str(e)}")
            financial_data = {}

        # 3-2. 투자자 매매 동향 조회 (외국인, 기관)
        print(f"📊 투자자 동향 조회 중...")
        try:
            investor_data = await get_investor_trend(symbol)
        except Exception as e:
            print(f"⚠️ 투자자 동향 조회 실패 (계속 진행): {str(e)}")
            investor_data = {}

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

        # 5. AI 분석 (재무 데이터 및 투자자 동향 포함)
        print(f"🤖 AI 분석 시작...")
        ai_result = await analyze_stock(
            symbol,
            symbol_name,
            indicators,
            news_data,
            financial_data=financial_data,
            investor_data=investor_data
        )

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

            # 재무비율 (신규)
            "per": financial_data.get("per"),
            "pbr": financial_data.get("pbr"),
            "roe": financial_data.get("roe"),
            "dividend_yield": financial_data.get("dividend_yield"),
            "eps": financial_data.get("eps"),
            "bps": financial_data.get("bps"),
            "operating_margin": financial_data.get("operating_margin"),
            "net_margin": financial_data.get("net_margin"),
            "debt_ratio": financial_data.get("debt_ratio"),

            # 투자자 동향 (신규)
            "foreign_net_buy": investor_data.get("foreign_net_buy"),
            "foreign_net_buy_amt": investor_data.get("foreign_net_buy_amt"),
            "institution_net_buy": investor_data.get("institution_net_buy"),
            "institution_net_buy_amt": investor_data.get("institution_net_buy_amt"),
            "individual_net_buy": investor_data.get("individual_net_buy"),
            "individual_net_buy_amt": investor_data.get("individual_net_buy_amt"),

            # AI 분석 결과
            "summary": ai_result["summary"],
            "risk_level": ai_result["risk_level"],
            "recommendation": ai_result["recommendation"],
            "evaluation_score": ai_result["evaluation_score"],

            # AI 분석 확장 (신규 - GPT-4)
            "investment_strategy": ai_result.get("investment_strategy", ""),
            "risk_factors": ai_result.get("risk_factors", ""),
            "catalysts": ai_result.get("catalysts", ""),
            "target_price_range": ai_result.get("target_price_range", ""),
            "time_horizon": ai_result.get("time_horizon", "medium_term"),
            "technical_analysis": ai_result.get("technical_analysis", ""),
            "fundamental_analysis": ai_result.get("fundamental_analysis", ""),
            "market_sentiment": ai_result.get("market_sentiment", ""),

            # 관련 뉴스
            "related_news_count": len(news_data),

            # 메타데이터
            "cached": False
        }

        # 7. Redis 캐싱
        set_cached_report(symbol, report_date_str, report)

        print(f"✅ 레포트 생성 완료: {symbol_name} ({symbol})\n")
        return report

    except Exception as e:
        print(f"❌ 레포트 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"레포트 생성 중 오류 발생: {str(e)}")


@app.post("/api/reports/bookmark")
async def bookmark_report(
    request: ReportRequest,
    response: Response,
    authorization: Optional[str] = Header(None)
):
    """
    레포트 북마크 저장

    Args:
        request: 종목 코드 및 종목명
        authorization: JWT 토큰

    Returns:
        Dict: 저장된 북마크 ID
    """
    # CORS 헤더
    response.headers["Access-Control-Allow-Origin"] = "*"

    user_id = get_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")

    symbol = request.symbol
    symbol_name = request.symbol_name
    report_date_str = date.today().isoformat()

    try:
        # 1. 캐시에서 레포트 조회
        cached_report = get_cached_report(symbol, report_date_str)
        if not cached_report:
            raise HTTPException(status_code=404, detail="레포트를 먼저 생성해주세요")

        # 2. 뉴스 데이터 조회 (related_news_ids용)
        news_result = supabase.table("news") \
            .select("id") \
            .contains("related_symbols", [symbol]) \
            .gte("published_at", datetime.now().replace(hour=0, minute=0, second=0).isoformat()) \
            .execute()
        related_news_ids = [news["id"] for news in (news_result.data or [])]

        # 3. Supabase에 북마크 저장
        bookmark_data = {
            "user_id": user_id,
            "symbol": symbol,
            "symbol_name": symbol_name,
            "report_date": report_date_str,
            **{k: v for k, v in cached_report.items() if k not in ["symbol", "symbol_name", "report_date", "cached", "related_news_count"]},
            "related_news_ids": related_news_ids,
            "is_bookmarked": True
        }

        result = supabase.table("stock_reports").upsert(
            bookmark_data,
            on_conflict="user_id,symbol,report_date"
        ).execute()

        print(f"✅ 북마크 저장: {symbol_name} ({symbol}) - user_id: {user_id}")

        return {
            "message": f"{symbol_name} 레포트를 북마크에 저장했습니다",
            "bookmark_id": result.data[0]["id"] if result.data else None
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 북마크 저장 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"북마크 저장 중 오류 발생: {str(e)}")


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


@app.delete("/api/reports/bookmarks/{bookmark_id}")
async def delete_bookmark(bookmark_id: str, authorization: Optional[str] = Header(None)):
    """
    북마크 삭제

    Args:
        bookmark_id: 북마크 ID (UUID)
        authorization: JWT 토큰

    Returns:
        Dict: 삭제 결과
    """
    user_id = get_user_id_from_token(authorization)

    if not user_id:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")

    try:
        # 먼저 북마크 소유자 확인
        check_result = supabase.table("stock_reports") \
            .select("symbol_name") \
            .eq("id", bookmark_id) \
            .eq("user_id", user_id) \
            .maybeSingle() \
            .execute()

        if not check_result.data:
            raise HTTPException(status_code=404, detail="북마크를 찾을 수 없습니다")

        # 삭제
        supabase.table("stock_reports") \
            .delete() \
            .eq("id", bookmark_id) \
            .eq("user_id", user_id) \
            .execute()

        symbol_name = check_result.data["symbol_name"]
        print(f"✅ 북마크 삭제: {symbol_name} - user_id: {user_id}")

        return {"message": f"{symbol_name} 북마크가 삭제되었습니다"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 북마크 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"북마크 삭제 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    # Railway/Render에서 제공하는 PORT 환경 변수 사용
    port = int(os.getenv("PORT", "3004"))
    print(f"🚀 Report Service starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
