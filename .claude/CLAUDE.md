# 📈 실시간 트레이딩 인텔리전스 플랫폼 (Trading Intelligence Platform)

## 📍 현재 프로젝트 위치
- **경로**: `/Users/dev/jusik`
- **프로젝트명**: Trading Intelligence Platform (TIP)
- **시작일**: 2025-10-18
- **개발 환경**: MacBook Pro M4 Pro (14-core CPU, 20-core GPU)
- **Supabase 프로젝트**: `lrmvoldeyetuzuwuazdm` (jusik)
- **리전**: ap-northeast-2 (서울)
- **프로젝트 URL**: https://lrmvoldeyetuzuwuazdm.supabase.co
- **프로젝트 상태**: ✅ ACTIVE_HEALTHY

---

## 🎯 프로젝트 개요

### 비전
한국 주식 시장을 대상으로 하는 **실시간 반응형 트레이딩 인텔리전스 플랫폼**으로, 초단타/단타 트레이더가 보유 종목과 관련된 실시간 시세, 뉴스, 경제/정책 이벤트를 즉시 인지하고 AI 기반 분석을 통해 빠르게 의사결정할 수 있도록 지원합니다.

### 핵심 목표
1. **1초 이내 시세 업데이트**: HFT 트레이더를 위한 초저지연 실시간 데이터
2. **AI 기반 뉴스 분석**: 요약 → 감성 분석 → 영향도 평가 → 행동 권고 자동 생성
3. **시니어 친화적 UX**: 50~60대 사용자를 위한 TTS, 큰 글꼴, 고대비 UI
4. **실시간 알림**: 웹 푸시 + 음성 알림으로 중요 이벤트 즉시 전달

---

## 🏗️ 시스템 아키텍처

### 기술 스택

#### 프론트엔드
- **Framework**: React 19 + TypeScript + Vite
- **스타일링**: TailwindCSS (시니어 친화 디자인)
- **상태 관리**: Zustand (전역 상태) + React Query (서버 상태)
- **실시간 통신**: Socket.IO Client / WebSocket
- **차트**: Recharts / Lightweight Charts
- **TTS**: Web Speech API (SpeechSynthesis)
- **배포**: Netlify

#### 백엔드 (마이크로서비스)
```
backend/
├── stream-service/      # Node.js - 실시간 주가 스트리밍
├── news-crawler/        # Python - RSS/API 뉴스 크롤링
├── ai-service/          # Python FastAPI - AI 분석 엔진
└── alert-service/       # Node.js - 알림 발송 시스템
```

**주요 기술**:
- Node.js (Express.js) - Stream/Alert 서비스
- Python (FastAPI) - News Crawler, AI Service
- Redis - Pub/Sub, 캐싱
- Socket.IO - WebSocket 서버
- APScheduler - 뉴스 크롤링 스케줄러
- 배포: Railway

#### 데이터베이스 & 인프라
- **DB**: Supabase (PostgreSQL + Realtime + Auth + Storage)
- **인증**: Supabase Auth (JWT)
- **캐싱**: Redis (Railway add-on)
- **AI**: Claude API (우선) + OpenAI API (폴백)
- **시세 데이터**: 한국투자증권 Open API
  - REST API: 현재가, 호가, 체결가 조회
  - WebSocket: 실시간 시세 (향후 구현)
  - Rate Limit: 초당 20건 (실전투자), 5건 (모의투자)
- **푸시 알림**: FCM (Firebase Cloud Messaging)

### 시스템 플로우
```
[사용자]
   ↓
[Frontend - React (Netlify)]
   ↓ WebSocket
[Stream Service] ← 한국투자증권 API (실시간 시세)
   ↓ Redis Pub/Sub
[Backend Services (Railway)]
   ├─ News Crawler → AI Service (Claude/OpenAI)
   └─ Alert Service → FCM / Web Push
   ↓
[Supabase DB - lrmvoldeyetuzuwuazdm]
   ├─ users, portfolios, watchlist
   ├─ news, alerts, stock_prices
   └─ events_log
```

