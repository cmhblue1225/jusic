# 📈 실시간 트레이딩 인텔리전스 플랫폼 (Jusik)

AI 기반 실시간 주식 뉴스 분석 및 가격 모니터링 시스템

## 🚀 주요 기능

### Phase 1: 핵심 인프라 ✅
- ✅ Supabase 인증 시스템
- ✅ 사용자 프로필 관리
- ✅ 포트폴리오 관리
- ✅ 관심 종목 관리
- ✅ 수익률 통계

### Phase 2: 실시간 시스템 ✅
- ✅ 한국투자증권 WebSocket 실시간 시세
- ✅ Socket.IO 기반 실시간 데이터 스트리밍
- ✅ Redis Pub/Sub 메시지 큐
- ✅ 프론트엔드 실시간 대시보드

### Phase 2.3: 뉴스 크롤링 & AI 분석 ✅
- ✅ 네이버 뉴스 검색 API 연동 (일일 25,000건)
- ✅ 상위 50개 종목 타겟 크롤링
- ✅ NER 기반 종목 코드 추출
- ✅ Claude AI 뉴스 분석 (영향도, 감정, 권고)
- ✅ Redis 캐싱 시스템

### Phase 2.4: 실시간 알림 시스템 ✅
- ✅ 가격 변동 모니터링 (5초 주기)
- ✅ 고영향도 뉴스 감지 (30초 주기)
- ✅ TTS 음성 알림 (Web Speech API)
- ✅ 중복 알림 방지

---

## 🏗️ 아키텍처

```
┌─────────────┐      ┌──────────────┐      ┌────────────┐
│  Frontend   │─────▶│Stream Service│─────▶│  Supabase  │
│(React+Vite) │      │(WebSocket+   │      │(PostgreSQL)│
│             │◀─────│ Socket.IO)   │◀─────│            │
└─────────────┘      └──────────────┘      └────────────┘
       │                     │
       │                     │
       ▼                     ▼
┌─────────────┐      ┌──────────────┐
│News Crawler │─────▶│ AI Service   │
│(Python      │      │(Claude AI/   │
│ FastAPI)    │      │ OpenAI)      │
└─────────────┘      └──────────────┘
       │                     │
       └──────┬──────────────┘
              ▼
       ┌─────────────┐
       │    Redis    │
       │(Pub/Sub +   │
       │  Cache)     │
       └─────────────┘
```

---

## 📦 기술 스택

### Frontend
- React 19 + TypeScript
- Vite
- Tailwind CSS 3.4
- Zustand (상태 관리)
- React Router 7
- Socket.IO Client

### Backend Services

#### Stream Service (Node.js)
- Express.js
- Socket.IO
- Redis (Pub/Sub)
- WebSocket (한국투자증권 API)

#### News Crawler (Python)
- FastAPI
- httpx (Async HTTP)
- Naver News Search API
- KoNLPy (NER)
- APScheduler

#### AI Service (Python)
- FastAPI
- Anthropic Claude AI
- OpenAI GPT
- Redis (Caching)

### 데이터베이스 & 인프라
- Supabase (PostgreSQL + Realtime + Auth)
- Redis (Pub/Sub + Caching)
- Railway (Deployment)

---

## 🛠️ 로컬 개발 환경 설정

### 1. 저장소 클론
```bash
git clone https://github.com/cmhblue1225/jusic.git
cd jusik
```

### 2. 환경 변수 설정
루트 디렉토리에 `.env` 파일 생성:

```env
# Supabase
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# AI API Keys
CLAUDE_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key

# 한국투자증권 API
KIS_APP_KEY=your_kis_app_key
KIS_APP_SECRET=your_kis_app_secret
KIS_BASE_URL=https://openapi.koreainvestment.com:9443

# 네이버 API
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret

# Redis
REDIS_URL=redis://localhost:6379
```

각 백엔드 서비스 디렉토리에도 `.env` 파일을 복사하세요.

### 3. Redis 설치 (필수)
```bash
# macOS
brew install redis
brew services start redis

# Linux
sudo apt-get install redis-server
sudo systemctl start redis
```

### 4. Frontend 실행
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### 5. Stream Service 실행
```bash
cd backend/stream-service
npm install
node server.js
# → http://localhost:3001
```

### 6. AI Service 실행
```bash
cd backend/ai-service
pip3 install -r requirements.txt
python3 main.py
# → http://localhost:3003
```

### 7. News Crawler 실행
```bash
cd backend/news-crawler
pip3 install -r requirements.txt
python3 main.py
# → http://localhost:3002
```

---

## 🚀 Railway 배포

### 배포 순서
1. **AI Service** 먼저 배포
2. **News Crawler** 배포 (AI Service URL 설정)
3. **Redis 추가** (Railway Add-on)
4. **Stream Service** 배포
5. **Frontend** 마지막 배포

### 환경 변수 설정
자세한 내용은 [`RAILWAY_ENV.md`](./RAILWAY_ENV.md) 참조

---

## 📊 데이터베이스 스키마

### 주요 테이블
- `profiles` - 사용자 프로필
- `portfolios` - 보유 종목
- `watchlist` - 관심 종목
- `news` - 뉴스 데이터 (AI 분석 포함)
- `stock_master` - 종목 마스터 데이터
- `stock_prices` - 실시간 가격 데이터
- `alerts` - 사용자 알림

---

## 📈 API 한도

| 서비스 | 일일 한도 | 현재 사용량 |
|--------|-----------|-------------|
| 네이버 뉴스 검색 | 25,000건 | ~14,400건 (5분 주기) |
| 한국투자증권 WebSocket | 무제한 | 실시간 스트리밍 |
| Claude AI | 사용량 기반 | 뉴스 분석 캐싱 적용 |

---

## 🔒 보안

- Supabase RLS (Row Level Security) 적용
- JWT 기반 인증
- API 키는 환경 변수로 관리 (.env 파일 gitignore)
- CORS 설정 (프로덕션 도메인만 허용)

---

## 📝 라이선스

MIT License

---

## 👨‍💻 개발자

- GitHub: [@cmhblue1225](https://github.com/cmhblue1225)
- Repository: [jusic](https://github.com/cmhblue1225/jusic)

---

## 🙏 감사의 말

- [Supabase](https://supabase.com/) - 백엔드 인프라
- [Railway](https://railway.app/) - 호스팅
- [Anthropic Claude](https://www.anthropic.com/) - AI 분석
- [Naver](https://developers.naver.com/) - 뉴스 API
- [한국투자증권](https://apiportal.koreainvestment.com/) - 실시간 시세 API
