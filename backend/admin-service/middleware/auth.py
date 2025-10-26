"""
Admin 인증 미들웨어
JWT 토큰 검증 + admin role 확인
"""
from fastapi import Header, HTTPException, Depends
from typing import Optional
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# Supabase 클라이언트 초기화
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError("SUPABASE_URL, SUPABASE_SERVICE_KEY 환경 변수가 설정되지 않았습니다.")

# JWT 검증용 클라이언트 (ANON_KEY 우선, 없으면 SERVICE_KEY 사용)
if SUPABASE_ANON_KEY:
    supabase_auth: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print("✅ Auth: ANON_KEY 사용")
else:
    supabase_auth: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print("⚠️  Auth: ANON_KEY 없음, SERVICE_KEY 사용 (권장하지 않음)")

# 데이터 조회용 클라이언트 (SERVICE_KEY 사용 - RLS 우회)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


async def verify_admin_token(authorization: Optional[str] = Header(None)) -> dict:
    """
    JWT 토큰 검증 및 admin role 확인

    Args:
        authorization: Authorization 헤더 (Bearer <token>)

    Returns:
        dict: 사용자 정보 (id, email, role)

    Raises:
        HTTPException: 인증 실패 시
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="인증 토큰이 없습니다. Authorization 헤더를 확인하세요."
        )

    token = authorization.replace("Bearer ", "")

    try:
        # Supabase JWT 검증 (ANON_KEY 클라이언트 사용)
        user_response = supabase_auth.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

        user_id = user_response.user.id

        # users 테이블에서 role 확인
        result = supabase.table("users").select("id, email, name, role").eq("id", user_id).maybe_single().execute()

        if not result.data:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")

        user_data = result.data

        # admin 또는 superadmin 권한 확인
        if user_data.get("role") not in ["admin", "superadmin"]:
            raise HTTPException(
                status_code=403,
                detail=f"관리자 권한이 필요합니다. 현재 권한: {user_data.get('role', 'user')}"
            )

        return {
            "id": user_data["id"],
            "email": user_data["email"],
            "name": user_data.get("name"),
            "role": user_data["role"]
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 토큰 검증 오류: {str(e)}")
        raise HTTPException(status_code=401, detail=f"토큰 검증 실패: {str(e)}")


# 의존성으로 사용
AdminUser = Depends(verify_admin_token)
