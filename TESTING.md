# 통합 테스트 가이드

Admin Service와 Admin Dashboard의 통합 테스트 및 보안 검증 가이드입니다.

---

## 📋 테스트 환경 준비

### 1. 환경 변수 설정

#### Admin Service `.env` 파일 생성
```bash
cd /Users/dev/jusik/backend/admin-service
cat > .env << 'EOF'
SUPABASE_URL=https://lrmvoldeyetuzuwuazdm.supabase.co
SUPABASE_SERVICE_KEY=your_service_key_here
SENTRY_DSN=
RAILWAY_ENVIRONMENT=development
PORT=8000

# 다른 서비스 URL (로컬 또는 Railway)
STREAM_SERVICE_URL=https://stream-service-production.up.railway.app
NEWS_CRAWLER_URL=https://news-crawler-production.up.railway.app
AI_SERVICE_URL=https://ai-service-production.up.railway.app
REPORT_SERVICE_URL=https://report-service-production.up.railway.app
FRONTEND_URL=https://jusik.minhyuk.kr
EOF
```

#### Admin Dashboard `.env` 파일 생성
```bash
cd /Users/dev/jusik/admin-dashboard
cat > .env << 'EOF'
VITE_SUPABASE_URL=https://lrmvoldeyetuzuwuazdm.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here
VITE_ADMIN_API_URL=http://localhost:8000
EOF
```

### 2. 의존성 설치

#### Admin Service
```bash
cd /Users/dev/jusik/backend/admin-service
pip install -r requirements.txt
```

#### Admin Dashboard
```bash
cd /Users/dev/jusik/admin-dashboard
npm install
```

---

## 🚀 서비스 실행

### Terminal 1: Admin Service 실행
```bash
cd /Users/dev/jusik/backend/admin-service
python -m uvicorn main:app --reload --port 8000

# 예상 출력:
# ============================================================
# 🔐 Admin Service 초기화 시작...
# ============================================================
# ✅ .env 로드 완료
# ✅ Sentry 초기화 완료 (환경: development)
# ✅ CORS 미들웨어 설정 완료
# ✅ 모든 라우터 등록 완료
# ============================================================
# ✅ Admin Service 초기화 완료
# 📡 서버 시작: http://0.0.0.0:8000
# ============================================================
```

### Terminal 2: Admin Dashboard 실행
```bash
cd /Users/dev/jusik/admin-dashboard
npm run dev

# 예상 출력:
# VITE v6.0.7  ready in 1234 ms
#
# ➜  Local:   http://localhost:3001/
# ➜  Network: use --host to expose
```

---

## 🧪 Phase 5.1: 기능 테스트

### Test 1: 헬스 체크

```bash
# Admin Service 헬스 체크
curl http://localhost:8000/health

# 예상 응답:
{
  "status": "ok",
  "service": "admin-service",
  "version": "1.0.0",
  "environment": "development"
}
```

**✅ 통과 기준**: status = "ok"

---

### Test 2: API 문서 접근

브라우저에서 확인:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

**✅ 통과 기준**: 31개 엔드포인트 표시

---

### Test 3: CORS 설정 확인

```bash
# OPTIONS 요청 (Preflight)
curl -X OPTIONS http://localhost:8000/api/admin/users \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: GET" \
  -v

# 예상 응답 헤더:
# Access-Control-Allow-Origin: http://localhost:3001
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
# Access-Control-Allow-Credentials: true
```

**✅ 통과 기준**: Access-Control-Allow-Origin 헤더 존재

---

### Test 4: 인증 없이 접근 차단

```bash
# JWT 토큰 없이 사용자 목록 조회 시도
curl http://localhost:8000/api/admin/users

# 예상 응답:
{
  "detail": "인증 토큰이 없습니다. Authorization 헤더를 확인하세요."
}
```

**✅ 통과 기준**: 401 Unauthorized

---

### Test 5: Admin Dashboard 로그인

1. **브라우저 접속**: http://localhost:3001/login
2. **Admin 계정 로그인**: test@test.com (Supabase에서 admin으로 승격된 계정)
3. **로그인 성공 확인**: Dashboard로 리디렉션

**✅ 통과 기준**:
- 로그인 성공
- localStorage에 `supabase.auth.token` 저장
- Dashboard 페이지 표시

---

### Test 6: 권한 없는 사용자 차단

1. **일반 사용자 계정으로 로그인 시도** (role = 'user')
2. **예상 결과**: "관리자 권한이 필요합니다. 일반 사용자는 접근할 수 없습니다."

**✅ 통과 기준**: 403 Forbidden, 자동 로그아웃

---

## 🧪 Phase 5.2: CRUD 기능 테스트

### Test 7: 사용자 목록 조회

**Admin Dashboard에서**:
1. `/users` 페이지 접속
2. 사용자 목록 표시 확인
3. 검색 기능 테스트 (이메일/이름)
4. 역할 필터 테스트 (user/admin/superadmin)

**✅ 통과 기준**:
- 사용자 목록 로딩
- 검색/필터 작동
- 페이지네이션 표시

---

### Test 8: 사용자 정지/활성화

