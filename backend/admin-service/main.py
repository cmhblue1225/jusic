"""
Admin Service - 관리자 서비스
사용자 관리, 시스템 모니터링, 비즈니스 지표 조회
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

print("=" * 60)
print("🔐 Admin Service 초기화 시작...")
print("=" * 60)

# 환경 변수 로드
load_dotenv()
print("✅ .env 로드 완료")

# Sentry 에러 추적 초기화
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

SENTRY_DSN = os.getenv("SENTRY_DSN")
ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "development")

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENVIRONMENT,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        integrations=[FastApiIntegration()],
    )
    print(f"✅ Sentry 초기화 완료 (환경: {ENVIRONMENT})")
else:
    print("⚠️  SENTRY_DSN 환경 변수 없음 - Sentry 비활성화")

# FastAPI 앱 생성
app = FastAPI(
    title="Admin Service API",
    description="관리자 전용 API - 사용자 관리, 시스템 모니터링, 비즈니스 지표",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",  # Admin Dashboard (개발)
    "http://localhost:3005",  # Admin Dashboard (개발 - 대체 포트)
    "http://localhost:5173",
    "https://admin-dashboard-production.up.railway.app",
    "https://admin.jusik.minhyuk.kr",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("✅ CORS 미들웨어 설정 완료")

# 라우터 임포트 및 등록
from routers import users, services, metrics, database, logs

app.include_router(users.router, prefix="/api/admin/users", tags=["Users"])
app.include_router(services.router, prefix="/api/admin/services", tags=["Services"])
app.include_router(metrics.router, prefix="/api/admin/metrics", tags=["Metrics"])
app.include_router(database.router, prefix="/api/admin/database", tags=["Database"])
app.include_router(logs.router, prefix="/api/admin/logs", tags=["Logs"])

print("✅ 모든 라우터 등록 완료")

# 헬스체크 엔드포인트
@app.get("/health")
async def health():
    """헬스 체크"""
    return {
        "status": "ok",
        "service": "admin-service",
        "version": "1.0.0",
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "local")
    }

# 루트 엔드포인트
@app.get("/")
async def root():
    """API 정보"""
    return {
        "message": "Admin Service API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }

print("=" * 60)
print("✅ Admin Service 초기화 완료")
print(f"📡 서버 시작: http://0.0.0.0:{os.getenv('PORT', '8000')}")
print("=" * 60)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True
    )
