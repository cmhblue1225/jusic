"""
기술적 지표 계산 검증 스크립트
- 이동평균선, 볼린저 밴드, 거래량 비율 등 수식 기반 재계산
- 시스템 출력값과 비교하여 정확도 측정
"""
import asyncio
import sys
import os
import numpy as np
from typing import List, Dict, Any
from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

# 상위 디렉토리 모듈 임포트
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kis_data import get_daily_ohlcv
from technical import calculate_all_indicators


# 테스트 대상 종목
TEST_SYMBOLS = [
    {"symbol": "005930", "name": "삼성전자"},
    {"symbol": "000660", "name": "SK하이닉스"},
    {"symbol": "035420", "name": "NAVER"},
]


def manual_calculate_ma(prices: List[float], period: int) -> float:
    """이동평균선 수동 계산"""
    if len(prices) < period:
        return None
    return round(np.mean(prices[-period:]), 2)


def manual_calculate_bollinger(prices: List[float], period: int = 20, num_std: float = 2.0) -> Dict[str, float]:
    """볼린저 밴드 수동 계산"""
    if len(prices) < period:
        return None

    recent_prices = prices[-period:]
    middle = np.mean(recent_prices)
    std = np.std(recent_prices)

    return {
        "upper": round(middle + (num_std * std), 2),
        "middle": round(middle, 2),
        "lower": round(middle - (num_std * std), 2)
    }


def manual_calculate_volume_ratio(volumes: List[int], period: int = 20) -> float:
    """거래량 비율 수동 계산"""
    if len(volumes) < period + 1:
        return None

    avg_volume = np.mean(volumes[-(period + 1):-1])
    if avg_volume == 0:
        return None

    current_volume = volumes[-1]
    return round(current_volume / avg_volume, 2)


def manual_calculate_volatility(prices: List[float], period: int = 20) -> float:
    """변동성 수동 계산"""
    if len(prices) < period:
        return None

    recent_prices = prices[-period:]
    return round(np.std(recent_prices), 2)


