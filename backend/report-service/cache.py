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

# 캐시 통계 (메모리 기반)
cache_stats = {
    "hits": 0,
    "misses": 0,
    "errors": 0
}

def get_cache_stats() -> Dict[str, Any]:
    """
    캐시 통계 조회

    Returns:
        Dict: HIT/MISS 비율, 총 요청 수 등
    """
    total = cache_stats["hits"] + cache_stats["misses"]
    hit_rate = (cache_stats["hits"] / total * 100) if total > 0 else 0

    return {
        "hits": cache_stats["hits"],
        "misses": cache_stats["misses"],
        "errors": cache_stats["errors"],
        "total_requests": total,
        "hit_rate_percent": round(hit_rate, 2)
    }

def get_next_market_open(current_time: datetime) -> datetime:
    """
    다음 장 시작 시간 계산 (주말/공휴일 고려)

    Args:
        current_time: 현재 시간

    Returns:
        datetime: 다음 장 시작 시간

    Logic:
        - 평일 15:30 이후 → 다음 평일 09:00
        - 토요일/일요일 → 월요일 09:00
        - 공휴일은 수동 처리 (향후 확장)
    """
    next_open = current_time

    # 시간만 09:00으로 설정하고 다음 날로 이동
    next_open = next_open.replace(hour=9, minute=0, second=0, microsecond=0)

    # 현재 시간이 장 마감 전이면 오늘, 이후면 내일부터 시작
    if current_time.time() >= MARKET_CLOSE_TIME or current_time.time() < MARKET_OPEN_TIME:
        next_open += timedelta(days=1)

    # 주말 처리: 토요일(5) → 월요일(0), 일요일(6) → 월요일(0)
    while next_open.weekday() >= 5:  # 5=토요일, 6=일요일
        next_open += timedelta(days=1)

    return next_open

def calculate_ttl(generation_time: datetime = None) -> int:
    """
    장 마감 시간 기준 캐시 TTL 계산 (주말/공휴일 고려)

    Args:
        generation_time: 레포트 생성 시간 (기본값: 현재 시간)

    Returns:
        int: TTL (초 단위)

    Logic:
        - 장 마감(15:30) 후 생성 → 다음 거래일 09:00까지 유효
        - 장중 생성 → 당일 15:30까지 유효
        - 주말/공휴일 고려하여 다음 거래일까지 연장
        - 최소 TTL: 30분 (1800초)
    """
    if generation_time is None:
        generation_time = datetime.now()

    current_time = generation_time.time()

    # 장 마감 후 (15:30 ~ 23:59) 또는 장 시작 전 (00:00 ~ 08:59)
    if current_time >= MARKET_CLOSE_TIME or current_time < MARKET_OPEN_TIME:
        # 다음 거래일 09:00까지 (주말 자동 건너뜀)
        next_open = get_next_market_open(generation_time)
        ttl = int((next_open - generation_time).total_seconds())

    # 장중 (09:00 ~ 15:29)
    else:
        # 당일 15:30까지
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
            cache_stats["hits"] += 1
            print(f"✅ 캐시 HIT: {cache_key}")
            return json.loads(cached_data)
        else:
            cache_stats["misses"] += 1
            print(f"❌ 캐시 MISS: {cache_key}")
            return None

    except Exception as e:
        cache_stats["errors"] += 1
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
        cache_stats["errors"] += 1
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
        cache_stats["errors"] += 1
        print(f"⚠️ Redis 삭제 오류: {str(e)}")
        return False
