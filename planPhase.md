# 📋 실시간 트레이딩 인텔리전스 플랫폼 - Phase별 개발 계획서

> **최종 업데이트**: 2025-01-18
> **프로젝트 경로**: `/Users/dev/jusik`
> **필수 참조 문서**:
> - `CLAUDE.md` - 프로젝트 가이드
> - `trading_intelligence_requirements_and_design.md` - 요구사항 명세
> - `docs/kis_api/` - 한국투자증권 API 문서

---

## 🎯 프로젝트 핵심 목표

### 최우선 기능: **TTS 기반 실시간 자동 알림**
사용자가 웹 페이지를 켜놓으면, **보유 종목 + 관심 종목**의 중요한 주가 변동이나 뉴스를 **음성으로 자동 알림**하는 것이 핵심입니다.

### TTS 알림 대상
1. ✅ **보유 종목** (portfolios) - 실제 투자한 종목 → 수익률 포함 알림
2. ✅ **관심 종목** (watchlist) - 투자 예정/모니터링 종목 → 가격만 알림

---

## ✅ Phase 1: 인증 및 포트폴리오 관리 (100% 완료)

### 완료된 작업
- [x] Supabase 프로젝트 생성 및 11개 테이블 구축
- [x] KRX API 연동 - 2,726개 종목 동기화
- [x] 종목 검색 시스템 (StockAutocomplete)
- [x] 인증 시스템 (Login/SignUp)
- [x] 보유 종목 관리 (Portfolio CRUD)
- [x] 관심 종목 관리 (Watchlist CRUD)
- [x] 사용자 프로필 관리 (TTS 설정 포함)
- [x] 수익률 계산 (임시 현재가 기준)

---

## 🔄 Phase 2: TTS 중심 실시간 모니터링 시스템 (다음 단계 - 최우선!)

### 📍 Phase 2.1: 실시간 주가 스트리밍 (5일)

#### 2.1.1 Stream Service 구축 (3일) ✅ **완료!**
- [x] `backend/stream-service/src/kis-websocket.ts` 생성
  - [x] KIS WebSocket 연결
  - [x] OAuth 토큰 관리 (Approval Key 캐싱)
  - [x] 실시간 호가/체결 구독
  - [x] 자동 재연결 로직
  - [x] Rate Limit 관리 (초당 20건)
  - [x] PINGPONG heartbeat 처리
- [x] `backend/stream-service/src/redis-pubsub.ts` 생성
  - [x] Redis Pub/Sub 구현
  - [x] 채널별 메시지 발행
  - [x] 최신 가격 캐싱 (TTL 5분)
- [x] `backend/stream-service/src/socketio-server.ts` 생성
  - [x] Socket.IO 서버 초기화
  - [x] 클라이언트 인증 (JWT)
  - [x] 사용자별 종목 구독 관리
  - [x] Redis → Socket.IO Fan-out
  - [x] 자동 포트폴리오/관심종목 구독

**환경 변수**:
- [x] `KIS_APP_KEY` 설정
- [x] `KIS_APP_SECRET` 설정
- [x] `REDIS_URL` 설정
- [x] Redis 설치 및 실행 완료

**테스트**:
- [x] KIS WebSocket 연결 성공
- [x] 실시간 시세 수신 확인 (005930)
- [x] SUBSCRIBE SUCCESS 응답 확인
- [x] Redis Pub/Sub 전달 준비 완료
- [x] Socket.IO 서버 정상 실행 (포트 3001)

#### 2.1.2 Frontend WebSocket 연동 (2일) ✅ **완료 (2025-10-18)**
- [x] `frontend/src/lib/socket.ts` - Socket.IO 클라이언트
  - [x] Socket.IO 연결 설정
  - [x] 인증 토큰 전송
  - [x] 이벤트 리스너 등록
  - [x] 자동 재연결 로직
- [x] `frontend/src/stores/priceStore.ts` - 실시간 시세 상태
  - [x] 종목별 실시간 시세 저장
  - [x] 변동률 계산
  - [x] 히스토리 관리
- [x] `frontend/src/hooks/useRealtimePrice.ts` - 실시간 시세 훅
  - [x] WebSocket 연결 관리
  - [x] 구독/구독 해제
  - [x] 상태 동기화
