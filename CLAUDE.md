# 📈 실시간 트레이딩 인텔리전스 플랫폼 (Trading Intelligence Platform)

> 이 문서는 Claude Code가 이 저장소에서 작업할 때 참고할 수 있도록 작성되었습니다.

## 🎯 프로젝트 개요

**실시간 트레이딩 인텔리전스 플랫폼**은 한국 주식 시장을 대상으로 실시간 시세, AI 뉴스 분석, 음성 알림을 제공하는 풀스택 애플리케이션입니다.

### 핵심 가치 제안
- **실시간 시세**: WebSocket 기반 1초 이내 초저지연 데이터 스트리밍
- **AI 뉴스 분석**: Claude/OpenAI를 활용한 감성 분석 및 투자 행동 권고
- **시니어 친화 UI**: 큰 글꼴(18px+), 고대비 모드, 음성 읽기(TTS) 지원
- **포트폴리오 관리**: 보유 종목 실시간 손익 계산 및 추적

### 타겟 사용자
- HFT(High-Frequency Trading) 트레이더
- 시니어 투자자 (접근성 및 음성 알림 중시)
- 한국 주식 시장 참여자

---

## 🏗️ 아키텍처

### 전체 시스템 구조

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (React 19 + TypeScript + Vite)                │
│  - Dashboard, Portfolio, Watchlist, News                │
│  - WebSocket Client (Socket.IO)                         │
│  - TTS Service (Web Speech API)                         │
│  - State: Zustand + React Query                         │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────┴────────────────────────────────────────┐
│  Backend Microservices (Express/FastAPI)                │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐ │
│  │ Stream       │ │ News Crawler │ │ AI Service      │ │
│  │ Service      │ │ (Python)     │ │ (Claude/OpenAI) │ │
│  │ (WebSocket)  │ │              │ │                 │ │
│  └──────────────┘ └──────────────┘ └─────────────────┘ │
│  ┌──────────────┐ ┌──────────────┐                     │
│  │ Alert        │ │ Data Service │                     │
│  │ Service      │ │ (Stock Data) │                     │
│  └──────────────┘ └──────────────┘                     │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────┴────────────────────────────────────────┐
│  Supabase (PostgreSQL + Auth + Realtime)               │
│  - 11개 핵심 테이블 (users, portfolios, news 등)        │
│  - Row Level Security (RLS) 적용                        │
│  - 실시간 구독 (Realtime Subscriptions)                 │
└─────────────────────────────────────────────────────────┘
```

### 핵심 데이터 플로우

#### 1. 종목 검색 시스템 (Stock Search)
```
사용자 입력 (종목코드/종목명)
    ↓
StockAutocomplete Component (300ms debounce)
    ↓
Supabase Query (ILIKE with pg_trgm index)
    ↓
stock_master 테이블 (2,726개 종목 - KOSPI + KOSDAQ)
    ↓
실시간 검색 결과 (키보드 네비게이션 지원)
```

**중요**: `stock_master` 테이블은 **KRX(한국거래소) 공개 API**에서 동기화됨. KIS API는 종목 마스터 데이터를 제공하지 않음.

#### 2. 실시간 시세 스트리밍 (Price Updates)
```
KIS API (WebSocket)
    ↓
Stream Service (Socket.IO 서버)
    ↓
Redis Pub/Sub (메시지 브로커)
    ↓
Frontend (Socket.IO Client)
    ↓
실시간 대시보드 업데이트
```

#### 3. AI 뉴스 분석 파이프라인
```
네이버 뉴스 API → News Crawler (Python)
    ↓
종목명 자동 추출 (NER - stock_master 매칭)
    ↓
AI Service (OpenAI GPT-4o-mini 우선 → Claude 폴백)
  ├─ 요약 (2~3문장)
  ├─ 감성 점수 (-1 ~ 1)
  ├─ 영향도 (0 ~ 1)
  └─ 행동 권고 (buy/sell/hold)
    ↓
Supabase `news` 테이블 저장
    ↓
Supabase Realtime → Frontend (실시간 뉴스 알림)
    ↓
