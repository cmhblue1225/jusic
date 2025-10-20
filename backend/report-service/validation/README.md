# 레포트 시스템 검증 스크립트

이 디렉토리에는 레포트 시스템의 정확성과 안정성을 검증하기 위한 자동화 스크립트가 포함되어 있습니다.

## 📂 파일 구조

```
validation/
├── README.md                           # 이 파일
├── VALIDATION_REPORT.md                # 종합 검증 리포트
├── validate_data_accuracy.py           # 데이터 정확성 검증 (KIS API vs 네이버 증권)
├── validate_technical_indicators.py    # 기술적 지표 계산 검증 (수식 재계산)
├── validate_ai_consistency.py          # AI 분석 일관성 검증 (GPT-4 반복 테스트)
└── validate_edge_cases.py              # 엣지 케이스 검증 (예외 처리)
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 프로젝트 루트로 이동
cd /Users/dev/jusik/backend/report-service

# 환경 변수 로드 (필수!)
source .env

# 또는 .env 파일에 다음 변수 설정:
# KIS_APP_KEY=your_key
# KIS_APP_SECRET=your_secret
# OPENAI_API_KEY=your_openai_key
# SUPABASE_URL=your_supabase_url
# SUPABASE_SERVICE_KEY=your_service_key
```

### 2. 의존성 설치

```bash
# Python 패키지 설치
pip install -r requirements.txt

# 추가 패키지 (크롤링용)
pip install beautifulsoup4
```

### 3. 검증 실행

#### 옵션 A: 전체 검증 (권장)

```bash
# 모든 검증 스크립트 순차 실행
python3 validation/validate_technical_indicators.py
python3 validation/validate_ai_consistency.py
python3 validation/validate_edge_cases.py
python3 validation/validate_data_accuracy.py
```

#### 옵션 B: 개별 검증

```bash
# 기술적 지표 검증 (가장 빠름, 5분 소요)
python3 validation/validate_technical_indicators.py

# AI 일관성 검증 (15분 소요, GPT-4 API 호출 다수)
python3 validation/validate_ai_consistency.py

# 엣지 케이스 검증 (10분 소요)
python3 validation/validate_edge_cases.py

# 데이터 정확성 검증 (10분 소요, 네이버 크롤링)
python3 validation/validate_data_accuracy.py
```

## 📊 검증 항목 상세

### 1. 데이터 정확성 검증 (`validate_data_accuracy.py`)

**목적**: KIS API 데이터를 외부 소스와 비교하여 정확도 측정

**검증 대상**:
- 주가 데이터 (현재가, 등락률, 거래량, 고가/저가)
- 재무비율 (PER, PBR)
- 투자자 동향 (외국인/기관/개인 순매수)

**외부 소스**:
- 네이버 증권 (크롤링)
- KRX 시장정보

**예상 결과**:
- 주가 데이터: 오차율 < 0.1%
- 재무비율: 오차율 < 1%

**실행 시간**: ~10분 (크롤링 간격 2초)

---

### 2. 기술적 지표 검증 (`validate_technical_indicators.py`)

**목적**: 시스템이 계산한 기술적 지표를 수식 기반으로 재계산하여 비교

**검증 대상**:
- 이동평균선 (MA5, MA20, MA60)
- 볼린저 밴드 (상단/하단)
- 거래량 비율
- 변동성 (표준편차)

**검증 방법**:
```python
# 이동평균선
manual_ma5 = np.mean(prices[-5:])
system_ma5 = calculate_moving_average(prices, 5)
assert abs(manual_ma5 - system_ma5) < 0.01
```

**예상 결과**: 절대 오차 < 0.01원 (거의 0)

**실행 시간**: ~5분

---

### 3. AI 일관성 검증 (`validate_ai_consistency.py`)

**목적**: GPT-4 분석의 일관성 및 객관성 검증

**테스트 시나리오**:

1. **일관성 테스트**: 동일 종목/시점 → 5회 반복 분석
   - 평가 점수 표준편차 측정
   - 투자 권고 일관성 (%) 계산

2. **객관성 테스트**: 긍정 뉴스 vs 부정 뉴스
   - 평가 점수 변화 확인
   - 상관관계 분석

**예상 결과**:
- 평가 점수 표준편차: < 5점
- 투자 권고 일관성: ≥ 80%
- 뉴스 감성 상관관계: R² ≥ 0.7

**실행 시간**: ~15분 (GPT-4 API 호출 다수)

**주의**: OpenAI API 비용 발생 (~$0.5)

---

### 4. 엣지 케이스 검증 (`validate_edge_cases.py`)

**목적**: 특수 상황에서 시스템 안정성 검증

**테스트 시나리오**:
- ✅ 데이터 부족 (신규 상장 종목, 60일 미만)
- ✅ 유효하지 않은 종목 코드 (999999)
- ✅ 극단적 변동 (상한가/하한가 시뮬레이션)
- ✅ 뉴스 부재 (소형주)
- ✅ 재무 데이터 부재

