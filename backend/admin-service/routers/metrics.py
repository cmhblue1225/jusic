"""
메트릭 조회 API
- 시스템 메트릭 (CPU, 메모리, API 지연, 에러율)
- 비즈니스 메트릭 (DAU, 레포트 생성 수, 뉴스 분석 수)
- 시계열 데이터 집계
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from middleware.auth import AdminUser
from services.supabase_client import get_supabase

router = APIRouter()
supabase = get_supabase()


class SystemMetricResponse(BaseModel):
    service_name: str
    metric_type: str
    value: float
    unit: Optional[str]
    timestamp: datetime


class BusinessMetricResponse(BaseModel):
    metric_name: str
    value: float
    date: str
    metadata: Optional[Dict[str, Any]]


class TimeSeriesDataPoint(BaseModel):
    timestamp: datetime
    value: float


class MetricSummary(BaseModel):
    metric_name: str
    current_value: float
    avg_value: float
    min_value: float
    max_value: float
    trend: str  # increasing, decreasing, stable
    time_series: List[TimeSeriesDataPoint]


@router.get("/system", response_model=List[SystemMetricResponse])
async def get_system_metrics(
    admin: dict = AdminUser,
    service_name: Optional[str] = None,
    metric_type: Optional[str] = None,
    hours: int = Query(24, ge=1, le=168, description="조회 기간 (시간)")
):
    """
    시스템 메트릭 조회

    Args:
        service_name: 서비스 이름 필터 (선택)
        metric_type: 메트릭 타입 필터 (cpu, memory, latency, error_rate 등)
        hours: 조회 기간 (기본 24시간, 최대 168시간/7일)

    Returns:
        List[SystemMetricResponse]: 시스템 메트릭 목록
    """
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)

        query = supabase.table("system_metrics") \
            .select("*") \
            .gte("timestamp", start_time.isoformat()) \
            .order("timestamp", desc=True)

        # 필터 적용
        if service_name:
            query = query.eq("service_name", service_name)

        if metric_type:
            query = query.eq("metric_type", metric_type)

        result = query.limit(1000).execute()

        return result.data

    except Exception as e:
        print(f"❌ 시스템 메트릭 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"시스템 메트릭 조회 실패: {str(e)}")


@router.get("/business", response_model=List[BusinessMetricResponse])
async def get_business_metrics(
    admin: dict = AdminUser,
    metric_name: Optional[str] = None,
    days: int = Query(30, ge=1, le=90, description="조회 기간 (일)")
):
    """
    비즈니스 메트릭 조회

    Args:
        metric_name: 메트릭 이름 필터 (선택)
        days: 조회 기간 (기본 30일, 최대 90일)

    Returns:
        List[BusinessMetricResponse]: 비즈니스 메트릭 목록
    """
    try:
        start_date = (datetime.utcnow() - timedelta(days=days)).date()

        query = supabase.table("business_metrics") \
            .select("*") \
            .gte("date", start_date.isoformat()) \
            .order("date", desc=True)

        if metric_name:
            query = query.eq("metric_name", metric_name)

        result = query.limit(1000).execute()

        return result.data

    except Exception as e:
        print(f"❌ 비즈니스 메트릭 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"비즈니스 메트릭 조회 실패: {str(e)}")


@router.get("/summary")
async def get_metrics_summary(
    admin: dict = AdminUser,
    hours: int = Query(24, ge=1, le=168)
):
    """
    메트릭 요약 대시보드 (주요 지표 집계)

    Args:
        hours: 조회 기간 (시간)

    Returns:
        dict: 메트릭 요약 정보
    """
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)

        # 1. 시스템 메트릭 집계
        system_metrics = supabase.table("system_metrics") \
            .select("service_name, metric_type, value") \
            .gte("timestamp", start_time.isoformat()) \
            .execute()

        # 서비스별 평균 지연시간 계산
        latency_by_service = {}
        error_rate_by_service = {}

        for metric in system_metrics.data:
            service = metric["service_name"]
            metric_type = metric["metric_type"]
            value = metric["value"]

            if metric_type == "latency":
                if service not in latency_by_service:
                    latency_by_service[service] = []
                latency_by_service[service].append(value)

            elif metric_type == "error_rate":
                if service not in error_rate_by_service:
                    error_rate_by_service[service] = []
                error_rate_by_service[service].append(value)

        # 평균 계산
        avg_latency = {
            service: sum(values) / len(values) if values else 0
            for service, values in latency_by_service.items()
        }

        avg_error_rate = {
            service: sum(values) / len(values) if values else 0
            for service, values in error_rate_by_service.items()
        }

        # 2. 비즈니스 메트릭 집계 (오늘 기준)
        today = datetime.utcnow().date()

        business_today = supabase.table("business_metrics") \
            .select("*") \
            .eq("date", today.isoformat()) \
            .execute()

        business_summary = {
            metric["metric_name"]: metric["value"]
            for metric in business_today.data
        }

        # 3. 사용자 통계
        users_count = supabase.table("users").select("id", count="exact").execute().count
        portfolios_count = supabase.table("portfolios").select("id", count="exact").execute().count
        watchlist_count = supabase.table("watchlist").select("id", count="exact").execute().count
        reports_count = supabase.table("stock_reports").select("id", count="exact").execute().count

        return {
            "time_range": {
                "start": start_time.isoformat(),
                "end": datetime.utcnow().isoformat(),
                "hours": hours
            },
            "system_metrics": {
                "avg_latency_by_service": avg_latency,
                "avg_error_rate_by_service": avg_error_rate
            },
            "business_metrics": business_summary,
            "user_statistics": {
                "total_users": users_count,
                "total_portfolios": portfolios_count,
                "total_watchlist": watchlist_count,
                "total_reports": reports_count
            },
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"❌ 메트릭 요약 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메트릭 요약 조회 실패: {str(e)}")


@router.get("/timeseries/{metric_name}", response_model=MetricSummary)
async def get_metric_timeseries(
    metric_name: str,
    admin: dict = AdminUser,
    hours: int = Query(24, ge=1, le=168)
):
    """
    특정 메트릭의 시계열 데이터 조회 (트렌드 분석)

    Args:
        metric_name: 메트릭 이름
        hours: 조회 기간 (시간)

    Returns:
        MetricSummary: 메트릭 요약 및 시계열 데이터
    """
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)

        # system_metrics 또는 business_metrics에서 조회
        # 먼저 system_metrics 시도
        system_result = supabase.table("system_metrics") \
            .select("value, timestamp") \
            .eq("metric_type", metric_name) \
            .gte("timestamp", start_time.isoformat()) \
            .order("timestamp", asc=True) \
            .execute()

        if system_result.data and len(system_result.data) > 0:
            values = [record["value"] for record in system_result.data]
            time_series = [
                TimeSeriesDataPoint(timestamp=record["timestamp"], value=record["value"])
                for record in system_result.data
            ]

            current_value = values[-1] if values else 0
            avg_value = sum(values) / len(values) if values else 0
            min_value = min(values) if values else 0
            max_value = max(values) if values else 0

            # 트렌드 계산 (최근 값과 평균 비교)
            if current_value > avg_value * 1.1:
                trend = "increasing"
            elif current_value < avg_value * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"

            return MetricSummary(
                metric_name=metric_name,
                current_value=current_value,
                avg_value=avg_value,
                min_value=min_value,
                max_value=max_value,
                trend=trend,
                time_series=time_series
            )

        # business_metrics에서 조회 (일별 데이터)
        business_result = supabase.table("business_metrics") \
            .select("value, date") \
            .eq("metric_name", metric_name) \
            .gte("date", start_time.date().isoformat()) \
            .order("date", asc=True) \
            .execute()

        if business_result.data and len(business_result.data) > 0:
            values = [record["value"] for record in business_result.data]
            time_series = [
                TimeSeriesDataPoint(
                    timestamp=datetime.fromisoformat(record["date"] + "T00:00:00"),
                    value=record["value"]
                )
                for record in business_result.data
            ]

            current_value = values[-1] if values else 0
            avg_value = sum(values) / len(values) if values else 0
            min_value = min(values) if values else 0
            max_value = max(values) if values else 0

            if current_value > avg_value * 1.1:
                trend = "increasing"
            elif current_value < avg_value * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"

            return MetricSummary(
                metric_name=metric_name,
                current_value=current_value,
                avg_value=avg_value,
                min_value=min_value,
                max_value=max_value,
                trend=trend,
                time_series=time_series
            )

        # 데이터가 없으면 404
        raise HTTPException(status_code=404, detail=f"메트릭을 찾을 수 없습니다: {metric_name}")

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 시계열 데이터 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"시계열 데이터 조회 실패: {str(e)}")


@router.post("/system")
async def create_system_metric(
    service_name: str,
    metric_type: str,
    value: float,
    unit: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    admin: dict = AdminUser
):
    """
    시스템 메트릭 생성 (수동 입력 또는 외부 서비스에서 호출)

    Args:
        service_name: 서비스 이름
        metric_type: 메트릭 타입 (cpu, memory, latency, error_rate 등)
        value: 메트릭 값
        unit: 단위 (선택)
        metadata: 추가 메타데이터 (선택)

    Returns:
        dict: 생성된 메트릭 정보
    """
    try:
        result = supabase.table("system_metrics").insert({
            "service_name": service_name,
            "metric_type": metric_type,
            "value": value,
            "unit": unit,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat()
        }).execute()

        # 활동 로그 기록
        supabase.table("admin_activity_logs").insert({
            "admin_id": admin["id"],
            "action": "system_metric_create",
            "target_type": "metric",
            "details": {
                "service_name": service_name,
                "metric_type": metric_type,
                "value": value
            }
        }).execute()

        return {
            "message": "시스템 메트릭이 생성되었습니다.",
            "data": result.data[0] if result.data else None
        }

    except Exception as e:
        print(f"❌ 시스템 메트릭 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"시스템 메트릭 생성 실패: {str(e)}")


@router.post("/business")
async def create_business_metric(
    metric_name: str,
    value: float,
    date: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    admin: dict = AdminUser
):
    """
    비즈니스 메트릭 생성 (수동 입력 또는 외부 서비스에서 호출)

    Args:
        metric_name: 메트릭 이름 (dau, report_count, news_analysis_count 등)
        value: 메트릭 값
        date: 날짜 (YYYY-MM-DD, 기본값: 오늘)
        metadata: 추가 메타데이터 (선택)

    Returns:
        dict: 생성된 메트릭 정보
    """
    try:
        target_date = date if date else datetime.utcnow().date().isoformat()

        # upsert (날짜별 중복 방지)
        result = supabase.table("business_metrics").upsert({
            "metric_name": metric_name,
            "value": value,
            "date": target_date,
            "metadata": metadata
        }, on_conflict="metric_name,date").execute()

        # 활동 로그 기록
        supabase.table("admin_activity_logs").insert({
            "admin_id": admin["id"],
            "action": "business_metric_create",
            "target_type": "metric",
            "details": {
                "metric_name": metric_name,
                "value": value,
                "date": target_date
            }
        }).execute()

        return {
            "message": "비즈니스 메트릭이 생성되었습니다.",
            "data": result.data[0] if result.data else None
        }

    except Exception as e:
        print(f"❌ 비즈니스 메트릭 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"비즈니스 메트릭 생성 실패: {str(e)}")