TTS 자동 재생 + Toast 알림
```

---

## 📂 프로젝트 구조

```
/Users/dev/jusik/
├── frontend/                 # React 프론트엔드
│   ├── src/
│   │   ├── components/       # 재사용 가능한 컴포넌트
│   │   │   └── StockAutocomplete.tsx  # 종목 검색 자동완성
│   │   ├── pages/            # 페이지 컴포넌트
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Portfolio.tsx
│   │   │   ├── Watchlist.tsx
│   │   │   └── News.tsx
│   │   ├── stores/           # Zustand 상태 관리
│   │   ├── lib/              # 유틸리티 라이브러리
│   │   │   └── supabase.ts   # Supabase 클라이언트
│   │   └── types/            # TypeScript 타입 정의
│   ├── package.json
│   └── vite.config.ts (존재하지 않음 - 기본 설정 사용)
│
├── backend/
│   ├── data-service/         # 🔥 종목 마스터 데이터 서비스 (NEW)
│   │   ├── src/
│   │   │   ├── lib/
│   │   │   │   └── kisApi.ts         # KIS API + KRX API 클라이언트
│   │   │   └── scripts/
│   │   │       └── syncStockMaster.ts # 종목 데이터 동기화 스크립트
│   │   └── package.json
│   ├── stream-service/       # 실시간 시세 스트리밍 (Socket.IO)
│   ├── news-crawler/         # 뉴스 크롤러 (Python)
│   ├── ai-service/           # AI 뉴스 분석 (Python)
│   └── alert-service/        # 알림 발송 (Node.js)
│
├── .env                      # 환경 변수 (gitignore)
├── .gitignore
├── package.json              # 루트 워크스페이스 설정
└── entire-api.md             # 🔥 KIS API 전체 명세 (참고용)
```

### 주요 파일 설명

#### Frontend

**`frontend/src/components/StockAutocomplete.tsx`**
- 종목 검색 자동완성 컴포넌트
- 300ms debounce로 API 호출 최적화
- 키보드 네비게이션 (↑↓ Enter Escape) 지원
- `Portfolio.tsx`, `Watchlist.tsx`에서 재사용

**`frontend/src/lib/supabase.ts`**
- Supabase 클라이언트 초기화
- 자동 세션 갱신 및 URL 기반 세션 감지 활성화

**`frontend/src/pages/Portfolio.tsx`**, **`frontend/src/pages/Watchlist.tsx`**
- 보유 종목 및 관심 종목 관리 페이지
- `StockAutocomplete` 컴포넌트를 사용하여 종목 추가
- Zustand 스토어를 통한 상태 관리

#### Backend

**`backend/data-service/src/lib/kisApi.ts`**
- **KIS API 클라이언트**: OAuth 토큰 발급 및 관리
- **토큰 캐싱**: `.kis-token-cache.json` 파일로 토큰 재사용 (rate limit 회피)
- **KRX API 통합**: `getAllStocksFromKRX()` 메서드로 KOSPI/KOSDAQ 전체 종목 조회
  - KIS API는 종목 마스터 일괄 조회를 지원하지 않음
  - KRX 공개 API 사용: `http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd`

**중요 코드 패턴**:
```typescript
// BigInt 변환 시 쉼표 제거 필수!
listed_shares: stock.LIST_SHRS ? BigInt(stock.LIST_SHRS.replace(/,/g, '')) : null
```

**`backend/data-service/src/scripts/syncStockMaster.ts`**
- 종목 마스터 데이터를 Supabase `stock_master` 테이블에 동기화
- 1,000개씩 배치로 upsert 처리
- 실행 명령: `npm run sync-stocks` (data-service 디렉토리에서)

---

## 🛠️ 개발 환경 설정

### 필수 환경 변수 (`.env` 파일)

```bash
# Supabase
VITE_SUPABASE_URL=https://lrmvoldeyetuzuwuazdm.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_key_here

# KIS API (한국투자증권)
KIS_APP_KEY=your_kis_app_key
KIS_APP_SECRET=your_kis_app_secret

# AI API
CLAUDE_API_KEY=your_claude_key
OPENAI_API_KEY=your_openai_key
```

### 자주 사용하는 명령어

#### 전체 개발 서버 실행 (루트)
```bash
npm run dev
# → frontend, stream-service, alert-service 동시 실행 (concurrently 사용)
```

#### Frontend만 실행
```bash
cd frontend
npm run dev
# → http://localhost:5173/ 실행
```

#### Data Service (종목 데이터 동기화)
```bash
cd backend/data-service
npm run sync-stocks
# → KRX API → Supabase stock_master 테이블 동기화
# → 결과: KOSPI(959개) + KOSDAQ(1,802개) = 총 2,726개 종목
```

#### 빌드
```bash
# Frontend 빌드
cd frontend
npm run build

