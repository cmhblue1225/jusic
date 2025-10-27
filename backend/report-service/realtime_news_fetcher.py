"""
실시간 뉴스 크롤링 및 AI 분석 모듈 (Report Service용)

하이브리드 뉴스 fetching 전략:
1. DB에서 최신 뉴스 조회
2. 최신 뉴스가 12시간 이상 오래되었으면 실시간 크롤링 트리거
3. AI 분석 후 DB에 저장
4. DB 뉴스 + 신규 뉴스 병합하여 반환
"""
import os
import httpx
import feedparser
import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple, Any
from urllib.parse import quote_plus
from supabase import create_client, Client

# 환경 변수
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8002")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# Supabase 클라이언트 (Lazy Initialization)
_supabase_client = None

def get_supabase_client() -> Client:
    """Supabase 클라이언트 Lazy 초기화"""
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_URL 및 SUPABASE_SERVICE_KEY 환경 변수가 설정되어 있지 않습니다.")
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _supabase_client


class NaverNewsAPI:
    """네이버 뉴스 검색 API 클라이언트"""

    def __init__(self):
        self.client_id = NAVER_CLIENT_ID
        self.client_secret = NAVER_CLIENT_SECRET
        self.base_url = "https://openapi.naver.com/v1/search/news.json"

        if not self.client_id or not self.client_secret:
            print("⚠️ 네이버 API 키가 설정되지 않았습니다.")

    def clean_html_tags(self, text: str) -> str:
        """HTML 태그 제거"""
        clean_text = re.sub(r'<[^>]+>', '', text)
        clean_text = clean_text.replace('&quot;', '"')
        clean_text = clean_text.replace('&amp;', '&')
        clean_text = clean_text.replace('&lt;', '<')
        clean_text = clean_text.replace('&gt;', '>')
        return clean_text

    async def search_stock_news(
        self,
        stock_name: str,
        max_results: int = 10
    ) -> List[Dict]:
        """특정 종목 관련 뉴스 검색"""
        if not self.client_id or not self.client_secret:
            return []

        try:
            headers = {
                "X-Naver-Client-Id": self.client_id,
                "X-Naver-Client-Secret": self.client_secret,
            }

            params = {
                "query": stock_name,
                "display": max_results,
                "start": 1,
                "sort": "date",
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.base_url,
                    headers=headers,
                    params=params
                )

                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])

                    # 파싱
                    parsed_news = []
                    for item in items:
                        title = self.clean_html_tags(item.get("title", ""))
                        description = self.clean_html_tags(item.get("description", ""))

                        # 날짜 파싱
                        pub_date_str = item.get("pubDate", "")
                        try:
                            pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
                        except:
                            pub_date = datetime.now(timezone.utc)

                        parsed_news.append({
                            "title": title,
                            "content": description,
                            "url": item.get("originallink") or item.get("link"),
                            "published_at": pub_date.isoformat(),
                            "source": "Naver 뉴스 검색",
                        })

                    return parsed_news
                else:
                    print(f"⚠️ 네이버 API 오류: {response.status_code}")
                    return []

        except Exception as e:
            print(f"❌ 네이버 API 호출 오류: {str(e)}")
            return []