**Admin Dashboard에서**:
1. 사용자 선택 → 정지 버튼 클릭
2. 확인 다이얼로그 → 확인
3. 사용자 상태가 "정지"로 변경 확인
4. 활성화 버튼 클릭 → 상태가 "활성"으로 복원 확인

**Backend 로그 확인**:
```bash
# admin_activity_logs 테이블 확인
# 액션이 기록되었는지 확인
```

**✅ 통과 기준**:
- 상태 변경 성공
- UI 즉시 업데이트
- 활동 로그 기록

---

### Test 9: 서비스 모니터링

**Admin Dashboard에서**:
1. `/services` 페이지 접속
2. 5개 서비스 상태 표시 확인:
   - stream-service
   - news-crawler
   - ai-service
   - report-service
   - frontend
3. 각 서비스의 응답 시간 표시 확인
4. "새로고침" 버튼 클릭 → 상태 재확인

**✅ 통과 기준**:
- 서비스 헬스 체크 성공
- 응답 시간 표시
- 온라인/오프라인 상태 정확히 표시

---

### Test 10: 메트릭 조회

**Admin Dashboard에서**:
1. `/metrics` 페이지 접속
2. 시스템 메트릭 표시 확인 (서비스별 평균 지연)
3. 비즈니스 메트릭 표시 확인 (DAU, 레포트 수 등)
4. 시간 범위 필터 변경 (24시간 → 7일)

**✅ 통과 기준**:
- 메트릭 데이터 로딩
- 시간 범위 필터 작동
- 통계 카드 표시

---

### Test 11: 데이터베이스 통계

**Admin Dashboard에서**:
1. `/database` 페이지 접속
2. 12개 테이블 목록 표시 확인
3. 각 테이블의 행 수 확인
4. DB 헬스 체크 (응답 시간)

**✅ 통과 기준**:
- 테이블 통계 로딩
- 행 수 정확히 표시
- DB 응답 시간 < 500ms

---

### Test 12: 활동 로그 조회

**Admin Dashboard에서**:
1. `/logs` 페이지 접속
2. 관리자 활동 로그 표시 확인
3. 액션 필터 적용 (user_update 등)
4. 로그 내보내기 (JSON) 테스트

**✅ 통과 기준**:
- 로그 목록 표시
- 필터 작동
- JSON 다운로드 성공

---

## 🔒 Phase 5.3: 보안 테스트

### Test 13: SQL Injection 방지

```bash
# 악의적인 SQL 쿼리 시도 (JWT 토큰 필요)
curl -X POST http://localhost:8000/api/admin/database/query \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT * FROM users; DROP TABLE users;",
    "description": "SQL Injection Test"
  }'

# 예상 응답:
{
  "detail": "보안상 DROP 명령어는 허용되지 않습니다."
}
```

**✅ 통과 기준**: 403 Forbidden, 위험한 쿼리 차단

---

### Test 14: XSS 방지

**Admin Dashboard에서**:
1. 사용자 이름에 스크립트 입력 시도:
   ```html
   <script>alert('XSS')</script>
   ```
2. React가 자동으로 이스케이프 처리하는지 확인

**✅ 통과 기준**: 스크립트가 텍스트로 표시됨 (실행되지 않음)

---

### Test 15: JWT 토큰 검증

```bash
# 유효하지 않은 토큰으로 API 호출
curl http://localhost:8000/api/admin/users \
  -H "Authorization: Bearer invalid_token_here"

# 예상 응답:
{
  "detail": "유효하지 않은 토큰입니다."
}
```

**✅ 통과 기준**: 401 Unauthorized

---

### Test 16: 환경 변수 노출 확인

**Admin Dashboard에서**:
1. 브라우저 콘솔 → Sources 탭
2. 빌드된 JavaScript 파일 확인
3. `VITE_SUPABASE_ANON_KEY`는 노출되어도 안전 (Anon Key)
4. `SUPABASE_SERVICE_KEY`는 절대 노출 안 됨 (Backend만)

**✅ 통과 기준**: SERVICE_KEY가 프론트엔드 번들에 없음

---

## ⚡ Phase 5.4: 성능 테스트

### Test 17: API 응답 시간

```bash
# 사용자 목록 조회 응답 시간 측정
time curl -X GET http://localhost:8000/api/admin/users \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 예상: < 500ms
```

**✅ 통과 기준**: 응답 시간 < 1초

---

### Test 18: 동시 요청 처리

```bash
# Apache Bench로 부하 테스트 (100개 요청, 10개 동시)
ab -n 100 -c 10 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/admin/users

# 예상: 모든 요청 성공
```

**✅ 통과 기준**:
- 100% 성공률
- 평균 응답 시간 < 1초

---

### Test 19: 메모리 누수 확인

1. **Admin Dashboard 실행**
2. **브라우저 개발자 도구 → Performance → Memory**
3. **여러 페이지 이동 반복 (10회)**
4. **메모리 사용량 증가 확인**

**✅ 통과 기준**: 메모리 사용량이 급격히 증가하지 않음

---

### Test 20: React Query 캐싱 확인