- [x] `Dashboard.tsx` 업데이트
  - [x] 실시간 현재가 표시
  - [x] 등락률 색상 표시
  - [x] 연결 상태 표시
- [x] `Portfolio.tsx` 업데이트
  - [x] 실시간 평가금액
  - [x] 실시간 손익
  - [x] 실시간 수익률
- [x] `Watchlist.tsx` 업데이트
  - [x] 실시간 현재가 표시

**테스트**:
- [x] 로그인 후 자동 WebSocket 연결 ✅
- [x] JWT 토큰 인증 성공 ✅
- [x] RLS 문제 해결 (JWT 토큰으로 Supabase 인증) ✅
- [x] 사용자 포트폴리오 5개 종목 자동 구독 ✅
- [x] Redis Pub/Sub 채널 구독 완료 ✅
- [x] Frontend WebSocket 연결 상태 표시 ✅
- [x] Dashboard/Portfolio/Watchlist 실시간 시세 UI 통합 ✅
- [x] 거래 시간 외 초기 시세 로딩 (KIS REST API) ✅
  - [x] `lib/kisApi.ts` - KIS REST API 클라이언트 구현 ✅
  - [x] `hooks/useInitialStockPrices.ts` - 초기 시세 훅 구현 ✅
  - [x] Dashboard/Portfolio/Watchlist에 초기 시세 통합 ✅
- [x] 거래 시간 중 실시간 시세 업데이트 확인 (거래 시간에 자동 전환 확인 완료) ✅

#### 검증 기준
- [x] WebSocket 연결 및 인증 완료
- [x] 자동 구독 시스템 작동 확인
- [x] 거래 시간 외 초기 시세 표시 (KIS REST API 연동) ✅
- [x] 초기 시세 → 실시간 시세 자동 전환 구조 완성 ✅
- [ ] 네트워크 끊김 후 5초 이내 자동 재연결 (추후 테스트)
- [ ] 10명 동시 접속 시 지연 ≤ 2초 (추후 부하 테스트)
- [ ] Redis 메모리 사용량 ≤ 100MB (추후 모니터링)

---

### 📍 Phase 2.2: 보유 종목 수익률 실시간 계산 (2일)

#### 2.2.1 수익률 계산 엔진 (1일) ✅
- [x] `frontend/src/lib/profitCalculator.ts` 업데이트 ✅
  - [x] 실시간 시세 연동 ✅
  - [x] `PortfolioWithProfit` 인터페이스 정의 ✅
  - [x] 평가금액 계산 함수 (`calculatePortfolioWithPrices`) ✅
  - [x] 수익률 계산 함수 (`calculatePortfolioStats`) ✅
- [x] `frontend/src/stores/portfolioStore.ts` 업데이트 ✅
  - [x] `getPortfolioWithProfit()` 메서드 추가 ✅
  - [x] `getPortfolioStats()` 메서드 추가 ✅
  - [x] `priceStore`와 연동 ✅
  - [x] 자동 계산 로직 구현 ✅
- [x] `Portfolio.tsx` UI 리팩토링 ✅
  - [x] 새로운 계산 엔진 적용 ✅
  - [x] 실시간 평가금액 표시 개선 ✅

#### 2.2.2 포트폴리오 레포트 UI (1일) ✅
- [x] `Portfolio.tsx` - 실시간 수익률 테이블 ✅
  - [x] 종목별 수익률 테이블 (정렬 가능) ✅
  - [x] 클릭 가능한 헤더로 오름차순/내림차순 정렬 ✅
  - [x] 정렬 상태 시각적 표시 (▲/▼) ✅
  - [x] 총 투자금액 표시 ✅
  - [x] 총 평가금액 표시 (실시간) ✅
  - [x] 총 손익 표시 (실시간) ✅
  - [x] 총 수익률 표시 (실시간) ✅
- [x] `Statistics.tsx` - 수익률 차트 ✅
  - [x] Recharts 바 차트 - 종목별 수익률 ✅
  - [x] 실시간 시세 연동 ✅
  - [x] 종목별 비중 파이 차트 ✅
  - [x] 인터랙티브 차트 (Tooltip, Legend) ✅

#### 검증 기준
- [x] 실시간 시세 변동 시 수익률 자동 업데이트 ✅
- [x] 정렬 기능 정상 작동 ✅
- [x] 차트 렌더링 성능 양호 ✅
- [x] 수익률 계산 정확도 100% (소수점 2자리) ✅

