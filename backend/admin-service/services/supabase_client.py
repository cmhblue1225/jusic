"""
Supabase 클라이언트 서비스
전역 Supabase 클라이언트 관리
"""
import os
from supabase import create_client, Client
from typing import Optional

# Supabase 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# 전역 Supabase 클라이언트
supabase: Optional[Client] = None

if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print("✅ Supabase 클라이언트 초기화 완료")
else:
    print("⚠️  SUPABASE_URL 또는 SUPABASE_SERVICE_KEY 환경 변수 없음")
    print(f"   SUPABASE_URL: {'설정됨' if SUPABASE_URL else '❌ 없음'}")
    print(f"   SUPABASE_SERVICE_KEY: {'설정됨' if SUPABASE_SERVICE_KEY else '❌ 없음'}")
    print("⚠️  Supabase 기능이 작동하지 않습니다. Railway Variables를 확인하세요!")


def get_supabase() -> Optional[Client]:
    """Supabase 클라이언트 가져오기"""
    if supabase is None:
        raise RuntimeError(
            "Supabase 클라이언트가 초기화되지 않았습니다. "
            "Railway Variables에서 SUPABASE_URL과 SUPABASE_SERVICE_KEY를 설정하세요."
        )
    return supabase
