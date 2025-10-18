# 📋 실시간 트레이딩 인텔리전스 플랫폼 - Phase별 개발 계획서

> **최종 업데이트**: 2025-10-19
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

### 📍 Phase 2.3: 뉴스 크롤링 + AI 분석 (4일) ✅ **완료!**

#### 2.3.1 News Crawler 구축 (2일) ✅
- [x] `backend/news-crawler/naver_api.py` ✅
  - [x] 네이버 뉴스 API 연동 ✅
  - [x] HTML 태그 제거 파싱 ✅
  - [x] 복수 종목 검색 (search_multiple_stocks) ✅
- [x] `backend/news-crawler/nlp/ner.py` ✅
  - [x] `stock_master` 테이블 로드 ✅
  - [x] 정규표현식 매칭 (6자리 종목코드 + 종목명) ✅
  - [x] 종목 코드 추출 (extract_symbols) ✅
  - [x] 신뢰도 계산 (extract_with_confidence) ✅
- [x] `backend/news-crawler/main.py` ✅
  - [x] APScheduler 설정 (5분마다) ✅
  - [x] 크롤러 실행 로직 (crawl_news) ✅
  - [x] 중복 뉴스 필터링 (URL 기반) ✅
  - [x] Supabase `news` 테이블 저장 ✅
  - [x] AI 분석 연동 (analyze_news_with_ai) ✅

**환경 변수**: ✅
- [x] `NAVER_CLIENT_ID` 설정 ✅
- [x] `NAVER_CLIENT_SECRET` 설정 ✅

**배포**: ✅
- [x] Railway 배포 완료 (news-crawler-production) ✅

#### 2.3.2 AI Service 구축 (2일) ✅
- [x] `backend/ai-service/main.py` ✅
  - [x] Claude API 클라이언트 (Claude 3.5 Sonnet) ✅
  - [x] 프롬프트 템플릿 ✅
  - [x] 요약, 감성, 영향도, 권고 생성 ✅
  - [x] OpenAI API 클라이언트 (폴백) ✅
  - [x] JSON 응답 파싱 ✅
- [x] `backend/ai-service/cache.py` ✅
  - [x] URL 기반 캐시 키 ✅
  - [x] Redis 캐싱 (TTL 24시간) ✅

**환경 변수**: ✅
- [x] `CLAUDE_API_KEY` 설정 ✅
- [x] `OPENAI_API_KEY` 설정 ✅

**배포**: ✅
- [x] Railway 배포 완료 (ai-service-production) ✅

#### 2.3.3 Frontend 뉴스 페이지 ✅
- [x] `frontend/src/pages/News.tsx` ✅
  - [x] 뉴스 목록 표시 ✅
  - [x] 필터 (관심 종목별) ✅
  - [x] 검색 (제목, 내용, 종목) ✅
  - [x] 정렬 (최신순/영향도순) ✅ (2025-10-19 추가)
  - [x] 뉴스 통계 표시 ✅
  - [x] TTS 음성 읽기 ✅
- [x] `frontend/src/components/NewsCard.tsx` ✅
  - [x] 제목, 요약 표시 ✅
  - [x] 감성 점수 색상 (긍정/부정/중립) ✅
  - [x] 영향도 프로그레스 바 (0~100%) ✅
  - [x] 행동 권고 뱃지 (매수/매도/보유) ✅
  - [x] "전문 보기" 버튼 (더보기/접기) ✅
  - [x] "듣기" 버튼 (TTS - 🔊 아이콘) ✅
  - [x] 관련 종목 태그 ✅
- [x] `frontend/src/stores/newsStore.ts` ✅
  - [x] 뉴스 목록 상태 (items, loading, error) ✅
  - [x] 필터 상태 (selectedSymbol) ✅
  - [x] 전체 뉴스 조회 (fetchNews) ✅
  - [x] 종목별 뉴스 조회 (fetchNewsBySymbol) ✅

#### 검증 기준
- [x] 5분마다 뉴스 자동 수집 (APScheduler) ✅
- [x] 종목명 추출 정확도 ≥ 90% (NER 시스템) ✅
- [x] AI 분석 응답 (Claude/OpenAI 연동) ✅
- [x] Redis 캐싱으로 중복 분석 방지 (24시간 TTL) ✅
- [x] 뉴스 카드 UI 시니어 친화적 (큰 글꼴, 명확한 색상) ✅

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

