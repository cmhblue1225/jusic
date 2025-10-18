"""
뉴스 크롤러 메인 서비스
네이버 뉴스 검색 API를 통해 종목별 뉴스를 수집하고 Supabase에 저장
"""
import os
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
from dotenv import load_dotenv
import httpx
from datetime import datetime
from supabase import create_client, Client
from nlp.ner import StockNER
from naver_api import NaverNewsAPI

load_dotenv()

app = FastAPI(title="News Crawler Service")

# Supabase 클라이언트
supabase: Client = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_SERVICE_KEY", "")
)

# AI Service URL
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:3003")

# 종목명 추출기 초기화
stock_ner = StockNER(supabase)

# 네이버 API 클라이언트 초기화
naver_api = NaverNewsAPI()


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
    """네이버 API를 사용한 뉴스 크롤링"""
    print(f"[{datetime.now()}] 네이버 API 뉴스 크롤링 시작...")

    # 1. 사용자 추적 종목 조회 (보유 + 관심)
    tracked_stocks = await get_user_tracked_stocks()
    stock_names = [stock["name"] for stock in tracked_stocks]

    print(f"🎯 사용자 추적 종목: {len(stock_names)}개")

    # 2. 네이버 API로 종목별 뉴스 검색 (종목당 5개)
    try:
        all_news = await naver_api.search_multiple_stocks(
            stock_names=stock_names,
            results_per_stock=5
        )

        print(f"📰 총 {len(all_news)}개 뉴스 수집 (중복 제거 후)")

        # API 사용량 로깅
        api_calls = len(stock_names) * 5
        print(f"📊 API 호출 수: {api_calls}개 (일일 한도: 25,000)")

    except Exception as e:
        print(f"❌ 네이버 API 호출 오류: {str(e)}")
        return

    # 3. 각 뉴스 처리
    new_count = 0
    duplicate_count = 0

    for news_item in all_news:
        try:
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

            # 5. AI 분석 요청 (URL 포함으로 캐싱 활용)
            ai_result = await analyze_news_with_ai(title, content, related_symbols, url)

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

        except Exception as e:
            print(f"❌ 뉴스 처리 오류: {str(e)}")
            continue

    print(f"\n[{datetime.now()}] 네이버 API 뉴스 크롤링 완료")
    print(f"📈 통계: 신규 {new_count}개, 중복 {duplicate_count}개\n")


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
    scheduler = BackgroundScheduler()
    # 5분마다 뉴스 크롤링
    scheduler.add_job(crawl_news_sync, 'interval', minutes=5)
    scheduler.start()
    print("📰 News Crawler Scheduler started (every 5 minutes)")

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)