# 전체 빌드
npm run build
```

#### Lint
```bash
cd frontend
npm run lint
```

---

## 🗄️ 데이터베이스 스키마 (Supabase)

### 핵심 테이블 (11개)

#### 1. `stock_master` (🔥 NEW - 종목 마스터)
```sql
CREATE TABLE stock_master (
  symbol text PRIMARY KEY,        -- 종목코드 (6자리, 예: '005930')
  name text NOT NULL,             -- 종목명 (예: '삼성전자')
  market text NOT NULL,           -- 시장 (KOSPI/KOSDAQ)
  sector text,                    -- 업종
  listed_shares bigint,           -- 상장주식수
  last_updated timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now()
);

-- 성능 최적화: pg_trgm 확장 + GIN 인덱스
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_stock_master_name ON stock_master USING gin(name gin_trgm_ops);
CREATE INDEX idx_stock_master_search ON stock_master USING gin(to_tsvector('simple', symbol || ' ' || name));

-- RLS 정책: 모든 사용자 읽기 가능
ALTER TABLE stock_master ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable read access for all users" ON stock_master FOR SELECT USING (true);
```

**검색 쿼리 패턴**:
```typescript
const { data } = await supabase
  .from('stock_master')
  .select('symbol, name, market')
  .or(`symbol.ilike.%${query}%,name.ilike.%${query}%`)
  .order('symbol', { ascending: true })
  .limit(10);
```

#### 2. `portfolios` (보유 종목)
```sql
CREATE TABLE portfolios (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users NOT NULL,
  symbol text NOT NULL,           -- 종목코드
  symbol_name text NOT NULL,      -- 종목명
  qty integer NOT NULL,           -- 보유 수량
  avg_price numeric NOT NULL,     -- 평균 단가
  created_at timestamptz DEFAULT now()
);
```

#### 3. `watchlist` (관심 종목)
```sql
CREATE TABLE watchlist (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users NOT NULL,
  symbol text NOT NULL,
  symbol_name text NOT NULL,
  note text,                      -- 메모 (선택사항)
  created_at timestamptz DEFAULT now()
);
```

#### 4. `news` (AI 분석 뉴스)
```sql
CREATE TABLE news (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol text,                    -- 관련 종목
  title text NOT NULL,
  summary text,                   -- AI 요약 (2~3문장)
  sentiment_score numeric,        -- 감성 점수 (-1 ~ 1)
  impact_score numeric,           -- 영향도 (0 ~ 1)
  action_recommendation text,     -- 행동 권고 (buy/sell/hold)
  source_url text,
  published_at timestamptz,
  created_at timestamptz DEFAULT now()
);
```

#### 5. `alerts` (사용자 알림)
```sql
CREATE TABLE alerts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users NOT NULL,
  type text NOT NULL,             -- price_change, volume_spike, news
  title text NOT NULL,
  message text NOT NULL,
  is_read boolean DEFAULT false,
  created_at timestamptz DEFAULT now()
);
```

---

## 🎨 주요 기능 구현 패턴

### 1. 종목 검색 (Stock Autocomplete)

**컴포넌트 사용법**:
```typescript
import StockAutocomplete from '@/components/StockAutocomplete';

<StockAutocomplete
  onSelect={(stock) => {
    setSymbol(stock.symbol);  // '005930'
    setName(stock.name);      // '삼성전자'
  }}
  placeholder="종목코드 또는 종목명 입력 (예: 삼성전자, 005930)"
  autoFocus={true}
