# Admin Service API

관리자 전용 백엔드 서비스 - FastAPI 기반

## 📋 기능

### 1. 사용자 관리 (`/api/admin/users`)
- ✅ 전체 사용자 목록 조회 (페이지네이션, 검색, 역할 필터)
- ✅ 사용자 상세 정보 조회
- ✅ 사용자 정보 수정 (이름, 역할)
- ✅ 사용자 정지/활성화
- ✅ 사용자 삭제 (CASCADE)
- ✅ 사용자 활동 로그 조회

### 2. 서비스 모니터링 (`/api/admin/services`)
- ✅ Railway 서비스 목록 및 헬스체크
- ✅ 서비스 상세 정보 (로그, 메트릭, Uptime)
- ✅ 전체 시스템 헬스 집계
- ✅ 서비스 재시작 (Railway API)

### 3. 메트릭 조회 (`/api/admin/metrics`)
- ✅ 시스템 메트릭 (CPU, 메모리, API 지연, 에러율)
- ✅ 비즈니스 메트릭 (DAU, 레포트 생성 수, 뉴스 분석 수)
- ✅ 시계열 데이터 및 트렌드 분석
- ✅ 메트릭 요약 대시보드

### 4. 데이터베이스 관리 (`/api/admin/database`)
- ✅ 테이블 목록 및 통계
- ✅ 테이블 상세 정보 (컬럼, 샘플 데이터)
- ✅ 커스텀 SQL 쿼리 실행 (READ ONLY)
- ✅ 데이터베이스 헬스체크
- ✅ 전체 통계 조회

### 5. 로그 조회 (`/api/admin/logs`)
- ✅ 관리자 활동 로그 조회 (필터, 페이지네이션)
- ✅ 로그 통계 및 분석
- ✅ 로그 내보내기 (JSON, CSV)
- ✅ 오래된 로그 일괄 삭제

---

## 🚀 로컬 개발 환경 설정

### 1. 환경 변수 설정

`.env` 파일을 생성하고 다음 변수를 설정하세요:

```bash
cp .env.example .env
```

```env
SUPABASE_URL=https://lrmvoldeyetuzuwuazdm.supabase.co
SUPABASE_SERVICE_KEY=your_service_key_here
SENTRY_DSN=your_sentry_dsn_here
RAILWAY_ENVIRONMENT=development
PORT=8000
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 개발 서버 실행

```bash
# 기본 실행
python -m uvicorn main:app --reload --port 8000

# 또는 main.py 직접 실행
python main.py
```

서버가 실행되면 다음 URL에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 🧪 API 테스트

### 1. 관리자 계정 생성

먼저 Supabase에서 관리자 계정을 생성하고 `role`을 `admin` 또는 `superadmin`으로 설정해야 합니다:

```sql
-- test@test.com 계정을 admin으로 승격
UPDATE public.users
SET role = 'admin'
WHERE email = 'test@test.com';
```

### 2. JWT 토큰 발급

Frontend에서 로그인하거나, Supabase 콘솔에서 직접 JWT 토큰을 발급받으세요.

### 3. API 호출 예시

```bash
# 헬스체크
curl http://localhost:8000/health

# 사용자 목록 조회 (JWT 토큰 필요)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/api/admin/users

# 서비스 상태 조회
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/api/admin/services/health

# 데이터베이스 통계 조회
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/api/admin/database/statistics
```

---

## 🔐 인증 및 권한

### JWT 토큰 검증

모든 API 엔드포인트는 `Authorization: Bearer <token>` 헤더로 JWT 토큰을 전달받아야 합니다.

토큰은 다음 단계로 검증됩니다:

1. **Supabase Auth 검증**: `supabase.auth.get_user(token)`
2. **users 테이블 조회**: 사용자 정보 및 role 확인
3. **admin/superadmin 권한 확인**: role이 `admin` 또는 `superadmin`인지 확인

권한이 없으면 `403 Forbidden` 에러가 발생합니다.

### 활동 로그 자동 기록

모든 admin 작업은 자동으로 `admin_activity_logs` 테이블에 기록됩니다:

- 누가 (admin_id, admin_email)
- 무엇을 (action)
- 언제 (created_at)
- 어떤 대상에게 (target_type, target_id)
- 어떤 내용으로 (details jsonb)

---

## 📦 Railway 배포

### 1. Railway 프로젝트 생성

```bash
# Railway CLI 설치
npm install -g @railway/cli

