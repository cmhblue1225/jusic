"""
Redis 캐싱 모듈
뉴스 분석 결과를 캐싱하여 중복 분석 방지
"""
import os
import json
import hashlib
import redis
from typing import Optional


class NewsCache:
    """뉴스 분석 결과 캐시"""

    def __init__(self):
        """Redis 클라이언트 초기화"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            # 연결 테스트
            self.client.ping()
            print(f"✅ Redis 연결 성공: {redis_url}")
        except Exception as e:
            print(f"⚠️ Redis 연결 실패: {str(e)}")
            print("   캐싱 기능이 비활성화됩니다.")
            self.client = None

    def get_cache_key(self, url: str) -> str:
        """
        URL 기반 캐시 키 생성

        Args:
            url: 뉴스 URL

        Returns:
            SHA256 해시 기반 캐시 키
        """
        # URL을 SHA256 해시로 변환하여 키 생성
        hash_object = hashlib.sha256(url.encode())
        return f"news:analysis:{hash_object.hexdigest()}"

    def get(self, url: str) -> Optional[dict]:
        """
        캐시에서 분석 결과 조회

        Args:
            url: 뉴스 URL

        Returns:
            분석 결과 dict 또는 None
        """
        if not self.client:
            return None

        try:
            cache_key = self.get_cache_key(url)
            cached_data = self.client.get(cache_key)

            if cached_data:
                print(f"✅ 캐시 HIT: {url[:50]}...")
                return json.loads(cached_data)
            else:
                print(f"❌ 캐시 MISS: {url[:50]}...")
                return None

        except Exception as e:
            print(f"⚠️ 캐시 조회 오류: {str(e)}")
            return None

    def set(self, url: str, analysis_result: dict, ttl: int = 86400):
        """
        분석 결과를 캐시에 저장

        Args:
            url: 뉴스 URL
            analysis_result: AI 분석 결과
            ttl: Time To Live (초), 기본 24시간
        """
        if not self.client:
            return

        try:
            cache_key = self.get_cache_key(url)
            self.client.setex(
                cache_key,
                ttl,
                json.dumps(analysis_result, ensure_ascii=False)
            )
            print(f"✅ 캐시 저장: {url[:50]}... (TTL: {ttl}s)")

        except Exception as e:
            print(f"⚠️ 캐시 저장 오류: {str(e)}")

    def delete(self, url: str):
        """
        캐시 삭제

        Args:
            url: 뉴스 URL
        """
        if not self.client:
            return

        try:
            cache_key = self.get_cache_key(url)
            self.client.delete(cache_key)
            print(f"✅ 캐시 삭제: {url[:50]}...")

        except Exception as e:
            print(f"⚠️ 캐시 삭제 오류: {str(e)}")

    def clear_all(self):
        """모든 뉴스 분석 캐시 삭제 (개발/테스트용)"""
        if not self.client:
            return

        try:
            keys = self.client.keys("news:analysis:*")
            if keys:
                self.client.delete(*keys)
                print(f"✅ 전체 캐시 삭제: {len(keys)}개")
            else:
                print("ℹ️ 삭제할 캐시 없음")

        except Exception as e:
            print(f"⚠️ 캐시 전체 삭제 오류: {str(e)}")


# 싱글톤 인스턴스
news_cache = NewsCache()


if __name__ == "__main__":
    # 테스트
    cache = NewsCache()

    test_url = "https://example.com/news/test-article-1"
    test_result = {
        "summary": "테스트 요약",
        "sentiment_score": 0.5,
        "impact_score": 0.8,
        "recommended_action": "buy"
    }

    # 캐시 저장
    cache.set(test_url, test_result, ttl=60)

    # 캐시 조회
    cached = cache.get(test_url)
    print(f"\n조회 결과: {cached}")

    # 캐시 삭제
    cache.delete(test_url)

    # 다시 조회 (None이어야 함)
    cached_again = cache.get(test_url)
    print(f"\n삭제 후 조회: {cached_again}")
