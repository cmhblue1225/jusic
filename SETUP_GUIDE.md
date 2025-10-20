# 🚀 Trading Intelligence Platform - 설정 가이드

## 📋 목차
1. [필수 환경 변수](#필수-환경-변수)
2. [선택적 환경 변수](#선택적-환경-변수)
3. [API 키 발급 방법](#api-키-발급-방법)
4. [서비스별 설정](#서비스별-설정)
5. [검증 및 테스트](#검증-및-테스트)

---

## 필수 환경 변수

### 1. Supabase 설정

```bash
# Supabase 프로젝트 정보
SUPABASE_URL=https://lrmvoldeyetuzuwuazdm.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_KEY=your_supabase_service_key_here
```

**발급 방법**:
1. Supabase 대시보드 접속: https://supabase.com/dashboard
2. 프로젝트 선택: `jusik` (lrmvoldeyetuzuwuazdm)
3. Settings → API → Project API keys
4. `anon` `public` 키 복사 → `SUPABASE_ANON_KEY`
5. `service_role` `secret` 키 복사 → `SUPABASE_SERVICE_KEY`

---

### 2. 한국투자증권 (KIS) API 설정

```bash
# KIS Open API
KIS_APP_KEY=your_kis_app_key_here
KIS_APP_SECRET=your_kis_app_secret_here
KIS_ACCOUNT_NO=your_account_number_here  # 선택적 (실제 거래 시)
```

**발급 방법**:
1. 한국투자증권 홈페이지: https://securities.koreainvestment.com/
2. [트레이딩] → [Open API] 메뉴
3. API 서비스 신청 (무료)
4. App Key, App Secret 발급
5. **주의**: 실전투자계좌와 모의투자계좌 API 키가 다릅니다

**Rate Limit**:
- 실전투자: **초당 20건**
- 모의투자: **초당 5건**

---

### 3. AI API 설정 (GPT-4 + Claude)

```bash
# OpenAI API (GPT-4)
OPENAI_API_KEY=sk-your_openai_api_key_here

# Claude API (Anthropic)
CLAUDE_API_KEY=sk-ant-your_claude_api_key_here
```

**발급 방법**:

#### OpenAI (GPT-4)
1. https://platform.openai.com/api-keys
2. "Create new secret key" 클릭
3. API 키 복사 (한 번만 표시됨!)
4. **요금**: 사용량 기반 과금 (GPT-4: $0.03/1K tokens)

#### Claude (Anthropic)
1. https://console.anthropic.com/settings/keys
2. "Create Key" 클릭
3. API 키 복사
4. **요금**: 사용량 기반 과금 (Claude Sonnet: $3/MTok input, $15/MTok output)

**우선순위**:
- AI 앙상블 모드에서는 **GPT-4 우선**, 실패 시 Claude 사용
- 환경 변수로 우선순위 변경 가능

---

## 선택적 환경 변수

### 1. 네이버 뉴스 API (Phase 2.1)

```bash
# 네이버 검색 API
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
```

**발급 방법**:
1. https://developers.naver.com/apps/#/register
2. 애플리케이션 등록 (검색 API 선택)
3. Client ID, Client Secret 복사
4. **무료**: 하루 **25,000건** 제한

**참고**: 네이버 API 없이도 Google News RSS로 뉴스 수집 가능

---

### 2. DART 전자공시 API (Phase 2.3)

```bash
# DART Open API
DART_API_KEY=your_dart_api_key_here
```

**발급 방법**:
1. https://opendart.fss.or.kr/
2. 인증키 신청/관리 메뉴
3. 개인정보 입력 후 신청
4. 이메일로 API 키 수신 (1~2일 소요)
5. **무료**: 제한 없음

**기능**:
- 상장기업 전자공시 조회
- 공시 중요도 자동 분류
- 긴급 공시 알림

---

### 3. 기타 설정

```bash
# AI 분석 활성화 (기본: true)
AI_ANALYSIS_ENABLED=true

# AI 앙상블 모드 (기본: true)
USE_AI_ENSEMBLE=true

# 허용된 도메인 (CORS)
ALLOWED_ORIGINS=http://localhost:5173,https://your-frontend-domain.com

# 서비스 URL
AI_SERVICE_URL=http://localhost:3003
NEWS_CRAWLER_URL=http://localhost:3002
STREAM_SERVICE_URL=http://localhost:3001

# Railway 배포 환경
RAILWAY_ENVIRONMENT=production  # 자동 설정됨
```

---

## 서비스별 설정

### 1. Report Service (Port 3000)

**위치**: `/Users/dev/jusik/backend/report-service`

**필수 환경 변수**:
```bash
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
KIS_APP_KEY=...
KIS_APP_SECRET=...
OPENAI_API_KEY=...
CLAUDE_API_KEY=...
```

**실행**:
```bash
cd backend/report-service
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 3000
```

**검증 URL**:
- Health Check: http://localhost:3000/health
- API Docs: http://localhost:3000/docs

---

### 2. News Crawler Service (Port 3002)

**위치**: `/Users/dev/jusik/backend/news-crawler`

**필수 환경 변수**:
```bash
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
AI_SERVICE_URL=http://localhost:3003
```

**선택적 환경 변수**:
```bash
NAVER_CLIENT_ID=...  # Phase 2.1
NAVER_CLIENT_SECRET=...  # Phase 2.1
DART_API_KEY=...  # Phase 2.3
```

**실행**:
```bash
cd backend/news-crawler
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 3002
```

**검증**:
```bash
# 네이버 토론방 크롤링 테스트
python naver_discussion_crawler.py

# DART 전자공시 크롤링 테스트
python dart_disclosure_crawler.py
```

---

### 3. AI Service (Port 3003)

**위치**: `/Users/dev/jusik/backend/ai-service`

**필수 환경 변수**:
```bash
OPENAI_API_KEY=...
CLAUDE_API_KEY=...
```

**실행**:
```bash
cd backend/ai-service
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 3003
```

**검증 URL**:
- Health Check: http://localhost:3003/health
- API Docs: http://localhost:3003/docs

---

### 4. Stream Service (Port 3001)

**위치**: `/Users/dev/jusik/backend/stream-service`

**필수 환경 변수**:
```bash
KIS_APP_KEY=...
KIS_APP_SECRET=...
```

**실행**:
```bash
cd backend/stream-service
npm install
npm run dev
```

**검증 URL**:
- WebSocket: ws://localhost:3001
- Health Check: http://localhost:3001/health

---

## 환경 변수 설정 방법

### 방법 1: .env 파일 (권장)

각 서비스 디렉토리에 `.env` 파일 생성:

```bash
# backend/report-service/.env
SUPABASE_URL=https://lrmvoldeyetuzuwuazdm.supabase.co
SUPABASE_SERVICE_KEY=your_key_here
KIS_APP_KEY=your_key_here
KIS_APP_SECRET=your_secret_here
OPENAI_API_KEY=sk-your_key_here
CLAUDE_API_KEY=sk-ant-your_key_here
```

### 방법 2: 시스템 환경 변수

```bash
# macOS/Linux (.zshrc 또는 .bashrc)
export SUPABASE_URL="https://lrmvoldeyetuzuwuazdm.supabase.co"
export KIS_APP_KEY="your_key_here"
# ... 나머지 변수

# 적용
source ~/.zshrc
```

### 방법 3: Railway 배포 환경

Railway 대시보드에서 설정:
1. 프로젝트 선택
2. Variables 탭
3. 환경 변수 추가

---

## 검증 및 테스트

### 1. 환경 변수 확인

```bash
# Python 서비스
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('SUPABASE_URL:', os.getenv('SUPABASE_URL')[:30]+'...')"

# Node.js 서비스
node -e "require('dotenv').config(); console.log('KIS_APP_KEY:', process.env.KIS_APP_KEY.substring(0, 20)+'...')"
```

### 2. API 키 유효성 검증

#### KIS API 토큰 발급 테스트
```bash
cd backend/report-service
python -c "
from kis_data import KISDataAPI
import asyncio

async def test():
    api = KISDataAPI()
    token = await api.get_access_token()
    print('✅ KIS API 토큰 발급 성공:', token[:30]+'...')

asyncio.run(test())
"
```

#### OpenAI API 테스트
```bash
python -c "
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

response = client.chat.completions.create(
    model='gpt-4',
    messages=[{'role': 'user', 'content': 'Hello'}],
    max_tokens=10
)
print('✅ OpenAI API 연결 성공:', response.choices[0].message.content)
"
```

#### Claude API 테스트
```bash
python -c "
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))

response = client.messages.create(
    model='claude-3-5-sonnet-20241022',
    max_tokens=10,
    messages=[{'role': 'user', 'content': 'Hello'}]
)
print('✅ Claude API 연결 성공:', response.content[0].text)
"
```

### 3. 통합 테스트

#### Report Service 종합 테스트
```bash
cd backend/report-service

# 서비스 시작
python -m uvicorn main:app --reload --port 3000 &

# API 테스트
sleep 5
curl -X POST http://localhost:3000/api/reports \
  -H "Content-Type: application/json" \
  -d '{"symbol":"005930","symbol_name":"삼성전자"}'

# 예상 결과: JSON 레포트 (2-3분 소요)
```

#### News Crawler 테스트
```bash
cd backend/news-crawler

# 네이버 토론방 크롤링
python naver_discussion_crawler.py

# DART 공시 크롤링 (API 키 필요)
python dart_disclosure_crawler.py

# 예상 결과: 크롤링된 데이터 출력
```

---

## 트러블슈팅

### 1. "No module named 'dotenv'" 에러
```bash
pip install python-dotenv
```

### 2. "SUPABASE_URL not found" 에러
- `.env` 파일이 서비스 디렉토리에 있는지 확인
- `.env` 파일 첫 줄이 주석이 아닌지 확인
- 환경 변수 이름 오타 확인

### 3. KIS API "접근토큰 발급 잠시 후 다시 시도" 에러
- **원인**: Rate limit (1분당 1회)
- **해결**: `.kis-token-cache.json` 파일 사용 (자동 캐싱)
- 토큰 만료 시간: 24시간

### 4. OpenAI/Claude API "Authentication failed" 에러
- API 키 형식 확인:
  - OpenAI: `sk-...` (51자)
  - Claude: `sk-ant-...` (108자)
- 키 복사 시 공백/줄바꿈 포함 여부 확인
- 계정 크레딧 잔액 확인

### 5. DART API "인증키가 유효하지 않습니다" 에러
- API 키 발급 완료 여부 확인 (1~2일 소요)
- 키 활성화 상태 확인 (DART 홈페이지)

---

## 보안 주의사항

### ⚠️ 절대 하지 말 것
1. **API 키를 Git에 커밋하지 마세요**
   - `.env` 파일은 `.gitignore`에 포함되어 있음
   - 실수로 커밋한 경우 즉시 키 재발급

2. **공개 저장소에 키 노출 금지**
   - GitHub, GitLab 등 public 저장소 주의
   - 코드 리뷰 시 키 노출 여부 확인

3. **프론트엔드에 Service Key 사용 금지**
   - `SUPABASE_ANON_KEY`만 프론트엔드에서 사용
   - `SUPABASE_SERVICE_KEY`는 백엔드 전용

### ✅ 권장 사항
1. API 키는 환경 변수로만 관리
2. `.env.example` 파일로 템플릿 제공
3. 정기적으로 API 키 교체 (3~6개월)
4. 사용하지 않는 API 키는 즉시 비활성화

---

## 비용 예상

### 무료 티어
- ✅ Supabase: 무료 (프로젝트 2개, DB 500MB)
- ✅ DART API: 완전 무료
- ✅ KIS API: 무료 (모의투자)
- ⚠️ 네이버 API: 하루 25,000건 (초과 시 유료)

### 유료 서비스 (사용량 기반)
- **OpenAI GPT-4**: $0.03/1K input tokens, $0.06/1K output tokens
  - 레포트 1건당 약 $0.10~0.20
  - 월 100건 기준: **$10~20**

- **Claude Sonnet**: $3/MTok input, $15/MTok output
  - 레포트 1건당 약 $0.05~0.10
  - 월 100건 기준: **$5~10**

- **Railway (배포)**: $5/월 (Hobby plan)
  - 무료 $5 크레딧 제공

**월 예상 비용**: **$10~25** (100개 레포트 기준)

---

## 다음 단계

환경 변수 설정이 완료되면:

1. ✅ **서비스 시작**
   ```bash
   # Terminal 1: Report Service
   cd backend/report-service && python -m uvicorn main:app --reload --port 3000

   # Terminal 2: AI Service
   cd backend/ai-service && python -m uvicorn main:app --reload --port 3003

   # Terminal 3: News Crawler
   cd backend/news-crawler && python -m uvicorn main:app --reload --port 3002
   ```

2. ✅ **API 테스트**
   ```bash
   # Report 생성
   curl -X POST http://localhost:3000/api/reports \
     -H "Content-Type: application/json" \
     -d '{"symbol":"005930","symbol_name":"삼성전자"}'
   ```

3. ✅ **결과 확인**
   - 레포트 생성 시간: 2~3분
   - 포함 데이터:
     - 기본 정보 (주가, 재무, 투자자 동향)
     - 기술적 지표 22개
     - AI 분석 (GPT-4 + Claude 앙상블)
     - 뉴스 분석 (7일 50개)
     - 업종 상대 평가
     - 시장 전체 맥락
     - 목표가 (보수적/중립적/공격적)
     - 매매 타이밍 신호

4. ✅ **프론트엔드 연동**
   - Frontend 프로젝트에 API URL 설정
   - 레포트 조회 UI 구현

---

**📞 문제 발생 시**: GitHub Issues에 등록하거나 CLAUDE.md 참조

**마지막 업데이트**: 2025-01-21
