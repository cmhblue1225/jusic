
# 실시간 트레이딩 인텔리전스 플랫폼 — 요구사항 및 기술 설계서

> 대상: 고빈도 트레이더(HFT) 및 50~60대 고연령 사용자도 쉽게 사용할 수 있는 접근성 강화 버전  
> 배포: Supabase (DB/Auth), Railway (백엔드 호스팅), Netlify (프론트엔드 호스팅) 기반 배포 환경을 사용

---

## 목차
1. 프로젝트 개요  
2. 비즈니스 및 사용자 요구사항  
3. 기능 요구사항 (기능적 요구사항)  
4. 비기능 요구사항  
5. 시스템 아키텍처 (기술 설계)  
6. 상세 컴포넌트 설계  
7. 배포 및 인프라 설계 (Supabase, Railway, Netlify 포함)  
8. 접근성(Accessibility) 및 시니어 친화적 UI/UX 가이드 (TTS 포함)  
9. 보안, 모니터링 및 로깅  
10. 개발/테스트/배포 일정(권장)  
11. 부록: API 목록 및 데이터베이스 스키마 개요

---

## 1. 프로젝트 개요
한국 주식 시장을 대상으로 하는 **실시간 반응형 트레이딩 인텔리전스 플랫폼**입니다.  
목표는 초단타/단타 트레이더가 보유 종목과 관련된 실시간 시세, 뉴스, 경제/정책 이벤트를 즉시 인지하고, AI 기반 분석을 통해 빠르게 의사결정 할 수 있도록 지원하는 것 입니다.  
특히 50~60대 사용자도 쉽게 사용할 수 있도록 TTS(텍스트 음성 변환), 큰 글꼴, 고대비 UI 등 접근성 요소를 강화합니다.

---

## 2. 비즈니스 및 사용자 요구사항
### 2.1 비즈니스 요구사항
- 사용자가 실시간으로 시장 변동을 인지하고, 그 즉시 매매 결정을 내리게끔 도움.
- 프론트엔드는 Netlify로 빠르게 배포하고, 백엔드는 Railway에 마이크로서비스로 배포.
- DB 및 인증은 Supabase를 사용하여 신속한 프로토타입 및 확장성 확보.
- AI 분석 기능은 Claude API 또는 OpenAI API를 선택적으로 사용 가능.

### 2.2 사용자 요구사항
- HFT/단타 트레이더: 1초 이내의 가격 갱신, 빠른 알림과 시각적 경고.
- 50~60대 시니어 유저: 가독성 높은 UI, 큰 버튼, 간단한 인터랙션, TTS 및 음성 알림.
- 모바일/데스크톱에서 모두 신속한 알림 수신(웹 푸시/모바일 푸시).

---

## 3. 기능 요구사항 (기능적)
### 3.1 실시간 시세 스트리밍
- WebSocket을 통해 초/틱 단위 가격, 호가, 체결량 업데이트.
- 종목별 실시간 미니차트(1분봉, 5분봉) 및 현재가/등락률 표시.

### 3.2 뉴스 수집 및 실시간 분석
- 다중 뉴스 소스(RSS/API) 크롤링: Naver, Yonhap, Google News RSS 등.
- 기사 → 요약 → 감성(긍정/부정/중립) → 영향도(0~1) → 행동권고(매수/매도/관망) 생성(Claude/OpenAI 사용).

### 3.3 포트폴리오 연동
- 사용자 보유 종목을 증권사 API 또는 수동 입력으로 등록.
- 종목별 수익률/평균단가/평가손익 실시간 계산.

### 3.4 알림 및 행동 트리거
- 변동률 기준(예: ±3%) 또는 AI 영향도 기준(예: 부정도 ≥ 0.7)으로 푸시 알림 발송.
- 웹 푸시(Notification API), FCM 연동(모바일 앱) 지원.
- TTS 자동 재생 옵션(중요 이벤트만).

### 3.5 AI 챗/질의응답
- 사용자가 자연어로 질의하면 포트폴리오·뉴스·지표를 반영해 응답.
- 예: "오늘 삼성전자 관련 부정 뉴스가 있어?" → 요약 + 영향 평가 제공.

### 3.6 백테스트 및 시뮬레이션 (옵션)
- 전략 백테스트(Backtrader 또는 Pandas 기반), 성능 지표 제공(MDD, CAGR 등).

---

## 4. 비기능 요구사항
- 반응성: 주가/뉴스 알림 지연 ≤ 5초 (목표 1~2초)
- 가용성: 99.5% 이상(프로덕션), 장애복구 자동 재연결
- 확장성: 마이크로서비스 구조로 AI/뉴스/스트리밍 분리
- 보안: TLS, JWT 기반 인증(Supabase Auth), 민감정보 암호화
- 로깅 & 모니터링: 중앙집중형 로깅(예: Logflare/Sentry), 지표 모니터링(Prometheus/Grafana or Railway built-in)

---