---

## 📊 데이터베이스 스키마 (Supabase PostgreSQL)

### 핵심 테이블 (11개)

#### 1. users (사용자)
```sql
CREATE TABLE users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text UNIQUE NOT NULL,
  name text,
  settings jsonb DEFAULT '{}',  -- TTS 설정, 알림 임계값 등
  created_at timestamptz DEFAULT now()
);
```

#### 2. portfolios (보유 종목)
```sql
CREATE TABLE portfolios (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES users(id) ON DELETE CASCADE,
  symbol text NOT NULL,           -- 종목 코드 (예: 005930)
  avg_price numeric NOT NULL,     -- 평균 단가
  qty numeric NOT NULL,            -- 수량
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);
```

#### 3. watchlist (관심 종목)
```sql
CREATE TABLE watchlist (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES users(id) ON DELETE CASCADE,
  symbol text NOT NULL,
  created_at timestamptz DEFAULT now(),
  UNIQUE(user_id, symbol)
);
```

#### 4. news (뉴스)
```sql
CREATE TABLE news (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source text NOT NULL,           -- 뉴스 출처 (Naver, Yonhap 등)
  title text NOT NULL,
  content text,
  published_at timestamptz NOT NULL,
  summary text,                   -- AI 요약
  sentiment_score numeric,        -- 감성 점수 (-1 ~ 1)
  impact_score numeric,           -- 영향도 (0 ~ 1)
  recommended_action text,        -- 매수/매도/관망
  related_symbols text[],         -- 관련 종목 코드 배열
  created_at timestamptz DEFAULT now()
);
```

#### 5. alerts (알림)
```sql
CREATE TABLE alerts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES users(id) ON DELETE CASCADE,
  type text NOT NULL,             -- price_change, news, system
  title text NOT NULL,
  message text NOT NULL,
  params jsonb,                   -- 추가 메타데이터
  status text DEFAULT 'unread',  -- unread, read, archived
  created_at timestamptz DEFAULT now()
);
```

#### 6. stock_prices (주가 데이터)
```sql
CREATE TABLE stock_prices (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol text NOT NULL,
  price numeric NOT NULL,
  change_rate numeric,            -- 등락률 (%)
  volume bigint,                  -- 거래량
  timestamp timestamptz DEFAULT now(),
  INDEX idx_symbol_timestamp (symbol, timestamp DESC)
);
```

#### 7. alert_rules (알림 규칙)
```sql
CREATE TABLE alert_rules (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES users(id) ON DELETE CASCADE,
  rule_type text NOT NULL,        -- price_threshold, volume_spike, news_impact
  conditions jsonb NOT NULL,      -- {symbol: "005930", threshold: 3.0}
  is_active boolean DEFAULT true,
  created_at timestamptz DEFAULT now()
);
```

#### 8. news_keywords (뉴스 키워드 매핑)
```sql
CREATE TABLE news_keywords (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol text NOT NULL,
  keywords text[] NOT NULL,       -- ["삼성전자", "갤럭시", "반도체"]
  created_at timestamptz DEFAULT now()
);
```

#### 9. events_log (시스템 이벤트 로그)
```sql
CREATE TABLE events_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  service text NOT NULL,          -- stream, news, ai, alert
  event_type text NOT NULL,
  payload jsonb,
  created_at timestamptz DEFAULT now()
);
```

#### 10. backtest_results (백테스트 결과)
```sql
CREATE TABLE backtest_results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES users(id) ON DELETE CASCADE,
  strategy_name text NOT NULL,
  params jsonb,
  results jsonb,                  -- {cagr: 0.25, mdd: -0.15, ...}
  created_at timestamptz DEFAULT now()
);
```

#### 11. user_sessions (세션 관리)
```sql
CREATE TABLE user_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES users(id) ON DELETE CASCADE,
  refresh_token text,
  expires_at timestamptz,
  created_at timestamptz DEFAULT now()
);
```

---

## 🔐 보안 및 RLS 정책

