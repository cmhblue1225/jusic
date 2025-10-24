"""
로그 조회 API
- 관리자 활동 로그 조회
- 시스템 이벤트 로그 조회
- 로그 필터링 및 검색
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from middleware.auth import AdminUser
from services.supabase_client import get_supabase

router = APIRouter()
supabase = get_supabase()


class AdminActivityLog(BaseModel):
    id: str
    admin_id: str
    admin_email: Optional[str]
    action: str
    target_type: Optional[str]
    target_id: Optional[str]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime


class LogStatistics(BaseModel):
    total_logs: int
    actions_count: Dict[str, int]
    top_admins: List[Dict[str, Any]]
    recent_activities: List[str]


@router.get("/admin-activity", response_model=List[AdminActivityLog])
async def get_admin_activity_logs(
    admin: dict = AdminUser,
    skip: int = 0,
    limit: int = 50,
    action: Optional[str] = None,
    admin_id: Optional[str] = None,
    target_type: Optional[str] = None,
    hours: Optional[int] = None
):
    """
    관리자 활동 로그 조회

    Args:
        skip: 건너뛸 레코드 수
        limit: 조회할 레코드 수 (최대 100)
        action: 액션 필터 (user_update, user_delete 등)
        admin_id: 관리자 ID 필터
        target_type: 타겟 타입 필터 (user, service, database 등)
        hours: 시간 범위 필터 (예: 24시간 이내)

    Returns:
        List[AdminActivityLog]: 관리자 활동 로그 목록
    """
    try:
        query = supabase.table("admin_activity_logs") \
            .select("*") \
            .order("created_at", desc=True)

        # 필터 적용
        if action:
            query = query.eq("action", action)

        if admin_id:
            query = query.eq("admin_id", admin_id)

        if target_type:
            query = query.eq("target_type", target_type)

        if hours:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            query = query.gte("created_at", start_time.isoformat())

        # 페이지네이션
        query = query.range(skip, skip + min(limit, 100) - 1)

        result = query.execute()

        # admin_email 정보 추가 (users 테이블 조인)
        logs_with_admin = []
        for log in result.data:
            admin_info = supabase.table("users") \
                .select("email") \
                .eq("id", log["admin_id"]) \
                .maybe_single() \
                .execute()

            log["admin_email"] = admin_info.data.get("email") if admin_info.data else None
            logs_with_admin.append(log)

        return logs_with_admin

    except Exception as e:
        print(f"❌ 관리자 활동 로그 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"관리자 활동 로그 조회 실패: {str(e)}")


@router.get("/admin-activity/{log_id}")
async def get_admin_activity_log_detail(log_id: str, admin: dict = AdminUser):
    """
    특정 관리자 활동 로그 상세 조회

    Args:
        log_id: 로그 ID

    Returns:
        dict: 로그 상세 정보
    """
    try:
        result = supabase.table("admin_activity_logs") \
            .select("*") \
            .eq("id", log_id) \
            .maybe_single() \
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="로그를 찾을 수 없습니다.")

        log = result.data

        # 관리자 정보 추가
        admin_info = supabase.table("users") \
            .select("email, name, role") \
            .eq("id", log["admin_id"]) \
            .maybe_single() \
            .execute()

        log["admin_info"] = admin_info.data if admin_info.data else None

        # 타겟 정보 추가 (target_type에 따라)
        if log.get("target_type") == "user" and log.get("target_id"):
            target_user = supabase.table("users") \
                .select("email, name, role") \
                .eq("id", log["target_id"]) \
                .maybe_single() \
                .execute()

            log["target_info"] = target_user.data if target_user.data else None

        return log

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 로그 상세 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"로그 상세 조회 실패: {str(e)}")


@router.get("/statistics", response_model=LogStatistics)
async def get_log_statistics(
    admin: dict = AdminUser,
    hours: int = Query(24, ge=1, le=168)
):
    """
    로그 통계 조회

    Args:
        hours: 조회 기간 (시간)

    Returns:
        LogStatistics: 로그 통계 정보
    """
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)

        # 전체 로그 수
        total_logs_result = supabase.table("admin_activity_logs") \
            .select("id", count="exact") \
            .gte("created_at", start_time.isoformat()) \
            .execute()

        total_logs = total_logs_result.count if total_logs_result.count is not None else 0

        # 액션별 카운트
        all_logs = supabase.table("admin_activity_logs") \
            .select("action, admin_id") \
            .gte("created_at", start_time.isoformat()) \
            .execute()

        actions_count = {}
        admin_activity_count = {}

        for log in all_logs.data:
            action = log.get("action", "unknown")
            admin_id = log.get("admin_id")

            # 액션별 카운트
            actions_count[action] = actions_count.get(action, 0) + 1

            # 관리자별 활동 카운트
            admin_activity_count[admin_id] = admin_activity_count.get(admin_id, 0) + 1

        # 상위 관리자 (활동이 많은 순)
        top_admin_ids = sorted(admin_activity_count.items(), key=lambda x: x[1], reverse=True)[:5]

        top_admins = []
        for admin_id, count in top_admin_ids:
            admin_info = supabase.table("users") \
                .select("email, name") \
                .eq("id", admin_id) \
                .maybe_single() \
                .execute()

            top_admins.append({
                "admin_id": admin_id,
                "email": admin_info.data.get("email") if admin_info.data else None,
                "name": admin_info.data.get("name") if admin_info.data else None,
                "activity_count": count
            })

        # 최근 활동 (액션 이름 목록)
        recent_activities_result = supabase.table("admin_activity_logs") \
            .select("action") \
            .gte("created_at", start_time.isoformat()) \
            .order("created_at", desc=True) \
            .limit(10) \
            .execute()

        recent_activities = [log.get("action") for log in recent_activities_result.data]

        return LogStatistics(
            total_logs=total_logs,
            actions_count=actions_count,
            top_admins=top_admins,
            recent_activities=recent_activities
        )

    except Exception as e:
        print(f"❌ 로그 통계 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"로그 통계 조회 실패: {str(e)}")


@router.get("/actions")
async def get_available_actions(admin: dict = AdminUser):
    """
    사용 가능한 액션 목록 조회 (필터링에 사용)

    Returns:
        dict: 액션 목록 및 설명
    """
    try:
        # admin_activity_logs 테이블에서 실제로 사용된 액션 목록 조회
        result = supabase.table("admin_activity_logs") \
            .select("action") \
            .execute()

        # 중복 제거
        actions = list(set([log.get("action") for log in result.data if log.get("action")]))
        actions.sort()

        # 액션별 설명
        action_descriptions = {
            "user_update": "사용자 정보 수정",
            "user_suspend": "사용자 정지",
            "user_activate": "사용자 활성화",
            "user_delete": "사용자 삭제",
            "service_detail_view": "서비스 상세 조회",
            "service_restart": "서비스 재시작",
            "database_tables_view": "데이터베이스 테이블 조회",
            "database_table_detail_view": "테이블 상세 조회",
            "database_query_execute": "커스텀 쿼리 실행",
            "database_table_truncate": "테이블 삭제",
            "system_metric_create": "시스템 메트릭 생성",
            "business_metric_create": "비즈니스 메트릭 생성",
            "services_list_view": "서비스 목록 조회"
        }

        return {
            "actions": actions,
            "descriptions": {action: action_descriptions.get(action, "설명 없음") for action in actions}
        }

    except Exception as e:
        print(f"❌ 액션 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"액션 목록 조회 실패: {str(e)}")


@router.delete("/{log_id}")
async def delete_admin_activity_log(log_id: str, admin: dict = AdminUser):
    """
    관리자 활동 로그 삭제

    Args:
        log_id: 로그 ID

    Returns:
        dict: 삭제 결과

    ⚠️  주의: 감사 추적을 위해 로그 삭제는 신중히 수행해야 합니다.
    """
    try:
        # 로그 존재 확인
        result = supabase.table("admin_activity_logs") \
            .select("action") \
            .eq("id", log_id) \
            .maybe_single() \
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="로그를 찾을 수 없습니다.")

        action = result.data.get("action")

        # 로그 삭제
        supabase.table("admin_activity_logs").delete().eq("id", log_id).execute()

        # 삭제 자체도 로그에 기록
        supabase.table("admin_activity_logs").insert({
            "admin_id": admin["id"],
            "action": "admin_log_delete",
            "target_type": "log",
            "target_id": log_id,
            "details": {"deleted_action": action}
        }).execute()

        return {
            "message": "관리자 활동 로그가 삭제되었습니다.",
            "log_id": log_id,
            "deleted_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 로그 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"로그 삭제 실패: {str(e)}")


@router.delete("/bulk")
async def delete_old_logs(
    admin: dict = AdminUser,
    days: int = Query(30, ge=7, le=365, description="삭제할 로그의 기준 일수")
):
    """
    오래된 로그 일괄 삭제

    Args:
        days: 기준 일수 (이 일수 이전의 로그 삭제)

    Returns:
        dict: 삭제 결과
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # 삭제 전 카운트 확인
        before_count = supabase.table("admin_activity_logs") \
            .select("id", count="exact") \
            .lt("created_at", cutoff_date.isoformat()) \
            .execute() \
            .count

        # 오래된 로그 삭제
        supabase.table("admin_activity_logs") \
            .delete() \
            .lt("created_at", cutoff_date.isoformat()) \
            .execute()

        # 삭제 작업 자체도 로그에 기록
        supabase.table("admin_activity_logs").insert({
            "admin_id": admin["id"],
            "action": "admin_logs_bulk_delete",
            "target_type": "log",
            "details": {
                "cutoff_date": cutoff_date.isoformat(),
                "deleted_count": before_count
            }
        }).execute()

        return {
            "message": f"{days}일 이전의 로그가 삭제되었습니다.",
            "deleted_count": before_count,
            "cutoff_date": cutoff_date.isoformat(),
            "deleted_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"❌ 로그 일괄 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"로그 일괄 삭제 실패: {str(e)}")


