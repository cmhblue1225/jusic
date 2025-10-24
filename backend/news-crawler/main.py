"""
뉴스 크롤러 메인 서비스
네이버 뉴스 검색 API + Google News RSS를 통해 종목별 뉴스를 수집하고 Supabase에 저장

🔥 Phase 2.1: Google News RSS 추가
"""
import os
from fastapi import FastAPI, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
from dotenv import load_dotenv
import httpx
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
from nlp.ner import StockNER
from naver_api import NaverNewsAPI
from google_news_rss import GoogleNewsRSS  # 🔥 Phase 2.1
from naver_discussion_crawler import NaverDiscussionCrawler  # 🔥 Phase 2.2
from dart_disclosure_crawler import DartDisclosureCrawler  # 🔥 Phase 2.3

load_dotenv()

app = FastAPI(title="News Crawler Service")

# Supabase 클라이언트
supabase: Client = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_SERVICE_KEY", "")
)

# AI Service URL
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:3003")

# 🔥 AI 분석 활성화 여부 (환경 변수로 제어)
AI_ANALYSIS_ENABLED = os.getenv("AI_ANALYSIS_ENABLED", "true").lower() == "true"

# 종목명 추출기 초기화
stock_ner = StockNER(supabase)

# 네이버 API 클라이언트 초기화
naver_api = NaverNewsAPI()

# 🔥 Phase 2.1: Google News RSS 클라이언트 초기화
google_news = GoogleNewsRSS()

# 🔥 Phase 2.2: 네이버 토론방 크롤러 초기화
naver_discussion = NaverDiscussionCrawler()

# 🔥 Phase 2.3: DART 전자공시 크롤러 초기화
dart_crawler = DartDisclosureCrawler()

# 🔥 스케줄러 전역 변수 (관리자 제어용)
scheduler: BackgroundScheduler = None