### Supabase RLS (Row Level Security)
```sql
-- 사용자는 자신의 데이터만 조회/수정
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their own portfolios"
  ON portfolios FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own portfolios"
  ON portfolios FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- 뉴스는 모든 사용자가 조회 가능
ALTER TABLE news ENABLE ROW LEVEL SECURITY;
CREATE POLICY "News are viewable by everyone"
  ON news FOR SELECT
  USING (true);
```

---

## 🎨 접근성 (Accessibility) 가이드라인

### 시니어 친화 UI/UX 원칙
1. **큰 글꼴**: 기본 18px 이상, 헤더 24px 이상
2. **큰 버튼**: 최소 48x48px (터치 친화적)
3. **고대비 모드**: WCAG AA 준수 (명도비 ≥ 4.5:1)
4. **색상 보조**: 색상만으로 의미 전달 금지 (아이콘/텍스트 병행)
5. **단순한 레이아웃**: 한 화면에 핵심 정보만 노출

### TTS (텍스트 음성 변환)
```javascript
// Web Speech API 사용 예시
const speak = (text) => {
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'ko-KR';
  utterance.rate = 0.9;  // 음성 속도
  utterance.pitch = 1.0; // 음성 높이
  window.speechSynthesis.speak(utterance);
};

// 중요 알림 자동 읽기
if (alert.impact_score >= 0.8 && userSettings.autoTTS) {
  speak(`중요 알림: ${alert.message}`);
}
```

### 음성 알림 설정 옵션
- 자동 읽기 임계값: impact_score ≥ 0.8
- 음성 속도: 0.8 ~ 1.2
- 음성 볼륨: 0.5 ~ 1.0
- 수동 재생: 각 뉴스 카드에 "듣기" 버튼

---

## ⚡ 개발 우선순위 (4단계)

### Phase 1: 인증 및 포트폴리오 관리 ✅
- Supabase Auth 연동 (이메일/비밀번호)
- 사용자 프로필 관리
- 보유 종목 등록/수정/삭제
- 관심 종목(Watchlist) 관리
- 수익률 계산 로직

### Phase 2: 실시간 시세 스트리밍 🔄
- WebSocket 서버 구축 (Socket.IO)
- 증권사 API 연동 (eBest/키움)
- Redis Pub/Sub 아키텍처
- 실시간 미니차트 (1분봉, 5분봉)
- 호가/체결 데이터 표시

### Phase 3: 뉴스 크롤링 + AI 분석 🔄
- RSS/API 크롤러 (Naver, Yonhap, Google News)
- NER (종목명 추출) 파이프라인
- Claude API 연동 (요약, 감성, 권고)
- OpenAI API 폴백 로직
- 뉴스-종목 매핑 자동화

### Phase 4: 알림 시스템 + TTS 🔄
- 알림 규칙 엔진 (룰 기반 + AI 점수)
- Web Push Notification API
- FCM 연동 (모바일 앱 준비)
- TTS 자동/수동 재생
- 알림 히스토리 관리

---

## 📁 프로젝트 디렉토리 구조