/>
```

**검색 로직** (300ms debounce):
```typescript
useEffect(() => {
  const timer = setTimeout(async () => {
    if (query.trim().length < 1) return;

    const { data } = await supabase
      .from('stock_master')
      .select('symbol, name, market')
      .or(`symbol.ilike.%${query}%,name.ilike.%${query}%`)
      .order('symbol', { ascending: true })
      .limit(10);

    setResults(data || []);
  }, 300);

  return () => clearTimeout(timer);
}, [query]);
```

### 2. 토큰 캐싱 (KIS API)

**문제**: KIS API는 토큰 발급이 1분당 1회로 제한됨.

**해결**: 파일 기반 토큰 캐싱 (`.kis-token-cache.json`)

```typescript
// backend/data-service/src/lib/kisApi.ts
private loadTokenFromCache(): void {
  try {
    if (fs.existsSync(this.tokenCachePath)) {
      const cached: KISTokenCache = JSON.parse(
        fs.readFileSync(this.tokenCachePath, 'utf-8')
      );
      const expiresAt = new Date(cached.expiresAt);

      // 토큰이 아직 유효하면 재사용
      if (expiresAt > new Date()) {
        this.token = cached.token;
        this.tokenExpiry = expiresAt;
        console.log('캐시된 KIS API 토큰 로드 완료');
      }
    }
  } catch (error) {
    console.warn('토큰 캐시 로드 실패:', error);
  }
}
```

**중요**: `.kis-token-cache.json`은 `.gitignore`에 포함되어 있음.

### 3. KRX 데이터 동기화

**Why KRX, not KIS?**
- KIS API는 종목 마스터 데이터 일괄 조회를 지원하지 않음 (`entire-api.md` 참조)
- KRX 공개 API는 무료이며 rate limit이 없음

**동기화 코드** (`backend/data-service/src/lib/kisApi.ts`):
```typescript
async getAllStocksFromKRX(): Promise<Array<{
  symbol: string;
  name: string;
  market: string;
  sector: string | null;
  listed_shares: bigint | null;
}>> {
  // KOSPI 조회
  const kospiResponse = await axios.get('http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd', {
    params: {
      bld: 'dbms/MDC/STAT/standard/MDCSTAT01501',
      mktId: 'STK',  // KOSPI
      trdDd: new Date().toISOString().slice(0, 10).replace(/-/g, ''),
    },
  });

  // KOSDAQ 조회
  const kosdaqResponse = await axios.get('...', {
    params: { mktId: 'KSQ' }  // KOSDAQ
  });

  // 쉼표 제거 후 BigInt 변환 (중요!)
  return allStocks.map(stock => ({
    ...stock,
    listed_shares: stock.LIST_SHRS ? BigInt(stock.LIST_SHRS.replace(/,/g, '')) : null
  }));
}
```

---

## ⚠️ 중요한 규칙 및 제약사항

### 1. 하드코딩 및 목업 데이터 금지
- **절대 금지**: 하드코딩된 종목 데이터, 목업 데이터 사용
- **이유**: 실제 운영 환경에서 데이터 불일치 방지
- **해결**: 항상 Supabase 또는 API에서 실시간 데이터 조회

### 2. KIS API 사용 시 주의사항
- **토큰 재사용**: 반드시 캐시된 토큰 사용 (rate limit 회피)
- **종목 마스터 조회**: KIS API 대신 KRX API 사용
- **API 명세 참조**: `/Users/dev/jusik/entire-api.md` 파일 참조

### 3. 검색 쿼리 최적화
- **Debounce**: 300ms 이상 설정
- **Limit**: 결과는 10개 이하로 제한
- **인덱스 활용**: `ILIKE` 쿼리 시 pg_trgm 인덱스 사용

### 4. BigInt 처리
- **쉼표 제거**: KRX API 응답의 숫자에는 쉼표가 포함되어 있음
- **변환 전 처리**: `.replace(/,/g, '')` 후 BigInt 변환

```typescript
// ❌ 잘못된 예
BigInt("45,252,759")  // Error: Cannot convert 45,252,759 to a BigInt

// ✅ 올바른 예
BigInt("45252759".replace(/,/g, ''))  // OK
```

### 5. 중복 체크 쿼리
- **`.single()` 대신 `.maybeSingle()` 사용**
- **이유**: 데이터가 없을 때 406 에러 방지

```typescript
// ❌ 잘못된 예
const { data } = await supabase
  .from('portfolios')
  .select('*')
  .eq('user_id', userId)
  .eq('symbol', symbol)
  .single();  // 데이터 없으면 406 에러

// ✅ 올바른 예
const { data } = await supabase
  .from('portfolios')
  .select('*')
  .eq('user_id', userId)
  .eq('symbol', symbol)
  .maybeSingle();  // 데이터 없으면 null 반환
```

---

## 🚀 배포 아키텍처 (Railway)

### ✅ 현재 배포 상태 (2025-10-19)

모든 5개 서비스가 **Railway 플랫폼**에 성공적으로 배포되어 운영 중입니다.

#### 1. Frontend (React 19 + Vite)
- **URL**: `https://frontend-production-7c4d.up.railway.app`
- **커스텀 도메인**: `https://jusik.minhyuk.kr` (DNS 전파 대기 중)
- **빌드 시스템**: Nixpacks (Node.js 20.19.5)
- **배포 명령**: `npm run build`
- **실행 명령**: `npm run preview` (Vite Preview Server)
- **환경 변수**:
  - `VITE_SUPABASE_URL`: Supabase 프로젝트 URL
  - `VITE_SUPABASE_ANON_KEY`: Supabase 익명 키
  - `VITE_STREAM_SERVICE_URL`: Stream Service WebSocket URL
  - `VITE_KIS_APP_KEY`, `VITE_KIS_APP_SECRET`: KIS API 키 (초기 시세 조회용)
