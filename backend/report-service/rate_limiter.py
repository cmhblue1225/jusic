"""
API Rate Limiter (Token Bucket 알고리즘)
- KIS API Rate Limit 관리 (초당 20건 제한)
- 토큰 버킷 기반 요청 제어
- 자동 대기 및 재시도
- 동시 요청 수 제한
"""
import asyncio
import time
from typing import Optional, Callable, Any
from datetime import datetime
from collections import deque


class TokenBucket:
    """
    Token Bucket 알고리즘 구현
    - 일정 속도로 토큰이 채워짐
    - 요청 시 토큰 소비
    - 토큰 부족 시 대기
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: 버킷 용량 (최대 토큰 수)
            refill_rate: 토큰 재충전 속도 (초당 토큰 수)
        """
        self.capacity = capacity          # 최대 토큰 수
        self.refill_rate = refill_rate    # 초당 토큰 재충전 속도
        self.tokens = capacity            # 현재 토큰 수
        self.last_refill = time.time()    # 마지막 재충전 시간
        self.lock = asyncio.Lock()        # 동시 접근 방지

    async def acquire(self, tokens: int = 1) -> float:
        """
        토큰 획득 (대기 시간 반환)

        Args:
            tokens: 필요한 토큰 수 (기본: 1)

        Returns:
            float: 대기 시간 (초)
        """
        async with self.lock:
            # 1. 토큰 재충전
            current_time = time.time()
            elapsed = current_time - self.last_refill
            refill_tokens = elapsed * self.refill_rate

            self.tokens = min(self.capacity, self.tokens + refill_tokens)
            self.last_refill = current_time

            # 2. 토큰 부족 시 대기 시간 계산
            if self.tokens < tokens:
                wait_time = (tokens - self.tokens) / self.refill_rate
                await asyncio.sleep(wait_time)

                # 대기 후 재충전
                self.tokens = min(self.capacity, self.tokens + wait_time * self.refill_rate)
                self.last_refill = time.time()

                # 토큰 소비
                self.tokens -= tokens
                return wait_time

            # 3. 토큰 충분 시 즉시 소비
            self.tokens -= tokens
            return 0.0

    def get_available_tokens(self) -> int:
        """현재 사용 가능한 토큰 수 반환"""
        current_time = time.time()
        elapsed = current_time - self.last_refill
        refill_tokens = elapsed * self.refill_rate
        return min(self.capacity, self.tokens + refill_tokens)