```
jusik/
├── .claude/
│   └── CLAUDE.md                 # 이 파일
├── frontend/                     # React 앱
│   ├── src/
│   │   ├── components/          # 재사용 컴포넌트
│   │   │   ├── common/          # 버튼, 카드, 모달 등
│   │   │   ├── charts/          # 주가 차트
│   │   │   ├── news/            # 뉴스 카드
│   │   │   └── tts/             # TTS 컨트롤러
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx   # 메인 대시보드
│   │   │   ├── Portfolio.tsx   # 포트폴리오 관리
│   │   │   ├── StockDetail.tsx # 종목 상세
│   │   │   ├── News.tsx         # 뉴스 피드
│   │   │   ├── Alerts.tsx       # 알림 센터
│   │   │   └── Settings.tsx     # 설정 (TTS, 접근성)
│   │   ├── stores/              # Zustand 상태
│   │   ├── lib/
│   │   │   ├── supabase.ts      # Supabase 클라이언트
│   │   │   ├── socket.ts        # WebSocket 클라이언트
│   │   │   └── tts.ts           # TTS 유틸리티
│   │   └── types/               # TypeScript 타입
│   ├── public/
│   └── package.json
├── backend/
│   ├── stream-service/          # Node.js
│   │   ├── src/
│   │   │   ├── server.ts
│   │   │   ├── websocket.ts
│   │   │   └── api-client.ts    # 증권사 API
│   │   └── package.json
│   ├── news-crawler/            # Python
│   │   ├── main.py
│   │   ├── crawlers/
│   │   │   ├── naver.py
│   │   │   └── yonhap.py
│   │   ├── nlp/
│   │   │   └── ner.py           # 종목명 추출
│   │   └── requirements.txt
│   ├── ai-service/              # Python FastAPI
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── claude.py
│   │   │   └── openai.py
│   │   ├── models/
│   │   │   └── analysis.py      # 분석 모델
│   │   └── requirements.txt
│   └── alert-service/           # Node.js
│       ├── src/
│       │   ├── server.ts
│       │   ├── rules-engine.ts
│       │   └── push.ts          # FCM/Web Push
│       └── package.json
├── supabase/
│   └── migrations/              # DB 마이그레이션
│       ├── 001_initial_schema.sql
│       ├── 002_rls_policies.sql
│       └── 003_triggers.sql
├── docs/
│   ├── architecture/            # 시스템 아키텍처
│   ├── api/                     # API 명세
│   ├── database/                # ERD
│   └── wireframes/              # UI/UX 설계
├── .env.example
├── .gitignore
├── docker-compose.yml           # Redis 로컬 개발
├── package.json                 # 워크스페이스
└── README.md
```

---

## 🔧 환경 변수

### `.env.example`
```bash
# Supabase
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# AI APIs
CLAUDE_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key

# 증권사 API
EBEST_API_KEY=your_ebest_key
EBEST_API_SECRET=your_ebest_secret

# Push 알림
FCM_SERVER_KEY=your_fcm_server_key

# Redis
REDIS_URL=redis://localhost:6379

# Railway (배포)
RAILWAY_TOKEN=your_railway_token
```

---

## 📈 핵심 기능 상세

### 1. 실시간 시세 스트리밍
- **목표 지연**: ≤ 1초
- **데이터**: 현재가, 등락률, 거래량, 호가, 체결
- **차트**: 1분봉, 5분봉 실시간 업데이트
- **기술**: WebSocket + Redis Pub/Sub

### 2. AI 뉴스 분석 파이프라인
```
뉴스 원문
  ↓
종목명 추출 (NER)
  ↓
Claude/OpenAI API
  ├─ 요약 (2~3문장)
  ├─ 감성 분석 (-1 ~ 1)
  ├─ 영향도 평가 (0 ~ 1)
  └─ 행동 권고 (매수/매도/관망)
  ↓
DB 저장 + 알림 트리거
```

### 3. 알림 규칙 엔진
**트리거 조건**:
- 가격 변동: ±3% 이상
- 거래량 급증: 평균 대비 2배 이상
- AI 영향도: impact_score ≥ 0.7
- 부정 뉴스: sentiment_score ≤ -0.5

**알림 채널**:
- Web Push Notification
- FCM (모바일 앱)
- TTS 자동 읽기 (설정 활성화 시)

### 4. 백테스트 (옵션)
- Backtrader 또는 Pandas 기반
- 전략 성과 지표: CAGR, MDD, Sharpe Ratio
- 시뮬레이션 결과 저장 및 비교

---

## 🚀 배포 아키텍처

### Netlify (Frontend)
```bash
# 빌드 설정
Build command: npm run build
Publish directory: dist
Environment variables: VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY
```

### Railway (Backend)
- 각 마이크로서비스를 별도 Railway 프로젝트로 배포
- Redis add-on 연결
- Health check: `/health` 엔드포인트

### Supabase
- 리전: ap-southeast-1 (싱가포르)
- Auth: 이메일/비밀번호 (OAuth 추가 가능)
- Realtime: 주가/알림 실시간 동기화
- Storage: 뉴스 이미지/스크린샷 저장

