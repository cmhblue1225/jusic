# 로컬 검증 환경 설정 가이드

## 📋 필요한 환경 변수

검증 스크립트 실행을 위해 다음 환경 변수가 필요합니다:

### ✅ 이미 설정되어 있는 환경 변수 (프로젝트 루트 `.env`)

```bash
# Supabase (필수)
VITE_SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_supabase_service_role_key_here

# KIS API (필수)
KIS_APP_KEY=your_kis_app_key_here
KIS_APP_SECRET=your_kis_app_secret_here

# OpenAI API (AI 일관성 검증에 필수)
OPENAI_API_KEY=sk-proj-YOUR_OPENAI_API_KEY_HERE
```

---

## 🚀 빠른 시작 (5분)

### Step 1: report-service에 .env 파일 생성

```bash
# report-service 디렉토리로 이동
cd /Users/dev/jusik/backend/report-service

# 프로젝트 루트의 .env 파일에서 필요한 변수만 복사
cat > .env << 'EOF'
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_supabase_service_role_key_here

# OpenAI API
OPENAI_API_KEY=sk-proj-YOUR_OPENAI_API_KEY_HERE

# KIS API
KIS_APP_KEY=your_kis_app_key_here
KIS_APP_SECRET=your_kis_app_secret_here
EOF

# .env 파일 확인
cat .env
```

### Step 2: Python 의존성 설치

```bash
# 가상 환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate

# 또는 기존 패키지에 추가 설치
pip install beautifulsoup4 lxml httpx
```

### Step 3: 검증 실행

```bash
# 환경 변수 로드 (매우 중요!)
export $(cat .env | xargs)

# 또는 각 스크립트 실행 시 환경 변수를 prefix로 지정
# (Step 1에서 .env 파일 생성했으면 이 방법 사용)
```

#### 옵션 A: 전체 검증 (순차 실행)

```bash
# 1. 기술적 지표 검증 (5분, 가장 빠름)
python3 validation/validate_technical_indicators.py

# 2. 엣지 케이스 검증 (10분)
python3 validation/validate_edge_cases.py

# 3. AI 일관성 검증 (15분, GPT-4 호출)
python3 validation/validate_ai_consistency.py

# 4. 데이터 정확성 검증 (10분, 네이버 크롤링)
python3 validation/validate_data_accuracy.py
```

#### 옵션 B: 개별 검증 (권장 순서)

**🥇 먼저 실행 (환경 설정 확인용)**

```bash
# 기술적 지표 검증 - KIS API + 계산 로직 확인
python3 validation/validate_technical_indicators.py
```

**예상 출력**:
```
================================================================================
🔬 기술적 지표 계산 정확성 검증 시작
================================================================================

============================================================
📊 기술적 지표 검증: 삼성전자 (005930)
============================================================
🔹 60일 OHLCV 데이터 조회 중...
✅ 캐시된 KIS 토큰 사용
✅ 데이터 조회 완료: 60일치

🔹 시스템 계산값 (technical.py) ...
   - MA5: 72340.0
   - MA20: 71850.0
   - MA60: 70920.0
   ...

🔹 수동 재계산 (NumPy 기반) ...
   - MA5: 72340.0
   - MA20: 71850.0
   - MA60: 70920.0
   ...

📈 오차 (절대값):
   - MA5: 0.0원
   - MA20: 0.0원
   - MA60: 0.0원
   ...

✅ 평균 오차: 0.0000 / 최대 오차: 0.0000 → 등급: A (완벽)
```

---

**🥈 다음 실행 (시스템 안정성 확인)**

```bash
# 엣지 케이스 검증 - 예외 처리 확인
python3 validation/validate_edge_cases.py
```

**예상 출력**:
```
============================================================
📊 시나리오 1: 데이터 부족 (신규 상장 종목)
============================================================
✅ OHLCV 데이터: 30일치 (요청: 60일)
⚠️ 데이터 부족: 30일 부족
✅ 시스템이 데이터 부족을 적절히 처리함 (None 반환)
...
```

---

**🥉 선택 실행 (GPT-4 API 비용 발생)**

```bash
# AI 일관성 검증 - GPT-4 호출 (~$0.5 소요)
python3 validation/validate_ai_consistency.py
```

**⚠️ 주의**: 이 스크립트는 GPT-4를 15회 이상 호출하므로 약 $0.5 비용이 발생합니다.

---

**🏅 선택 실행 (네이버 크롤링)**

```bash
# 데이터 정확성 검증 - 외부 소스 비교
python3 validation/validate_data_accuracy.py
```

**⚠️ 주의**: 과도한 요청 시 네이버 IP 차단 가능 (간격 2초 설정됨)

---

## 🔧 환경 변수 설명

### 1. SUPABASE_URL & SUPABASE_SERVICE_KEY

**용도**: Supabase 데이터베이스 접근

**필수 검증**:
- ✅ 모든 스크립트

**값 확인 방법**:
```bash
echo $SUPABASE_URL
# 출력: https://lrmvoldeyetuzuwuazdm.supabase.co
```

---

### 2. KIS_APP_KEY & KIS_APP_SECRET

**용도**: 한국투자증권 Open API 인증

**필수 검증**:
- ✅ validate_technical_indicators.py (OHLCV 데이터 조회)
- ✅ validate_edge_cases.py (OHLCV 데이터 조회)
- ✅ validate_data_accuracy.py (재무비율, 투자자동향)