**Admin Dashboard에서**:
1. `/services` 페이지 접속 (API 호출 발생)
2. 다른 페이지로 이동
3. 다시 `/services` 페이지로 돌아옴
4. **Network 탭 확인**: 캐시된 데이터 사용 (API 호출 없음)

**✅ 통과 기준**: 5분 이내 재방문 시 API 호출 없음 (Stale Time)

---

## 📊 Phase 5.5: 통합 시나리오 테스트

### Scenario 1: 신규 사용자 정지 플로우

1. **사용자 목록 조회** (`/users`)
2. **사용자 선택** → 정지
3. **활동 로그 확인** (`/logs`) → "user_suspend" 로그 생성 확인
4. **사용자 목록 재조회** → 상태가 "정지"로 변경

**✅ 통과 기준**: 전체 플로우 정상 작동

---

### Scenario 2: 서비스 모니터링 → 메트릭 분석

1. **서비스 모니터링** (`/services`) → 모든 서비스 온라인 확인
2. **메트릭 페이지** (`/metrics`) → 평균 응답 시간 확인
3. **시간 범위 변경** (24시간 → 7일) → 데이터 재로딩 확인

**✅ 통과 기준**: 페이지 간 데이터 일관성

---

### Scenario 3: 전체 시스템 모니터링

1. **Dashboard** (`/`) → 전체 통계 확인
2. **Services** → Railway 서비스 상태 확인
3. **Database** → 테이블 통계 확인
4. **Logs** → 최근 활동 로그 확인

**✅ 통과 기준**: 모든 데이터가 일관되게 표시

---

## ✅ 테스트 체크리스트

### 기능 테스트 (12개)
- [ ] Test 1: 헬스 체크
- [ ] Test 2: API 문서 접근
- [ ] Test 3: CORS 설정 확인
- [ ] Test 4: 인증 없이 접근 차단
- [ ] Test 5: Admin Dashboard 로그인
- [ ] Test 6: 권한 없는 사용자 차단
- [ ] Test 7: 사용자 목록 조회
- [ ] Test 8: 사용자 정지/활성화
- [ ] Test 9: 서비스 모니터링
- [ ] Test 10: 메트릭 조회
- [ ] Test 11: 데이터베이스 통계
- [ ] Test 12: 활동 로그 조회

### 보안 테스트 (4개)
- [ ] Test 13: SQL Injection 방지
- [ ] Test 14: XSS 방지
- [ ] Test 15: JWT 토큰 검증
- [ ] Test 16: 환경 변수 노출 확인

### 성능 테스트 (4개)
- [ ] Test 17: API 응답 시간
- [ ] Test 18: 동시 요청 처리
- [ ] Test 19: 메모리 누수 확인
- [ ] Test 20: React Query 캐싱 확인

### 통합 시나리오 (3개)
- [ ] Scenario 1: 신규 사용자 정지 플로우
- [ ] Scenario 2: 서비스 모니터링 → 메트릭 분석
- [ ] Scenario 3: 전체 시스템 모니터링

**총 23개 테스트 케이스**

---

## 🐛 알려진 이슈 및 제한사항

### 1. 커스텀 SQL 쿼리 실행

**현재 상태**: Supabase는 PostgREST를 통해서만 접근 가능하므로, 직접 SQL 실행이 제한됨.

**해결 방안**:
- Supabase Dashboard의 SQL Editor 사용
- 또는 PostgreSQL 직접 연결 (psycopg2) 추가

### 2. Railway API 연동

**현재 상태**: 서비스 재시작 기능이 플레이스홀더로 구현됨.

**해결 방안**:
- Railway GraphQL API 연동 필요
- `RAILWAY_TOKEN` 환경 변수 설정

### 3. 실시간 메트릭 수집

**현재 상태**: `system_metrics`, `business_metrics` 테이블이 비어있을 수 있음.

**해결 방안**:
- 각 서비스에서 메트릭 수집 코드 추가
- Admin Service API를 통해 수동으로 메트릭 생성

---

## 📝 테스트 결과 기록

### 테스트 실행 로그

```bash
# 테스트 시작 시간
echo "테스트 시작: $(date)" > test-results.log

# 각 테스트 결과 기록
echo "Test 1: ✅ PASS - 헬스 체크 성공" >> test-results.log
echo "Test 2: ✅ PASS - API 문서 접근 가능" >> test-results.log
# ...

# 테스트 종료
echo "테스트 종료: $(date)" >> test-results.log
echo "총 23개 테스트 중 23개 통과 (100%)" >> test-results.log
```

---

## 🚀 다음 단계

모든 테스트가 통과하면:

1. **Git에 커밋**:
   ```bash
   git add .
   git commit -m "test: Phase 5 통합 테스트 완료"
   git push origin main
   ```

2. **Railway 배포**:
   - DEPLOYMENT.md 참조
   - Admin Service 먼저 배포
   - Admin Dashboard 나중 배포

3. **프로덕션 검증**:
   - 배포된 URL에서 전체 테스트 재실행
   - 모니터링 설정 (Sentry, Railway Metrics)

---

**마지막 업데이트**: 2025-10-21
**테스트 환경**: Local Development