class GoogleNewsRSS:
    """Google News RSS Feed 크롤러"""

    def __init__(self):
        self.base_url = "https://news.google.com/rss/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

    async def search_stock_news(
        self,
        stock_name: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """특정 종목명으로 Google News 검색"""
        try:
            query = f"{stock_name} 주식"
            encoded_query = quote_plus(query)

            rss_url = (
                f"{self.base_url}?q={encoded_query}"
                f"&hl=ko"
                f"&gl=KR"
                f"&ceid=KR:ko"
            )

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(rss_url, headers=self.headers)
                response.raise_for_status()

            feed = feedparser.parse(response.text)

            if not feed.entries:
                return []

            news_list = []
            for entry in feed.entries[:max_results]:
                try:
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                        published_iso = published_dt.isoformat()
                    else:
                        published_iso = datetime.now(timezone.utc).isoformat()

                    content = ""
                    if hasattr(entry, 'summary'):
                        content = entry.summary
                    elif hasattr(entry, 'description'):
                        content = entry.description

                    if content:
                        content = re.sub(r'<[^>]+>', '', content).strip()

                    news_list.append({
                        "title": entry.title,
                        "url": entry.link,
                        "published_at": published_iso,
                        "source": "Google News",
                        "content": content[:500] if content else ""
                    })

                except Exception as e:
                    print(f"⚠️ [Google News RSS] 항목 파싱 오류: {str(e)}")
                    continue

            return news_list

        except Exception as e:
            print(f"❌ [Google News RSS] 오류: {str(e)}")
            return []


async def check_news_freshness(
    symbol: str,
    threshold_hours: int = 12
) -> Tuple[bool, Optional[datetime]]:
    """
    뉴스 신선도 확인

    Args:
        symbol: 종목 코드 (예: "005930")
        threshold_hours: 신선도 임계값 (시간 단위)

    Returns:
        (is_fresh, latest_news_timestamp)
        - is_fresh: True if 최신 뉴스 < threshold_hours
        - latest_news_timestamp: 최신 뉴스 발행 시간
    """
    try:
        result = get_supabase_client().table("news") \
            .select("published_at") \
            .contains("related_symbols", [symbol]) \
            .order("published_at", desc=True) \
            .limit(1) \
            .execute()

        if not result.data:
            print(f"⚠️ 뉴스 신선도 체크: {symbol} - DB에 뉴스 없음 (실시간 크롤링 필요)")
            return False, None

        latest_news = result.data[0]
        published_at_str = latest_news["published_at"]
        published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))

        now = datetime.now(timezone.utc)
        age_hours = (now - published_at).total_seconds() / 3600

        is_fresh = age_hours < threshold_hours

        if is_fresh:
            print(f"✅ 뉴스 신선도 체크: {symbol} - 최신 뉴스 {age_hours:.1f}시간 전 (DB 사용)")
        else:
            print(f"⚠️ 뉴스 신선도 체크: {symbol} - 최신 뉴스 {age_hours:.1f}시간 전 (실시간 크롤링 트리거)")

        return is_fresh, published_at

    except Exception as e:
        print(f"❌ 뉴스 신선도 체크 오류: {str(e)}")
        return False, None


async def fetch_realtime_news(
    symbol: str,
    stock_name: str,
    max_results: int = 10
) -> List[Dict]:
    """
    실시간 뉴스 크롤링 (Naver + Google RSS)

    Args:
        symbol: 종목 코드
        stock_name: 종목명
        max_results: 최대 결과 수

    Returns:
        원시 뉴스 데이터 리스트 (AI 분석 전)
    """
    print(f"🔄 실시간 크롤링 시작: {stock_name} ({symbol})")

    all_news = []
    seen_urls = set()

    # 1. 네이버 뉴스 크롤링
    try:
        naver_api = NaverNewsAPI()
        naver_news = await naver_api.search_stock_news(stock_name, max_results=max_results)

        for news in naver_news:
            url = news["url"]
            if url not in seen_urls:
                seen_urls.add(url)
                all_news.append(news)

        print(f"✅ 네이버 뉴스: {len(naver_news)}개 수집")
    except Exception as e:
        print(f"⚠️ 네이버 뉴스 크롤링 실패: {str(e)}")

    # 2. Google News RSS 크롤링
    try:
        google_rss = GoogleNewsRSS()
        google_news = await google_rss.search_stock_news(stock_name, max_results=max_results)

        for news in google_news:
            url = news["url"]
            if url not in seen_urls:
                seen_urls.add(url)
                all_news.append(news)

        print(f"✅ Google News: {len(google_news)}개 수집")
    except Exception as e:
        print(f"⚠️ Google News 크롤링 실패: {str(e)}")

    print(f"📊 실시간 크롤링 완료: 총 {len(all_news)}개 (중복 제거 후)")
    return all_news


async def analyze_and_save_news(
    news_items: List[Dict],
    symbol: str
) -> List[Dict]:
    """
    AI 분석 후 Supabase에 저장

    Args:
        news_items: 원시 뉴스 데이터
        symbol: 종목 코드

    Returns:
        분석된 뉴스 데이터 (DB 저장 완료)
    """
    if not news_items:
        return []

    print(f"🤖 AI 분석 시작: {len(news_items)}개 뉴스")

    analyzed_news = []

    for news in news_items:
        try:
            # AI 분석 요청
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{AI_SERVICE_URL}/analyze",
                    json={
                        "title": news["title"],
                        "content": news["content"],
                        "symbols": [symbol],
                        "url": news["url"]
                    }
                )

                if response.status_code == 200:
                    ai_result = response.json()

                    # DB 저장용 데이터 준비
                    news_data = {
                        "title": news["title"],
                        "url": news["url"],
                        "source": news["source"],
                        "published_at": news["published_at"],
                        "summary": ai_result.get("summary"),
                        "sentiment_score": ai_result.get("sentiment_score"),
                        "impact_score": ai_result.get("impact_score"),
                        "recommended_action": ai_result.get("recommended_action"),
                        "related_symbols": [symbol],
                    }

                    # Supabase에 저장
                    try:
                        get_supabase_client().table("news").insert(news_data).execute()
                        analyzed_news.append(news_data)
                        print(f"✅ AI 분석 + 저장 성공: {news['title'][:50]}...")
                    except Exception as e:
                        print(f"⚠️ DB 저장 실패 (분석은 성공): {str(e)}")
                        # 저장 실패해도 분석된 뉴스는 반환
                        analyzed_news.append(news_data)

                else:
                    print(f"⚠️ AI 분석 실패 (status {response.status_code}): {news['title'][:50]}...")

        except Exception as e:
            print(f"❌ 뉴스 분석 오류: {str(e)}")
            continue

    print(f"✅ AI 분석 완료: {len(analyzed_news)}개 성공")
    return analyzed_news


