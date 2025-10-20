# 🚂 Railway 배포 가이드

## 📋 현재 배포 상태

### 배포된 서비스 (6개)
1. **frontend** - React 프론트엔드
2. **stream-service** - WebSocket 실시간 시세
3. **news-crawler** - 뉴스 크롤링 서비스
4. **ai-service** - AI 분석 엔진
5. **report-service** - 종합 레포트 생성 API
6. **redis** - 캐싱 및 Pub/Sub

### 자동 배포 설정
- ✅ Git Push → Railway 자동 빌드 & 배포
- ✅ 각 서비스별 독립적인 환경 변수
- ✅ SSL 인증서 자동 제공

---

## 🔑 Railway 환경 변수 설정

### Report Service 환경 변수

#### 현재 설정된 변수 (9개)
```bash
ANTHROPIC_API_KEY=sk-ant-api...  # Claude API (실제 코드에서 사용)
KIS_APP_KEY=PSv...
KIS_APP_SECRET=v6l...
OPENAI_API_KEY=sk-proj-...
PORT=3000  # Railway 자동 설정
REDIS_URL=redis://...  # Railway Redis add-on
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_URL=https://lrmvoldeyetuzuwuazdm.supabase.co
USE_AI_ENSEMBLE=true
```

#### 추가 권장 변수 (선택적)
```bash
# Phase 2.1: 네이버 뉴스 API (Google News로 대체 가능)
NAVER_CLIENT_ID=YD_yXJJDefvDhROi14Tc
NAVER_CLIENT_SECRET=kjucl...

# Phase 2.3: DART 전자공시 (선택적)
DART_API_KEY=7de49de23f...

# AI 분석 활성화 (기본값: true)
AI_ANALYSIS_ENABLED=true

# CORS 설정 (프론트엔드 도메인)
ALLOWED_ORIGINS=https://your-frontend-domain.up.railway.app
```

---

## 🚀 배포 절차

### 1단계: 로컬 검증

```bash
cd /Users/dev/jusik/backend/report-service

# 환경 변수 확인
python3 verify_setup.py

# 예상 결과:
# ✅ 모든 검증 통과! (9/10) - Supabase 검증은 무시 가능
# ✅ KIS API 토큰 발급 성공
# ✅ OpenAI API 연결 성공
# ✅ Claude API 연결 성공
```

### 2단계: Git Commit & Push

```bash
cd /Users/dev/jusik

# 현재 브랜치 확인
git branch

# 변경사항 확인
git status

# 커밋 (이미 완료됨)
# git add -A
# git commit -m "feat: Phase 2.2, 2.3 + 검증 스크립트 완료"

# Railway에 푸시 (자동 배포 시작)
git push origin main
```

### 3단계: Railway 배포 모니터링

1. **Railway 대시보드 접속**: https://railway.app/dashboard
2. **report-service 프로젝트 선택**
3. **Deployments 탭 확인**
   - 빌드 로그 실시간 확인
   - 배포 상태: Building → Deploying → Active
4. **예상 빌드 시간**: 3~5분

### 4단계: 배포 후 검증

```bash
# Railway 배포 URL 확인 (예시)
RAILWAY_URL="https://report-service-production.up.railway.app"

# Health Check
curl $RAILWAY_URL/health

# API Docs
curl $RAILWAY_URL/docs

# 레포트 생성 테스트
curl -X POST $RAILWAY_URL/api/reports \
  -H "Content-Type: application/json" \
  -d '{"symbol":"005930","symbol_name":"삼성전자"}'
```

---

## 📊 배포 완료 후 확인 사항

### ✅ 필수 체크리스트

- [ ] Railway 빌드 성공 (Deployments 탭 확인)
- [ ] 서비스 Active 상태 (초록색 표시)
- [ ] Health Check API 응답 200 OK
- [ ] Logs에서 "FastAPI 앱 생성 완료" 메시지 확인
- [ ] 환경 변수 모두 설정됨 (Variables 탭)

### ✅ 기능 테스트

1. **레포트 생성 API**
   ```bash
   curl -X POST $RAILWAY_URL/api/reports \
     -H "Content-Type: application/json" \
     -d '{"symbol":"005930","symbol_name":"삼성전자"}'
   ```
   - 예상 응답 시간: 2~3분
   - 응답 크기: ~100KB JSON

2. **새로운 Phase 기능 확인**
   - Phase 5.1: 목표가 (conservative, neutral, aggressive)
   - Phase 5.2: 매매 신호 (signal, confidence, entry_timing)
   - Phase 2.2: 토론방 심리 (선택적, NAVER API 설정 시)
   - Phase 2.3: DART 공시 (선택적, DART API 설정 시)

---

## 🔍 트러블슈팅

### 1. 빌드 실패 (Build Failed)

**원인**: 의존성 설치 실패 또는 Python 버전 불일치

**해결**:
1. Railway 로그 확인
2. `requirements.txt` 확인
3. Python 버전 확인 (Python 3.10+ 권장)

```bash
# Railway에서 Python 버전 지정 (runtime.txt)
echo "python-3.11" > runtime.txt
git add runtime.txt
git commit -m "chore: Python 버전 명시"
git push origin main
```