- **특이사항**:
  - `vite.config.ts`에 Railway 도메인 allowedHosts 설정 필요
  - `.nvmrc` 파일로 Node 버전 고정 (20.19.5)

#### 2. Stream Service (Node.js + Socket.IO)
- **URL**: `https://stream-service-production.up.railway.app`
- **기능**: 실시간 주가 스트리밍 (KIS API WebSocket → Redis → Socket.IO)
- **포트**: Railway 자동 할당 (`PORT` 환경 변수)
- **환경 변수**:
  - `KIS_APP_KEY`, `KIS_APP_SECRET`: KIS API 인증
  - `SUPABASE_URL`, `SUPABASE_ANON_KEY`: Supabase 연결 (주의: VITE_ 접두사 없음!)
  - `REDIS_URL`: Redis 연결 (`${{Redis.REDIS_URL}}` 참조)
  - `PORT`: Railway 할당 포트
- **특이사항**:
  - WebSocket 연결 시 JWT 토큰 인증 필요
  - Redis Pub/Sub 방식으로 실시간 시세 전달
  - Health check 엔드포인트: `/health`

#### 3. AI Service (Python FastAPI)
- **URL**: `https://ai-service-production.up.railway.app` (예상)
- **기능**: Claude/OpenAI API를 이용한 뉴스 분석
- **환경 변수**:
  - `CLAUDE_API_KEY`: Claude API 키
  - `OPENAI_API_KEY`: OpenAI API 키 (폴백)
  - `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`: Supabase 연결
  - `REDIS_URL`: Redis 캐싱

#### 4. News Crawler (Python)
- **URL**: `https://news-crawler-production.up.railway.app` (예상)
- **기능**: 네이버/연합뉴스 크롤링 + 종목명 추출
- **환경 변수**:
  - `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`: 네이버 API
  - `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`: Supabase 연결

#### 5. Redis (In-Memory Cache)
- **서비스**: Railway Redis Add-on
- **기능**: Pub/Sub 메시지 브로커 + 캐싱
- **연결 방법**: 다른 서비스에서 `${{Redis.REDIS_URL}}` 참조

### 배포 워크플로우

```
GitHub Repository (main 브랜치)
    ↓ (Push 감지)
Railway Auto Deploy
    ↓
Nixpacks 빌드
    ↓
컨테이너 이미지 생성
    ↓
Railway 인프라 배포
    ↓
Public URL 생성 + SSL 자동 발급
```

### Railway 배포 시 주의사항

#### 1. 환경 변수 네이밍
- **Frontend**: `VITE_` 접두사 필수 (빌드 타임에 번들에 포함됨)
- **Backend**: `VITE_` 접두사 사용 금지 (런타임 환경 변수)

#### 2. 서비스 간 참조
- **Backend → Backend**: `${{service-name.VARIABLE}}` 문법 사용 가능 (예: `${{Redis.REDIS_URL}}`)
- **Frontend → Backend**: 빌드 타임에 환경 변수로 URL 주입 필요

#### 3. 포트 설정
- Railway는 `PORT` 환경 변수로 자동 포트 할당
- 코드에서 `process.env.PORT || 기본포트` 패턴 사용

#### 4. Docker 캐시 이슈
- Railway는 빌드 레이어를 캐시하여 속도 향상
- 코드 변경이 반영되지 않으면 "Clear build cache" 버튼 사용

#### 5. TypeScript 빌드
- Strict mode에서 모든 타입 에러 해결 필수
- Type-only imports: `import type { ... }` 사용
- Recharts 등 외부 라이브러리는 `as any` 캐스팅 필요할 수 있음

### 커스텀 도메인 설정

#### DNS 설정 (Cloudflare/가비아)
```
Type: CNAME
Name: jusik
Value: frontend-production-7c4d.up.railway.app
TTL: Auto
```

#### Railway 설정
1. Frontend 서비스 → Settings → Networking
2. "Add Custom Domain" 클릭
3. `jusik.minhyuk.kr` 입력
4. Railway가 자동으로 Let's Encrypt SSL 발급 (5~10분 소요)

### 모니터링