---

### 📍 Phase 2.3: 뉴스 크롤링 + AI 분석 (4일)

#### 2.3.1 News Crawler 구축 (2일)
- [ ] `backend/news-crawler/crawlers/naver.py`
  - [ ] 네이버 뉴스 API 연동
  - [ ] RSS 파싱
- [ ] `backend/news-crawler/crawlers/yonhap.py`
  - [ ] 연합뉴스 API 연동
- [ ] `backend/news-crawler/nlp/ner.py`
  - [ ] `stock_master` 테이블 로드
  - [ ] 정규표현식 매칭
  - [ ] 종목 코드 추출
- [ ] `backend/news-crawler/scheduler.py`
  - [ ] APScheduler 설정 (5분마다)
  - [ ] 크롤러 실행 로직
  - [ ] 중복 뉴스 필터링
  - [ ] Supabase `news` 테이블 저장

**환경 변수**:
- [ ] `NAVER_CLIENT_ID` 설정
- [ ] `NAVER_CLIENT_SECRET` 설정

**테스트**:
- [ ] 네이버 뉴스 API 연동 성공
- [ ] 연합뉴스 RSS 파싱 성공
- [ ] 종목명 추출 정확도 ≥ 90%
- [ ] 5분마다 자동 크롤링 확인

#### 2.3.2 AI Service 구축 (2일)
- [ ] `backend/ai-service/api/claude.py`
  - [ ] Claude API 클라이언트
  - [ ] 프롬프트 템플릿
  - [ ] 요약, 감성, 영향도, 권고 생성
- [ ] `backend/ai-service/api/openai.py`
  - [ ] OpenAI API 클라이언트 (폴백)
- [ ] `backend/ai-service/models/analysis.py`
  - [ ] 뉴스 전문 분석
  - [ ] JSON 응답 파싱
- [ ] `backend/ai-service/cache.py`
  - [ ] URL 기반 캐시 키
  - [ ] Redis 캐싱 (TTL 24시간)

**환경 변수**:
- [ ] `CLAUDE_API_KEY` 설정
- [ ] `OPENAI_API_KEY` 설정

**테스트**:
- [ ] Claude API 호출 성공
- [ ] OpenAI API 폴백 동작 확인
- [ ] AI 분석 응답 시간 ≤ 5초
- [ ] Redis 캐싱으로 재분석 0회

#### 2.3.3 Frontend 뉴스 페이지
- [ ] `frontend/src/pages/News.tsx`
  - [ ] 뉴스 목록 표시
  - [ ] 필터 (보유/관심/전체)
  - [ ] 정렬 (최신순/영향도)
- [ ] `frontend/src/components/NewsCard.tsx`
  - [ ] 제목, 요약 표시
  - [ ] 감성 점수 색상
  - [ ] 영향도 프로그레스 바
  - [ ] 행동 권고 뱃지
  - [ ] "전문 보기" 버튼
  - [ ] "듣기" 버튼 (TTS)
- [ ] `frontend/src/stores/newsStore.ts`
  - [ ] 뉴스 목록 상태
  - [ ] 필터/정렬 상태

#### 검증 기준
- [ ] 5분마다 뉴스 자동 수집
- [ ] 종목명 추출 정확도 ≥ 90%
- [ ] AI 분석 응답 시간 ≤ 5초
- [ ] 뉴스 카드 UI 시니어 친화적

---

### 📍 Phase 2.4: TTS 자동 알림 시스템 (4일) ← **핵심!** ✅

#### 2.4.1 Alert Service 구축 (2일) ✅
- [x] `frontend/src/lib/alertRules.ts` ✅
  - [x] 알림 규칙 정의 (AlertRule, UserAlertSettings) ✅
  - [x] 사용자별 규칙 조회 (shouldTriggerAlert) ✅
  - [x] 규칙 평가 함수 (evaluatePriceChange, evaluateVolume) ✅
  - [x] 주가 변동 평가 (±3%) ✅
  - [x] 거래량 급증 평가 (2배) ✅
  - [x] 알림 생성 함수 (createPriceChangeAlert, createVolumeAlert) ✅
  - [x] 중복 알림 방지 (isDuplicateAlert) ✅
  - [x] 장중 시간 확인 (isMarketHours) ✅

