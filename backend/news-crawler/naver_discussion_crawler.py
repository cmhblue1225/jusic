"""
🔥 Phase 2.2: 네이버 증권 토론방 크롤링
투자자 심리 및 커뮤니티 의견 수집
"""
import os
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import re

load_dotenv()


class NaverDiscussionCrawler:
    """네이버 증권 토론방 크롤러"""

    def __init__(self):
        self.base_url = "https://finance.naver.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://finance.naver.com/"
        }

    async def crawl_discussions(
        self,
        symbol: str,
        days: int = 7,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        특정 종목의 토론방 게시글 크롤링

        Args:
            symbol: 종목 코드 (예: '005930')
            days: 수집 기간 (일)
            limit: 최대 게시글 수

        Returns:
            List[Dict]: 토론방 게시글 목록
        """
        discussions = []
        cutoff_date = datetime.now() - timedelta(days=days)

        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                # 페이지별로 크롤링 (한 페이지당 20개 게시글)
                page = 1
                max_pages = (limit // 20) + 1

                while len(discussions) < limit and page <= max_pages:
                    url = f"{self.base_url}/item/board.naver?code={symbol}&page={page}"

                    async with session.get(url, timeout=10) as response:
                        if response.status != 200:
                            print(f"⚠️ HTTP {response.status}: {url}")
                            break

                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # 게시글 테이블 찾기
                        table = soup.find('table', class_='type2')
                        if not table:
                            print(f"⚠️ 토론방 테이블을 찾을 수 없습니다 (page {page})")
                            break

                        rows = table.find('tbody').find_all('tr')

                        for row in rows:
                            try:
                                # 공지사항 제외
                                if 'notice' in row.get('class', []):
                                    continue

                                # 제목 및 링크
                                title_elem = row.find('td', class_='title')
                                if not title_elem:
                                    continue

                                link_elem = title_elem.find('a')
                                if not link_elem:
                                    continue

                                title = link_elem.get_text(strip=True)
                                link = self.base_url + link_elem.get('href', '')

                                # 작성자
                                writer_elem = row.find('td', class_='p11')
                                writer = writer_elem.get_text(strip=True) if writer_elem else "Unknown"

                                # 조회수
                                view_elem = row.find('td', class_='p10')
                                view_count = 0
                                if view_elem:
                                    view_text = view_elem.get_text(strip=True)
                                    view_count = int(view_text) if view_text.isdigit() else 0

                                # 좋아요/공감수
                                like_elem = row.find('td', class_='p9')
                                like_count = 0
                                if like_elem:
                                    like_text = like_elem.get_text(strip=True)
                                    like_count = int(like_text) if like_text.isdigit() else 0

                                # 날짜
                                date_elem = row.find('td', class_='p11', attrs={'align': 'center'})
                                if not date_elem:
                                    date_elem = row.find_all('td', class_='p11')[-1] if row.find_all('td', class_='p11') else None

                                date_str = date_elem.get_text(strip=True) if date_elem else ""
                                published_at = self._parse_date(date_str)

                                # 기간 필터링
                                if published_at and published_at < cutoff_date:
                                    print(f"  ℹ️ 기간 초과 게시글 발견 (page {page}), 크롤링 중단")
                                    break

                                discussion = {
                                    "title": title,
                                    "link": link,
                                    "writer": writer,
                                    "view_count": view_count,
                                    "like_count": like_count,
                                    "published_at": published_at.isoformat() if published_at else None,
                                    "source": "naver_discussion",
                                    "symbol": symbol
                                }

                                discussions.append(discussion)

                                if len(discussions) >= limit:
                                    break

                            except Exception as e:
                                print(f"  ⚠️ 게시글 파싱 오류: {str(e)}")
                                continue

                        # 기간 초과 시 중단
                        if len(discussions) > 0 and discussions[-1].get("published_at"):
                            last_date = datetime.fromisoformat(discussions[-1]["published_at"])
                            if last_date < cutoff_date:
                                break

                    page += 1
                    await asyncio.sleep(0.5)  # Rate limiting

            print(f"✅ 네이버 토론방 크롤링 완료: {len(discussions)}개")
            return discussions[:limit]

        except Exception as e:
            print(f"❌ 토론방 크롤링 실패: {str(e)}")
            return []

    async def get_discussion_content(
        self,
        discussion_url: str
    ) -> Optional[str]:
        """
        게시글 본문 내용 가져오기

        Args:
            discussion_url: 게시글 URL

        Returns:
            str: 게시글 본문 (없으면 None)
        """
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(discussion_url, timeout=10) as response:
                    if response.status != 200:
                        return None

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # 본문 찾기
                    content_elem = soup.find('div', class_='board_txt')
                    if not content_elem:
                        content_elem = soup.find('div', class_='view_info')

                    if content_elem:
                        # HTML 태그 제거 및 정리
                        content = content_elem.get_text(separator='\n', strip=True)
                        content = re.sub(r'\n{3,}', '\n\n', content)  # 과도한 줄바꿈 제거
                        return content

                    return None

        except Exception as e:
            print(f"  ⚠️ 본문 가져오기 실패: {str(e)}")
            return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        날짜 문자열 파싱

        Args:
            date_str: 날짜 문자열 (예: '2025.01.18', '01.18', '15:30')

        Returns:
            datetime: 파싱된 날짜
        """
        try:
            now = datetime.now()

            # 오늘 날짜 (시간만 표시: '15:30')
            if ':' in date_str and '.' not in date_str:
                time_parts = date_str.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                return now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # 월.일 형식 ('01.18')
            elif date_str.count('.') == 1:
                month, day = map(int, date_str.split('.'))
                # 올해로 가정
                year = now.year
                # 만약 미래 날짜면 작년으로 조정
                dt = datetime(year, month, day)
                if dt > now:
                    dt = datetime(year - 1, month, day)
                return dt

            # 년.월.일 형식 ('2025.01.18')
            elif date_str.count('.') == 2:
                year, month, day = map(int, date_str.split('.'))
                return datetime(year, month, day)

            else:
                print(f"  ⚠️ 알 수 없는 날짜 형식: {date_str}")
                return None

        except Exception as e:
            print(f"  ⚠️ 날짜 파싱 오류 ({date_str}): {str(e)}")
            return None

    async def analyze_sentiment_from_discussions(
        self,
        discussions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        토론방 게시글로부터 투자 심리 분석

        Args:
            discussions: 토론방 게시글 목록

        Returns:
            Dict: 심리 분석 결과
                - sentiment_score: 감성 점수 (-1 ~ 1)
                - bullish_count: 긍정 게시글 수
                - bearish_count: 부정 게시글 수
                - neutral_count: 중립 게시글 수
                - total_count: 전체 게시글 수
                - avg_view_count: 평균 조회수
                - avg_like_count: 평균 공감수
                - hot_topics: 주요 키워드
        """
        if not discussions:
            return {
                "sentiment_score": 0,
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0,
                "total_count": 0,
                "avg_view_count": 0,
                "avg_like_count": 0,
                "hot_topics": []
            }

        # 긍정/부정 키워드
        bullish_keywords = [
            "급등", "상승", "매수", "불타", "추가매수", "오른다", "올라", "강세",
            "호재", "기대", "좋다", "최고", "대박", "쌍따봉", "갑니다", "가즈아"
        ]
        bearish_keywords = [
            "급락", "하락", "매도", "손절", "떨어", "내려", "약세", "악재",
            "망했", "물렸", "최악", "폭락", "빠진다", "조심", "위험"
        ]

        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        total_views = 0
        total_likes = 0

        for discussion in discussions:
            title = discussion.get("title", "").lower()

            # 제목에서 감성 판단
            is_bullish = any(keyword in title for keyword in bullish_keywords)
            is_bearish = any(keyword in title for keyword in bearish_keywords)

            if is_bullish and not is_bearish:
                bullish_count += 1
            elif is_bearish and not is_bullish:
                bearish_count += 1
            else:
                neutral_count += 1

            total_views += discussion.get("view_count", 0)
            total_likes += discussion.get("like_count", 0)

        total_count = len(discussions)
        avg_view_count = total_views / total_count if total_count > 0 else 0
        avg_like_count = total_likes / total_count if total_count > 0 else 0

        # 감성 점수 계산 (-1 ~ 1)
        if total_count > 0:
            sentiment_score = (bullish_count - bearish_count) / total_count
        else:
            sentiment_score = 0

        # 주요 키워드 추출 (간단한 빈도 분석)
        all_titles = " ".join([d.get("title", "") for d in discussions])
        hot_topics = self._extract_hot_topics(all_titles)

        return {
            "sentiment_score": round(sentiment_score, 3),
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "neutral_count": neutral_count,
            "total_count": total_count,
            "avg_view_count": round(avg_view_count, 1),
            "avg_like_count": round(avg_like_count, 1),
            "hot_topics": hot_topics[:10],  # 상위 10개
            "community_sentiment": "bullish" if sentiment_score > 0.2 else "bearish" if sentiment_score < -0.2 else "neutral"
        }

    def _extract_hot_topics(self, text: str) -> List[str]:
        """주요 키워드 추출 (간단한 빈도 분석)"""
        # 불용어 제거
        stopwords = [
            "는", "은", "이", "가", "을", "를", "의", "에", "와", "과", "도",
            "으로", "에서", "한", "하다", "있다", "되다", "없다", "아니다",
            "그", "저", "이", "그거", "저거", "뭐", "좀", "더", "잘", "안"
        ]

        # 단어 분리 (간단한 공백 기반)
        words = re.findall(r'\b\w{2,}\b', text)
        word_freq = {}

        for word in words:
            if word not in stopwords and len(word) >= 2:
                word_freq[word] = word_freq.get(word, 0) + 1

        # 빈도순 정렬
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words if freq >= 2]  # 최소 2회 이상 등장


async def main():
    """테스트 함수"""
    crawler = NaverDiscussionCrawler()

    # 삼성전자 토론방 크롤링
    symbol = "005930"
    print(f"🔍 네이버 토론방 크롤링 시작: {symbol}")

    discussions = await crawler.crawl_discussions(symbol, days=7, limit=30)
    print(f"\n✅ 크롤링 완료: {len(discussions)}개 게시글")

    if discussions:
        print("\n📊 최근 게시글 5개:")
        for i, disc in enumerate(discussions[:5], 1):
            print(f"{i}. {disc['title']}")
            print(f"   작성자: {disc['writer']} | 조회: {disc['view_count']} | 공감: {disc['like_count']}")
            print(f"   날짜: {disc['published_at']}")
            print()

        # 투자 심리 분석
        sentiment = await crawler.analyze_sentiment_from_discussions(discussions)
        print("\n💭 커뮤니티 투자 심리:")
        print(f"  - 감성 점수: {sentiment['sentiment_score']:.3f}")
        print(f"  - 긍정 게시글: {sentiment['bullish_count']}개")
        print(f"  - 부정 게시글: {sentiment['bearish_count']}개")
        print(f"  - 중립 게시글: {sentiment['neutral_count']}개")
        print(f"  - 평균 조회수: {sentiment['avg_view_count']:.1f}")
        print(f"  - 평균 공감수: {sentiment['avg_like_count']:.1f}")
        print(f"  - 커뮤니티 심리: {sentiment['community_sentiment'].upper()}")
        print(f"  - 주요 키워드: {', '.join(sentiment['hot_topics'][:10])}")


if __name__ == "__main__":
    asyncio.run(main())