### 2. 환경 변수 오류 (Environment Variable Error)

**원인**: 필수 환경 변수 누락

**해결**:
1. Railway 대시보드 → report-service → Variables 탭
2. 누락된 변수 추가:
   ```
   ANTHROPIC_API_KEY=sk-ant-api...
   SUPABASE_SERVICE_KEY=eyJ...
   ```
3. 서비스 재시작 (Redeploy)

### 3. API 호출 타임아웃 (Timeout)

**원인**: KIS API Rate Limit 또는 AI API 응답 지연

**해결**:
1. Logs에서 에러 확인
2. Rate Limit 확인 (KIS: 초당 20건)
3. AI API 크레딧 잔액 확인

### 4. Redis 연결 실패

**원인**: REDIS_URL 환경 변수 누락 또는 Redis 서비스 중단

**해결**:
1. Railway → Add-ons → Redis 상태 확인
2. `REDIS_URL` 환경 변수 재설정
3. Redis 서비스 재시작

---

## 📈 배포 후 모니터링

### Railway Metrics (자동 제공)
- CPU 사용률
- 메모리 사용량
- 네트워크 트래픽
- 응답 시간

### Logs 확인
```bash
# Railway CLI 설치 (선택)
npm install -g @railway/cli

# 로그인
railway login

# 로그 실시간 확인
railway logs
```

### 주요 모니터링 지표
- **API 응답 시간**: 평균 2~3분 (레포트 생성)
- **메모리 사용량**: 약 512MB~1GB
- **에러율**: 5% 미만 권장
- **KIS API 호출 횟수**: 레포트 1건당 약 15~20회

---

## 💰 비용 관리

### Railway 요금제
- **Hobby Plan**: $5/월 (무료 $5 크레딧 포함)
- **Pro Plan**: $20/월 (더 많은 리소스)

### 비용 최적화 팁
1. **캐싱 활용**: Redis로 레포트 24시간 캐싱
2. **Rate Limiting**: API 호출 제한 설정
3. **AI API 비용 관리**:
   - GPT-4: 레포트 1건당 $0.10~0.20
   - Claude: 레포트 1건당 $0.05~0.10
   - 월 100건 기준: $10~15

### 예상 월 비용
- Railway: $5 (Hobby Plan)
- AI API: $10~15 (100개 레포트)
- **총합**: **$15~20/월**

---

## 🔒 보안 체크리스트

### ✅ 필수 보안 설정

- [ ] 환경 변수로 API 키 관리 (코드에 하드코딩 금지)
- [ ] `.env` 파일 `.gitignore`에 포함
- [ ] CORS 설정 (허용된 도메인만 접근)
- [ ] RLS (Row Level Security) 활성화 (Supabase)
- [ ] API Rate Limiting 적용
- [ ] HTTPS 강제 (Railway 자동 제공)

### ⚠️ 주의사항

1. **API 키 노출 방지**
   - Git 커밋 전 `.env` 파일 확인
   - GitHub public 저장소 주의
   - 로그에 API 키 출력 금지

2. **정기적인 키 교체**
   - 3~6개월마다 API 키 재발급
   - 사용하지 않는 키 즉시 비활성화

3. **권한 최소화**
   - Supabase Service Key는 백엔드 전용
   - 프론트엔드는 Anon Key만 사용

---

## 📚 관련 문서

- **SETUP_GUIDE.md** - 전체 환경 설정 가이드
- **CLAUDE.md** - 프로젝트 아키텍처 및 개발 가이드
- **README.md** - 프로젝트 개요
- **verify_setup.py** - 자동 검증 스크립트

---

## 🎯 배포 성공 기준

### ✅ 배포 완료 조건

1. **빌드 성공**: Railway Deployments 탭에서 "Active" 상태
2. **Health Check 통과**: `/health` 엔드포인트 200 OK 응답
3. **레포트 생성 성공**: 삼성전자 테스트 레포트 정상 생성
4. **모든 Phase 기능 작동**:
   - Phase 1-5.2 모든 기능 포함된 레포트 생성
   - AI 앙상블 정상 작동
   - 목표가 및 매매 신호 출력

### ✅ 성능 기준

- API 응답 시간: 레포트 생성 2~3분 이내
- 에러율: 5% 미만
- 메모리 사용량: 1GB 이하
- CPU 사용률: 평균 50% 이하

---

## 🚀 다음 단계

배포 완료 후:

1. **프론트엔드 연동**
   - Frontend에 Railway URL 설정
   - API 호출 테스트

2. **성능 모니터링**
   - Railway Metrics 확인
   - 응답 시간 분석
   - 에러 로그 모니터링

3. **사용자 테스트**
   - 실제 종목 레포트 생성
   - 다양한 시나리오 테스트
   - 피드백 수집

4. **최적화**
   - 캐싱 전략 개선
   - AI 프롬프트 최적화
   - 비용 효율화

---

**마지막 업데이트**: 2025-01-21
**배포 상태**: 준비 완료 ✅
**다음 작업**: Git Push → 자동 배포 시작
