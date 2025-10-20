"""
Report Service - FastAPI 서버
종목 레포트 생성 및 조회 API
- AI Ensemble (GPT-4 + Claude) 지원
- 고급 기술적 지표 (RSI, MACD, Stochastic 등 22개)
- 호가/체결 데이터 통합
- 섹터 비교 분석
- API Rate Limiting
"""
import os
import sys
import traceback
import asyncio
from datetime import datetime, date, timedelta, timezone
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
    from kis_data import (
        get_daily_ohlcv,
        get_financial_ratio,
        get_investor_trend,
        # 🔥 Phase 1.2: 신규 엔드포인트 7개
        get_analyst_opinion,
        get_sector_info,
        get_credit_balance_trend,
        get_short_selling_trend,
        get_program_trading_trend,
        get_institutional_flow_estimate,
        get_index_price,
        # 🔥 Phase 4.1: 업종 상대 평가
        get_sector_relative_analysis,
        # 🔥 Phase 4.2: 시장 전체 맥락 분석
        get_market_context
    )
    print("  ✅ kis_data 모듈 (7개 신규 API 포함)")
    from technical import calculate_all_indicators
    print("  ✅ technical 모듈")
    from ai_analyzer import analyze_stock
    print("  ✅ ai_analyzer 모듈")

    # 🔥 신규 모듈 임포트
    from ai_ensemble import analyze_with_ensemble
    print("  ✅ ai_ensemble 모듈 (GPT-4 + Claude)")
    from kis_data_advanced import get_advanced_stock_data
    print("  ✅ kis_data_advanced 모듈 (호가/체결)")
    from sector_analysis import compare_with_sector, detect_sector_rotation
    # 🔥 Phase 5.1: 목표가 산출 모듈
    from target_price_calculator import calculate_target_prices
    print("  ✅ target_price_calculator 모듈 (목표가 산출)")
    # 🔥 Phase 5.2: 매매 타이밍 신호 생성 모듈
    from trading_signal_generator import generate_trading_signals
    print("  ✅ trading_signal_generator 모듈 (매매 신호)")
    print("  ✅ sector_analysis 모듈 (섹터 비교)")
    from rate_limiter import rate_limited_kis_request
    print("  ✅ rate_limiter 모듈 (API Rate Limit)")

    print("✅ 모든 모듈 임포트 완료")