---

## 📊 모니터링 & 로깅

### 주요 모니터링 지표
- WebSocket 연결 수
- 평균 응답 시간 (시세 업데이트)
- Redis Pub/Sub 메시지 처리율
- AI API 호출 횟수 및 비용
- 알림 발송 성공률

### 로깅 전략
- **중앙 집중형**: Logflare / Sentry
- **로그 레벨**: ERROR, WARN, INFO, DEBUG
- **보관 기간**: 30일 (정책에 따라 조정)

---

## 🧪 테스트 전략

### 단위 테스트
- AI 분석 로직 (감성 점수, 영향도 계산)
- 알림 규칙 엔진
- 수익률 계산 함수

### 통합 테스트
- WebSocket 연결 및 재연결
- Supabase Auth 플로우
- 뉴스 크롤링 → AI 분석 → 알림 발송 전체 파이프라인

### E2E 테스트
- 사용자 회원가입 → 포트폴리오 등록 → 실시간 시세 확인
- 뉴스 알림 → TTS 재생 확인

---

## 📅 개발 현황 (Phase 기반)

### ✅ Phase 1: 인증 및 포트폴리오 관리 (100% 완료)

#### 기반 시스템
- **Supabase 설정**: 11개 테이블, RLS 정책, 샘플 데이터 ✅
- **한국투자증권 API 연동**: REST API 클라이언트 구현 ✅
- **Frontend 구조**: React 19 + TypeScript + Vite + TailwindCSS ✅

#### Phase 1.1: Supabase Auth 연동 ✅
**파일**:
- `frontend/src/stores/authStore.ts` - Zustand 기반 인증 상태 관리
- `frontend/src/pages/Login.tsx` - 로그인 페이지
- `frontend/src/pages/SignUp.tsx` - 회원가입 페이지
- `frontend/src/components/ProtectedRoute.tsx` - 인증 보호 라우트

**기능**:
- 이메일/비밀번호 인증
- 자동 세션 복원
- 자동 프로필 생성 (TTS 기본 설정 포함)
- JWT 기반 인증

#### Phase 1.2: 사용자 프로필 관리 ✅
**파일**:
- `frontend/src/stores/profileStore.ts` - 프로필 상태 관리
- `frontend/src/pages/Profile.tsx` - 프로필 설정 페이지

**기능**:
- 프로필 정보 수정 (이름)
- TTS 설정 (활성화, 속도, 볼륨, 자동재생 임계값)
- 화면 설정 (테마, 글꼴 크기, 고대비 모드)
- 설정 실시간 적용

#### Phase 1.3: 보유 종목 관리 ✅
**파일**:
- `frontend/src/stores/portfolioStore.ts` - 포트폴리오 상태 관리
- `frontend/src/pages/Portfolio.tsx` - 보유 종목 관리 페이지

**기능**:
- 종목 추가/수정/삭제
- 평균 단가 자동 계산 (추가 매수 시)
- 투자금액 요약 통계
- 보유 종목 목록 테이블

#### Phase 1.4: 관심 종목(Watchlist) 관리 ✅
**파일**:
- `frontend/src/stores/watchlistStore.ts` - Watchlist 상태 관리
- `frontend/src/pages/Watchlist.tsx` - 관심 종목 관리 페이지

**기능**:
- 관심 종목 추가/삭제
- 종목별 메모 작성/수정
- 중복 등록 방지
- 관심 종목 목록

#### Phase 1.5: 수익률 계산 로직 ✅
**파일**:
- `frontend/src/lib/profitCalculator.ts` - 수익률 계산 유틸리티
- `frontend/src/pages/Statistics.tsx` - 수익률 통계 페이지

**기능**:
- 개별 종목 수익률 계산
- 전체 포트폴리오 수익률 계산
- 총 투자금액/평가금액/손익 표시
- 종목별 수익률 테이블
- 임시 현재가 생성 (Phase 2에서 실시간 시세로 대체)

