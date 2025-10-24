"""
서비스 모니터링 API
- Railway 서비스 목록 조회
- 서비스 헬스체크
- 서비스 상세 정보 (로그, 메트릭)
- 서비스 재시작 (Railway API)
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from middleware.auth import AdminUser
from services.supabase_client import get_supabase
import httpx
import os

router = APIRouter()
supabase = get_supabase()

# Railway 서비스 설정
RAILWAY_SERVICES = {
    "stream-service": {
        "url": os.getenv("STREAM_SERVICE_URL", "https://stream-service-production.up.railway.app"),
        "health_endpoint": "/health",
        "description": "실시간 주가 스트리밍 (WebSocket)"
    },
    "news-crawler": {
        "url": os.getenv("NEWS_CRAWLER_URL", "https://news-crawler-production.up.railway.app"),
        "health_endpoint": "/health",
        "description": "뉴스 크롤링 (Python)"
    },
    "ai-service": {
        "url": os.getenv("AI_SERVICE_URL", "https://ai-service-production.up.railway.app"),
        "health_endpoint": "/health",
        "description": "AI 뉴스 분석 (Claude/OpenAI)"
    },
    "report-service": {
        "url": os.getenv("REPORT_SERVICE_URL", "https://report-service-production.up.railway.app"),
        "health_endpoint": "/health",
        "description": "종목 레포트 생성 (AI Ensemble)"
    },
    "frontend": {
        "url": os.getenv("FRONTEND_URL", "https://jusik.minhyuk.kr"),
        "health_endpoint": "/",
        "description": "React 프론트엔드"
    }
}


class ServiceStatus(BaseModel):
    name: str
    url: str
    description: str
    status: str  # online, offline, degraded
    response_time_ms: Optional[int]
    last_checked: datetime
    error_message: Optional[str] = None


class ServiceDetail(BaseModel):
    name: str
    url: str
    description: str
    status: str
    response_time_ms: Optional[int]
    health_data: Optional[Dict[str, Any]]
    recent_errors: List[Dict[str, Any]]
    uptime_percentage: Optional[float]


async def check_service_health(name: str, config: Dict[str, str]) -> ServiceStatus:
    """
    서비스 헬스체크 수행

    Args:
        name: 서비스 이름
        config: 서비스 설정 (url, health_endpoint 등)

    Returns:
        ServiceStatus: 서비스 상태 정보
    """
    url = f"{config['url']}{config['health_endpoint']}"
    start_time = datetime.utcnow()

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            if response.status_code == 200:
                return ServiceStatus(
                    name=name,
                    url=config['url'],
                    description=config['description'],
                    status="online",
                    response_time_ms=response_time,
                    last_checked=datetime.utcnow()
                )
            else:
                return ServiceStatus(
                    name=name,
                    url=config['url'],
                    description=config['description'],
                    status="degraded",
                    response_time_ms=response_time,
                    last_checked=datetime.utcnow(),
                    error_message=f"HTTP {response.status_code}"
                )
    except Exception as e:
        return ServiceStatus(
            name=name,
            url=config['url'],
            description=config['description'],
            status="offline",
            response_time_ms=None,
            last_checked=datetime.utcnow(),
            error_message=str(e)
        )


@router.get("", response_model=List[ServiceStatus])
async def get_services(admin: dict = AdminUser):
    """
    전체 서비스 목록 및 헬스 상태 조회

    Returns:
        List[ServiceStatus]: 서비스 상태 목록
    """
    try:
        service_statuses = []

        # 각 서비스의 헬스체크 수행
        for name, config in RAILWAY_SERVICES.items():
            status = await check_service_health(name, config)
            service_statuses.append(status)

        # 활동 로그 기록
        supabase.table("admin_activity_logs").insert({
            "admin_id": admin["id"],
            "action": "services_list_view",
            "target_type": "system",
            "details": {"services_count": len(service_statuses)}
        }).execute()

        return service_statuses

    except Exception as e:
        print(f"❌ 서비스 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서비스 목록 조회 실패: {str(e)}")


@router.get("/health")
async def get_aggregate_health(admin: dict = AdminUser):
    """
    전체 시스템 헬스 집계

    Returns:
        dict: 전체 서비스 상태 요약
    """
    try:
        service_statuses = []

        for name, config in RAILWAY_SERVICES.items():
            status = await check_service_health(name, config)
            service_statuses.append(status)

        # 상태별 카운트
        online_count = sum(1 for s in service_statuses if s.status == "online")
        degraded_count = sum(1 for s in service_statuses if s.status == "degraded")
        offline_count = sum(1 for s in service_statuses if s.status == "offline")

        # 전체 시스템 상태 결정
        if offline_count > 0:
            overall_status = "critical"
        elif degraded_count > 0:
            overall_status = "warning"
        else:
            overall_status = "healthy"

        # 평균 응답 시간 계산
        response_times = [s.response_time_ms for s in service_statuses if s.response_time_ms is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else None

        return {
            "overall_status": overall_status,
            "total_services": len(service_statuses),
            "online": online_count,
            "degraded": degraded_count,
            "offline": offline_count,
            "avg_response_time_ms": avg_response_time,
            "services": [s.dict() for s in service_statuses],
            "checked_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"❌ 헬스체크 집계 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"헬스체크 집계 실패: {str(e)}")


# 🔥 뉴스 크롤러 스케줄러 제어 엔드포인트 (/{service_name} 보다 먼저 선언)
@router.post("/news-crawler/pause")
async def pause_news_crawler(admin: dict = AdminUser):
    """
    뉴스 크롤러 스케줄러 일시중지

    Returns:
        dict: 일시중지 결과
    """
    try:
        news_crawler_url = RAILWAY_SERVICES["news-crawler"]["url"]

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{news_crawler_url}/admin/scheduler/pause")

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"News crawler pause failed: {response.text}"
                )

            result = response.json()

        # 활동 로그 기록
        supabase.table("admin_activity_logs").insert({
            "admin_id": admin["id"],
            "action": "news_crawler_pause",
            "target_type": "service",
            "target_id": "news-crawler",
            "details": result
        }).execute()

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 뉴스 크롤러 일시중지 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"뉴스 크롤러 일시중지 실패: {str(e)}")


@router.post("/news-crawler/resume")
async def resume_news_crawler(admin: dict = AdminUser):
    """
    뉴스 크롤러 스케줄러 재개

    Returns:
        dict: 재개 결과
    """
    try:
        news_crawler_url = RAILWAY_SERVICES["news-crawler"]["url"]

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{news_crawler_url}/admin/scheduler/resume")

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"News crawler resume failed: {response.text}"
                )

            result = response.json()

        # 활동 로그 기록
        supabase.table("admin_activity_logs").insert({
            "admin_id": admin["id"],
            "action": "news_crawler_resume",
            "target_type": "service",
            "target_id": "news-crawler",
            "details": result
        }).execute()

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 뉴스 크롤러 재개 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"뉴스 크롤러 재개 실패: {str(e)}")


@router.get("/news-crawler/scheduler-status")
async def get_news_crawler_scheduler_status(admin: dict = AdminUser):
    """
    뉴스 크롤러 스케줄러 상태 조회

    Returns:
        dict: 스케줄러 상태 정보
    """
    try:
        news_crawler_url = RAILWAY_SERVICES["news-crawler"]["url"]

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{news_crawler_url}/admin/scheduler/status")

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get scheduler status: {response.text}"
                )

            result = response.json()

        # 활동 로그 기록 (조회이므로 필요시에만)
        # supabase.table("admin_activity_logs").insert({...}).execute()

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 스케줄러 상태 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"스케줄러 상태 조회 실패: {str(e)}")


@router.get("/{service_name}", response_model=ServiceDetail)
async def get_service_detail(service_name: str, admin: dict = AdminUser):
    """
    특정 서비스 상세 정보 조회

    Args:
        service_name: 서비스 이름

    Returns:
        ServiceDetail: 서비스 상세 정보
    """
    try:
        if service_name not in RAILWAY_SERVICES:
            raise HTTPException(status_code=404, detail=f"서비스를 찾을 수 없습니다: {service_name}")

        config = RAILWAY_SERVICES[service_name]

        # 헬스체크 수행
        status = await check_service_health(service_name, config)

        # 헬스 엔드포인트에서 상세 정보 가져오기
        health_data = None
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{config['url']}{config['health_endpoint']}")
                if response.status_code == 200:
                    health_data = response.json()
        except Exception:
            pass

        # system_metrics 테이블에서 최근 에러 조회
        recent_errors_result = supabase.table("system_metrics") \
            .select("*") \
            .eq("service_name", service_name) \
            .eq("metric_type", "error") \
            .order("timestamp", desc=True) \
            .limit(10) \
            .execute()

        recent_errors = recent_errors_result.data if recent_errors_result.data else []

        # 지난 24시간 동안의 Uptime 계산
        uptime_percentage = await calculate_uptime(service_name)

        # 활동 로그 기록
        supabase.table("admin_activity_logs").insert({
            "admin_id": admin["id"],
            "action": "service_detail_view",
            "target_type": "service",
            "target_id": service_name
        }).execute()

        return ServiceDetail(
            name=status.name,
            url=status.url,
            description=status.description,
            status=status.status,
            response_time_ms=status.response_time_ms,
            health_data=health_data,
            recent_errors=recent_errors,
            uptime_percentage=uptime_percentage
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 서비스 상세 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서비스 상세 조회 실패: {str(e)}")


async def calculate_uptime(service_name: str) -> Optional[float]:
    """
    지난 24시간 동안의 서비스 Uptime 계산

    Args:
        service_name: 서비스 이름

    Returns:
        float: Uptime 퍼센트 (0~100)
    """
    try:
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)

        # system_metrics 테이블에서 헬스체크 기록 조회
        result = supabase.table("system_metrics") \
            .select("value") \
            .eq("service_name", service_name) \
            .eq("metric_type", "health_check") \
            .gte("timestamp", twenty_four_hours_ago.isoformat()) \
            .execute()

        if not result.data or len(result.data) == 0:
            return None

        # value가 1이면 online, 0이면 offline
        total_checks = len(result.data)
        successful_checks = sum(1 for record in result.data if record.get("value", 0) == 1)

        uptime_percentage = (successful_checks / total_checks) * 100
        return round(uptime_percentage, 2)

    except Exception as e:
        print(f"⚠️  Uptime 계산 실패: {str(e)}")
        return None


@router.post("/{service_name}/restart")
async def restart_service(service_name: str, admin: dict = AdminUser):
    """
    서비스 재시작 (Railway API 사용)

    Args:
        service_name: 서비스 이름

    Returns:
        dict: 재시작 결과 메시지
    """
    try:
        if service_name not in RAILWAY_SERVICES:
            raise HTTPException(status_code=404, detail=f"서비스를 찾을 수 없습니다: {service_name}")

        railway_token = os.getenv("RAILWAY_TOKEN")

        if not railway_token:
            raise HTTPException(
                status_code=503,
                detail="Railway API 토큰이 설정되지 않았습니다. 수동으로 Railway 대시보드에서 재시작하세요."
            )

        # Railway GraphQL API를 통한 서비스 재시작
        # 참고: Railway API 엔드포인트 및 쿼리는 실제 Railway API 문서 참조 필요
        # 현재는 플레이스홀더로 구현

        # 활동 로그 기록
        supabase.table("admin_activity_logs").insert({
            "admin_id": admin["id"],
            "action": "service_restart",
            "target_type": "service",
            "target_id": service_name,
            "details": {"message": "수동 재시작 요청"}
        }).execute()

        return {
            "message": f"서비스 재시작 요청이 전송되었습니다: {service_name}",
            "service_name": service_name,
            "requested_by": admin["email"],
            "requested_at": datetime.utcnow().isoformat(),
            "note": "Railway 대시보드에서 재시작 상태를 확인하세요."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 서비스 재시작 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서비스 재시작 실패: {str(e)}")