@router.get("/export")
async def export_logs(
    admin: dict = AdminUser,
    hours: int = Query(24, ge=1, le=720),
    format: str = Query("json", regex="^(json|csv)$")
):
    """
    로그 내보내기 (JSON 또는 CSV)

    Args:
        hours: 조회 기간 (시간)
        format: 파일 형식 (json 또는 csv)

    Returns:
        dict: 내보내기 결과
    """
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)

        # 로그 조회
        result = supabase.table("admin_activity_logs") \
            .select("*") \
            .gte("created_at", start_time.isoformat()) \
            .order("created_at", desc=True) \
            .limit(10000) \
            .execute()

        logs = result.data

        # 활동 로그 기록
        supabase.table("admin_activity_logs").insert({
            "admin_id": admin["id"],
            "action": "admin_logs_export",
            "target_type": "log",
            "details": {
                "format": format,
                "hours": hours,
                "exported_count": len(logs)
            }
        }).execute()

        if format == "json":
            return {
                "format": "json",
                "data": logs,
                "exported_count": len(logs),
                "exported_at": datetime.utcnow().isoformat()
            }

        elif format == "csv":
            # CSV 형식으로 변환 (간단한 구현)
            csv_lines = ["id,admin_id,action,target_type,target_id,created_at"]

            for log in logs:
                csv_lines.append(
                    f"{log.get('id')},"
                    f"{log.get('admin_id')},"
                    f"{log.get('action')},"
                    f"{log.get('target_type') or ''},"
                    f"{log.get('target_id') or ''},"
                    f"{log.get('created_at')}"
                )

            return {
                "format": "csv",
                "data": "\n".join(csv_lines),
                "exported_count": len(logs),
                "exported_at": datetime.utcnow().isoformat()
            }

    except Exception as e:
        print(f"❌ 로그 내보내기 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"로그 내보내기 실패: {str(e)}")