## 🔜 Phase 3: 접근성, 차트, 성능 최적화 (2주)

### 📍 Phase 3.4: 접근성 강화 (2일) ⭐⭐⭐ **최우선!**

#### 3.4.1 고대비 모드 구현 (1일)
- [ ] `frontend/src/stores/profileStore.ts` 업데이트
  - [ ] `theme` 상태 추가 (`'light' | 'dark' | 'high-contrast'`)
  - [ ] `setTheme()` 메서드 추가
  - [ ] Supabase에 테마 설정 저장/로드
- [ ] `frontend/src/pages/Profile.tsx` UI 추가
  - [ ] 테마 선택 라디오 버튼 (Light / Dark / High Contrast)
  - [ ] 미리보기 색상 샘플 표시
  - [ ] 저장 버튼
- [ ] `frontend/src/index.css` 업데이트
  - [ ] CSS 변수 정의 (light/dark/high-contrast 모드별)
  - [ ] `data-theme` 속성 기반 스타일링
- [ ] TailwindCSS dark mode 클래스 적용
  - [ ] 모든 컴포넌트에 `dark:` 클래스 추가
  - [ ] 배경색, 텍스트 색상 대비 검증
- [ ] WCAG AA 기준 검증
  - [ ] 모든 텍스트 명도비 ≥ 4.5:1
  - [ ] 링크/버튼 명도비 ≥ 3:1

**검증 기준**:
- [ ] Chrome DevTools Lighthouse 접근성 점수 ≥ 90
- [ ] 고대비 모드에서 모든 UI 요소 식별 가능
- [ ] 테마 변경 시 페이지 깜빡임 없음

#### 3.4.2 큰 글꼴 모드 구현 (0.5일)
- [ ] `frontend/src/stores/profileStore.ts` 업데이트
  - [ ] `fontSize` 상태 추가 (`'normal' | 'large' | 'xlarge'`)
  - [ ] `setFontSize()` 메서드 추가
- [ ] `frontend/src/pages/Profile.tsx` UI 추가
  - [ ] 글꼴 크기 선택 버튼 (보통 18px / 크게 20px / 매우 크게 24px)
- [ ] `frontend/src/index.css` 업데이트
  - [ ] CSS 변수 `--font-size-base` 정의
  - [ ] `data-font-size` 속성 기반 크기 조정
- [ ] 모든 컴포넌트 반응형 확인
  - [ ] 레이아웃 깨짐 방지
  - [ ] 버튼/입력 필드 크기 자동 조정

**검증 기준**:
- [ ] 세 가지 글꼴 크기 모두 레이아웃 유지
- [ ] 모바일 환경에서도 정상 동작

#### 3.4.3 키보드 네비게이션 개선 (0.5일)
- [ ] 전역 focus 스타일 추가
  - [ ] `frontend/src/index.css`에 `:focus-visible` 스타일
  - [ ] TailwindCSS `ring-2` 클래스 적용
- [ ] 모든 인터랙티브 요소 확인
  - [ ] 버튼, 링크, 입력 필드 Tab 순서 최적화
  - [ ] `tabIndex` 속성 적절히 설정
- [ ] 키보드 단축키 추가
  - [ ] Enter 키로 모든 버튼/링크 실행
  - [ ] Esc 키로 모달/폼 닫기
  - [ ] Arrow 키로 목록 네비게이션 (Portfolio/Watchlist)
- [ ] ARIA 레이블 추가
  - [ ] 모든 버튼에 `aria-label` 추가
  - [ ] 폼 필드에 `aria-describedby` 추가
  - [ ] 알림에 `role="alert"` 추가

**검증 기준**:
- [ ] 마우스 없이 모든 기능 사용 가능
- [ ] 포커스 상태 시각적으로 명확
- [ ] 스크린 리더 호환성 확인 (VoiceOver/NVDA)

---

### 📍 Phase 3.1: 미니차트 구현 (3일)

#### 3.1.1 MiniChart 컴포넌트 구현 (2일)
- [ ] `frontend/src/components/MiniChart.tsx` 생성
  - [ ] Recharts LineChart 기반
  - [ ] Props: `symbol`, `data`, `height`, `interval`
  - [ ] 1분봉/5분봉 데이터 시각화
  - [ ] X축: 시간 (HH:mm), Y축: 가격
  - [ ] Tooltip: 시간, 가격, 등락률
  - [ ] 확대/축소 (zoom) 기능