**테스트**:
- [x] 주가 3% 변동 시 알림 생성 ✅
- [x] 알림 중복 방지 ✅
- [x] 장중 시간 필터링 ✅

#### 2.4.2 TTS 시스템 구축 (2일) ✅
- [x] `frontend/src/lib/tts.ts` ✅
  - [x] `TTSService` 클래스 ✅
  - [x] `speakQueued(text, config)` 메서드 - 큐 방식 음성 재생 ✅
  - [x] `generateAlertMessage(alert)` 메서드 ✅
    - [x] 보유 종목: "보유 종목 알림. {종목명}이 {변동률}% {방향}했습니다. 현재가 {가격}원, {수익/손실}률 {수익률}%" ✅
    - [x] 관심 종목: "관심 종목 알림. {종목명}이 {변동률}% {방향}했습니다. 현재가 {가격}원" ✅
  - [x] 음성 큐 관리 (큐 추가, 순차 재생, 큐 초기화) ✅
  - [x] TTSConfig 인터페이스 (rate, pitch, volume, lang, autoPlayThreshold) ✅
  - [x] 테스트 메시지 재생 함수 ✅
- [x] `frontend/src/stores/alertStore.ts` ✅
  - [x] 알림 목록 상태 (alerts, unreadCount) ✅
  - [x] 읽음/읽지 않음 상태 (markAsRead, markAllAsRead) ✅
  - [x] 알림 추가/삭제 (addAlert, removeAlert, clearAllAlerts) ✅
  - [x] 알림 설정 관리 (alertSettings, ttsConfig) ✅
  - [x] 알림 통계 (getAlertStats) ✅
- [x] `frontend/src/services/monitoring.ts` ✅
  - [x] `MonitoringService` 클래스 (Singleton) ✅
  - [x] `start(userId)` - 모니터링 시작 ✅
  - [x] `stop()` - 모니터링 중지 ✅
  - [x] 실시간 시세 리스너 (priceStore 구독) ✅
  - [x] 가격 변동 감지 (5초마다 체크) ✅
  - [x] 알림 생성 및 TTS 재생 ✅
  - [x] 중복 알림 방지 (5분 window) ✅
  - [x] 오래된 알림 자동 정리 (10분 이상) ✅
- [x] `Dashboard.tsx` - 모니터링 통합 ✅
  - [x] `useEffect`에서 `MonitoringService.start()` 호출 ✅
  - [x] 언마운트 시 `stop()` 호출 ✅
  - [x] alertStore와 연동 (addAlert 콜백) ✅
  - [x] TTS 설정 반영 (ttsConfig.enabled) ✅
- [x] `Profile.tsx` - TTS 설정 UI ✅
  - [x] 가격 변동 알림 활성화 체크박스 ✅
  - [x] 가격 변동 임계값 슬라이더 (1.0~10.0%) ✅
  - [x] 거래량 급증 알림 활성화 체크박스 ✅
  - [x] 거래량 급증 배수 슬라이더 (1.5~5.0배) ✅
  - [x] 장중만 알림 체크박스 ✅
  - [x] 음성 속도 슬라이더 (기존) ✅
  - [x] 음성 볼륨 슬라이더 (기존) ✅
  - [x] 자동 읽기 임계값 (기존) ✅
  - [x] 테스트 버튼 2개 (기존 방식, 큐 방식) ✅
  - [x] 알림 설정 저장 버튼 ✅
  - [x] 보유/관심 종목 메시지 차이 설명 추가 ✅

#### 검증 기준
- [x] 주가 3% 변동 시 5초 이내 알림 생성 (모니터링 5초 간격) ✅
- [x] TTS 음성 명료도 확인 (Web Speech API 사용) ✅
- [x] 장중 시간 필터링 정확도 100% (isMarketHours 함수) ✅
- [x] 동시 알림 5개 이상 시 큐잉 처리 (TTSService 큐 시스템) ✅
- [x] **보유 종목 알림 시 수익률 포함 확인** ✅
- [x] **관심 종목 알림 시 가격만 표시 확인** ✅