**토큰 발급 확인**:
```bash
# 토큰 캐시 파일 확인 (kis_data.py가 자동 생성)
ls -la .kis-token-cache.json
cat .kis-token-cache.json
```

**예상 출력**:
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "expiresAt": "2025-10-21T10:30:00.000Z"
}
```

---

### 3. OPENAI_API_KEY

**용도**: GPT-4 Turbo API 인증

**필수 검증**:
- ✅ validate_ai_consistency.py (반복 분석, 감성 상관관계)
- ⚠️ validate_edge_cases.py (일부 시나리오)

**비용**:
- validate_ai_consistency.py: 약 $0.3-0.5
- validate_edge_cases.py: 약 $0.1-0.2

**잔액 확인**:
```bash
# OpenAI 대시보드 확인
# https://platform.openai.com/usage
```

**스킵 방법** (비용 절감):
```bash
# AI 검증 제외하고 실행
python3 validation/validate_technical_indicators.py
python3 validation/validate_edge_cases.py
python3 validation/validate_data_accuracy.py
```

---

## 🐛 트러블슈팅

### 문제 1: 환경 변수 미인식

```bash
❌ ValueError: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.
```

**해결 A: .env 파일 로드**
```bash
# 방법 1: export로 로드
export $(cat .env | xargs)

# 방법 2: source로 로드
set -a
source .env
set +a

# 환경 변수 확인
echo $OPENAI_API_KEY
```

**해결 B: python-dotenv 사용**
```bash
# 패키지 설치
pip install python-dotenv

# 각 검증 스크립트 상단에 추가 (이미 추가되어 있음)
# from dotenv import load_dotenv
# load_dotenv()
```

---

### 문제 2: KIS API 403 오류

```bash
❌ KIS 토큰 발급 실패: 403 {"error_code":"EGW00002"}
```

**원인**:
- KIS_APP_KEY 또는 KIS_APP_SECRET 잘못됨
- 1분당 1회 토큰 발급 제한 초과

**해결**:
```bash
# 1. 환경 변수 확인
echo $KIS_APP_KEY
echo $KIS_APP_SECRET

# 2. 토큰 캐시 삭제 후 재시도
rm -f .kis-token-cache.json
python3 validation/validate_technical_indicators.py

# 3. 1분 대기 후 재시도
sleep 60
python3 validation/validate_technical_indicators.py
```

---

### 문제 3: BeautifulSoup 설치 오류

```bash
❌ ModuleNotFoundError: No module named 'bs4'
```

**해결**:
```bash
pip install beautifulsoup4 lxml httpx
```

---

### 문제 4: 네이버 크롤링 차단 (403)

```bash
❌ 네이버 증권 크롤링 실패: 403
```

**해결**:
```bash
# validate_data_accuracy.py 수정
# 크롤링 간격 늘리기 (2초 → 5초)
await asyncio.sleep(5)  # 기존: 2
```

---

### 문제 5: OpenAI API 오류 (RateLimitError)

```bash
❌ openai.RateLimitError: Rate limit exceeded
```

**해결**:
```bash
# validate_ai_consistency.py 수정
# 반복 횟수 줄이기 (5회 → 3회)
REPEAT_COUNT = 3  # 기존: 5

# 또는 sleep 추가
await asyncio.sleep(2)  # 각 요청 사이
```

---

## 📊 검증 소요 시간 & 비용

| 스크립트 | 소요 시간 | API 호출 | 비용 |
|---------|----------|---------|------|
| validate_technical_indicators.py | ~5분 | KIS API (무료) | $0 |
| validate_edge_cases.py | ~10분 | KIS + GPT-4 (5회) | ~$0.1 |
| validate_ai_consistency.py | ~15분 | GPT-4 (15회) | ~$0.5 |
| validate_data_accuracy.py | ~10분 | KIS + 크롤링 | $0 |

**총 소요**: 약 40분 / **총 비용**: 약 $0.6

**절약 팁**:
- AI 일관성 검증 스킵 → 25분 / $0.1
- 기술적 지표 + 엣지 케이스만 실행 → 15분 / $0.1

---

## ✅ 검증 체크리스트

실행 전 확인:

- [ ] `.env` 파일이 `/Users/dev/jusik/backend/report-service/` 에 존재
- [ ] SUPABASE_URL 환경 변수 설정 확인
- [ ] KIS_APP_KEY 환경 변수 설정 확인
- [ ] OPENAI_API_KEY 환경 변수 설정 확인 (AI 검증 시)
- [ ] Python 패키지 설치 (beautifulsoup4, httpx)
- [ ] 인터넷 연결 확인 (API 호출 필요)

---

## 🎯 권장 검증 순서

**최소 검증** (5분):
```bash
python3 validation/validate_technical_indicators.py
```
→ 기술적 지표 계산 정확성만 확인 (가장 중요)

**기본 검증** (15분):
```bash
python3 validation/validate_technical_indicators.py
python3 validation/validate_edge_cases.py
```
→ 계산 정확성 + 시스템 안정성 확인

**전체 검증** (40분, $0.6):
```bash
python3 validation/validate_technical_indicators.py
python3 validation/validate_edge_cases.py
python3 validation/validate_ai_consistency.py
python3 validation/validate_data_accuracy.py
```
→ 모든 영역 종합 검증

---

**준비 완료!** 이제 검증을 시작하세요 🚀

```bash
cd /Users/dev/jusik/backend/report-service
export $(cat .env | xargs)
python3 validation/validate_technical_indicators.py
```