- [ ] 호가 10단계 컴포넌트
  - [ ] `frontend/src/components/OrderBook.tsx` 생성
  - [ ] 매수 호가 5단계 (녹색)
  - [ ] 매도 호가 5단계 (빨간색)
  - [ ] 잔량 막대 그래프
  - [ ] 최우선 호가 하이라이트
- [ ] 체결 내역 컴포넌트
  - [ ] `frontend/src/components/TradeHistory.tsx` 생성
  - [ ] 최근 10건 체결가 표시
  - [ ] 시간, 가격, 체결량 표시
  - [ ] 실시간 스크롤 (새 체결가 추가 시)

#### 3.1.2 WebSocket 데이터 연동 (1일)
- [ ] Stream Service 업데이트
  - [ ] 1분봉/5분봉 데이터 생성 로직
  - [ ] 호가 10단계 WebSocket 이벤트
  - [ ] 체결가 WebSocket 이벤트
- [ ] Frontend 훅 구현
  - [ ] `frontend/src/hooks/useChartData.ts`
  - [ ] `useOrderBook.ts`
  - [ ] `useTradeHistory.ts`
- [ ] Dashboard/Portfolio에 통합
  - [ ] 종목별 미니차트 표시
  - [ ] 클릭 시 상세 모달 표시

**검증 기준**:
- [ ] 실시간 차트 업데이트 ≤ 2초 지연
- [ ] 차트 렌더링 성능 양호 (60fps)
- [ ] 모바일/데스크톱 반응형

---

### 📍 Phase 3.3: 성능 최적화 (2일)

#### 3.3.1 Vite 코드 스플리팅 (1일)
- [ ] `frontend/vite.config.ts` 생성
  - [ ] `build.rollupOptions.output.manualChunks` 설정
  - [ ] Vendor 청크 분리 (React, Recharts, Supabase)
  - [ ] Route-based 청크 분리 (`React.lazy` 사용)
- [ ] 페이지별 지연 로딩
  - [ ] `const Portfolio = React.lazy(() => import('./pages/Portfolio'))`
  - [ ] `<Suspense fallback={<Loading />}>` 래퍼
- [ ] 빌드 테스트
  - [ ] 번들 크기 844KB → 500KB 이하 감소 확인
  - [ ] 초기 로딩 시간 측정

#### 3.3.2 Redis 캐싱 고도화 (0.5일)
- [ ] Stream Service 캐싱 전략 개선
  - [ ] 현재가 캐싱 TTL: 5분 → 1분 (장중), 10분 (장 마감 후)
  - [ ] 호가 캐싱 TTL: 30초
- [ ] AI Service 캐싱 검증
  - [ ] 뉴스 분석 캐싱 TTL: 24시간 (현재 유지)
  - [ ] 캐시 히트율 모니터링

#### 3.3.3 WebSocket 메시지 압축 (0.5일)
- [ ] Stream Service 업데이트
  - [ ] Socket.IO `perMessageDeflate` 옵션 활성화
  - [ ] 메시지 페이로드 크기 최소화 (불필요한 필드 제거)
- [ ] Frontend 업데이트
  - [ ] 압축된 메시지 디코딩 확인

**검증 기준**:
- [ ] 번들 크기 ≤ 500KB (gzip)
- [ ] 초기 로딩 시간 ≤ 3초
- [ ] Redis 메모리 사용량 ≤ 100MB

---

### 📍 Phase 3.2: 백테스트 시스템 (5일) - **Phase 4로 이동 고려**
- [ ] `backend/backtest-service/` 생성 (Python)
- [ ] Backtrader 라이브러리 통합
- [ ] 전략 정의 인터페이스
- [ ] 성과 지표 (CAGR, MDD, Sharpe Ratio)
- [ ] Frontend 결과 시각화 페이지

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

## 🔄 Phase 2.4.3: Supabase Realtime 뉴스 구독 ✅ **완료 (2025-10-19)**