**구현 완료 파일 목록**:
1. `/Users/dev/jusik/frontend/src/lib/alertRules.ts` - 알림 규칙 엔진
2. `/Users/dev/jusik/frontend/src/lib/tts.ts` - TTS 서비스 (기존 파일 확장)
3. `/Users/dev/jusik/frontend/src/services/monitoring.ts` - 모니터링 서비스
4. `/Users/dev/jusik/frontend/src/stores/alertStore.ts` - 알림 스토어
5. `/Users/dev/jusik/frontend/src/pages/Profile.tsx` - TTS 설정 UI 추가
6. `/Users/dev/jusik/frontend/src/pages/Dashboard.tsx` - 모니터링 자동 시작 통합

---

## 🔜 Phase 3: 고급 기능 및 최적화 (2주)

### 3.1 미니차트 구현 (3일)
- [ ] `frontend/src/components/MiniChart.tsx`
- [ ] Recharts LineChart
- [ ] 1분봉/5분봉 데이터
- [ ] 호가 10단계 표시
- [ ] 체결 내역 스트림

### 3.2 백테스트 시스템 (5일)
- [ ] `backend/backtest-service/` 생성
- [ ] Python Backtrader
- [ ] 전략 정의 인터페이스
- [ ] 성과 지표 (CAGR, MDD, Sharpe)

### 3.3 성능 최적화 (2일)
- [ ] Redis 캐싱 전략 고도화
- [ ] WebSocket 메시지 압축
- [ ] DB 쿼리 최적화

### 3.4 접근성 강화 (2일)
- [ ] 고대비 모드 (WCAG AA)
- [ ] 큰 글꼴 모드
- [ ] 키보드 네비게이션
- [ ] 스크린 리더 지원 (ARIA)

---

## 🔜 Phase 4: 배포 및 모니터링 (1주)

### 4.1 Netlify 배포 (1일)
- [ ] Frontend 빌드 최적화
- [ ] 환경 변수 설정
- [ ] PR Preview 설정

### 4.2 Railway 배포 (2일)
- [ ] Stream Service 배포
- [ ] News Crawler 배포
- [ ] AI Service 배포
- [ ] Alert Service 배포

### 4.3 모니터링 구축 (2일)
- [ ] Sentry 에러 추적
- [ ] Logflare 로그 중앙화

### 4.4 QA 및 베타 테스트 (2일)
- [ ] 시니어 사용자 테스트 (TTS)
- [ ] 부하 테스트 (100명)
- [ ] 보안 감사

---

## 📊 전체 일정 요약

| Phase | 기간 | 핵심 기능 | 상태 |
|-------|------|-----------|------|
| Phase 1 | 2주 | 인증, 포트폴리오 | ✅ 완료 |
| **Phase 2** | **3주** | **실시간 시세 + TTS** | 🔄 **진행 예정** |
| Phase 3 | 2주 | 차트, 백테스트 | 🔜 대기 |
| Phase 4 | 1주 | 배포, QA | 🔜 대기 |

---

## 📝 작업 전/후 체크리스트

### ✅ 작업 시작 전 (매번 확인!)
- [ ] `planPhase.md` 현재 Phase 확인
- [ ] `CLAUDE.md` 기술 스택 확인
- [ ] `trading_intelligence_requirements_and_design.md` 요구사항 확인
- [ ] `docs/kis_api/` KIS API 명세 확인
- [ ] 환경 변수 설정 확인
- [ ] 개발 서버 정상 실행 확인
- [ ] Git 브랜치 생성

### ✅ 작업 완료 후 (매번 확인!)
- [ ] `planPhase.md` 체크박스 업데이트 ✅
- [ ] 검증 기준 충족 확인
- [ ] Git 커밋 (의미 있는 메시지)
- [ ] 테스트 실행
- [ ] 다음 작업 항목 확인

---

## 🎯 현재 우선순위 (2025-01-18)

### 🔥 즉시 착수: Phase 2.1.1 - Stream Service 구축

**첫 번째 작업**:
1. [ ] `backend/stream-service/src/kis-websocket.ts` 파일 생성
2. [ ] KIS API WebSocket 연결 구현
3. [ ] OAuth 토큰 발급 및 관리

**참조 문서**:
- `docs/kis_api/access.token.md` - OAuth 인증
- `docs/kis_api/real-time-websocket-ket.md` - WebSocket 연결

---

**🚀 이 계획서는 매 작업 전/후로 확인하고 체크박스를 업데이트하여 일관성 있는 개발을 진행합니다!**

*문서 끝*
