"""
데이터 정확성 검증 스크립트
- KIS API 데이터를 외부 소스(네이버 증권)와 비교
- 주가, 재무비율, 투자자 동향 정확도 측정
"""
import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, List, Any
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

# 상위 디렉토리 모듈 임포트
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kis_data import get_daily_ohlcv, get_financial_ratio, get_investor_trend


# 테스트 대상 종목 (10개)
TEST_SYMBOLS = [
    {"symbol": "005930", "name": "삼성전자"},
    {"symbol": "000660", "name": "SK하이닉스"},
    {"symbol": "035420", "name": "NAVER"},
    {"symbol": "035720", "name": "카카오"},
    {"symbol": "005380", "name": "현대차"},
    {"symbol": "373220", "name": "LG에너지솔루션"},
    {"symbol": "000270", "name": "기아"},
    {"symbol": "005490", "name": "포스코홀딩스"},
    {"symbol": "207940", "name": "삼성바이오로직스"},
    {"symbol": "105560", "name": "KB금융"},
]


async def crawl_naver_stock_price(symbol: str) -> Dict[str, Any]:
    """
    네이버 증권에서 주가 데이터 크롤링

    Args:
        symbol: 종목 코드

    Returns:
        Dict: 주가 정보
            - current_price: 현재가
            - change_rate: 등락률
            - volume: 거래량
            - high: 고가
            - low: 저가
    """
    url = f"https://finance.naver.com/item/main.nhn?code={symbol}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        if response.status_code != 200:
            raise Exception(f"네이버 증권 크롤링 실패: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')

        # 현재가
        current_price_elem = soup.select_one(".no_today .blind")
        current_price = int(current_price_elem.text.replace(",", "")) if current_price_elem else None

        # 등락률
        change_rate_elem = soup.select_one(".no_exday .blind")
        change_rate_text = change_rate_elem.text if change_rate_elem else "0"
        # "상승5.00%" → 5.00 또는 "하락3.50%" → -3.50
        if "상승" in change_rate_text:
            change_rate = float(change_rate_text.replace("상승", "").replace("%", ""))
        elif "하락" in change_rate_text:
            change_rate = -float(change_rate_text.replace("하락", "").replace("%", ""))
        else:
            change_rate = 0.0

        # 거래량 (전일 기준)
        volume_elem = soup.select_one(".lst_dt tbody tr:nth-child(3) td .blind")
        volume = int(volume_elem.text.replace(",", "")) if volume_elem else None

        # 고가/저가
        high_elem = soup.select_one(".lst_dt tbody tr:nth-child(4) td .blind")
        low_elem = soup.select_one(".lst_dt tbody tr:nth-child(5) td .blind")
        high = int(high_elem.text.replace(",", "")) if high_elem else None
        low = int(low_elem.text.replace(",", "")) if low_elem else None

        return {
            "current_price": current_price,
            "change_rate": change_rate,
            "volume": volume,
            "high": high,
            "low": low,
        }


async def crawl_naver_financial_ratio(symbol: str) -> Dict[str, Any]:
    """
    네이버 증권에서 재무비율 크롤링

    Returns:
        Dict: PER, PBR, ROE 등
    """
    url = f"https://finance.naver.com/item/main.nhn?code={symbol}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        soup = BeautifulSoup(response.text, 'html.parser')

        # PER, PBR (시가총액 정보 영역)
        per_elem = soup.select_one(".per")
        pbr_elem = soup.select_one(".pbr")

        per = float(per_elem.text.replace(",", "")) if per_elem and per_elem.text.strip() else None
        pbr = float(pbr_elem.text.replace(",", "")) if pbr_elem and pbr_elem.text.strip() else None

        return {
            "per": per,
            "pbr": pbr,
        }


async def validate_stock_price(symbol: str, name: str) -> Dict[str, Any]:
    """
    주가 데이터 정확성 검증
    """
    print(f"\n{'='*60}")
    print(f"📊 주가 데이터 검증: {name} ({symbol})")
    print(f"{'='*60}")

    try:
        # 1. KIS API 데이터 조회
        print("🔹 KIS API 데이터 조회 중...")
        kis_ohlcv = await get_daily_ohlcv(symbol, days=2)  # 최근 2일
        kis_latest = kis_ohlcv[-1]

        kis_data = {
            "current_price": kis_latest["close"],
            "high": kis_latest["high"],
            "low": kis_latest["low"],
            "volume": kis_latest["volume"],
        }

        # 등락률 계산
        if len(kis_ohlcv) >= 2:
            prev_close = kis_ohlcv[-2]["close"]
            kis_data["change_rate"] = round(((kis_latest["close"] - prev_close) / prev_close) * 100, 2)
        else:
            kis_data["change_rate"] = 0.0

        print(f"✅ KIS 현재가: {kis_data['current_price']:,}원 ({kis_data['change_rate']:+.2f}%)")

        # 2. 네이버 증권 데이터 크롤링
        print("🔹 네이버 증권 데이터 크롤링 중...")
        naver_data = await crawl_naver_stock_price(symbol)
        print(f"✅ 네이버 현재가: {naver_data['current_price']:,}원 ({naver_data['change_rate']:+.2f}%)")

        # 3. 오차 계산
        errors = {}
        for key in ["current_price", "change_rate", "volume", "high", "low"]:
            kis_val = kis_data.get(key)
            naver_val = naver_data.get(key)

            if kis_val is not None and naver_val is not None:
                if key == "change_rate":
                    # 등락률: 절대 오차
                    error = abs(kis_val - naver_val)
                else:
                    # 가격/거래량: 상대 오차 (%)
                    error = abs((kis_val - naver_val) / naver_val * 100) if naver_val != 0 else 0
                errors[key] = round(error, 4)
            else:
                errors[key] = None

        print(f"\n📈 오차율:")
        print(f"   - 현재가: {errors['current_price']}%")
        print(f"   - 등락률: {errors['change_rate']}%p (절대 오차)")
        print(f"   - 거래량: {errors['volume']}%")
        print(f"   - 고가: {errors['high']}%")
        print(f"   - 저가: {errors['low']}%")

        # 4. 결과 판정
        avg_error = sum([e for e in errors.values() if e is not None]) / len([e for e in errors.values() if e is not None])

        if avg_error < 0.1:
            grade = "A (매우 정확)"
        elif avg_error < 0.5:
            grade = "B (정확)"
        elif avg_error < 1.0:
            grade = "C (보통)"
        else:
            grade = "D (부정확)"

        print(f"\n✅ 평균 오차율: {avg_error:.4f}% → 등급: {grade}")

        return {
            "symbol": symbol,
            "name": name,
            "kis_data": kis_data,
            "naver_data": naver_data,
            "errors": errors,
            "avg_error": avg_error,
            "grade": grade,
            "status": "success"
        }

    except Exception as e:
        print(f"❌ 검증 실패: {str(e)}")
        return {
            "symbol": symbol,
            "name": name,
            "status": "failed",
            "error": str(e)
        }


async def validate_financial_ratios(symbol: str, name: str) -> Dict[str, Any]:
    """
    재무비율 정확성 검증
    """
    print(f"\n{'='*60}")
    print(f"💰 재무비율 검증: {name} ({symbol})")
    print(f"{'='*60}")

    try:
        # 1. KIS API 데이터 조회
        print("🔹 KIS API 재무비율 조회 중...")
        kis_financial = await get_financial_ratio(symbol)
        print(f"✅ KIS PER: {kis_financial.get('per')}, PBR: {kis_financial.get('pbr')}")

        # 2. 네이버 증권 데이터 크롤링
        print("🔹 네이버 증권 재무비율 크롤링 중...")
        naver_financial = await crawl_naver_financial_ratio(symbol)
        print(f"✅ 네이버 PER: {naver_financial.get('per')}, PBR: {naver_financial.get('pbr')}")

        # 3. 오차 계산
        errors = {}
        for key in ["per", "pbr"]:
            kis_val = kis_financial.get(key)
            naver_val = naver_financial.get(key)

            if kis_val is not None and naver_val is not None:
                error = abs((kis_val - naver_val) / naver_val * 100) if naver_val != 0 else 0
                errors[key] = round(error, 4)
            else:
                errors[key] = None

        print(f"\n📈 오차율:")
        print(f"   - PER: {errors['per']}%")
        print(f"   - PBR: {errors['pbr']}%")

        return {
            "symbol": symbol,
            "name": name,
            "kis_data": kis_financial,
            "naver_data": naver_financial,
            "errors": errors,
            "status": "success"
        }

    except Exception as e:
        print(f"❌ 검증 실패: {str(e)}")
        return {
            "symbol": symbol,
            "name": name,
            "status": "failed",
            "error": str(e)
        }


async def main():
    """메인 검증 실행"""
    print("=" * 80)
    print("🔬 레포트 시스템 데이터 정확성 검증 시작")
    print("=" * 80)
    print(f"📅 검증 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 검증 종목 수: {len(TEST_SYMBOLS)}개")
    print()

    # Phase 1: 주가 데이터 검증
    print("\n" + "=" * 80)
    print("📊 Phase 1: 주가 데이터 정확성 검증")
    print("=" * 80)

    price_results = []
    for stock in TEST_SYMBOLS[:3]:  # 처음 3개만 테스트 (시간 절약)
        result = await validate_stock_price(stock["symbol"], stock["name"])
        price_results.append(result)
        await asyncio.sleep(2)  # 크롤링 간격

    # Phase 2: 재무비율 검증
    print("\n" + "=" * 80)
    print("💰 Phase 2: 재무비율 정확성 검증")
    print("=" * 80)

    financial_results = []
    for stock in TEST_SYMBOLS[:3]:  # 처음 3개만 테스트
        result = await validate_financial_ratios(stock["symbol"], stock["name"])
        financial_results.append(result)
        await asyncio.sleep(2)

    # 최종 리포트
    print("\n" + "=" * 80)
    print("📋 검증 결과 요약")
    print("=" * 80)

    print("\n✅ 주가 데이터 검증 결과:")
    success_count = sum(1 for r in price_results if r["status"] == "success")
    print(f"   - 성공: {success_count}/{len(price_results)}개")

    if success_count > 0:
        avg_errors = [r["avg_error"] for r in price_results if r["status"] == "success"]
        total_avg = sum(avg_errors) / len(avg_errors)
        print(f"   - 전체 평균 오차율: {total_avg:.4f}%")

        grades = [r["grade"] for r in price_results if r["status"] == "success"]
        print(f"   - 등급 분포: {', '.join(set(grades))}")

    print("\n✅ 재무비율 검증 결과:")
    financial_success = sum(1 for r in financial_results if r["status"] == "success")
    print(f"   - 성공: {financial_success}/{len(financial_results)}개")

    print("\n" + "=" * 80)
    print("🎉 검증 완료!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