#### Railway Dashboard
- **Metrics**: CPU, 메모리, 네트워크 사용량 실시간 확인
- **Logs**: 각 서비스의 stdout/stderr 로그 스트리밍
- **Deployments**: 배포 히스토리 및 롤백 기능

#### 주요 확인 사항
- WebSocket 연결 수 (Stream Service)
- Redis 메모리 사용량 (< 100MB 권장)
- API 호출 횟수 (KIS, Claude, OpenAI)
- 평균 응답 시간 (실시간 시세 < 1초)

---

## 📚 참고 자료

### 주요 문서
- **KIS API 전체 명세**: `/Users/dev/jusik/entire-api.md`
- **README**: `/Users/dev/jusik/README.md`
- **데이터베이스 스키마**: `docs/database/schema.md` (예정)

### 외부 API
- **KRX (한국거래소) 공개 데이터**: `http://data.krx.co.kr`
- **KIS API 문서**: KIS Developers (한국투자증권)

### 기술 스택 문서
- **Supabase**: https://supabase.com/docs
- **React Query**: https://tanstack.com/query
- **Zustand**: https://zustand-demo.pmnd.rs/
- **Socket.IO**: https://socket.io/docs/

---

## 🧪 테스트 시나리오

### 종목 검색 테스트
```bash
# 1. Frontend 실행
cd frontend && npm run dev

# 2. Portfolio 페이지 접속 (http://localhost:5173/portfolio)
# 3. "종목 추가" 버튼 클릭
# 4. 검색창에 "삼성" 입력
# 5. 결과: "삼성전자", "삼성SDI" 등 자동완성 표시
# 6. 종목 선택 후 수량/단가 입력하여 추가
```

### 종목 데이터 동기화 테스트
```bash
cd backend/data-service
npm run sync-stocks

# 예상 출력:
# KOSPI: 959개, KOSDAQ: 1,802개 종목 조회 완료
# ✅ 성공: 2726개
```

---

## 💡 자주 발생하는 문제 및 해결

### 1. "접근토큰 발급 잠시 후 다시 시도하세요(1분당 1회)"
**원인**: 토큰 캐시를 사용하지 않고 매번 새로 발급 시도

**해결**: `kisApi.ts`의 토큰 캐싱 로직 확인
```typescript
// .kis-token-cache.json 파일이 생성되어 있는지 확인
ls -la backend/data-service/.kis-token-cache.json
```

### 2. "Cannot convert 45,252,759 to a BigInt"
**원인**: KRX API 응답의 숫자에 쉼표가 포함됨

**해결**: `.replace(/,/g, '')` 추가
```typescript
BigInt(stock.LIST_SHRS.replace(/,/g, ''))
```

### 3. "406 (Not Acceptable)" 에러
**원인**: `.single()` 사용 시 데이터가 없으면 에러 발생

**해결**: `.maybeSingle()` 사용
```typescript
const { data } = await supabase
  .from('portfolios')
  .select('*')
  .eq('symbol', symbol)
  .maybeSingle();  // null 반환
```

### 4. 종목 검색이 느림
**원인**: pg_trgm 인덱스가 생성되지 않음

