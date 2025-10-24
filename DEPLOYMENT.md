# Railway 배포 가이드

Admin Service (백엔드)와 Admin Dashboard (프론트엔드)를 Railway에 배포하는 단계별 가이드입니다.

---

## 📋 사전 준비

### 1. Railway 계정
- Railway 계정이 없다면 [railway.app](https://railway.app)에서 가입
- GitHub 계정 연동 권장

### 2. GitHub Repository
```bash
# 코드를 GitHub에 푸시
cd /Users/dev/jusik
git add .
git commit -m "feat: Admin Service 및 Dashboard 완성"
git push origin main
```

### 3. 필요한 환경 변수 준비
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY` (admin-service용)
- `SUPABASE_ANON_KEY` (admin-dashboard용)
- `SENTRY_DSN` (선택사항)

---

## 🚀 Phase 4.1: Admin Service 배포 (Backend)

### Step 1: Railway 프로젝트 생성

1. **Railway 대시보드** 접속: https://railway.app/dashboard
2. **"New Project"** 클릭
3. **"Deploy from GitHub repo"** 선택
4. **jusik** 저장소 선택

### Step 2: 서비스 설정

1. **Root Directory 설정**:
   - Settings → Root Directory: `backend/admin-service`
   - 저장

2. **환경 변수 설정**:
   - Settings → Variables 탭
   - 다음 환경 변수 추가:

```bash
# Supabase
SUPABASE_URL=https://lrmvoldeyetuzuwuazdm.supabase.co
SUPABASE_SERVICE_KEY=your_service_key_here

# Sentry (선택사항)
SENTRY_DSN=your_sentry_dsn_here

# Railway 자동 설정 (수동 설정 불필요)
RAILWAY_ENVIRONMENT=production
PORT=${{PORT}}

# 다른 서비스 URL (배포 후 업데이트)
STREAM_SERVICE_URL=https://stream-service-production.up.railway.app
NEWS_CRAWLER_URL=https://news-crawler-production.up.railway.app
AI_SERVICE_URL=https://ai-service-production.up.railway.app
REPORT_SERVICE_URL=https://report-service-production.up.railway.app
FRONTEND_URL=https://jusik.minhyuk.kr
```

### Step 3: 배포 트리거

1. **Deploy** 탭에서 **"Deploy"** 버튼 클릭
2. 빌드 로그 확인:
   ```
   ✓ Installing dependencies (pip install -r requirements.txt)
   ✓ Starting server (uvicorn main:app --host 0.0.0.0 --port $PORT)
   ✓ Health check passed (/health)
   ```

3. **배포 URL 확인**:
   - Settings → Domains
   - Railway 자동 생성 도메인: `https://admin-service-production.up.railway.app`

### Step 4: 헬스 체크 확인

```bash
# 배포된 서비스 헬스 체크
curl https://admin-service-production.up.railway.app/health

# 예상 응답:
{
  "status": "ok",
  "service": "admin-service",
  "version": "1.0.0",
  "environment": "production"
}
```

### Step 5: API 문서 확인

- **Swagger UI**: https://admin-service-production.up.railway.app/docs
- **ReDoc**: https://admin-service-production.up.railway.app/redoc

---

## 🎨 Phase 4.2: Admin Dashboard 배포 (Frontend)

### Step 1: 새 서비스 생성

1. **같은 Railway 프로젝트**에서 **"New Service"** 클릭
2. **"Deploy from GitHub repo"** 선택
3. **jusik** 저장소 선택

### Step 2: 서비스 설정

1. **Root Directory 설정**:
   - Settings → Root Directory: `admin-dashboard`
   - 저장

2. **환경 변수 설정**:
   - Settings → Variables 탭
   - 다음 환경 변수 추가:

```bash
# Supabase (VITE_ 접두사 필수!)
VITE_SUPABASE_URL=https://lrmvoldeyetuzuwuazdm.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here

# Admin Service API URL (Phase 4.1에서 배포된 URL)
VITE_ADMIN_API_URL=https://admin-service-production.up.railway.app

# Railway 자동 설정
PORT=${{PORT}}
```

### Step 3: 배포 트리거

1. **Deploy** 탭에서 **"Deploy"** 버튼 클릭
2. 빌드 로그 확인:
   ```
   ✓ Installing dependencies (npm ci)
   ✓ Building (npm run build)
   ✓ Starting preview server (npm run preview)
   ✓ Health check passed (/)
   ```

3. **배포 URL 확인**:
   - Settings → Domains
   - Railway 자동 생성 도메인: `https://admin-dashboard-production.up.railway.app`

### Step 4: 배포 확인

브라우저에서 접속:
```
https://admin-dashboard-production.up.railway.app
```

- ✅ 로그인 페이지 표시 확인
- ✅ Admin 계정으로 로그인 테스트
- ✅ 대시보드 데이터 로딩 확인

---

## 🌐 Phase 4.3: 커스텀 도메인 설정 (선택사항)

### Admin Service 도메인

1. **Railway Settings → Domains**
2. **"Add Custom Domain"** 클릭
3. 도메인 입력: `admin-api.jusik.minhyuk.kr`
4. **DNS 설정** (Cloudflare/가비아):
   ```
   Type: CNAME
   Name: admin-api
   Value: admin-service-production.up.railway.app
   TTL: Auto
   ```

### Admin Dashboard 도메인

1. **Railway Settings → Domains**
2. **"Add Custom Domain"** 클릭
3. 도메인 입력: `admin.jusik.minhyuk.kr`
4. **DNS 설정** (Cloudflare/가비아):
   ```
   Type: CNAME
   Name: admin
   Value: admin-dashboard-production.up.railway.app
   TTL: Auto
   ```

### SSL 인증서

- Railway가 자동으로 Let's Encrypt SSL 인증서 발급 (5~10분 소요)
- HTTPS 자동 활성화

---

## 🔄 Phase 4.4: 환경 변수 업데이트

### Admin Service 환경 변수 업데이트

커스텀 도메인 설정 후, Admin Service의 CORS 허용 도메인에 추가:

```python
# main.py - ALLOWED_ORIGINS
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://admin-dashboard-production.up.railway.app",
    "https://admin.jusik.minhyuk.kr",  # 커스텀 도메인 추가
]
```

변경 후 Git push → Railway 자동 재배포

### Admin Dashboard 환경 변수 업데이트

커스텀 도메인 사용 시, Railway 환경 변수 업데이트:

```bash
# Railway Dashboard → admin-dashboard → Variables
VITE_ADMIN_API_URL=https://admin-api.jusik.minhyuk.kr
```

---

## 🧪 Phase 4.5: 배포 검증

### 1. Admin Service 테스트

```bash
# 헬스 체크
curl https://admin-service-production.up.railway.app/health

# 사용자 목록 조회 (JWT 토큰 필요)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     https://admin-service-production.up.railway.app/api/admin/users

# 서비스 헬스 체크
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     https://admin-service-production.up.railway.app/api/admin/services/health
```

### 2. Admin Dashboard 테스트

1. **로그인 테스트**:
   - https://admin-dashboard-production.up.railway.app/login
   - test@test.com (또는 admin 계정) 로그인

2. **각 페이지 확인**:
   - [ ] 대시보드: 전체 통계 표시
   - [ ] 사용자 관리: 사용자 목록 로딩
   - [ ] 서비스 모니터링: Railway 서비스 상태
   - [ ] 메트릭: 시스템 메트릭 표시
   - [ ] 데이터베이스: 테이블 통계
   - [ ] 로그: 관리자 활동 로그
   - [ ] 설정: 프로필 정보

3. **API 연동 확인**:
   - 브라우저 개발자 도구 → Network 탭
   - API 호출이 `https://admin-service-production.up.railway.app`로 가는지 확인
   - 200 응답 코드 확인

### 3. CORS 확인

브라우저 콘솔에서 CORS 에러가 없는지 확인:
```
✓ No CORS errors
✓ All API requests return 200 OK
```

---

## 🔒 Phase 4.6: 보안 체크리스트

### Admin Service

- [ ] `SUPABASE_SERVICE_KEY`가 환경 변수로 설정됨 (코드에 하드코딩 안 됨)
- [ ] Sentry 에러 추적 활성화
- [ ] CORS가 필요한 도메인만 허용
- [ ] `/health` 엔드포인트만 Public, 나머지는 JWT 인증 필요
- [ ] Railway 로그에서 민감한 정보 노출 안 됨

### Admin Dashboard

- [ ] `VITE_SUPABASE_ANON_KEY` 사용 (SERVICE_KEY 아님!)
- [ ] 환경 변수가 `VITE_` 접두사로 시작
- [ ] 로그인하지 않은 사용자는 `/login`으로 리디렉션
- [ ] admin/superadmin이 아닌 사용자는 접근 거부
- [ ] JWT 토큰이 localStorage에 안전하게 저장

---

## 📊 Phase 4.7: 모니터링 설정

### Railway 대시보드

각 서비스의 **Metrics** 탭에서 모니터링:

- **CPU 사용률**: < 50% (정상)
- **메모리 사용률**: < 80% (정상)
- **네트워크**: 요청/응답 트래픽
- **헬스 체크**: 성공률 100%

### Sentry 에러 추적

1. **Sentry 프로젝트 생성**: https://sentry.io
2. **DSN 복사**
3. **Railway 환경 변수에 추가**:
   ```
   SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
   ```
4. **배포 후 에러 모니터링**

---

## 🚨 트러블슈팅

### 문제 1: Admin Service 빌드 실패

**증상**: `pip install` 실패

**해결**:
```bash
# requirements.txt 확인
cat backend/admin-service/requirements.txt

# Python 버전 확인 (runtime.txt)
cat backend/admin-service/runtime.txt
# → python-3.11.9
```

### 문제 2: Admin Dashboard 빌드 실패

**증상**: `npm run build` 실패

**해결**:
```bash
# 로컬에서 빌드 테스트
cd admin-dashboard
npm run build

# TypeScript 에러 확인
npm run lint
```

### 문제 3: CORS 에러

**증상**: 브라우저 콘솔에서 CORS 에러

**해결**:
```python
# backend/admin-service/main.py
ALLOWED_ORIGINS = [
    "https://admin-dashboard-production.up.railway.app",  # 추가
    "https://admin.jusik.minhyuk.kr",  # 커스텀 도메인 추가
]
```

### 문제 4: 환경 변수 누락

**증상**: `RuntimeError: 환경 변수가 설정되지 않았습니다`

**해결**:
1. Railway Dashboard → Variables 탭
2. 필요한 모든 환경 변수 추가
3. Redeploy

### 문제 5: 헬스 체크 실패

**증상**: Railway가 서비스를 "Unhealthy"로 표시

**해결**:
```bash
# 헬스 체크 엔드포인트 확인
curl https://your-service.up.railway.app/health

# 로그 확인
# Railway Dashboard → Logs
```

---

## 📝 배포 체크리스트

### Admin Service ✅

- [ ] Railway 프로젝트 생성
- [ ] Root Directory: `backend/admin-service`
- [ ] 환경 변수 설정 (SUPABASE_URL, SUPABASE_SERVICE_KEY)
- [ ] 배포 성공
- [ ] `/health` 엔드포인트 응답 확인
- [ ] `/docs` API 문서 접근 가능
- [ ] CORS 설정 확인

### Admin Dashboard ✅

- [ ] Railway 서비스 생성
- [ ] Root Directory: `admin-dashboard`
- [ ] 환경 변수 설정 (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_ADMIN_API_URL)
- [ ] 배포 성공
- [ ] 로그인 페이지 접근 가능
- [ ] Admin 로그인 테스트 성공
- [ ] 모든 페이지 정상 작동

### 통합 테스트 ✅

- [ ] Dashboard: 전체 통계 표시
- [ ] Users: 사용자 목록 로딩
- [ ] Services: Railway 서비스 상태 표시
- [ ] Metrics: 메트릭 데이터 표시
- [ ] Database: 테이블 통계 표시
- [ ] Logs: 활동 로그 표시
- [ ] CORS 에러 없음
- [ ] API 호출 200 응답

---

## 🎉 배포 완료!

축하합니다! Admin Service와 Admin Dashboard가 Railway에 성공적으로 배포되었습니다.

### 배포된 URL

- **Admin Service API**: https://admin-service-production.up.railway.app
- **Admin Dashboard**: https://admin-dashboard-production.up.railway.app
- **API 문서**: https://admin-service-production.up.railway.app/docs

### 다음 단계

**Phase 5**: 통합 테스트 및 보안 강화
- 전체 시스템 통합 테스트
- 보안 취약점 점검
- 성능 최적화
- 모니터링 설정

---

**마지막 업데이트**: 2025-10-21
**배포 플랫폼**: Railway