except Exception as e:
    print(f"❌ 모듈 임포트 실패: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

# FastAPI 앱 초기화
print("📦 FastAPI 앱 초기화 중...")
app = FastAPI(
    title="Report Service",
    version="2.0.0",  # 🔥 Major Update: AI Ensemble + Advanced Indicators
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
        "version": "2.0.0",
        "features": {
            "ai_ensemble": True,
            "advanced_indicators": True,
            "order_book": True,
            "rate_limiting": True,
            "parallel_processing": True
        }
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
        # 2. 병렬 데이터 조회 (asyncio.gather 사용)
        print(f"📈 데이터 조회 시작 (병렬 처리)...")

        # 2-1. 필수 데이터 (OHLCV) 먼저 조회
        ohlcv_data = await rate_limited_kis_request(get_daily_ohlcv, symbol, days=60)

        if not ohlcv_data or len(ohlcv_data) < 20:
            raise HTTPException(
                status_code=400,
                detail=f"주가 데이터가 부족합니다. (최소 20일 필요, 현재: {len(ohlcv_data)}일)"
            )

        # 2-2. 병렬로 조회할 데이터 정의
        async def safe_get_financial():
            try:
                return await rate_limited_kis_request(get_financial_ratio, symbol)
            except Exception as e:
                print(f"⚠️ 재무비율 조회 실패: {str(e)}")
                return {}

        async def safe_get_investor():
            try:
                return await rate_limited_kis_request(get_investor_trend, symbol)
            except Exception as e:
                print(f"⚠️ 투자자 동향 조회 실패: {str(e)}")
                return {}

        async def safe_get_advanced():
            try:
                return await rate_limited_kis_request(get_advanced_stock_data, symbol)
            except Exception as e:
                print(f"⚠️ 고급 데이터 조회 실패: {str(e)}")
                return {}

        async def safe_get_news():
            try:
                # 🔥 Phase 1.1: 뉴스 데이터 확장 (당일 → 7일, 10개 → 50개)
                seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

                news_result = supabase.table("news") \
                    .select("id, title, summary, sentiment_score, impact_score, published_at, url") \
                    .contains("related_symbols", [symbol]) \
                    .gte("published_at", seven_days_ago) \
                    .order("impact_score", desc=True) \
                    .order("published_at", desc=True) \
                    .limit(50) \
                    .execute()
                return news_result.data or []
            except Exception as e:
                print(f"⚠️ 뉴스 조회 실패: {str(e)}")
                return []

        # 🔥 Phase 1.2: 신규 데이터 조회 함수 7개
        async def safe_get_analyst_opinion():
            try:
                return await rate_limited_kis_request(get_analyst_opinion, symbol)
            except Exception as e:
                print(f"⚠️ 애널리스트 의견 조회 실패: {str(e)}")
                return {"buy_count": 0, "hold_count": 0, "sell_count": 0, "avg_target_price": None, "total_count": 0}

        async def safe_get_sector_info():
            try:
                return await rate_limited_kis_request(get_sector_info, symbol)
            except Exception as e:
                print(f"⚠️ 업종 정보 조회 실패: {str(e)}")
                return {"sector_name": None, "sector_code": None}

        async def safe_get_credit_balance():
            try:
                return await rate_limited_kis_request(get_credit_balance_trend, symbol, days=5)
            except Exception as e:
                print(f"⚠️ 신용잔고 조회 실패: {str(e)}")
                return []

        async def safe_get_short_selling():
            try:
                return await rate_limited_kis_request(get_short_selling_trend, symbol, days=5)
            except Exception as e:
                print(f"⚠️ 공매도 조회 실패: {str(e)}")
                return []

        async def safe_get_program_trading():
            try:
                return await rate_limited_kis_request(get_program_trading_trend, symbol, days=5)
            except Exception as e:
                print(f"⚠️ 프로그램매매 조회 실패: {str(e)}")
                return []

        async def safe_get_institutional_flow():
            try:
                return await rate_limited_kis_request(get_institutional_flow_estimate, symbol)
            except Exception as e:
                print(f"⚠️ 매매 가집계 조회 실패: {str(e)}")
                return {"foreign_net_buy_amt": 0, "institution_net_buy_amt": 0}

        async def safe_get_kospi_index():
            try:
                return await rate_limited_kis_request(get_index_price, "0001")  # 코스피
            except Exception as e:
                print(f"⚠️ 코스피 지수 조회 실패: {str(e)}")
                return {"index_value": 0, "change_rate": 0}

        # 병렬 실행 (asyncio.gather) - 🔥 신규 데이터 포함
        (
            financial_data,
            investor_data,
            advanced_data,
            news_data,
            analyst_opinion,
            sector_info,
            credit_balance,
            short_selling,
            program_trading,
            institutional_flow,
            kospi_index
        ) = await asyncio.gather(
            safe_get_financial(),
            safe_get_investor(),
            safe_get_advanced(),
            safe_get_news(),
            # 🔥 Phase 1.2: 신규 데이터 조회 7개 추가
            safe_get_analyst_opinion(),
            safe_get_sector_info(),
            safe_get_credit_balance(),
            safe_get_short_selling(),
            safe_get_program_trading(),
            safe_get_institutional_flow(),
            safe_get_kospi_index()
        )

        # 🔥 Phase 4.1: 업종 상대 평가 (sector_info 조회 후 실행)
        sector_relative = {}
        if sector_info.get("sector_code"):
            try:
                sector_relative = await rate_limited_kis_request(
                    get_sector_relative_analysis,
                    symbol,
                    sector_info.get("sector_code")
                )
                print(f"✅ 업종 상대 평가: 상대강도 {sector_relative.get('relative_strength', 1.0):.2f}")
            except Exception as e:
                print(f"⚠️ 업종 상대 평가 실패: {str(e)}")
                sector_relative = {
                    "sector_avg_change_rate": 0,
                    "relative_strength": 1.0,
                    "sector_rank_pct": 50,
                    "sector_avg_volume_ratio": 1.0,
                    "sector_avg_per": 0,
                    "sector_avg_pbr": 0,
                    "outperformance": 0,
                    "sample_size": 0
                }

        # 🔥 Phase 4.2: 시장 전체 맥락 분석
        market_context = {}
        try:
            market_context = await rate_limited_kis_request(get_market_context)
            print(f"✅ 시장 맥락: {market_context.get('market_trend', 'N/A').upper()} (심리: {market_context.get('market_sentiment', 'N/A')})")
        except Exception as e:
            print(f"⚠️ 시장 맥락 분석 실패: {str(e)}")
            market_context = {
                "market_trend": "neutral",
                "market_strength": 50,
                "market_sentiment": "데이터 부족",
                "kospi": {"value": 0, "change_rate": 0, "momentum": "N/A"},
                "kosdaq": {"value": 0, "change_rate": 0, "momentum": "N/A"},
                "volatility_level": "medium",
                "volatility_value": 0,
                "market_breadth": "neutral",
                "market_breadth_pct": 50
            }

        print(f"✅ 데이터 조회 완료 (병렬 처리)")
        print(f"   - 뉴스: {len(news_data)}개")
        print(f"   - 고급 데이터: {'✅' if advanced_data else '❌'}")

        # 3. 기술적 지표 계산 (고급 지표 포함)
        print(f"📊 기술적 지표 계산 중 (22개 지표)...")
        indicators = calculate_all_indicators(ohlcv_data, include_advanced=True)

        # 4. AI 앙상블 분석 (GPT-4 + Claude)
        print(f"🤖 AI Ensemble 분석 시작...")
        use_ensemble = os.getenv("USE_AI_ENSEMBLE", "true").lower() == "true"

        if use_ensemble:
            # 🔥 Phase 1.3: 확장된 데이터를 AI Ensemble에 전달
            ai_result = await analyze_with_ensemble(
                symbol,
                symbol_name,
                indicators,
                news_data,
                financial_data=financial_data,
                investor_data=investor_data,
                analyst_opinion=analyst_opinion,
                sector_info=sector_info,
                market_index=kospi_index,
                credit_balance=credit_balance,
                short_selling=short_selling,
                program_trading=program_trading,
                institutional_flow=institutional_flow,
                sector_relative=sector_relative,  # 🔥 Phase 4.1: 업종 상대 평가
                market_context=market_context  # 🔥 Phase 4.2: 시장 전체 맥락
            )
        else:
            # 폴백: 단일 모델 (GPT-4)
            ai_result = await analyze_stock(
                symbol,
                symbol_name,
                indicators,
                news_data,
                financial_data=financial_data,
                investor_data=investor_data
            )

        # 🔥 Phase 5.1: 목표가 산출 (보수적/중립적/공격적)
        print(f"💰 목표가 산출...")
        target_prices = calculate_target_prices(
            current_price=indicators["current_price"],
            financial_data=financial_data,
            analyst_opinion=analyst_opinion,
            price_data=indicators,
            sector_relative=sector_relative,
            market_context=market_context
        )

        # 🔥 Phase 5.2: 매매 타이밍 신호 생성
        print(f"📊 매매 신호 생성... (버전: v2.1 - risk_scores 변환 포함)")

        # ai_result의 risk_score를 risk_scores 형식으로 변환
        ai_risk_score = ai_result.get("risk_score", 50)
        print(f"🔍 [DEBUG] ai_risk_score: {ai_risk_score} (type: {type(ai_risk_score)})")
        print(f"🔍 [DEBUG] ai_result keys: {ai_result.keys() if isinstance(ai_result, dict) else 'NOT A DICT'}")
        print(f"🔍 [DEBUG] ai_result: {ai_result}")
        risk_scores_formatted = {
            "short_term": {"score": ai_risk_score},
            "mid_term": {"score": ai_risk_score},
            "long_term": {"score": ai_risk_score}
        }
        print(f"🔍 [DEBUG] risk_scores_formatted: {risk_scores_formatted}")

        trading_signals = generate_trading_signals(
            current_price=indicators["current_price"],
            target_prices=target_prices,
            technical_indicators=indicators,
            risk_scores=risk_scores_formatted,
            market_context=market_context,
            ai_recommendations=ai_result,
            analyst_opinion=analyst_opinion
        )

        # 5. 레포트 데이터 구성
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

            # 기본 기술적 지표 (7개)
            "ma5": indicators.get("ma5"),
            "ma20": indicators.get("ma20"),
            "ma60": indicators.get("ma60"),
            "volume_ratio": indicators.get("volume_ratio"),
            "volatility": indicators.get("volatility"),
            "bollinger_upper": indicators.get("bollinger_upper"),
            "bollinger_lower": indicators.get("bollinger_lower"),

            # 🔥 고급 기술적 지표 (15개 - 신규)
            "rsi": indicators.get("rsi"),
            "macd": indicators.get("macd"),
            "macd_signal": indicators.get("macd_signal"),
            "macd_histogram": indicators.get("macd_histogram"),
            "stochastic_k": indicators.get("stochastic_k"),
            "stochastic_d": indicators.get("stochastic_d"),
            "williams_r": indicators.get("williams_r"),
            "cci": indicators.get("cci"),
            "adx": indicators.get("adx"),
            "obv": indicators.get("obv"),
            "mfi": indicators.get("mfi"),
            "vwap": indicators.get("vwap"),
            "atr": indicators.get("atr"),
            "keltner_upper": indicators.get("keltner_upper"),
            "keltner_middle": indicators.get("keltner_middle"),
            "keltner_lower": indicators.get("keltner_lower"),

            # 재무비율
            "per": financial_data.get("per"),
            "pbr": financial_data.get("pbr"),
            "roe": financial_data.get("roe"),
            "dividend_yield": financial_data.get("dividend_yield"),
            "eps": financial_data.get("eps"),
            "bps": financial_data.get("bps"),
            "operating_margin": financial_data.get("operating_margin"),
            "net_margin": financial_data.get("net_margin"),
            "debt_ratio": financial_data.get("debt_ratio"),

            # 투자자 동향
            "foreign_net_buy": investor_data.get("foreign_net_buy"),
            "foreign_net_buy_amt": investor_data.get("foreign_net_buy_amt"),
            "institution_net_buy": investor_data.get("institution_net_buy"),
            "institution_net_buy_amt": investor_data.get("institution_net_buy_amt"),
            "individual_net_buy": investor_data.get("individual_net_buy"),
            "individual_net_buy_amt": investor_data.get("individual_net_buy_amt"),

            # 🔥 고급 데이터 (호가/체결 - 신규)
            "order_book": advanced_data.get("order_book", {}),
            "execution": advanced_data.get("execution", {}),

            # AI Ensemble 분석 결과
            "summary": ai_result["summary"],
            "risk_level": ai_result["risk_level"],
            "recommendation": ai_result["recommendation"],
            "evaluation_score": ai_result["evaluation_score"],

            # 🔥 AI Ensemble 메타데이터 (신규)
            "confidence_score": ai_result.get("confidence_score", 50.0),  # 앙상블 신뢰도
            "model_agreement": ai_result.get("model_agreement", {}),      # 모델별 결과

            # AI 분석 확장
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

            # 🔥 Phase 1.2: 신규 데이터 7개
            "analyst_opinion": {
                "buy_count": analyst_opinion.get("buy_count", 0),
                "hold_count": analyst_opinion.get("hold_count", 0),
                "sell_count": analyst_opinion.get("sell_count", 0),
                "avg_target_price": analyst_opinion.get("avg_target_price"),
                "total_count": analyst_opinion.get("total_count", 0)
            },
            "sector_info": {
                "sector_name": sector_info.get("sector_name"),
                "sector_code": sector_info.get("sector_code")
            },
            # 🔥 Phase 4.1: 업종 상대 평가
            "sector_relative": {
                "sector_avg_change_rate": sector_relative.get("sector_avg_change_rate", 0),
                "relative_strength": sector_relative.get("relative_strength", 1.0),
                "sector_rank_pct": sector_relative.get("sector_rank_pct", 50),
                "outperformance": sector_relative.get("outperformance", 0),
                "sample_size": sector_relative.get("sample_size", 0),
                "note": sector_relative.get("note", "")
            },
            "credit_balance_trend": credit_balance,
            "short_selling_trend": short_selling,
            "program_trading_trend": program_trading,
            "institutional_flow_today": {
                "foreign_net_buy_amt": institutional_flow.get("foreign_net_buy_amt", 0),
                "institution_net_buy_amt": institutional_flow.get("institution_net_buy_amt", 0)
            },
            "market_index": {
                "kospi_value": kospi_index.get("index_value", 0),
                "kospi_change_rate": kospi_index.get("change_rate", 0)
            },
            # 🔥 Phase 4.2: 시장 전체 맥락
            "market_context": {
                "market_trend": market_context.get("market_trend", "neutral"),
                "market_strength": market_context.get("market_strength", 50),
                "market_sentiment": market_context.get("market_sentiment", "N/A"),
                "kospi": market_context.get("kospi", {}),
                "kosdaq": market_context.get("kosdaq", {}),
                "volatility_level": market_context.get("volatility_level", "medium"),
                "volatility_value": market_context.get("volatility_value", 0),
                "market_breadth": market_context.get("market_breadth", "neutral"),
                "market_breadth_pct": market_context.get("market_breadth_pct", 50)
            },
            # 🔥 Phase 5.1: 목표가 산출
            "target_prices": {
                "conservative": target_prices.get("conservative"),
                "neutral": target_prices.get("neutral"),
                "aggressive": target_prices.get("aggressive"),
                "current_price": target_prices.get("current_price"),
                "upside_potential": target_prices.get("upside_potential", {}),
                "methods": target_prices.get("methods", {}),
                "market_adjustment_factor": target_prices.get("market_adjustment_factor", 1.0)
            },
            # 🔥 Phase 5.2: 매매 타이밍 신호
            "trading_signals": {
                "signal": trading_signals.get("signal"),  # buy/sell/hold
                "confidence": trading_signals.get("confidence"),  # 0-100
                "strength": trading_signals.get("strength"),  # weak/moderate/strong
                "entry_timing": trading_signals.get("entry_timing"),  # immediate/wait/gradual
                "position_size": trading_signals.get("position_size"),  # small/medium/large
                "entry_price_range": trading_signals.get("entry_price_range", {}),
                "stop_loss": trading_signals.get("stop_loss"),
                "take_profit": trading_signals.get("take_profit", {}),
                "reasoning": trading_signals.get("reasoning", ""),
                "risks": trading_signals.get("risks", []),
                "favorable_factors": trading_signals.get("favorable_factors", []),
                "unfavorable_factors": trading_signals.get("unfavorable_factors", []),
                "analysis_breakdown": trading_signals.get("analysis_breakdown", {})
            },

            # 메타데이터
            "cached": False,
            "ai_model": "ensemble" if use_ensemble else "gpt-4",
            "indicators_count": 22  # 기본 7개 + 고급 15개
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
        # bigint 타입 필드 정수 변환 (소수점 제거)
        bigint_fields = ["volume", "obv", "foreign_net_buy", "institution_net_buy", "individual_net_buy"]

        bookmark_data = {
            "user_id": user_id,
            "symbol": symbol,
            "symbol_name": symbol_name,
            "report_date": report_date_str,
            "related_news_ids": related_news_ids,
            "is_bookmarked": True
        }

        # 캐시 데이터 추가 (cached, related_news_count 제외)
        for k, v in cached_report.items():
            if k in ["symbol", "symbol_name", "report_date", "cached", "related_news_count"]:
                continue

            # bigint 필드는 정수로 변환
            if k in bigint_fields and v is not None:
                bookmark_data[k] = int(float(v))
            else:
                bookmark_data[k] = v

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
