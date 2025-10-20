"""
Redis 캐싱 모듈
- 장 마감 시간 기준 동적 TTL 계산
- 레포트 캐싱 및 조회
"""
import os
import json
import redis
from datetime import datetime, time, timedelta
from typing import Optional, Dict, Any

# Redis 클라이언트 (지연 초기화)
redis_client = None

def get_redis_client():
    """Redis 클라이언트 지연 초기화"""
    global redis_client
    if redis_client is None:
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            redis_client = redis.from_url(redis_url, decode_responses=True)
            # 연결 테스트
            redis_client.ping()
            print(f"✅ Redis 연결 성공: {redis_url}")
        except Exception as e:
            print(f"⚠️ Redis 연결 실패: {str(e)}")
            print("   → 캐싱 기능 비활성화 (레포트는 정상 작동)")
            redis_client = None
    return redis_client

# 한국 주식 시장 시간 (KST 기준)
MARKET_OPEN_TIME = time(9, 0)    # 09:00
MARKET_CLOSE_TIME = time(15, 30) # 15:30

def calculate_ttl(generation_time: datetime = None) -> int:
    """
    장 마감 시간 기준 캐시 TTL 계산

    Args:
        generation_time: 레포트 생성 시간 (기본값: 현재 시간)

    Returns:
        int: TTL (초 단위)

    Logic:
        - 장 마감(15:30) 후 생성 → 다음날 09:00까지 유효
        - 장중 생성 → 당일 15:30까지 유효
        - 최소 TTL: 30분 (1800초)
    """
    if generation_time is None:
        generation_time = datetime.now()

    current_time = generation_time.time()

    # 장 마감 후 (15:30 ~ 23:59)
    if current_time >= MARKET_CLOSE_TIME:
        # 다음날 09:00까지
        tomorrow = generation_time.date() + timedelta(days=1)
        target_time = datetime.combine(tomorrow, MARKET_OPEN_TIME)
        ttl = int((target_time - generation_time).total_seconds())

    # 장중 (09:00 ~ 15:29) 또는 장 시작 전 (00:00 ~ 08:59)
    else:
        if current_time < MARKET_OPEN_TIME:
            # 장 시작 전: 당일 15:30까지
            target_time = datetime.combine(generation_time.date(), MARKET_CLOSE_TIME)
        else:
            # 장중: 당일 15:30까지
            target_time = datetime.combine(generation_time.date(), MARKET_CLOSE_TIME)

        ttl = int((target_time - generation_time).total_seconds())

    # 최소 TTL: 30분 (1800초)
    return max(ttl, 1800)


def get_cache_key(symbol: str, report_date: str) -> str:
    """
    캐시 키 생성

    Args:
        symbol: 종목 코드 (예: '005930')
        report_date: 레포트 날짜 (YYYY-MM-DD)

    Returns:
        str: Redis 캐시 키 (예: 'report:005930:2025-10-19')
    """
    return f"report:{symbol}:{report_date}"


def get_cached_report(symbol: str, report_date: str) -> Optional[Dict[str, Any]]:
    """
    캐시된 레포트 조회

    Args:
        symbol: 종목 코드
        report_date: 레포트 날짜 (YYYY-MM-DD)

    Returns:
        Optional[Dict]: 캐시된 레포트 데이터 또는 None
    """
    try:
        client = get_redis_client()
        if client is None:
            return None

        cache_key = get_cache_key(symbol, report_date)
        cached_data = client.get(cache_key)

        if cached_data:
            print(f"✅ 캐시 HIT: {cache_key}")
            return json.loads(cached_data)
        else:
            print(f"❌ 캐시 MISS: {cache_key}")
            return None

    except Exception as e:
        print(f"⚠️ Redis 조회 오류: {str(e)}")
        return None


def set_cached_report(symbol: str, report_date: str, report_data: Dict[str, Any]) -> bool:
    """
    레포트 캐싱

    Args:
        symbol: 종목 코드
        report_date: 레포트 날짜 (YYYY-MM-DD)
        report_data: 레포트 데이터

    Returns:
        bool: 캐싱 성공 여부
    """
    try:
        client = get_redis_client()
        if client is None:
            return False

        cache_key = get_cache_key(symbol, report_date)
        ttl = calculate_ttl()

        # JSON 직렬화 (datetime은 ISO format 문자열로 변환)
        serialized_data = json.dumps(report_data, ensure_ascii=False, default=str)

        # Redis에 저장
        client.setex(cache_key, ttl, serialized_data)

        print(f"✅ 캐시 저장 성공: {cache_key} (TTL: {ttl // 60}분)")
        return True

    except Exception as e:
        print(f"⚠️ Redis 저장 오류: {str(e)}")
        return False


def delete_cached_report(symbol: str, report_date: str) -> bool:
    """
    캐시된 레포트 삭제

    Args:
        symbol: 종목 코드
        report_date: 레포트 날짜 (YYYY-MM-DD)

    Returns:
        bool: 삭제 성공 여부
    """
    try:
        client = get_redis_client()
        if client is None:
            return False

        cache_key = get_cache_key(symbol, report_date)
        result = client.delete(cache_key)

        if result > 0:
            print(f"✅ 캐시 삭제 성공: {cache_key}")
            return True
        else:
            print(f"⚠️ 캐시 없음: {cache_key}")
            return False

    except Exception as e:
        print(f"⚠️ Redis 삭제 오류: {str(e)}")
        return False