# Railway 로그인
railway login

# 새 프로젝트 생성
railway init
```

### 2. 환경 변수 설정

Railway 대시보드에서 다음 환경 변수를 설정하세요:

```
SUPABASE_URL=https://lrmvoldeyetuzuwuazdm.supabase.co
SUPABASE_SERVICE_KEY=your_service_key_here
SENTRY_DSN=your_sentry_dsn_here
RAILWAY_ENVIRONMENT=production
PORT=8000
STREAM_SERVICE_URL=${{stream-service.url}}
NEWS_CRAWLER_URL=${{news-crawler.url}}
AI_SERVICE_URL=${{ai-service.url}}
REPORT_SERVICE_URL=${{report-service.url}}
```

### 3. 배포

```bash
# Git에 커밋
git add .
git commit -m "feat: Admin Service 구축 완료"
git push

# Railway 자동 배포 트리거
```

Railway는 자동으로 Python 환경을 감지하고 다음 명령을 실행합니다:

```bash
# Build
pip install -r requirements.txt

# Start
uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## 📁 프로젝트 구조

```
admin-service/
├── main.py                    # FastAPI 앱 진입점
├── requirements.txt           # Python 의존성
├── .env.example              # 환경 변수 예시
├── README.md                 # 이 문서
│
├── middleware/
│   └── auth.py               # JWT 인증 미들웨어
│
├── services/
│   └── supabase_client.py    # Supabase 클라이언트
│
└── routers/
    ├── users.py              # 사용자 관리 API
    ├── services.py           # 서비스 모니터링 API
    ├── metrics.py            # 메트릭 조회 API
    ├── database.py           # 데이터베이스 관리 API
    └── logs.py               # 로그 조회 API
```

---

## 🔧 개발 시 주의사항

### 1. Supabase Service Key 사용

Admin Service는 **Supabase Service Key**를 사용하여 RLS를 우회합니다.

⚠️  **보안**: Service Key는 절대 프론트엔드에 노출하지 마세요. 백엔드에서만 사용해야 합니다.

### 2. 활동 로그 기록 필수

모든 중요한 admin 작업 후에는 반드시 활동 로그를 기록하세요:

```python
supabase.table("admin_activity_logs").insert({
    "admin_id": admin["id"],
    "action": "user_update",
    "target_type": "user",
    "target_id": user_id,
    "details": {"updated_fields": ["name", "role"]}
}).execute()
```

### 3. 에러 처리

모든 엔드포인트는 적절한 HTTP 상태 코드와 에러 메시지를 반환해야 합니다:

- `400`: Bad Request (잘못된 입력)
- `401`: Unauthorized (인증 실패)
- `403`: Forbidden (권한 없음)
- `404`: Not Found (리소스 없음)
- `500`: Internal Server Error (서버 오류)

### 4. Pagination

대량의 데이터를 반환하는 엔드포인트는 반드시 페이지네이션을 구현하세요:

```python
@router.get("")
async def get_items(skip: int = 0, limit: int = 50):
    query = supabase.table("items").select("*").range(skip, skip + min(limit, 100) - 1)
    return query.execute().data
```

---

## 📊 모니터링

### Sentry 에러 추적

Sentry가 자동으로 모든 에러를 추적합니다:

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment=ENVIRONMENT,
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
    integrations=[FastApiIntegration()],
)
```

### 헬스체크 엔드포인트

Railway는 `/health` 엔드포인트를 주기적으로 호출하여 서비스 상태를 확인합니다:

```json
GET /health

{
  "status": "ok",
  "service": "admin-service",
  "version": "1.0.0",
  "environment": "production"
}
```

---

## 🎯 다음 단계

1. **Phase 3**: Admin Frontend 구축 (React + 8개 페이지)
2. **Phase 4**: Railway 배포 설정
3. **Phase 5**: 통합 테스트 및 보안 강화

---

**마지막 업데이트**: 2025-10-21
**개발자**: Trading Intelligence Platform Team