### 📊 Phase 1 완성도 요약
- **총 구현 파일**: 17개
  - Stores: 3개 (authStore, profileStore, portfolioStore, watchlistStore)
  - Pages: 6개 (Login, SignUp, Dashboard, Profile, Portfolio, Watchlist, Statistics)
  - Components: 1개 (ProtectedRoute)
  - Utils: 2개 (supabase, tts, profitCalculator)
- **총 기능**: 25개 이상
- **개발 서버**: http://localhost:5173/ ✅ 정상 실행 중

### 🔄 다음 단계
- **Phase 2**: 실시간 시세 스트리밍 (WebSocket + KIS API)
- **Phase 3**: 뉴스 크롤링 + AI 분석
- **Phase 4**: 알림 시스템 + TTS

---

## 🚨 작업 시 주의사항

### 데이터베이스 작업
1. **Supabase MCP 사용**: `mcp__supabase__*` 도구로 직접 연결
2. **마이그레이션 관리**: 모든 스키마 변경은 마이그레이션 파일로 관리
3. **RLS 정책 필수**: 모든 테이블에 적절한 RLS 정책 적용

### 개발 환경
1. **경로**: `/Users/dev/jusik`
2. **개발 서버**: `npm run dev` (Frontend, Backend 각각)
3. **환경 변수**: `.env` 파일 생성 (`.env.example` 참조)

### 보안
1. **API 키**: 절대 코드에 하드코딩 금지
2. **JWT 토큰**: 클라이언트에서 안전하게 관리
3. **CORS**: 허용된 도메인만 접근 가능하도록 설정

### 접근성
1. **TTS 테스트**: 실제 시니어 사용자 피드백 반영
2. **색상 대비**: 모든 UI 요소 WCAG AA 준수
3. **키보드 네비게이션**: 마우스 없이도 모든 기능 사용 가능

---

## 📚 참고 자료

### API 문서
- [Supabase Docs](https://supabase.com/docs)
- [Claude API](https://docs.anthropic.com/claude/reference)
- [OpenAI API](https://platform.openai.com/docs/api-reference)
- [Socket.IO](https://socket.io/docs/v4/)

### 디자인 가이드
- [WCAG 2.1](https://www.w3.org/WAI/WCAG21/quickref/)
- [Material Design - Accessibility](https://m3.material.io/foundations/accessible-design/overview)

### 한국 주식 API
- [eBest 투자증권 API](https://www.ebestsec.co.kr/)
- [키움증권 OpenAPI](https://www.kiwoom.com/h/customer/download/VOpenApiInfoView)

---

## 🎯 성공 지표 (KPI)

### 기술적 지표
- 시세 업데이트 지연: **≤ 1초**
- 뉴스 분석 정확도: **≥ 85%**
- 시스템 가용성: **≥ 99.5%**
- 알림 발송 성공률: **≥ 98%**

### 사용자 경험 지표
- TTS 사용률: **≥ 40%** (시니어 사용자)
- 일일 활성 사용자(DAU): 목표 **500명** (3개월 내)
- 평균 세션 시간: **≥ 15분**
- 사용자 만족도: **≥ 4.5/5.0**

---

## 💡 향후 확장 아이디어

### 기능 확장
1. **소셜 트레이딩**: 우수 트레이더 전략 공유
2. **AI 챗봇**: 자연어 질의응답 (예: "삼성전자 지금 사도 돼?")
3. **멀티 에셋**: 암호화폐, 선물/옵션 지원
4. **모바일 앱**: React Native 기반 네이티브 앱

### 인프라 확장
1. **마이크로서비스 고도화**: Kubernetes 오케스트레이션
2. **Elasticsearch**: 고급 뉴스 검색 엔진
3. **GraphQL**: 효율적인 데이터 fetching
4. **CDN**: 글로벌 사용자 대응

---

**🎉 이 프로젝트는 한국 주식 트레이더를 위한 최첨단 실시간 인텔리전스 플랫폼으로, AI와 접근성을 결합한 차세대 트레이딩 도구입니다!**