**예상 결과**: 모든 시나리오에서 안정적 처리 (오류 없이 작동)

**실행 시간**: ~10분

---

## 🎯 검증 결과 해석

### 등급 체계

| 등급 | 기준 | 의미 |
|------|------|------|
| **A** | 오차 < 0.1% 또는 일관성 ≥ 90% | 매우 우수 |
| **B** | 오차 < 0.5% 또는 일관성 ≥ 80% | 우수 |
| **C** | 오차 < 1.0% 또는 일관성 ≥ 70% | 양호 |
| **D** | 오차 ≥ 1.0% 또는 일관성 < 70% | 개선 필요 |

### 검증 통과 기준

✅ **시스템이 실전 투자에 사용 가능한 수준**:
- 주가 데이터 오차율 < 0.1%
- 기술적 지표 오차 < 0.01원
- AI 일관성 ≥ 80%
- 엣지 케이스 100% 처리

⚠️ **개선 필요**:
- 주가 데이터 오차율 ≥ 0.5%
- AI 일관성 < 70%
- 엣지 케이스 처리 실패

## 📋 검증 리포트

전체 검증 결과는 **`VALIDATION_REPORT.md`**에서 확인하세요.

**주요 내용**:
- 종합 평가 등급 (A-/우수)
- 영역별 상세 검증 결과
- 강점 및 약점 분석
- 개선 권고사항
- 실전 투자 활용 가능 여부

## 🔧 트러블슈팅

### 1. KIS API 인증 오류 (403)

```
❌ KIS 토큰 발급 실패: 403 {"error_code":"EGW00002"}
```

**원인**: 환경 변수 `KIS_APP_KEY`, `KIS_APP_SECRET` 미설정

**해결**:
```bash
# .env 파일 확인
cat .env | grep KIS

# 환경 변수 로드
source .env

# 또는 직접 export
export KIS_APP_KEY=your_key
export KIS_APP_SECRET=your_secret
```

---

### 2. OpenAI API 오류 (401)

```
❌ OpenAI API 인증 실패
```

**원인**: `OPENAI_API_KEY` 미설정 또는 잔액 부족

**해결**:
```bash
# 환경 변수 설정
export OPENAI_API_KEY=sk-...

# 또는 AI 일관성 테스트 스킵
# (다른 검증은 정상 실행 가능)
```

---

### 3. BeautifulSoup 설치 오류

```
❌ ModuleNotFoundError: No module named 'bs4'
```

**해결**:
```bash
pip install beautifulsoup4 lxml
```

---

### 4. 네이버 크롤링 차단 (403)

```
❌ 네이버 증권 크롤링 실패: 403
```

**원인**: 과도한 요청으로 IP 차단

**해결**:
```python
# 크롤링 간격 늘리기 (validate_data_accuracy.py 수정)
await asyncio.sleep(5)  # 2초 → 5초
```

---

## 📅 정기 검증 권장 사항

### 월 1회 정기 검증

```bash
# 매월 1일 실행 (cron 설정)
0 0 1 * * cd /Users/dev/jusik/backend/report-service && python3 validation/validate_technical_indicators.py >> logs/validation.log 2>&1
```

### 코드 변경 시 검증

```bash
# Git pre-commit hook
git add .git/hooks/pre-commit

#!/bin/bash
cd backend/report-service
python3 validation/validate_technical_indicators.py
if [ $? -ne 0 ]; then
  echo "검증 실패! 커밋이 중단되었습니다."
  exit 1
fi
```

### 배포 전 검증 (CI/CD)

```yaml
# .github/workflows/validation.yml
name: Validation
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run validation
        env:
          KIS_APP_KEY: ${{ secrets.KIS_APP_KEY }}
          KIS_APP_SECRET: ${{ secrets.KIS_APP_SECRET }}
        run: |
          cd backend/report-service
          python3 validation/validate_technical_indicators.py
```

## 🤝 기여 가이드

새로운 검증 시나리오를 추가하려면:

1. 새 파일 생성 (예: `validate_performance.py`)
2. `async def main()` 함수 정의
3. 검증 로직 작성
4. `README.md` 업데이트
5. Pull Request 생성

**검증 스크립트 작성 가이드**:
```python
"""
검증 스크립트 템플릿
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def validate_something():
    """검증 로직"""
    try:
        # 검증 코드
        result = {"status": "success", ...}
    except Exception as e:
        result = {"status": "failed", "error": str(e)}
    return result

async def main():
    print("=" * 80)
    print("🔬 검증 시작")
    print("=" * 80)

    result = await validate_something()

    print("\n📋 검증 결과:")
    print(f"   상태: {result['status']}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
```

## 📞 문의

검증 관련 문의사항은 GitHub Issues에 등록해주세요.

---

**마지막 업데이트**: 2025-10-20
**작성자**: Claude Code
**버전**: 1.0.0