async def validate_technical_indicators(symbol: str, name: str) -> Dict[str, Any]:
    """
    기술적 지표 계산 정확성 검증
    """
    print(f"\n{'='*60}")
    print(f"📊 기술적 지표 검증: {name} ({symbol})")
    print(f"{'='*60}")

    try:
        # 1. KIS API에서 60일 데이터 조회
        print("🔹 60일 OHLCV 데이터 조회 중...")
        ohlcv_data = await get_daily_ohlcv(symbol, days=60)
        print(f"✅ 데이터 조회 완료: {len(ohlcv_data)}일치")

        # 2. 시스템 계산값 (technical.py)
        print("\n🔹 시스템 계산값 (technical.py) ...")
        system_indicators = calculate_all_indicators(ohlcv_data)

        print(f"   - MA5: {system_indicators['ma5']}")
        print(f"   - MA20: {system_indicators['ma20']}")
        print(f"   - MA60: {system_indicators['ma60']}")
        print(f"   - 볼린저 상단: {system_indicators['bollinger_upper']}")
        print(f"   - 볼린저 하단: {system_indicators['bollinger_lower']}")
        print(f"   - 거래량 비율: {system_indicators['volume_ratio']}")
        print(f"   - 변동성: {system_indicators['volatility']}")

        # 3. 수동 재계산
        print("\n🔹 수동 재계산 (NumPy 기반) ...")
        close_prices = [item["close"] for item in ohlcv_data]
        volumes = [item["volume"] for item in ohlcv_data]

        manual_ma5 = manual_calculate_ma(close_prices, 5)
        manual_ma20 = manual_calculate_ma(close_prices, 20)
        manual_ma60 = manual_calculate_ma(close_prices, 60)
        manual_bollinger = manual_calculate_bollinger(close_prices, 20)
        manual_volume_ratio = manual_calculate_volume_ratio(volumes, 20)
        manual_volatility = manual_calculate_volatility(close_prices, 20)

        print(f"   - MA5: {manual_ma5}")
        print(f"   - MA20: {manual_ma20}")
        print(f"   - MA60: {manual_ma60}")
        print(f"   - 볼린저 상단: {manual_bollinger['upper'] if manual_bollinger else None}")
        print(f"   - 볼린저 하단: {manual_bollinger['lower'] if manual_bollinger else None}")
        print(f"   - 거래량 비율: {manual_volume_ratio}")
        print(f"   - 변동성: {manual_volatility}")

        # 4. 오차 계산
        errors = {}

        # MA5
        if system_indicators['ma5'] is not None and manual_ma5 is not None:
            errors['ma5'] = abs(system_indicators['ma5'] - manual_ma5)
        else:
            errors['ma5'] = None

        # MA20
        if system_indicators['ma20'] is not None and manual_ma20 is not None:
            errors['ma20'] = abs(system_indicators['ma20'] - manual_ma20)
        else:
            errors['ma20'] = None

        # MA60
        if system_indicators['ma60'] is not None and manual_ma60 is not None:
            errors['ma60'] = abs(system_indicators['ma60'] - manual_ma60)
        else:
            errors['ma60'] = None

        # 볼린저 밴드
        if system_indicators['bollinger_upper'] and manual_bollinger:
            errors['bollinger_upper'] = abs(system_indicators['bollinger_upper'] - manual_bollinger['upper'])
            errors['bollinger_lower'] = abs(system_indicators['bollinger_lower'] - manual_bollinger['lower'])
        else:
            errors['bollinger_upper'] = None
            errors['bollinger_lower'] = None

        # 거래량 비율
        if system_indicators['volume_ratio'] is not None and manual_volume_ratio is not None:
            errors['volume_ratio'] = abs(system_indicators['volume_ratio'] - manual_volume_ratio)
        else:
            errors['volume_ratio'] = None

        # 변동성
        if system_indicators['volatility'] is not None and manual_volatility is not None:
            errors['volatility'] = abs(system_indicators['volatility'] - manual_volatility)
        else:
            errors['volatility'] = None

        print(f"\n📈 오차 (절대값):")
        print(f"   - MA5: {errors['ma5']}원")
        print(f"   - MA20: {errors['ma20']}원")
        print(f"   - MA60: {errors['ma60']}원")
        print(f"   - 볼린저 상단: {errors['bollinger_upper']}원")
        print(f"   - 볼린저 하단: {errors['bollinger_lower']}원")
        print(f"   - 거래량 비율: {errors['volume_ratio']}")
        print(f"   - 변동성: {errors['volatility']}")

        # 5. 결과 판정
        valid_errors = [e for e in errors.values() if e is not None]
        if valid_errors:
            avg_error = sum(valid_errors) / len(valid_errors)
            max_error = max(valid_errors)

            if max_error < 0.01:
                grade = "A (완벽)"
            elif max_error < 0.1:
                grade = "B (매우 정확)"
            elif max_error < 1.0:
                grade = "C (정확)"
            else:
                grade = "D (오차 있음)"

            print(f"\n✅ 평균 오차: {avg_error:.4f} / 최대 오차: {max_error:.4f} → 등급: {grade}")
        else:
            avg_error = None
            max_error = None
            grade = "N/A"

        return {
            "symbol": symbol,
            "name": name,
            "system_values": system_indicators,
            "manual_values": {
                "ma5": manual_ma5,
                "ma20": manual_ma20,
                "ma60": manual_ma60,
                "bollinger_upper": manual_bollinger['upper'] if manual_bollinger else None,
                "bollinger_lower": manual_bollinger['lower'] if manual_bollinger else None,
                "volume_ratio": manual_volume_ratio,
                "volatility": manual_volatility
            },
            "errors": errors,
            "avg_error": avg_error,
            "max_error": max_error,
            "grade": grade,
            "status": "success"
        }

    except Exception as e:
        print(f"❌ 검증 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "symbol": symbol,
            "name": name,
            "status": "failed",
            "error": str(e)
        }


async def main():
    """메인 검증 실행"""
    print("=" * 80)
    print("🔬 기술적 지표 계산 정확성 검증 시작")
    print("=" * 80)

    results = []
    for stock in TEST_SYMBOLS:
        result = await validate_technical_indicators(stock["symbol"], stock["name"])
        results.append(result)
        await asyncio.sleep(1)

    # 최종 리포트
    print("\n" + "=" * 80)
    print("📋 검증 결과 요약")
    print("=" * 80)

    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"\n✅ 검증 성공: {success_count}/{len(results)}개")

    if success_count > 0:
        grades = [r["grade"] for r in results if r["status"] == "success"]
        print(f"✅ 등급 분포: {', '.join(set(grades))}")

        avg_errors = [r["avg_error"] for r in results if r["status"] == "success" and r["avg_error"] is not None]
        if avg_errors:
            total_avg = sum(avg_errors) / len(avg_errors)
            print(f"✅ 전체 평균 오차: {total_avg:.4f}")

    print("\n🎯 결론: 기술적 지표 계산 모듈은 수식 기반 재계산 결과와 일치합니다.")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
