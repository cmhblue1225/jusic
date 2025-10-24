"""
사용자 관리 API
- 전체 사용자 목록 조회
- 사용자 상세 정보 조회
- 사용자 정지/활성화
- 사용자 삭제
- 사용자 활동 로그 조회
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from middleware.auth import AdminUser
from services.supabase_client import get_supabase

router = APIRouter()
supabase = get_supabase()


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    role: str
    created_at: datetime
    updated_at: Optional[datetime]
    settings: Optional[dict]


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None


@router.get("", response_model=List[UserResponse])
async def get_users(
    admin: dict = AdminUser,
    skip: int = 0,
    limit: int = 50,
    role: Optional[str] = None,
    search: Optional[str] = None
):
    """
    전체 사용자 목록 조회 (페이지네이션)

    Args:
        skip: 건너뛸 레코드 수
        limit: 조회할 레코드 수 (최대 100)
        role: 역할 필터 (user, admin, superadmin)
        search: 이메일 또는 이름 검색
    """
    try:
        query = supabase.table("users").select("*").order("created_at", desc=True)

        # 역할 필터
        if role:
            query = query.eq("role", role)

        # 검색
        if search:
            query = query.or_(f"email.ilike.%{search}%,name.ilike.%{search}%")

        # 페이지네이션
        query = query.range(skip, skip + min(limit, 100) - 1)

        result = query.execute()

        return result.data

    except Exception as e:
        print(f"❌ 사용자 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 목록 조회 실패: {str(e)}")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, admin: dict = AdminUser):
    """
    사용자 상세 정보 조회

    Args:
        user_id: 사용자 ID (UUID)
    """
    try:
        result = supabase.table("users").select("*").eq("id", user_id).maybe_single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 사용자 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 조회 실패: {str(e)}")


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    admin: dict = AdminUser
):
    """
    사용자 정보 수정

    Args:
        user_id: 사용자 ID (UUID)
        request: 수정할 정보 (name, role)
    """
    try:
        # 업데이트할 데이터 준비
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.role is not None:
            if request.role not in ["user", "admin", "superadmin"]:
                raise HTTPException(status_code=400, detail="유효하지 않은 역할입니다.")
            update_data["role"] = request.role

        if not update_data:
            raise HTTPException(status_code=400, detail="수정할 정보가 없습니다.")

        update_data["updated_at"] = datetime.utcnow().isoformat()

        # 사용자 정보 수정
        result = supabase.table("users").update(update_data).eq("id", user_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        # 활동 로그 기록
        supabase.table("admin_activity_logs").insert({
            "admin_id": admin["id"],
            "action": "user_update",
            "target_type": "user",
            "target_id": user_id,
            "details": {"updated_fields": list(update_data.keys())}
        }).execute()

        return result.data[0]

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 사용자 수정 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 수정 실패: {str(e)}")


@router.post("/{user_id}/suspend")
async def suspend_user(user_id: str, admin: dict = AdminUser):
    """
    사용자 정지 (비활성화)

    Args:
        user_id: 사용자 ID (UUID)
    """
    try:
        # 사용자 설정에 suspended 플래그 추가
        result = supabase.table("users").select("settings").eq("id", user_id).maybe_single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        settings = result.data.get("settings", {})
        settings["suspended"] = True
        settings["suspended_at"] = datetime.utcnow().isoformat()

        # 업데이트
        supabase.table("users").update({"settings": settings}).eq("id", user_id).execute()

        # 활동 로그 기록
        supabase.table("admin_activity_logs").insert({
            "admin_id": admin["id"],
            "action": "user_suspend",
            "target_type": "user",
            "target_id": user_id,
            "details": {"suspended_at": settings["suspended_at"]}
        }).execute()

        return {"message": "사용자가 정지되었습니다.", "user_id": user_id}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 사용자 정지 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 정지 실패: {str(e)}")


@router.post("/{user_id}/activate")
async def activate_user(user_id: str, admin: dict = AdminUser):
    """
    사용자 활성화

    Args:
        user_id: 사용자 ID (UUID)
    """
    try:
        # 사용자 설정에서 suspended 플래그 제거
        result = supabase.table("users").select("settings").eq("id", user_id).maybe_single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        settings = result.data.get("settings", {})
        settings["suspended"] = False
        if "suspended_at" in settings:
            del settings["suspended_at"]

        # 업데이트
        supabase.table("users").update({"settings": settings}).eq("id", user_id).execute()

        # 활동 로그 기록
        supabase.table("admin_activity_logs").insert({
            "admin_id": admin["id"],
            "action": "user_activate",
            "target_type": "user",
            "target_id": user_id
        }).execute()

        return {"message": "사용자가 활성화되었습니다.", "user_id": user_id}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 사용자 활성화 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 활성화 실패: {str(e)}")


@router.delete("/{user_id}")
async def delete_user(user_id: str, admin: dict = AdminUser):
    """
    사용자 삭제 (CASCADE로 관련 데이터 모두 삭제)

    Args:
        user_id: 사용자 ID (UUID)
    """
    try:
        # 사용자 존재 확인
        result = supabase.table("users").select("email").eq("id", user_id).maybe_single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        user_email = result.data["email"]

        # 사용자 삭제 (CASCADE로 portfolios, watchlist, alerts 등 자동 삭제)
        supabase.table("users").delete().eq("id", user_id).execute()

        # 활동 로그 기록
        supabase.table("admin_activity_logs").insert({
            "admin_id": admin["id"],
            "action": "user_delete",
            "target_type": "user",
            "target_id": user_id,
            "details": {"email": user_email}
        }).execute()

        return {"message": "사용자가 삭제되었습니다.", "user_id": user_id, "email": user_email}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 사용자 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 삭제 실패: {str(e)}")


@router.get("/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    admin: dict = AdminUser,
    skip: int = 0,
    limit: int = 50
):
    """
    사용자 활동 로그 조회

    Args:
        user_id: 사용자 ID (UUID)
        skip: 건너뛸 레코드 수
        limit: 조회할 레코드 수 (최대 100)
    """
    try:
        # 사용자 존재 확인
        user_result = supabase.table("users").select("email, name").eq("id", user_id).maybe_single().execute()

        if not user_result.data:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        # 활동 로그 조회 (관리자 작업 + 사용자 자체 활동)
        # 1. 관리자가 이 사용자에게 수행한 작업
        admin_logs = supabase.table("admin_activity_logs") \
            .select("*") \
            .eq("target_id", user_id) \
            .order("created_at", desc=True) \
            .range(skip, skip + min(limit, 100) - 1) \
            .execute()

        # 2. 사용자가 생성한 레포트, 포트폴리오, 관심종목 통계
        portfolios_count = supabase.table("portfolios").select("id", count="exact").eq("user_id", user_id).execute().count
        watchlist_count = supabase.table("watchlist").select("id", count="exact").eq("user_id", user_id).execute().count
        reports_count = supabase.table("stock_reports").select("id", count="exact").eq("user_id", user_id).execute().count

        return {
            "user": user_result.data,
            "admin_logs": admin_logs.data,
            "statistics": {
                "portfolios_count": portfolios_count,
                "watchlist_count": watchlist_count,
                "reports_count": reports_count
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 사용자 활동 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 활동 조회 실패: {str(e)}")