async def analyze_news_with_ai(title: str, content: str, symbols: list, url: str) -> dict:
    """AI 서비스로 뉴스 분석 (URL 포함으로 캐싱 활용)"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{AI_SERVICE_URL}/analyze",
                json={
                    "title": title,
                    "content": content,
                    "symbols": symbols,
                    "url": url  # 캐싱을 위한 URL 추가
                }
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️ AI 분석 실패 (status {response.status_code})")
                return None

    except Exception as e:
        print(f"❌ AI 분석 오류: {str(e)}")
        return None


async def create_alerts_for_news(news_data: dict, ai_result: dict):
    """
    영향도가 높은 뉴스에 대해 관련 종목을 보유/관심 중인 사용자에게 알림 생성

    Args:
        news_data: 뉴스 데이터
        ai_result: AI 분석 결과
    """
    try:
        related_symbols = news_data.get("related_symbols", [])
        if not related_symbols:
            return

        impact_score = ai_result.get("impact_score", 0)
        sentiment_score = ai_result.get("sentiment_score", 0)
        recommended_action = ai_result.get("recommended_action", "hold")

        # 1. 해당 종목을 보유/관심 중인 사용자 조회
        portfolio_users = supabase.table("portfolios") \
            .select("user_id") \
            .in_("symbol", related_symbols) \
            .execute()

        watchlist_users = supabase.table("watchlist") \
            .select("user_id") \
            .in_("symbol", related_symbols) \
            .execute()

        # 사용자 ID 중복 제거
        user_ids = set()
        if portfolio_users.data:
            user_ids.update([item["user_id"] for item in portfolio_users.data])
        if watchlist_users.data:
            user_ids.update([item["user_id"] for item in watchlist_users.data])

        if not user_ids:
            print(f"   ℹ️ 관련 사용자 없음 (종목: {related_symbols})")
            return

        # 2. 각 사용자에게 알림 생성
        alerts = []
        for user_id in user_ids:
            # 감성에 따른 이모지
            emoji = "📈" if sentiment_score > 0 else "📉" if sentiment_score < 0 else "📊"

            # 권고에 따른 액션 텍스트
            action_text = {
                "buy": "매수 검토",
                "sell": "매도 검토",
                "hold": "관망 권장"
            }.get(recommended_action, "정보 확인")

            alert = {
                "user_id": user_id,
                "type": "news",
                "title": f"{emoji} 중요 뉴스 ({', '.join(related_symbols[:3])})",
                "message": f"{news_data['title'][:100]}... [{action_text}]",
                "params": {
                    "news_url": news_data.get("url"),
                    "impact_score": impact_score,
                    "sentiment_score": sentiment_score,
                    "recommended_action": recommended_action,
                    "related_symbols": related_symbols,
                },
                "status": "unread",
            }
            alerts.append(alert)

        # 3. 배치 삽입
        if alerts:
            supabase.table("alerts").insert(alerts).execute()
            print(f"   🔔 알림 생성 완료: {len(alerts)}명 사용자")

    except Exception as e:
        print(f"❌ 알림 생성 오류: {str(e)}")


async def get_user_tracked_stocks() -> list:
    """모든 사용자의 보유 종목 + 관심 종목 조회 (중복 제거)"""
    try:
        # 1. 보유 종목 조회
        portfolio_result = supabase.table("portfolios") \
            .select("symbol") \
            .execute()

        # 2. 관심 종목 조회
        watchlist_result = supabase.table("watchlist") \
            .select("symbol") \
            .execute()

        # 3. 종목 코드 합치고 중복 제거
        portfolio_symbols = {item["symbol"] for item in (portfolio_result.data or [])}
        watchlist_symbols = {item["symbol"] for item in (watchlist_result.data or [])}
        all_symbols = portfolio_symbols | watchlist_symbols  # 집합 합집합 (중복 자동 제거)

        if not all_symbols:
            print("⚠️ 사용자의 보유/관심 종목이 없습니다. 기본 종목 사용")
            return [
                {"symbol": "005930", "name": "삼성전자"},
                {"symbol": "000660", "name": "SK하이닉스"},
                {"symbol": "035420", "name": "NAVER"},
                {"symbol": "035720", "name": "카카오"},
                {"symbol": "051910", "name": "LG화학"},
            ]

        # 4. stock_master에서 종목명 조회
        symbols_list = list(all_symbols)
        stock_master_result = supabase.table("stock_master") \
            .select("symbol, name") \
            .in_("symbol", symbols_list) \
            .execute()

        if stock_master_result.data:
            print(f"📊 사용자 추적 종목 {len(stock_master_result.data)}개 조회 완료 (보유 {len(portfolio_symbols)}개 + 관심 {len(watchlist_symbols)}개)")
            return [{"symbol": item["symbol"], "name": item["name"]} for item in stock_master_result.data]
        else:
            print("⚠️ stock_master에서 종목 정보를 찾을 수 없습니다. 기본 종목 사용")
            return [
                {"symbol": "005930", "name": "삼성전자"},
                {"symbol": "000660", "name": "SK하이닉스"},
                {"symbol": "035420", "name": "NAVER"},
                {"symbol": "035720", "name": "카카오"},
                {"symbol": "051910", "name": "LG화학"},
            ]
    except Exception as e:
        print(f"❌ 종목 조회 오류: {str(e)}")
        # 폴백: 기본 종목 반환
        return [
            {"symbol": "005930", "name": "삼성전자"},
            {"symbol": "000660", "name": "SK하이닉스"},
            {"symbol": "035420", "name": "NAVER"},
            {"symbol": "035720", "name": "카카오"},
            {"symbol": "051910", "name": "LG화학"},
        ]


async def crawl_news():
    """🔥 Phase 2.1: 네이버 API + Google News RSS 뉴스 크롤링"""
    print(f"[{datetime.now()}] 멀티 소스 뉴스 크롤링 시작...")

    # 1. 사용자 추적 종목 조회 (보유 + 관심)
    tracked_stocks = await get_user_tracked_stocks()
    stock_names = [stock["name"] for stock in tracked_stocks]

    print(f"🎯 사용자 추적 종목: {len(stock_names)}개")

    # 2. 네이버 API로 종목별 뉴스 검색 (종목당 10개)
    naver_news = []
    try:
        naver_news = await naver_api.search_multiple_stocks(
            stock_names=stock_names,
            results_per_stock=10
        )

        print(f"📰 [Naver] {len(naver_news)}개 뉴스 수집 (중복 제거 후)")

        # API 사용량 로깅
        api_calls = len(stock_names) * 10
        print(f"📊 [Naver] API 호출 수: {api_calls}개 (일일 한도: 25,000)")

    except Exception as e:
        print(f"⚠️ [Naver] API 호출 오류: {str(e)}")

    # 🔥 Phase 2.1: Google News RSS로 추가 뉴스 검색 (종목당 5개)
    google_news_list = []
    try:
        google_news_list = await google_news.search_multiple_stocks(
            stock_names=stock_names,
            results_per_stock=5
        )

        print(f"📰 [Google News] {len(google_news_list)}개 뉴스 수집 (중복 제거 후)")

    except Exception as e:
        print(f"⚠️ [Google News] RSS 크롤링 오류: {str(e)}")

    # 3. 두 소스 병합 및 URL 기준 중복 제거
    all_news = naver_news + google_news_list
    seen_urls = set()
    unique_news = []

    for news in all_news:
        if news["url"] not in seen_urls:
            seen_urls.add(news["url"])
            unique_news.append(news)

    all_news = unique_news
    print(f"📊 [통합] 총 {len(all_news)}개 뉴스 (Naver + Google News, 중복 제거 후)")

    if not all_news:
        print("⚠️ 수집된 뉴스가 없습니다.")
        return

    # 3. 각 뉴스 처리
    new_count = 0
    duplicate_count = 0
    old_news_count = 0

    # 3일 이전 시간 계산 (최신 뉴스 위주)
    # UTC timezone aware datetime 사용
    cutoff_time = datetime.now(timezone.utc) - timedelta(days=3)

    for news_item in all_news:
        try:
            # 발행 시간 체크 (3일 이내만 처리)
            published_at = datetime.fromisoformat(news_item["published_at"].replace('Z', '+00:00'))
            if published_at < cutoff_time:
                old_news_count += 1
                continue

            # 중복 체크 (URL 기준)
            existing = supabase.table("news").select("id").eq("url", news_item["url"]).execute()

            if existing.data:
                duplicate_count += 1
                continue

            title = news_item["title"]
            content = news_item["content"]
            url = news_item["url"]

            # 4. NER로 종목 코드 추출 및 검증
            full_text = f"{title} {content}"
            related_symbols = stock_ner.extract_symbols(full_text)

            print(f"\n📰 새 뉴스: {title[:50]}...")
            print(f"   URL: {url}")
            print(f"   NER 추출 종목: {related_symbols}")

            # 5. AI 분석 요청 (환경 변수로 제어)
            ai_result = None
            if AI_ANALYSIS_ENABLED:
                ai_result = await analyze_news_with_ai(title, content, related_symbols, url)
            else:
                print(f"   ⏸️ AI 분석 비활성화됨 (AI_ANALYSIS_ENABLED=false)")

            # 6. Supabase에 저장
            news_data = {
                "source": news_item["source"],
                "title": title,
                "content": content,
                "url": url,
                "published_at": news_item["published_at"],
                "related_symbols": related_symbols,
            }

            # AI 분석 결과 추가
            if ai_result:
                news_data.update({
                    "summary": ai_result.get("summary"),
                    "sentiment_score": ai_result.get("sentiment_score"),
                    "impact_score": ai_result.get("impact_score"),
                    "recommended_action": ai_result.get("recommended_action"),
                })
                print(f"   AI 분석 완료 - 영향도: {ai_result.get('impact_score'):.2f}, 감정: {ai_result.get('sentiment_score'):.2f}, 권고: {ai_result.get('recommended_action')}")

            # DB 저장
            result = supabase.table("news").insert(news_data).execute()
            new_count += 1
            print(f"✅ 뉴스 저장 완료")

            # 7. 영향도 기반 알림 생성 (impact_score >= 0.7)
            if ai_result and ai_result.get("impact_score", 0) >= 0.7:
                await create_alerts_for_news(news_data, ai_result)

        except Exception as e:
            print(f"❌ 뉴스 처리 오류: {str(e)}")
            continue

    print(f"\n[{datetime.now()}] 멀티 소스 뉴스 크롤링 완료 (Naver + Google News)")
    print(f"📈 통계: 신규 {new_count}개, 중복 {duplicate_count}개, 3일 이전 {old_news_count}개\n")


def crawl_news_sync():
    """동기 wrapper 함수 - 스케줄러에서 호출"""
    # 새 이벤트 루프 생성 및 실행
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(crawl_news())
    finally:
        loop.close()


@app.on_event("startup")
async def startup_event():
    """앱 시작 시 스케줄러 실행"""
    global scheduler
    scheduler = BackgroundScheduler()
    # 5분마다 뉴스 크롤링
    scheduler.add_job(crawl_news_sync, 'interval', minutes=5)
    scheduler.start()
    print("📰 News Crawler Scheduler started (every 5 minutes)")
    print(f"🤖 AI 분석: {'✅ 활성화' if AI_ANALYSIS_ENABLED else '⏸️ 비활성화'}")

    # 시작 시 즉시 한 번 실행
    print("🚀 초기 크롤링 실행...")
    asyncio.create_task(crawl_news())


@app.get("/health")
async def health():
    return {"status": "ok", "service": "news-crawler"}


@app.post("/crawl")
async def trigger_crawl():
    """수동 크롤링 트리거"""
    await crawl_news()
    return {"message": "Crawling triggered"}


# 🔥 관리자 제어 엔드포인트
@app.post("/admin/scheduler/pause")
async def pause_scheduler():
    """스케줄러 일시중지 (관리자 전용)"""
    global scheduler
    if scheduler is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")

    try:
        scheduler.pause()
        return {
            "status": "paused",
            "message": "News crawler scheduler has been paused"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause scheduler: {str(e)}")


@app.post("/admin/scheduler/resume")
async def resume_scheduler():
    """스케줄러 재개 (관리자 전용)"""
    global scheduler
    if scheduler is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")

    try:
        scheduler.resume()
        return {
            "status": "running",
            "message": "News crawler scheduler has been resumed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume scheduler: {str(e)}")


@app.get("/admin/scheduler/status")
async def get_scheduler_status():
    """스케줄러 상태 조회"""
    global scheduler
    if scheduler is None:
        return {
            "status": "not_initialized",
            "state": None,
            "jobs": []
        }

    # APScheduler 상태: 0=stopped, 1=running, 2=paused
    state_map = {0: "stopped", 1: "running", 2: "paused"}
    state_code = scheduler.state
    status = state_map.get(state_code, "unknown")

    # 등록된 job 목록
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
        })

    return {
        "status": status,
        "state": state_code,
        "jobs": jobs,
        "ai_analysis_enabled": AI_ANALYSIS_ENABLED
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)
