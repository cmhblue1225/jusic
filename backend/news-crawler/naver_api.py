"""
네이버 뉴스 검색 API 클라이언트
"""
import os
import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class NaverNewsAPI:
    """네이버 뉴스 검색 API 클래스"""

    def __init__(self):
        self.client_id = os.getenv("NAVER_CLIENT_ID")
        self.client_secret = os.getenv("NAVER_CLIENT_SECRET")
        self.base_url = "https://openapi.naver.com/v1/search/news.json"

        if not self.client_id or not self.client_secret:
            raise ValueError("네이버 API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")

    async def search_news(
        self,
        query: str,
        display: int = 10,
        start: int = 1,
        sort: str = "date"
    ) -> Optional[List[Dict]]:
        """
        네이버 뉴스 검색

        Args:
            query: 검색어
            display: 검색 결과 출력 건수 (최대 100)
            start: 검색 시작 위치 (최대 1000)
            sort: 정렬 옵션 (date: 날짜순, sim: 정확도순)

        Returns:
            뉴스 아이템 리스트
        """
        try:
            headers = {
                "X-Naver-Client-Id": self.client_id,
                "X-Naver-Client-Secret": self.client_secret,
            }

            params = {
                "query": query,
                "display": display,
                "start": start,
                "sort": sort,
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.base_url,
                    headers=headers,
                    params=params
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("items", [])
                else:
                    print(f"⚠️ 네이버 API 오류: {response.status_code}")
                    print(f"   응답: {response.text}")
                    return None

        except Exception as e:
            print(f"❌ 네이버 API 호출 오류: {str(e)}")
            return None

    def clean_html_tags(self, text: str) -> str:
        """
        HTML 태그 제거

        Args:
            text: HTML 태그가 포함된 텍스트

        Returns:
            태그가 제거된 텍스트
        """
        import re
        # <b>, </b> 등 태그 제거
        clean_text = re.sub(r'<[^>]+>', '', text)
        # HTML 엔티티 변환
        clean_text = clean_text.replace('&quot;', '"')
        clean_text = clean_text.replace('&amp;', '&')
        clean_text = clean_text.replace('&lt;', '<')
        clean_text = clean_text.replace('&gt;', '>')
        return clean_text

    def parse_news_item(self, item: Dict) -> Dict:
        """
        네이버 API 응답 파싱

        Args:
            item: 네이버 API 뉴스 아이템

        Returns:
            파싱된 뉴스 데이터
        """
        # HTML 태그 제거
        title = self.clean_html_tags(item.get("title", ""))
        description = self.clean_html_tags(item.get("description", ""))

        # 날짜 파싱 (YYYYMMDD 형식)
        pub_date_str = item.get("pubDate", "")
        try:
            # "Tue, 14 Jan 2025 10:30:00 +0900" 형식 파싱
            pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
        except:
            pub_date = datetime.now()

        return {
            "title": title,
            "content": description,
            "url": item.get("originallink") or item.get("link"),
            "published_at": pub_date.isoformat(),
            "source": "Naver 뉴스 검색",
        }

    async def search_stock_news(
        self,
        stock_name: str,
        max_results: int = 5
    ) -> List[Dict]:
        """
        특정 종목 관련 뉴스 검색

        Args:
            stock_name: 종목명 (예: "삼성전자", "SK하이닉스")
            max_results: 최대 결과 수

        Returns:
            파싱된 뉴스 리스트
        """
        # 검색어 최적화
        query = f"{stock_name} 주가 OR {stock_name} 실적"

        items = await self.search_news(query=query, display=max_results, sort="date")

        if not items:
            return []

        # 파싱
        parsed_news = []
        for item in items:
            parsed = self.parse_news_item(item)
            parsed_news.append(parsed)

        return parsed_news

    async def search_multiple_stocks(
        self,
        stock_names: List[str],
        results_per_stock: int = 5
    ) -> List[Dict]:
        """
        여러 종목 뉴스 동시 검색

        Args:
            stock_names: 종목명 리스트
            results_per_stock: 종목당 결과 수

        Returns:
            모든 뉴스 리스트 (중복 제거됨)
        """
        all_news = []
        seen_urls = set()

        for stock_name in stock_names:
            print(f"🔍 {stock_name} 뉴스 검색 중...")

            news_items = await self.search_stock_news(stock_name, results_per_stock)

            # 중복 제거
            for news in news_items:
                url = news["url"]
                if url not in seen_urls:
                    seen_urls.add(url)
                    all_news.append(news)

        print(f"✅ 총 {len(all_news)}개 뉴스 수집 (중복 제거 후)")
        return all_news


# 테스트용
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()

    async def test():
        api = NaverNewsAPI()

        # 단일 종목 검색 테스트
        print("\n=== 삼성전자 뉴스 검색 ===")
        news = await api.search_stock_news("삼성전자", max_results=3)

        for item in news:
            print(f"\n제목: {item['title']}")
            print(f"내용: {item['content'][:100]}...")
            print(f"URL: {item['url']}")
            print(f"발행일: {item['published_at']}")

        # 다중 종목 검색 테스트
        print("\n\n=== 다중 종목 뉴스 검색 ===")
        stocks = ["삼성전자", "SK하이닉스", "NAVER"]
        all_news = await api.search_multiple_stocks(stocks, results_per_stock=2)

        print(f"\n총 {len(all_news)}개 뉴스")

    asyncio.run(test())
