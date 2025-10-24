"""
데이터베이스 관리 API
- 테이블 목록 및 통계
- 커스텀 SQL 쿼리 실행
- 데이터베이스 헬스체크
- 백업 및 복원 (향후 구현)
"""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from middleware.auth import AdminUser
from services.supabase_client import get_supabase

router = APIRouter()
supabase = get_supabase()

# 주요 테이블 목록
MAIN_TABLES = [
    "users",
    "portfolios",
    "watchlist",
    "stock_reports",
    "news",
    "alerts",
    "alert_rules",
    "stock_prices",
    "stock_master",
    "admin_activity_logs",
    "system_metrics",
    "business_metrics"
]


class TableStatistics(BaseModel):
    table_name: str
    row_count: int
    size_bytes: Optional[int]
    last_updated: Optional[datetime]


class QueryRequest(BaseModel):
    query: str
    description: Optional[str] = None


class QueryResponse(BaseModel):
    success: bool
    data: Optional[List[Dict[str, Any]]]
    row_count: Optional[int]
    execution_time_ms: Optional[float]
    error: Optional[str]


@router.get("/tables", response_model=List[TableStatistics])
async def get_table_statistics(admin: dict = AdminUser):
    """
    전체 테이블 목록 및 통계 조회

    Returns:
        List[TableStatistics]: 테이블 통계 목록
    """
    try:
        table_stats = []

        for table_name in MAIN_TABLES:
            try:
                # 테이블 행 수 조회
                result = supabase.table(table_name).select("id", count="exact").limit(1).execute()
                row_count = result.count if result.count is not None else 0

                # 최근 업데이트 시간 조회 (updated_at 또는 created_at 컬럼 사용)
                last_updated = None
                try:
                    recent = supabase.table(table_name) \
                        .select("updated_at") \
                        .order("updated_at", desc=True) \
                        .limit(1) \
                        .execute()

                    if recent.data and len(recent.data) > 0:
                        last_updated = recent.data[0].get("updated_at")
                except Exception:
                    # updated_at 컬럼이 없으면 created_at 시도
                    try:
                        recent = supabase.table(table_name) \
                            .select("created_at") \
                            .order("created_at", desc=True) \
                            .limit(1) \
                            .execute()

                        if recent.data and len(recent.data) > 0:
                            last_updated = recent.data[0].get("created_at")
                    except Exception:
                        pass

                table_stats.append(TableStatistics(
                    table_name=table_name,
                    row_count=row_count,
                    size_bytes=None,  # Supabase에서 직접 조회 불가 (pg_total_relation_size 필요)
                    last_updated=last_updated
                ))

            except Exception as e:
                print(f"⚠️  테이블 {table_name} 통계 조회 실패: {str(e)}")
                table_stats.append(TableStatistics(
                    table_name=table_name,
                    row_count=0,
                    size_bytes=None,
                    last_updated=None
                ))

        # 활동 로그 기록
        supabase.table("admin_activity_logs").insert({
            "admin_id": admin["id"],
            "action": "database_tables_view",
            "target_type": "database"
        }).execute()

        return table_stats

    except Exception as e:
        print(f"❌ 테이블 통계 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"테이블 통계 조회 실패: {str(e)}")


@router.get("/tables/{table_name}")
async def get_table_detail(table_name: str, admin: dict = AdminUser):
    """
    특정 테이블 상세 정보 조회

    Args:
        table_name: 테이블 이름

    Returns:
        dict: 테이블 상세 정보
    """
    try:
        if table_name not in MAIN_TABLES:
            raise HTTPException(status_code=404, detail=f"테이블을 찾을 수 없습니다: {table_name}")

        # 행 수 조회
        result = supabase.table(table_name).select("*", count="exact").limit(1).execute()
        row_count = result.count if result.count is not None else 0

        # 최근 10개 레코드 샘플
        sample_data = supabase.table(table_name) \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(10) \
            .execute()

        # 컬럼 정보 (첫 번째 레코드에서 추출)
        columns = []
        if sample_data.data and len(sample_data.data) > 0:
            columns = list(sample_data.data[0].keys())

        # 활동 로그 기록
        supabase.table("admin_activity_logs").insert({
            "admin_id": admin["id"],
            "action": "database_table_detail_view",
            "target_type": "database",
            "target_id": table_name
        }).execute()

        return {
            "table_name": table_name,
            "row_count": row_count,
            "columns": columns,
            "sample_data": sample_data.data,
            "accessed_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 테이블 상세 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"테이블 상세 조회 실패: {str(e)}")


@router.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest, admin: dict = AdminUser):
    """
    커스텀 SQL 쿼리 실행 (READ ONLY)

    Args:
        request: QueryRequest (query, description)

    Returns:
        QueryResponse: 쿼리 실행 결과

    ⚠️  보안: SELECT 쿼리만 허용
    """
    try:
        query = request.query.strip()

        # 보안 검증: SELECT만 허용
        if not query.upper().startswith("SELECT"):
            raise HTTPException(
                status_code=403,
                detail="보안상 SELECT 쿼리만 허용됩니다. INSERT/UPDATE/DELETE는 Supabase Dashboard를 사용하세요."
            )

        # 위험한 키워드 차단
        dangerous_keywords = ["DROP", "TRUNCATE", "ALTER", "CREATE", "GRANT", "REVOKE"]
        for keyword in dangerous_keywords:
            if keyword in query.upper():
                raise HTTPException(
                    status_code=403,
                    detail=f"보안상 {keyword} 명령어는 허용되지 않습니다."
                )

        # 쿼리 실행 (Supabase RPC 또는 PostgREST 사용)
        start_time = datetime.utcnow()

        # Supabase는 직접 SQL 실행을 지원하지 않으므로,
        # RPC 함수를 통해 실행하거나 별도의 PostgreSQL 클라이언트 필요
        # 현재는 플레이스홀더로 구현

        # 실제 구현 예시 (psycopg2 또는 asyncpg 사용):
        # import psycopg2
        # conn = psycopg2.connect(DATABASE_URL)
        # cursor = conn.cursor()
        # cursor.execute(query)
        # data = cursor.fetchall()
        # conn.close()

        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # 활동 로그 기록
        supabase.table("admin_activity_logs").insert({
            "admin_id": admin["id"],
            "action": "database_query_execute",
            "target_type": "database",
            "details": {
                "query": query[:200],  # 처음 200자만 로그
                "description": request.description
            }
        }).execute()

        return QueryResponse(
            success=False,
            data=None,
            row_count=None,
            execution_time_ms=execution_time,
            error="직접 SQL 실행은 Supabase Service Key가 필요합니다. 현재는 Supabase Dashboard를 사용하세요."
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 쿼리 실행 실패: {str(e)}")
        return QueryResponse(
            success=False,
            data=None,
            row_count=None,
            execution_time_ms=None,
            error=str(e)
        )


@router.get("/health")
async def check_database_health(admin: dict = AdminUser):
    """
    데이터베이스 헬스체크

    Returns:
        dict: 데이터베이스 상태 정보
    """
    try:
        # 1. 간단한 쿼리로 연결 확인
        start_time = datetime.utcnow()
        test_query = supabase.table("users").select("id").limit(1).execute()
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # 2. 전체 테이블 수 확인
        total_tables = len(MAIN_TABLES)

        # 3. 전체 레코드 수 계산
        total_records = 0
        for table_name in MAIN_TABLES:
            try:
                result = supabase.table(table_name).select("id", count="exact").limit(1).execute()
                total_records += result.count if result.count is not None else 0
            except Exception:
                pass

        # 4. 최근 활동 확인 (admin_activity_logs)
        recent_activity = supabase.table("admin_activity_logs") \
            .select("created_at") \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        last_activity_time = None
        if recent_activity.data and len(recent_activity.data) > 0:
            last_activity_time = recent_activity.data[0].get("created_at")

        return {
            "status": "healthy" if response_time < 500 else "degraded",
            "response_time_ms": round(response_time, 2),
            "total_tables": total_tables,
            "total_records": total_records,
            "last_activity": last_activity_time,
            "checked_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"❌ 데이터베이스 헬스체크 실패: {str(e)}")
        return {
            "status": "unhealthy",
            "response_time_ms": None,
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat()
        }


@router.delete("/tables/{table_name}/truncate")
async def truncate_table(table_name: str, admin: dict = AdminUser):
    """
    테이블 전체 데이터 삭제 (TRUNCATE)

    Args:
        table_name: 테이블 이름

    Returns:
        dict: 삭제 결과

    ⚠️  위험: 이 작업은 되돌릴 수 없습니다!
    """
    try:
        if table_name not in MAIN_TABLES:
            raise HTTPException(status_code=404, detail=f"테이블을 찾을 수 없습니다: {table_name}")

        # 중요 테이블 보호
        protected_tables = ["users", "admin_activity_logs"]
        if table_name in protected_tables:
            raise HTTPException(
                status_code=403,
                detail=f"보안상 {table_name} 테이블은 삭제할 수 없습니다."
            )

        # 삭제 전 행 수 확인
        before_count = supabase.table(table_name).select("id", count="exact").limit(1).execute().count

        # 전체 삭제 (Supabase에서는 delete().neq("id", "") 패턴 사용)
        # 실제 TRUNCATE는 PostgreSQL 직접 연결 필요
        supabase.table(table_name).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

        # 활동 로그 기록
        supabase.table("admin_activity_logs").insert({
            "admin_id": admin["id"],
            "action": "database_table_truncate",
            "target_type": "database",
            "target_id": table_name,
            "details": {"deleted_rows": before_count}
        }).execute()

        return {
            "message": f"테이블 {table_name}의 모든 데이터가 삭제되었습니다.",
            "deleted_rows": before_count,
            "deleted_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 테이블 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"테이블 삭제 실패: {str(e)}")


@router.get("/statistics")
async def get_database_statistics(admin: dict = AdminUser):
    """
    데이터베이스 전체 통계

    Returns:
        dict: 데이터베이스 통계 정보
    """
    try:
        # 1. 사용자 통계
        users_count = supabase.table("users").select("id", count="exact").execute().count
        admin_count = supabase.table("users").select("id", count="exact").eq("role", "admin").execute().count

        # 2. 포트폴리오 통계
        portfolios_count = supabase.table("portfolios").select("id", count="exact").execute().count
        watchlist_count = supabase.table("watchlist").select("id", count="exact").execute().count

        # 3. 레포트 통계
        reports_count = supabase.table("stock_reports").select("id", count="exact").execute().count

        # 4. 뉴스 통계
        news_count = supabase.table("news").select("id", count="exact").execute().count

        # 5. 알림 통계
        alerts_count = supabase.table("alerts").select("id", count="exact").execute().count
        unread_alerts = supabase.table("alerts").select("id", count="exact").eq("status", "unread").execute().count

        # 6. 시스템 메트릭 통계
        system_metrics_count = supabase.table("system_metrics").select("id", count="exact").execute().count

        # 7. 관리자 활동 로그 통계
        admin_logs_count = supabase.table("admin_activity_logs").select("id", count="exact").execute().count

        return {
            "users": {
                "total": users_count,
                "admins": admin_count,
                "regular_users": users_count - admin_count
            },
            "portfolios": {
                "total": portfolios_count,
                "watchlist": watchlist_count
            },
            "reports": {
                "total": reports_count
            },
            "news": {
                "total": news_count
            },
            "alerts": {
                "total": alerts_count,
                "unread": unread_alerts,
                "read": alerts_count - unread_alerts
            },
            "system": {
                "system_metrics": system_metrics_count,
                "admin_logs": admin_logs_count
            },
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"❌ 데이터베이스 통계 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"데이터베이스 통계 조회 실패: {str(e)}")