**해결**: Supabase SQL Editor에서 인덱스 생성
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_stock_master_name ON stock_master USING gin(name gin_trgm_ops);
```

---

## 🎯 다음 개발 우선순위

### ✅ Phase 2 완료 (2025-10-19)
- [x] ✅ Phase 2.1: 실시간 시세 스트리밍 (WebSocket + KIS REST API)
  - [x] Stream Service 백엔드 구축 완료
  - [x] Frontend WebSocket 통합 완료
  - [x] 초기 시세 로딩 (KIS REST API) 완료
- [x] ✅ Phase 2.2: 보유 종목 수익률 실시간 계산
  - [x] 수익률 계산 엔진 구현
  - [x] Portfolio 정렬 기능
  - [x] Statistics 차트 (Recharts)
- [x] ✅ Phase 2.3: 뉴스 크롤링 + AI 분석 파이프라인
  - [x] News Crawler (Python) - Railway 배포
  - [x] AI Service (OpenAI GPT-4o-mini 우선, Claude 폴백)
  - [x] 사용자 보유/관심 종목 기반 크롤링
  - [x] News 페이지 (필터, 검색, 정렬, TTS)
- [x] ✅ Phase 2.4: TTS 자동 알림 시스템
  - [x] Alert Rules 엔진
  - [x] TTS Service (큐 시스템)
  - [x] Monitoring Service (전역 통합)
  - [x] **Phase 2.4.3**: Supabase Realtime 뉴스 구독 + 전역 Toast 알림

### 🔜 Phase 3 - 다음 개발 우선순위 (2주 예상)

#### 🎯 즉시 착수: Phase 3.4 - 접근성 강화 (2일)
**우선순위**: ⭐⭐⭐ 시니어 사용자 타겟이므로 매우 중요!
- [ ] **고대비 모드** (1일)
  - [ ] Profile.tsx에 테마 토글 추가 (light/dark/high-contrast)
  - [ ] TailwindCSS dark: 클래스 적용
  - [ ] WCAG AA 기준 준수 (명도비 ≥ 4.5:1)
  - [ ] 모든 UI 요소 색상 대비 검증
- [ ] **큰 글꼴 모드** (0.5일)
  - [ ] Profile.tsx에 글꼴 크기 선택 (18px/20px/24px)
  - [ ] CSS 변수 `--font-size-base` 적용
  - [ ] 반응형 레이아웃 유지 확인
- [ ] **키보드 네비게이션 개선** (0.5일)
  - [ ] 모든 버튼/링크 Tab 순서 최적화
  - [ ] Enter 키로 모든 액션 실행
  - [ ] Esc 키로 모달/폼 닫기
  - [ ] 포커스 시각화 (outline ring)

#### Phase 3.1 - 미니차트 구현 (3일)
**우선순위**: ⭐⭐ 실시간 시세와 연동된 차트로 높은 가치
- [ ] `frontend/src/components/MiniChart.tsx` 생성
  - [ ] Recharts LineChart 기반
  - [ ] 1분봉/5분봉 데이터 표시
  - [ ] 호가 10단계 표시 (매수/매도)
  - [ ] 체결 내역 스트림 (최근 10건)
  - [ ] 차트 확대/축소 (zoom) 기능
- [ ] Dashboard/Portfolio/Watchlist에 통합
- [ ] WebSocket 실시간 데이터 연동
- [ ] 반응형 디자인 (모바일/데스크톱)

#### Phase 3.3 - 성능 최적화 (2일)
**우선순위**: ⭐⭐ 현재 번들 크기 844KB → 500KB 이하로 감소
- [ ] **Vite 코드 스플리팅** (1일)
  - [ ] `vite.config.ts`에 manualChunks 설정
  - [ ] Vendor 청크 분리 (React, Recharts 등)
  - [ ] Route-based 청크 분리 (React.lazy)
- [ ] **Redis 캐싱 고도화** (0.5일)
  - [ ] 시세 캐싱 전략 개선 (현재 5분 → 동적 TTL)
  - [ ] AI 분석 캐싱 전략 검증 (현재 24시간)
- [ ] **WebSocket 메시지 압축** (0.5일)
  - [ ] Socket.IO compression 활성화
  - [ ] 메시지 페이로드 최적화

#### Phase 3.2 - 백테스트 시스템 (5일)
**우선순위**: ⭐ 나중 단계 (Phase 4로 이동 고려)
- [ ] `backend/backtest-service/` 생성 (Python)
- [ ] Backtrader 라이브러리 통합
- [ ] 전략 정의 인터페이스 (매수/매도 조건)
- [ ] 성과 지표 계산 (CAGR, MDD, Sharpe Ratio)
- [ ] Frontend 결과 시각화 페이지

---

## 📝 코드 스타일 가이드

### TypeScript
- **Strict mode** 사용
- **명시적 타입** 선언 권장
- **인터페이스** 우선 (type alias는 유니온 타입에만)

### React
- **Functional Components** + Hooks
- **Props 타입 명시** 필수
- **useEffect 의존성 배열** 정확히 명시

### 네이밍
- **컴포넌트**: PascalCase (`StockAutocomplete`)
- **함수/변수**: camelCase (`fetchStockData`)
- **상수**: UPPER_SNAKE_CASE (`MAX_RESULTS`)
- **파일명**: kebab-case (`stock-autocomplete.tsx`) 또는 PascalCase (컴포넌트)

---

---

## 📋 작업 관리 규칙 (필수!)

### planPhase.md - Phase별 개발 계획서

**위치**: `/Users/dev/jusik/planPhase.md`

**목적**: 전체 개발 로드맵을 체크박스 TODO 형식으로 관리하여 일관성 있는 개발 진행

**필수 작업 흐름**:

#### ✅ 작업 시작 전 (매번 확인!)
1. **planPhase.md 열기** → 현재 Phase 및 작업 항목 확인
2. **CLAUDE.md 참조** → 기술 스택 및 아키텍처 확인
3. **trading_intelligence_requirements_and_design.md** → 요구사항 재확인
4. **docs/kis_api/** → KIS API 명세 확인 (필요 시)
5. **환경 변수** → `.env` 파일 설정 확인
6. **개발 서버** → `http://localhost:5173/` 정상 실행 확인
7. **Git 브랜치** → 새 브랜치 생성 (예: `feature/phase2-websocket`)

