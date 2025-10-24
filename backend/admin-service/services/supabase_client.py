"""
Supabase 클라이언트 서비스
전역 Supabase 클라이언트 관리
"""
import os
from supabase import create_client, Client

# Supabase 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError("SUPABASE_URL 또는 SUPABASE_SERVICE_KEY 환경 변수가 설정되지 않았습니다.")

# 전역 Supabase 클라이언트
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

print("✅ Supabase 클라이언트 초기화 완료")


def get_supabase() -> Client:
    """Supabase 클라이언트 가져오기"""
    return supabase
