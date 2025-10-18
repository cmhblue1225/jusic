# Railway 환경 변수 설정 가이드

Railway에서 각 서비스마다 아래 환경 변수를 설정해야 합니다.

---

## 🔵 AI Service

```
# Supabase
SUPABASE_URL=https://lrmvoldeyetuzuwuazdm.supabase.co
SUPABASE_SERVICE_KEY=your_supabase_service_key

# AI API Keys
CLAUDE_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key

# Redis (Railway에서 Redis 추가 후 자동 생성됨)
REDIS_URL=${{Redis.REDIS_URL}}

# Port (자동 설정)
PORT=${{PORT}}
```

---

## 📰 News Crawler Service

```
# Supabase
SUPABASE_URL=https://lrmvoldeyetuzuwuazdm.supabase.co
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Naver API
NAVER_CLIENT_ID=YD_yXJJDefvDhROi14Tc
NAVER_CLIENT_SECRET=kjuclsjh9N

# AI Service URL (Railway 내부 URL)
AI_SERVICE_URL=http://ai-service.railway.internal:${{AI_Service.PORT}}

# Port (자동 설정)
PORT=${{PORT}}
```

---

## 🌊 Stream Service

```
# Supabase
VITE_SUPABASE_URL=https://lrmvoldeyetuzuwuazdm.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# KIS API
KIS_APP_KEY=your_kis_app_key
KIS_APP_SECRET=your_kis_app_secret
KIS_BASE_URL=https://openapi.koreainvestment.com:9443

# Redis (Railway에서 Redis 추가 후 자동 생성됨)
REDIS_URL=${{Redis.REDIS_URL}}

# CORS
CORS_ORIGIN=${{Frontend.RAILWAY_PUBLIC_DOMAIN}}

# Port (자동 설정)
PORT=${{PORT}}
```

---

## 🎨 Frontend

```
# Supabase
VITE_SUPABASE_URL=https://lrmvoldeyetuzuwuazdm.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key

# Backend Services URLs
VITE_STREAM_SERVICE_URL=${{Stream_Service.RAILWAY_PUBLIC_DOMAIN}}

# Port (자동 설정)
PORT=${{PORT}}
```

---

## 📝 설정 순서

1. **AI Service** 배포 → URL 복사
2. **News Crawler** 배포 → AI_SERVICE_URL 설정
3. **Redis 추가** → Stream Service와 AI Service에 연결
4. **Stream Service** 배포 → URL 복사
5. **Frontend** 배포 → VITE_STREAM_SERVICE_URL 설정

---

## 🔗 Railway 내부 URL 형식

- `http://서비스이름.railway.internal:포트`
- 예: `http://ai-service.railway.internal:3003`
- Railway는 서비스 간 내부 네트워킹을 자동으로 처리합니다.

---

## ⚠️ 주의사항

1. `.env` 파일은 절대 커밋하지 마세요 (.gitignore에 추가됨)
2. API 키는 Railway UI에서 직접 입력하세요
3. `${{변수명}}` 형식은 Railway의 변수 참조 문법입니다
4. 프로덕션에서는 반드시 `SUPABASE_SERVICE_KEY`를 사용하세요 (RLS 우회)