class RateLimiter:
    """
    API Rate Limiter
    - 여러 API 엔드포인트에 대한 Rate Limit 관리
    - 동시 요청 수 제한
    - 통계 수집
    """

    def __init__(self, requests_per_second: int = 20, max_concurrent: int = 5):
        """
        Args:
            requests_per_second: 초당 최대 요청 수 (기본: 20)
            max_concurrent: 최대 동시 요청 수 (기본: 5)
        """
        self.bucket = TokenBucket(
            capacity=requests_per_second,
            refill_rate=requests_per_second
        )
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # 통계
        self.total_requests = 0
        self.total_wait_time = 0.0
        self.request_history = deque(maxlen=100)  # 최근 100개 요청 기록

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Rate Limit 적용하여 함수 실행

        Args:
            func: 실행할 비동기 함수
            *args, **kwargs: 함수 인자

        Returns:
            함수 실행 결과
        """
        # 1. 동시 요청 수 제한
        async with self.semaphore:
            # 2. 토큰 획득 (대기 필요 시 자동 대기)
            wait_time = await self.bucket.acquire(tokens=1)

            # 3. 함수 실행
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                # 에러 발생 시에도 통계 기록
                self._record_request(wait_time, time.time() - start_time, success=False)
                raise e

            # 4. 통계 기록
            execution_time = time.time() - start_time
            self._record_request(wait_time, execution_time, success=True)

            return result

    def _record_request(self, wait_time: float, execution_time: float, success: bool):
        """요청 통계 기록"""
        self.total_requests += 1
        self.total_wait_time += wait_time

        record = {
            "timestamp": datetime.now().isoformat(),
            "wait_time": wait_time,
            "execution_time": execution_time,
            "success": success
        }
        self.request_history.append(record)

    def get_stats(self) -> dict:
        """통계 조회"""
        if not self.request_history:
            return {
                "total_requests": 0,
                "avg_wait_time": 0.0,
                "avg_execution_time": 0.0,
                "success_rate": 0.0,
                "available_tokens": self.bucket.get_available_tokens()
            }

        recent_requests = list(self.request_history)
        success_count = sum(1 for r in recent_requests if r["success"])

        return {
            "total_requests": self.total_requests,
            "avg_wait_time": round(self.total_wait_time / self.total_requests, 4),
            "avg_execution_time": round(
                sum(r["execution_time"] for r in recent_requests) / len(recent_requests), 4
            ),
            "success_rate": round(success_count / len(recent_requests) * 100, 2),
            "available_tokens": int(self.bucket.get_available_tokens()),
            "recent_requests": len(recent_requests)
        }

    def reset_stats(self):
        """통계 초기화"""
        self.total_requests = 0
        self.total_wait_time = 0.0
        self.request_history.clear()


# 전역 Rate Limiter 인스턴스
_kis_rate_limiter = None


def get_kis_rate_limiter() -> RateLimiter:
    """
    KIS API Rate Limiter 싱글톤 인스턴스 반환

    Returns:
        RateLimiter: KIS API용 Rate Limiter (초당 20건)
    """
    global _kis_rate_limiter
    if _kis_rate_limiter is None:
        _kis_rate_limiter = RateLimiter(
            requests_per_second=20,  # KIS API 제한: 초당 20건
            max_concurrent=5         # 동시 요청 5개
        )
    return _kis_rate_limiter


async def rate_limited_kis_request(func: Callable, *args, **kwargs) -> Any:
    """
    KIS API 요청에 Rate Limit 적용

    사용 예시:
    ```python
    result = await rate_limited_kis_request(
        get_daily_ohlcv,
        symbol="005930",
        days=60
    )
    ```

    Args:
        func: 실행할 비동기 함수
        *args, **kwargs: 함수 인자

    Returns:
        함수 실행 결과
    """
    limiter = get_kis_rate_limiter()
    return await limiter.execute(func, *args, **kwargs)


class AdaptiveRateLimiter(RateLimiter):
    """
    적응형 Rate Limiter
    - 에러 발생 시 자동으로 속도 감소
    - 성공률 높아지면 속도 증가
    """

    def __init__(self, initial_rps: int = 20, max_concurrent: int = 5):
        super().__init__(initial_rps, max_concurrent)
        self.initial_rps = initial_rps
        self.current_rps = initial_rps
        self.error_count = 0
        self.success_count = 0

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Rate Limit 적용 + 적응형 조정"""
        try:
            result = await super().execute(func, *args, **kwargs)
            self.success_count += 1

            # 연속 성공 시 속도 증가 (최대 초기 속도까지)
            if self.success_count >= 10 and self.current_rps < self.initial_rps:
                self.current_rps = min(self.initial_rps, self.current_rps + 1)
                self._update_bucket_rate(self.current_rps)
                print(f"✅ Rate Limit 증가: {self.current_rps} req/s")
                self.success_count = 0

            return result

        except Exception as e:
            self.error_count += 1
            self.success_count = 0

            # 연속 에러 시 속도 감소 (최소 1 req/s)
            if self.error_count >= 3 and self.current_rps > 1:
                self.current_rps = max(1, self.current_rps - 5)
                self._update_bucket_rate(self.current_rps)
                print(f"⚠️ Rate Limit 감소 (에러 발생): {self.current_rps} req/s")
                self.error_count = 0

            raise e

    def _update_bucket_rate(self, new_rps: int):
        """토큰 버킷의 재충전 속도 업데이트"""
        self.bucket.refill_rate = new_rps
        self.bucket.capacity = new_rps


# 테스트용 메인 함수
async def test_rate_limiter():
    """Rate Limiter 테스트"""
    print("🧪 Rate Limiter 테스트 시작\n")

    limiter = RateLimiter(requests_per_second=5, max_concurrent=2)

    async def mock_api_call(request_id: int):
        """모의 API 호출 (0.1초 소요)"""
        await asyncio.sleep(0.1)
        print(f"✅ 요청 {request_id} 완료")
        return f"Response {request_id}"

    # 10개 요청 동시 실행
    tasks = [limiter.execute(mock_api_call, i) for i in range(10)]
    start_time = time.time()

    results = await asyncio.gather(*tasks)

    elapsed = time.time() - start_time

    print(f"\n📊 테스트 결과:")
    print(f"   - 총 소요 시간: {elapsed:.2f}초")
    print(f"   - 요청 수: {len(results)}개")
    print(f"   - 실제 RPS: {len(results) / elapsed:.2f} req/s")

    stats = limiter.get_stats()
    print(f"\n📈 Rate Limiter 통계:")
    print(f"   - 총 요청: {stats['total_requests']}개")
    print(f"   - 평균 대기 시간: {stats['avg_wait_time']:.4f}초")
    print(f"   - 평균 실행 시간: {stats['avg_execution_time']:.4f}초")
    print(f"   - 성공률: {stats['success_rate']}%")
    print(f"   - 사용 가능 토큰: {stats['available_tokens']}개")


if __name__ == "__main__":
    asyncio.run(test_rate_limiter())