#### ✅ 작업 완료 후 (매번 확인!)
1. **planPhase.md 업데이트** → 완료한 체크박스 ✅ 체크
2. **검증 기준 확인** → Phase별 검증 기준 충족 여부
3. **Git 커밋** → 의미 있는 커밋 메시지 작성
   ```bash
   git add .
   git commit -m "feat(phase2): WebSocket 실시간 시세 연동 완료"
   ```
4. **테스트 실행** → 단위 테스트 + 통합 테스트
5. **다음 작업 확인** → planPhase.md에서 다음 항목 파악

### 핵심 원칙

1. **TTS 우선**: 모든 중요 이벤트는 TTS 알림 지원
2. **보유 vs 관심 구분**:
   - **보유 종목** → TTS 메시지에 수익률 포함
   - **관심 종목** → TTS 메시지에 가격만 포함
3. **하드코딩 금지**: 모든 데이터는 API 또는 DB에서 조회
4. **목업 데이터 금지**: 실제 KIS API 및 KRX 데이터 사용
5. **토큰 재사용**: `.kis-token-cache.json` 파일 기반 캐싱 필수

---

## 📚 필수 참조 문서

### 프로젝트 문서
1. **CLAUDE.md** (이 파일) - 프로젝트 전체 가이드
2. **planPhase.md** - Phase별 개발 계획 (체크박스 TODO)
3. **trading_intelligence_requirements_and_design.md** - 요구사항 및 기술 설계

### KIS API 문서 (`docs/kis_api/`)
- **access.token.md** - OAuth 인증 및 토큰 발급
- **access-token-expire.md** - 토큰 만료 및 갱신
- **real-time-websocket-ket.md** - WebSocket 실시간 시세 연결
- **hash-key-api.md** - 해시 키 생성 (거래 시)
- **entire-api.md** - 전체 API 명세
- **매수가능조회.md** - 매수 가능 금액 조회

### 외부 문서
- [Supabase Docs](https://supabase.com/docs)
- [Socket.IO Docs](https://socket.io/docs/v4/)
- [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
- [Claude API](https://docs.anthropic.com/claude/reference)

---

**💡 중요**: 매 작업 시작 전 반드시 `planPhase.md`를 확인하여 현재 Phase 및 작업 항목을 파악하고, 작업 완료 후 즉시 체크박스를 업데이트하여 일관성을 유지하세요!

---

**마지막 업데이트**: 2025-10-19
**프로젝트 상태**: Phase 2 완료 ✅ → Phase 3 준비 중

**완료된 Phase**:
- ✅ **Phase 1** (2025-10-18): 인증, 포트폴리오, 관심종목, 종목검색
- ✅ **Phase 2.1** (2025-10-18): 실시간 주가 스트리밍 (WebSocket + KIS REST API)
- ✅ **Phase 2.2** (2025-10-18): 보유 종목 수익률 실시간 계산
- ✅ **Phase 2.3** (2025-10-19): 뉴스 크롤링 + AI 분석 파이프라인
  - 네이버 뉴스 API 연동
  - AI Service (OpenAI GPT-4o-mini 우선 → Claude 폴백)
  - 사용자 보유/관심 종목 기반 크롤링
- ✅ **Phase 2.4** (2025-10-19): TTS 자동 알림 시스템
  - Alert Rules 엔진
  - Supabase Realtime 뉴스 구독
  - 전역 모니터링 서비스 (App.tsx)
  - 모든 페이지에서 Toast 알림 수신

**현재 배포**: Railway (4개 서비스 운영 중)
- ✅ Frontend: https://jusik.minhyuk.kr
- ✅ stream-service: WebSocket 실시간 시세
- ✅ news-crawler: 5분마다 뉴스 수집
- ✅ ai-service: OpenAI GPT-4o-mini 기반 분석

**다음 마일스톤**: Phase 3.4 접근성 강화 (시니어 UX 최우선) → Phase 3.1 미니차트 → Phase 3.3 성능 최적화