async def get_news_hybrid(
    symbol: str,
    stock_name: Optional[str] = None,
    threshold_hours: int = 12,
    max_fresh_news: int = 10
) -> List[Dict]:
    """
    하이브리드 뉴스 조회 (메인 함수)

    전략:
    1. DB에서 최신 뉴스 조회
    2. 신선도 확인 (< threshold_hours)
    3. 오래되었으면 실시간 크롤링 + AI 분석 + DB 저장
    4. DB 뉴스 + 신규 뉴스 병합 반환

    Args:
        symbol: 종목 코드
        stock_name: 종목명 (선택사항, 없으면 stock_master에서 조회)
        threshold_hours: 신선도 임계값 (기본 12시간)
        max_fresh_news: 실시간 크롤링 최대 개수

    Returns:
        뉴스 리스트 (DB + 신규 병합)
    """
    try:
        # 0. 종목명이 없으면 stock_master에서 조회
        if not stock_name:
            try:
                stock_result = get_supabase_client().table("stock_master") \
                    .select("name") \
                    .eq("symbol", symbol) \
                    .limit(1) \
                    .execute()

                if stock_result.data and len(stock_result.data) > 0:
                    stock_name = stock_result.data[0]["name"]
                    print(f"✅ 종목명 조회: {symbol} → {stock_name}")
                else:
                    stock_name = symbol  # 폴백: 종목 코드 사용
                    print(f"⚠️ 종목명 조회 실패, 종목 코드 사용: {symbol}")

            except Exception as e:
                stock_name = symbol  # 폴백: 종목 코드 사용
                print(f"⚠️ stock_master 조회 오류: {str(e)}, 종목 코드 사용")

        # 1. 신선도 확인
        is_fresh, latest_timestamp = await check_news_freshness(symbol, threshold_hours)

        # 2. 실시간 크롤링 필요 여부 판단
        fresh_news = []
        if not is_fresh:
            # 실시간 크롤링 트리거
            raw_news = await fetch_realtime_news(symbol, stock_name, max_fresh_news)

            if raw_news:
                # AI 분석 + DB 저장
                fresh_news = await analyze_and_save_news(raw_news, symbol)
            else:
                print("⚠️ 실시간 크롤링 결과 없음")

        # 3. DB에서 뉴스 조회 (최근 7일, 최대 50개)
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

        db_news_result = get_supabase_client().table("news") \
            .select("id, title, summary, sentiment_score, impact_score, published_at, url") \
            .contains("related_symbols", [symbol]) \
            .gte("published_at", seven_days_ago) \
            .order("impact_score", desc=True) \
            .order("published_at", desc=True) \
            .limit(50) \
            .execute()

        db_news = db_news_result.data or []

        # 4. 병합 (중복 제거 - URL 기준)
        seen_urls = set()
        combined_news = []

        # 신규 뉴스 우선 추가
        for news in fresh_news:
            url = news.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                combined_news.append(news)

        # DB 뉴스 추가 (중복 제거)
        for news in db_news:
            url = news.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                combined_news.append(news)

        print(f"📊 최종 반환: DB {len(db_news)}개 + 신규 {len(fresh_news)}개 = 총 {len(combined_news)}개")
        return combined_news

    except Exception as e:
        print(f"❌ 하이브리드 뉴스 조회 실패: {str(e)}")
        # 폴백: DB 전용 조회
        return await get_news_db_only(symbol)


async def get_news_db_only(symbol: str) -> List[Dict]:
    """
    DB 전용 뉴스 조회 (폴백용)

    Args:
        symbol: 종목 코드

    Returns:
        DB 뉴스 리스트
    """
    try:
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

        result = get_supabase_client().table("news") \
            .select("id, title, summary, sentiment_score, impact_score, published_at, url") \
            .contains("related_symbols", [symbol]) \
            .gte("published_at", seven_days_ago) \
            .order("impact_score", desc=True) \
            .order("published_at", desc=True) \
            .limit(50) \
            .execute()

        return result.data or []

    except Exception as e:
        print(f"❌ DB 전용 뉴스 조회 실패: {str(e)}")
        return []
