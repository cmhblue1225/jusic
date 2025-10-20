"""
🔥 Phase 2.1: Google News RSS 크롤러
- Google News RSS Feed를 통해 종목 관련 뉴스 수집
- 네이버 API 보완용 추가 뉴스 소스
"""
import feedparser
import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any
from urllib.parse import quote_plus


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
        """
        특정 종목명으로 Google News 검색

        Args:
            stock_name: 종목명 (예: "삼성전자")
            max_results: 최대 결과 수

        Returns:
            List[Dict]: 뉴스 리스트
                - title: 제목
                - url: URL
                - published_at: 발행 시간 (ISO 8601)
                - source: 출처 (예: "Google News")
                - content: 요약 (RSS description)
        """
        try:
            # Google News RSS 검색 쿼리
            # 예: https://news.google.com/rss/search?q=삼성전자+주식&hl=ko&gl=KR&ceid=KR:ko
            query = f"{stock_name} 주식"
            encoded_query = quote_plus(query)

            rss_url = (
                f"{self.base_url}?q={encoded_query}"
                f"&hl=ko"  # 한국어
                f"&gl=KR"  # 대한민국
                f"&ceid=KR:ko"  # 한국 뉴스
            )

            print(f"📰 [Google News RSS] 검색: {stock_name} (URL: {rss_url[:80]}...)")

            # HTTP 요청 (비동기)
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(rss_url, headers=self.headers)
                response.raise_for_status()

            # RSS 파싱
            feed = feedparser.parse(response.text)

            if not feed.entries:
                print(f"⚠️ [Google News RSS] 검색 결과 없음: {stock_name}")
                return []

            # 결과 변환
            news_list = []
            for entry in feed.entries[:max_results]:
                try:
                    # 발행 시간 파싱 (feedparser는 struct_time 반환)
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                        published_iso = published_dt.isoformat()
                    else:
                        published_iso = datetime.now(timezone.utc).isoformat()

                    # 콘텐츠 추출 (description 또는 summary)
                    content = ""
                    if hasattr(entry, 'summary'):
                        content = entry.summary
                    elif hasattr(entry, 'description'):
                        content = entry.description

                    # HTML 태그 제거 (간단한 처리)
                    if content:
                        import re
                        content = re.sub(r'<[^>]+>', '', content)
                        content = content.strip()

                    news_item = {
                        "title": entry.title,
                        "url": entry.link,
                        "published_at": published_iso,
                        "source": "Google News",
                        "content": content[:500] if content else ""  # 500자로 제한
                    }

                    news_list.append(news_item)

                except Exception as e:
                    print(f"⚠️ [Google News RSS] 항목 파싱 오류: {str(e)}")
                    continue

            print(f"✅ [Google News RSS] {stock_name}: {len(news_list)}개 수집")
            return news_list

        except httpx.HTTPError as e:
            print(f"❌ [Google News RSS] HTTP 오류: {str(e)}")
            return []
        except Exception as e:
            print(f"❌ [Google News RSS] 오류: {str(e)}")
            return []

    async def search_multiple_stocks(
        self,
        stock_names: List[str],
        results_per_stock: int = 5
    ) -> List[Dict[str, Any]]:
        """
        여러 종목에 대해 뉴스 검색 (중복 제거)

        Args:
            stock_names: 종목명 리스트
            results_per_stock: 종목당 결과 수

        Returns:
            List[Dict]: 중복 제거된 뉴스 리스트
        """
        all_news = []
        seen_urls = set()

        for stock_name in stock_names:
            news_list = await self.search_stock_news(stock_name, results_per_stock)

            # 중복 제거 (URL 기준)
            for news in news_list:
                if news["url"] not in seen_urls:
                    seen_urls.add(news["url"])
                    all_news.append(news)

        print(f"📊 [Google News RSS] 총 {len(all_news)}개 뉴스 수집 (중복 제거 후)")
        return all_news


# 테스트 코드
if __name__ == "__main__":
    import asyncio

    async def test():
        crawler = GoogleNewsRSS()

        # 단일 종목 테스트
        print("\n=== 단일 종목 테스트 ===")
        news = await crawler.search_stock_news("삼성전자", max_results=5)
        for i, item in enumerate(news, 1):
            print(f"\n{i}. {item['title']}")
            print(f"   URL: {item['url'][:80]}...")
            print(f"   발행: {item['published_at']}")
            print(f"   내용: {item['content'][:100]}...")

        # 다중 종목 테스트
        print("\n\n=== 다중 종목 테스트 ===")
        stocks = ["삼성전자", "SK하이닉스", "NAVER"]
        all_news = await crawler.search_multiple_stocks(stocks, results_per_stock=3)
        print(f"\n총 {len(all_news)}개 뉴스 수집")

    asyncio.run(test())
