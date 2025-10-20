"""
섹터 비교 분석 모듈
- 동일 섹터 내 종목 성과 비교
- 업종 평균 대비 상대 강도
- 섹터 리더/라거드 식별
- 섹터 로테이션 신호 탐지
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np

from kis_data import get_daily_ohlcv, get_financial_ratio
from technical import calculate_all_indicators


# 한국 주식 시장 주요 섹터 정의
SECTORS = {
    "반도체": ["005930", "000660", "035420"],  # 삼성전자, SK하이닉스, NAVER
    "자동차": ["005380", "000270"],            # 현대차, 기아
    "배터리": ["373220"],                      # LG에너지솔루션
    "바이오": ["207940"],                      # 삼성바이오로직스
    "금융": ["105560"],                        # KB금융
    "철강": ["005490"]                         # 포스코홀딩스
}


async def get_sector_performance(sector_name: str, period_days: int = 20) -> Dict[str, Any]:
    """
    섹터 전체 성과 계산

    Args:
        sector_name: 섹터명 (예: "반도체")
        period_days: 분석 기간 (기본: 20일)

    Returns:
        Dict: 섹터 성과
            - sector_name: 섹터명
            - stocks: 종목별 성과 리스트
            - sector_avg_return: 섹터 평균 수익률 (%)
            - sector_avg_volume_ratio: 섹터 평균 거래량 비율
            - leader: 섹터 리더 (최고 수익률 종목)
            - laggard: 섹터 라거드 (최저 수익률 종목)
    """
    if sector_name not in SECTORS:
        raise ValueError(f"알 수 없는 섹터: {sector_name}")

    symbols = SECTORS[sector_name]
    print(f"\n📊 섹터 성과 분석: {sector_name} ({len(symbols)}개 종목)")

    stocks_performance = []

    for symbol in symbols:
        try:
            # OHLCV 데이터 조회
            ohlcv_data = await get_daily_ohlcv(symbol, days=period_days + 1)

            if len(ohlcv_data) < 2:
                print(f"⚠️ {symbol}: 데이터 부족 (건너뜀)")
                continue

            # 기술적 지표 계산
            indicators = calculate_all_indicators(ohlcv_data, include_advanced=False)

            # 수익률 계산 (period_days일 전 대비)
            if len(ohlcv_data) >= period_days + 1:
                start_price = ohlcv_data[-(period_days + 1)]["close"]
                end_price = ohlcv_data[-1]["close"]
                period_return = ((end_price - start_price) / start_price) * 100
            else:
                period_return = 0.0

            stock_perf = {
                "symbol": symbol,
                "current_price": indicators["current_price"],
                "change_rate": indicators["change_rate"],
                "period_return": round(period_return, 2),
                "volume_ratio": indicators.get("volume_ratio", 1.0),
                "ma5": indicators.get("ma5"),
                "ma20": indicators.get("ma20")
            }

            stocks_performance.append(stock_perf)
            print(f"   ✅ {symbol}: {period_return:+.2f}% ({period_days}일)")

        except Exception as e:
            print(f"   ❌ {symbol}: 조회 실패 ({str(e)})")
            continue

    # 섹터 평균 계산
    if stocks_performance:
        sector_avg_return = np.mean([s["period_return"] for s in stocks_performance])
        sector_avg_volume_ratio = np.mean([s["volume_ratio"] for s in stocks_performance if s["volume_ratio"]])

        # 리더/라거드
        leader = max(stocks_performance, key=lambda x: x["period_return"])
        laggard = min(stocks_performance, key=lambda x: x["period_return"])
    else:
        sector_avg_return = 0.0
        sector_avg_volume_ratio = 1.0
        leader = None
        laggard = None

    result = {
        "sector_name": sector_name,
        "period_days": period_days,
        "stocks": stocks_performance,
        "sector_avg_return": round(sector_avg_return, 2),
        "sector_avg_volume_ratio": round(sector_avg_volume_ratio, 2),
        "leader": leader,
        "laggard": laggard,
        "timestamp": datetime.now().isoformat()
    }

    print(f"✅ 섹터 평균 수익률: {sector_avg_return:+.2f}%")
    if leader:
        print(f"   🏆 리더: {leader['symbol']} ({leader['period_return']:+.2f}%)")
    if laggard:
        print(f"   🐢 라거드: {laggard['symbol']} ({laggard['period_return']:+.2f}%)")

    return result


async def compare_with_sector(symbol: str, sector_name: str, period_days: int = 20) -> Dict[str, Any]:
    """
    특정 종목을 섹터 평균과 비교

    Args:
        symbol: 종목 코드
        sector_name: 섹터명
        period_days: 분석 기간

    Returns:
        Dict: 비교 분석 결과
            - symbol: 종목 코드
            - sector_name: 섹터명
            - stock_return: 종목 수익률 (%)
            - sector_avg_return: 섹터 평균 수익률 (%)
            - relative_strength: 상대 강도 (주식 수익률 - 섹터 평균)
            - percentile_rank: 섹터 내 백분위 순위 (0~100, 높을수록 강함)
            - outperformance: 섹터 평균 대비 초과 수익 여부 (True/False)
    """
    print(f"\n🔍 섹터 비교 분석: {symbol} vs {sector_name}")

    # 1. 섹터 전체 성과 조회
    sector_perf = await get_sector_performance(sector_name, period_days)

    # 2. 대상 종목 찾기
    target_stock = None
    for stock in sector_perf["stocks"]:
        if stock["symbol"] == symbol:
            target_stock = stock
            break

    if not target_stock:
        raise ValueError(f"종목 {symbol}이 섹터 {sector_name}에 포함되어 있지 않습니다.")

    # 3. 상대 강도 계산
    stock_return = target_stock["period_return"]
    sector_avg_return = sector_perf["sector_avg_return"]
    relative_strength = stock_return - sector_avg_return

    # 4. 백분위 순위 계산
    returns = [s["period_return"] for s in sector_perf["stocks"]]
    percentile_rank = (np.sum(np.array(returns) < stock_return) / len(returns)) * 100

    # 5. 초과 수익 여부
    outperformance = stock_return > sector_avg_return

    result = {
        "symbol": symbol,
        "sector_name": sector_name,
        "period_days": period_days,
        "stock_return": stock_return,
        "sector_avg_return": sector_avg_return,
        "relative_strength": round(relative_strength, 2),
        "percentile_rank": round(percentile_rank, 2),
        "outperformance": outperformance,
        "sector_leader": sector_perf["leader"]["symbol"] if sector_perf["leader"] else None,
        "sector_laggard": sector_perf["laggard"]["symbol"] if sector_perf["laggard"] else None,
        "timestamp": datetime.now().isoformat()
    }

    print(f"\n📈 비교 결과:")
    print(f"   - 종목 수익률: {stock_return:+.2f}%")
    print(f"   - 섹터 평균: {sector_avg_return:+.2f}%")
    print(f"   - 상대 강도: {relative_strength:+.2f}%p")
    print(f"   - 섹터 내 순위: 상위 {100 - percentile_rank:.1f}%")
    print(f"   - 초과 수익: {'✅ Yes' if outperformance else '❌ No'}")

    return result


async def detect_sector_rotation(period_days: int = 20) -> Dict[str, Any]:
    """
    섹터 로테이션 탐지 - 어떤 섹터가 강세/약세인지 파악

    Args:
        period_days: 분석 기간

    Returns:
        Dict: 섹터 로테이션 분석
            - sectors: 섹터별 성과 리스트 (수익률 순)
            - leading_sector: 강세 섹터 (최고 수익률)
            - lagging_sector: 약세 섹터 (최저 수익률)
            - rotation_signal: 로테이션 신호
                - "DEFENSIVE": 방어주 섹터 강세 (금융, 필수소비재)
                - "CYCLICAL": 경기민감주 섹터 강세 (반도체, 자동차)
                - "NEUTRAL": 균형 상태
    """
    print(f"\n🔄 섹터 로테이션 분석 ({period_days}일)")
    print(f"{'='*60}")

    sector_results = []

    for sector_name in SECTORS.keys():
        try:
            sector_perf = await get_sector_performance(sector_name, period_days)
            sector_results.append({
                "sector_name": sector_name,
                "avg_return": sector_perf["sector_avg_return"],
                "avg_volume_ratio": sector_perf["sector_avg_volume_ratio"]
            })
        except Exception as e:
            print(f"❌ {sector_name}: 분석 실패 ({str(e)})")
            continue

    # 수익률 순 정렬
    sector_results.sort(key=lambda x: x["avg_return"], reverse=True)

    # 강세/약세 섹터
    leading_sector = sector_results[0] if sector_results else None
    lagging_sector = sector_results[-1] if sector_results else None

    # 로테이션 신호 탐지
    rotation_signal = "NEUTRAL"

    if leading_sector:
        # 경기민감주 섹터 (반도체, 자동차) 강세 → CYCLICAL
        if leading_sector["sector_name"] in ["반도체", "자동차", "철강"]:
            rotation_signal = "CYCLICAL"
        # 방어주 섹터 (금융, 필수소비재) 강세 → DEFENSIVE
        elif leading_sector["sector_name"] in ["금융", "바이오"]:
            rotation_signal = "DEFENSIVE"

    result = {
        "period_days": period_days,
        "sectors": sector_results,
        "leading_sector": leading_sector,
        "lagging_sector": lagging_sector,
        "rotation_signal": rotation_signal,
        "timestamp": datetime.now().isoformat()
    }

    print(f"\n📊 로테이션 분석 결과:")
    for i, sector in enumerate(sector_results, 1):
        print(f"   {i}. {sector['sector_name']}: {sector['avg_return']:+.2f}%")

    if leading_sector:
        print(f"\n🏆 강세 섹터: {leading_sector['sector_name']} ({leading_sector['avg_return']:+.2f}%)")
    if lagging_sector:
        print(f"🐢 약세 섹터: {lagging_sector['sector_name']} ({lagging_sector['avg_return']:+.2f}%)")

    print(f"\n🔄 로테이션 신호: {rotation_signal}")
    if rotation_signal == "CYCLICAL":
        print("   → 경기민감주 강세 (경기 확장 국면 가능성)")
    elif rotation_signal == "DEFENSIVE":
        print("   → 방어주 강세 (경기 둔화/하락 국면 가능성)")
    else:
        print("   → 균형 상태 (명확한 로테이션 없음)")

    print(f"{'='*60}\n")

    return result


async def analyze_sector_fundamentals(sector_name: str) -> Dict[str, Any]:
    """
    섹터 기본적 분석 - 섹터 내 종목들의 평균 재무비율

    Args:
        sector_name: 섹터명

    Returns:
        Dict: 섹터 기본적 분석
            - sector_name: 섹터명
            - avg_per: 평균 PER
            - avg_pbr: 평균 PBR
            - avg_roe: 평균 ROE (%)
            - avg_debt_ratio: 평균 부채비율 (%)
            - valuation_level: 밸류에이션 수준 ('undervalued', 'fair', 'overvalued')
    """
    if sector_name not in SECTORS:
        raise ValueError(f"알 수 없는 섹터: {sector_name}")

    symbols = SECTORS[sector_name]
    print(f"\n📊 섹터 기본적 분석: {sector_name}")

    financials = []

    for symbol in symbols:
        try:
            financial_data = await get_financial_ratio(symbol)

            if financial_data.get("per") and financial_data.get("pbr"):
                financials.append({
                    "symbol": symbol,
                    "per": financial_data.get("per"),
                    "pbr": financial_data.get("pbr"),
                    "roe": financial_data.get("roe"),
                    "debt_ratio": financial_data.get("debt_ratio")
                })
                print(f"   ✅ {symbol}: PER={financial_data.get('per')}, PBR={financial_data.get('pbr')}")

        except Exception as e:
            print(f"   ❌ {symbol}: 재무 데이터 조회 실패")
            continue

    # 평균 계산
    if financials:
        avg_per = np.mean([f["per"] for f in financials if f["per"]])
        avg_pbr = np.mean([f["pbr"] for f in financials if f["pbr"]])
        avg_roe = np.mean([f["roe"] for f in financials if f["roe"]])
        avg_debt_ratio = np.mean([f["debt_ratio"] for f in financials if f["debt_ratio"]])

        # 밸류에이션 판단 (PER, PBR 기준)
        if avg_per < 10 and avg_pbr < 1:
            valuation_level = "undervalued"
        elif avg_per > 30 or avg_pbr > 3:
            valuation_level = "overvalued"
        else:
            valuation_level = "fair"
    else:
        avg_per = None
        avg_pbr = None
        avg_roe = None
        avg_debt_ratio = None
        valuation_level = "unknown"

    result = {
        "sector_name": sector_name,
        "stocks_count": len(financials),
        "avg_per": round(avg_per, 2) if avg_per else None,
        "avg_pbr": round(avg_pbr, 2) if avg_pbr else None,
        "avg_roe": round(avg_roe, 2) if avg_roe else None,
        "avg_debt_ratio": round(avg_debt_ratio, 2) if avg_debt_ratio else None,
        "valuation_level": valuation_level,
        "timestamp": datetime.now().isoformat()
    }

    print(f"\n📈 섹터 평균 재무비율:")
    print(f"   - PER: {result['avg_per']}")
    print(f"   - PBR: {result['avg_pbr']}")
    print(f"   - ROE: {result['avg_roe']}%")
    print(f"   - 부채비율: {result['avg_debt_ratio']}%")
    print(f"   - 밸류에이션: {valuation_level.upper()}")

    return result


# 테스트용 메인 함수
async def main():
    """섹터 분석 테스트"""
    from dotenv import load_dotenv
    load_dotenv()

    # 1. 섹터 로테이션 분석
    rotation_result = await detect_sector_rotation(period_days=20)

    # 2. 특정 종목 섹터 비교 (삼성전자 vs 반도체 섹터)
    # compare_result = await compare_with_sector("005930", "반도체", period_days=20)

    # 3. 섹터 기본적 분석
    # fundamentals = await analyze_sector_fundamentals("반도체")


if __name__ == "__main__":
    asyncio.run(main())