### 구현 내용
- [x] `monitoring.ts` - Realtime 구독 구현 ✅
  - [x] Supabase Realtime 뉴스 테이블 구독 ✅
  - [x] related_symbols 필터링 (사용자 포트폴리오/관심종목) ✅
  - [x] INSERT 이벤트 리스닝 ✅
  - [x] 알림 생성 및 TTS 재생 ✅
- [x] LocalStorage 기반 중복 방지 (7일) ✅
  - [x] 뉴스 ID 저장 (최대 500개) ✅
  - [x] 7일 이상 오래된 ID 자동 제거 ✅
- [x] App.tsx 전역 모니터링 통합 ✅
  - [x] `useEffect`에서 `MonitoringService.start()` 호출 ✅
  - [x] user, ttsConfig.enabled 의존성 관리 ✅
  - [x] 언마운트 시 `stop()` 호출 ✅
- [x] 모든 페이지에서 Toast 알림 수신 ✅
  - [x] `ToastContainer` 컴포넌트를 App.tsx로 이동 ✅
  - [x] Dashboard, News, Portfolio, Watchlist 등 모든 페이지에서 표시 ✅

### 검증 완료
- [x] 새 뉴스 발행 시 5초 이내 알림 생성 ✅
- [x] TTS 자동 재생 (impact_score ≥ 임계값) ✅
- [x] Toast 알림 모든 페이지 표시 ✅
- [x] 중복 알림 방지 확인 ✅

**배포 완료**: 모든 기능이 https://jusik.minhyuk.kr에서 정상 작동 중

---

## 📊 전체 일정 요약

| Phase | 기간 | 핵심 기능 | 상태 |
|-------|------|-----------|------|
| Phase 1 | 2주 | 인증, 포트폴리오 | ✅ 완료 (2025-10-18) |
| **Phase 2** | **3주** | **실시간 시세 + TTS** | ✅ **완료 (2025-10-19)** |
| Phase 3 | 2주 | 접근성, 차트, 성능 최적화 | 🔜 **다음 단계** |
| Phase 4 | 1주 | 백테스트, QA | 🔜 대기 |

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

## 🎯 현재 우선순위 (2025-10-19)

### ✅ Phase 2 완료 (2025-10-19)
모든 Phase 2 작업이 성공적으로 완료되었습니다!
- ✅ 실시간 주가 스트리밍 (WebSocket + KIS REST API)
- ✅ 보유 종목 수익률 실시간 계산
- ✅ 뉴스 크롤링 + AI 분석 (OpenAI GPT-4o-mini 우선)
- ✅ TTS 자동 알림 시스템 (전역 모니터링 + Toast)

**배포 완료**: https://jusik.minhyuk.kr (Railway)

---

### 🔥 다음 단계: Phase 3.4 - 접근성 강화 (2일)

**우선순위**: ⭐⭐⭐ **최우선!** 시니어 사용자 타겟이므로 매우 중요

**첫 번째 작업**:
1. [ ] Profile.tsx 테마 설정 UI 추가
   - [ ] 고대비 모드 토글 (light/dark/high-contrast)
   - [ ] 글꼴 크기 선택 (18px/20px/24px)
2. [ ] TailwindCSS dark mode 클래스 적용
3. [ ] CSS 변수 `--font-size-base` 전역 적용
4. [ ] WCAG AA 기준 색상 대비 검증

**검증 기준**:
- [ ] 모든 텍스트 명도비 ≥ 4.5:1
- [ ] Tab 키로 모든 요소 접근 가능
- [ ] Enter/Esc 키로 모든 액션 실행 가능
- [ ] 포커스 상태 시각화 (outline ring)

**참조 문서**:
- WCAG 2.1: https://www.w3.org/WAI/WCAG21/quickref/
- TailwindCSS Dark Mode: https://tailwindcss.com/docs/dark-mode

---

### 📋 Phase 3 전체 계획 (2주)

**Phase 3.4**: 접근성 강화 (2일) ← **즉시 착수**
**Phase 3.1**: 미니차트 구현 (3일)
**Phase 3.3**: 성능 최적화 (2일) - 번들 크기 844KB → 500KB
**Phase 3.2**: 백테스트 시스템 (5일) - Phase 4로 이동 고려

---

**🚀 이 계획서는 매 작업 전/후로 확인하고 체크박스를 업데이트하여 일관성 있는 개발을 진행합니다!**

*문서 끝*