## 5. 시스템 아키텍처 (기술 설계)
```
[Frontend - Netlify]
  - React + TailwindCSS
  - WebSocket Client (Socket.IO or native)
  - Web Push, TTS (Web Speech API)
  - Accessibility layer (큰 글꼴, 고대비, 간단한 버튼)

[Backend - Railway (Microservices)]
  - Stream Service (Node.js) : 실시간 주가 수신, Redis Pub/Sub
  - News Crawler (Python) : RSS/API 크롤링, 키워드 필터링
  - AI Service (Python FastAPI) : Claude/OpenAI 호출, 결과 후처리
  - Alert Service (Node.js) : 이벤트 트리거 및 Push 전송
  - Auth & DB : Supabase (Postgres) - 사용자, 포트폴리오, 로그 저장

[Optional]
  - Worker (Backtesting) : Python (Celery/RQ)
  - Caching : Redis (또는 Railway의 Redis add-on)
```

---

## 6. 상세 컴포넌트 설계

### 6.1 Frontend (React)
- 페이지
  - Dashboard: 종목 카드 Grid, 전체 포트폴리오 요약
  - Detail: 종목 상세 (호가/체결/뉴스/AI 코멘트)
  - Alerts: 알림 로그
  - Settings: 알림 민감도, TTS 설정, 접근성 옵션
- 컴포넌트
  - RealtimeTicker (WebSocket connect, reconnect logic)
  - MiniChart (1min/5min)
  - NewsCard (요약, 감성, 영향도, '더보기' 버튼)
  - LargeActionButton (시니어 친화적 크기)
- TTS
  - Web Speech API (SpeechSynthesis)
  - 옵션: 자동재생(중요 이벤트), 수동재생(뉴스 카드의 큰 재생 버튼)
- Accessibility
  - High contrast mode, Large font mode, Reduced motion mode
  - Keyboard navigation support
  - ARIA attributes

### 6.2 Backend Services
- Stream Service (Node.js)
  - Data sources: 한국 증권사 WebSocket / KRX 데이터 provider
  - Responsibilities: 데이터 수집 → Redis Pub/Sub 발행 → DB 저널링(선택)
  - Rate-limiting, Fan-out: 다수 클라이언트에 실시간 전송
- News Crawler (Python)
  - Scheduler: cron 또는 APScheduler
  - NLP: Named-entity recognition(종목명 추출), 키워드 태깅
  - 결과: raw news + summary + tags 저장
- AI Service (FastAPI)
  - Input: article text + context(포트폴리오, 종목)
  - Model: Claude/OpenAI API (추천), fallback to Hugging Face models
  - Output: summary, sentiment_score, impact_score(0~1), recommended_action
  - Caching: 동일 뉴스 재분석 방지
- Alert Service
  - 트리거 규칙 엔진 (룰 기반 + AI 점수)
  - Push 발송: Web Push / FCM
  - 用户定制规则 평가

### 6.3 데이터베이스 (Supabase/Postgres) 기본 테이블
- users (id, email, name, settings)
- portfolios (id, user_id, symbol, avg_price, qty, created_at)
- watchlist (user_id, symbol)
- news (id, source, title, content, published_at, summary, sentiment_score, impact_score, related_symbols)
- alerts (id, user_id, type, payload, status, created_at)
- events_log (service, payload, created_at)

---

## 7. 배포 및 인프라 설계 (Supabase, Railway, Netlify)
### 7.1 Netlify (Frontend)
- 빌드: React (Vite or Create React App)
- 환경변수: REACT_APP_WS_URL, REACT_APP_SUPABASE_URL, REACT_APP_SUPABASE_ANON_KEY
- 배포 파이프라인: GitHub → Netlify 자동 배포 (PR preview)

### 7.2 Railway (Backend)
- 각 마이크로서비스를 Railway 프로젝트로 생성
  - stream-service (Node.js)
  - news-service (Python)
  - ai-service (Python)
  - alert-service (Node.js)
- Railway 플러그인: PostgreSQL (선택) 또는 Supabase DB 사용, Redis add-on 사용 권장
- 환경변수: OPENAI_API_KEY / CLAUDE_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY, FCM_SERVER_KEY 등
- 권장: 각 서비스에 Health-check 및 readiness probe 설정

### 7.3 Supabase
- Auth: Supabase Auth (이메일/비밀번호 + OAuth 옵션)
- DB: Postgres (위 테이블 생성)
- Storage: 뉴스 원문/이미지 저장(필요 시)
- RLS (Row Level Security) 정책: 사용자 데이터 보호
- Supabase Edge Functions (필요 시): 간단한 서버리스 엔드포인트

---

## 8. 접근성(Accessibility) 및 시니어 친화적 UI/UX 가이드
### 8.1 비주얼 가이드
- 기본 글꼴 크기: 18px 이상, 헤더는 24px 이상 권장
- 버튼 크기: 최소 48x48 px (터치 친화적)
- 명도 대비: WCAG AA 또는 AAA 준수 (텍스트와 배경 간 명도비 ≥ 4.5:1)
- 색상 사용: 색상만으로 의미 전달하지 않기 (아이콘/텍스트 보조)
- 레이아웃: 카드/그리드로 단일 뷰에서 핵심 정보 노출

### 8.2 TTS & 음성 알림
- Web 환경: Web Speech API (SpeechSynthesis) 사용
- 음성 옵션: 음성 속도, 음성 볼륨, 자동 읽기 임계값(예: impact_score ≥ 0.8)
- 음성 UI: 각 뉴스 카드에 “▶ 듣기” 버튼, 설정에서 자동 알림 읽기 ON/OFF
- 음성 언어: 한국어 자연스러운 발음 사용 (locale: ko-KR)
- 폴백: 브라우저가 TTS 미지원일 경우, 알림 배너로 대체

### 8.3 상호작용 단순화
- 핵심 버튼만 배치 (매수/매도/관망-권고 표시)
- 한 화면에 너무 많은 정보 집약 금지 — 중요한 항목을 우선 노출
- 도움말/도구팁 제공 (큰 글씨/짧은 문장)

---

## 9. 보안, 모니터링 및 로깅
### 9.1 보안
- 모든 통신 TLS(HTTPS/WSS)
- Supabase Auth(JWT) 사용, 서비스 키는 서버 측에서만 사용
- API Rate limit 및 Abuse 검출
- 민감 데이터(사용자 토큰 등) 암호화 저장

### 9.2 모니터링
- Sentry 또는 Railway 내장 모니터링으로 오류 추적
- Logflare 또는 Elastic Stack을 통한 로그 중앙화
- Redis/DB 지표 모니터링: 연결수, 대기열 길이 등

### 9.3 로깅
- 중요한 이벤트(알림 전송, AI 분석 결과, 웹소켓 연결/재연결) 로깅
- 사용자 조작 로그(설정 변경, 마감 주문 실행 등) 보관(기간 정책 필요)

---

## 10. 개발/테스트/배포 일정(권장)
- Week 0: 요구사항 최종화, 인프라 계정 생성(Supabase, Netlify, Railway)
- Week 1-2: 기본 인프라 및 인증(로그인), 포트폴리오 DB 설계
- Week 3-4: 실시간 스트리밍(기초), 프론트엔드 대시보드 MVP
- Week 5-6: 뉴스 크롤러 + AI 분석 연동 (Claude/OpenAI)
- Week 7: 알림 시스템(FCM/Web Push) 연동, TTS 통합
- Week 8: 백테스트/시뮬레이션, QA 및 퍼포먼스 튜닝
- Week 9: 베타 배포, 사용자 테스트(특히 50~60대 표본)
- Week 10: 수정 및 정식 배포

---

## 11. 부록: API 목록 (주요 엔드포인트 예시) 및 DB 스키마 개요
### 11.1 대표 API (REST)
- `POST /api/auth/login` - 로그인 (Supabase Auth 사용 권장)
- `GET /api/stream/connect` - WebSocket 업그레이드 (실시간 시세)
- `GET /api/news/recent?symbols=XXX` - 특정 종목 관련 최신 뉴스
- `POST /api/ai/analyze` - 기사 텍스트에 대한 AI 분석 요청 (요약/감성/권고)
- `POST /api/alerts` - 사용자 알림 규칙 등록
- `GET /api/portfolio/:userId` - 사용자 포트폴리오 조회

### 11.2 간단 DB 스키마 예제 (Postgres)
```sql
CREATE TABLE users (
  id uuid PRIMARY KEY,
  email text UNIQUE,
  name text,
  settings jsonb,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE portfolios (
  id uuid PRIMARY KEY,
  user_id uuid REFERENCES users(id),
  symbol text,
  avg_price numeric,
  qty numeric,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE news (
  id uuid PRIMARY KEY,
  source text,
  title text,
  content text,
  published_at timestamptz,
  summary text,
  sentiment_score numeric,
  impact_score numeric,
  related_symbols text[],
  created_at timestamptz DEFAULT now()
);

CREATE TABLE alerts (
  id uuid PRIMARY KEY,
  user_id uuid REFERENCES users(id),
  type text,
  params jsonb,
  status text,
  created_at timestamptz DEFAULT now()
);
```

---

## 최종 요약
- Netlify(프론트엔드) + Railway(마이크로서비스 백엔드) + Supabase(DB/Auth)를 기본 인프라로 채택합니다.  
- AI 분석은 Claude 혹은 OpenAI API를 사용하며, NLP 파이프라인은 파이썬 기반(행동 권고, 감성, 요약)으로 구성합니다.  
- 시니어 사용자를 고려한 접근성(큰 글꼴, 고대비 모드, TTS 자동 읽기 등)을 핵심 비기능 요구사항으로 반영합니다.  
- MVP 우선순위: 실시간 시세 + 실시간 뉴스 수집 + AI 간단 분석 + 푸시 알림 + 시니어 친화 UI

---

*문서 끝*
