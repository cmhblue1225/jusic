"""
AI 분석 백테스팅 시스템
- 과거 시점의 AI 분석 결과 → 실제 수익률 비교
- 전략 성과 지표: 승률, 평균 수익률, MDD, Sharpe Ratio
- 신호별 분석: buy/sell/hold 신호의 정확도
"""
import asyncio
import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# 상위 디렉토리 모듈 임포트
from kis_data import get_daily_ohlcv, get_financial_ratio, get_investor_trend
from technical import calculate_all_indicators
from ai_ensemble import analyze_with_ensemble


def calculate_forward_return(
    ohlcv_data: List[Dict[str, Any]],
    entry_index: int,
    holding_days: int = 5
) -> Optional[float]:
    """
    특정 시점에서 진입했을 때의 미래 수익률 계산

    Args:
        ohlcv_data: 전체 OHLCV 데이터
        entry_index: 진입 시점 인덱스
        holding_days: 보유 기간 (일)

    Returns:
        float: 수익률 (%) 또는 None (데이터 부족 시)
    """
    if entry_index + holding_days >= len(ohlcv_data):
        return None

    entry_price = ohlcv_data[entry_index]["close"]
    exit_price = ohlcv_data[entry_index + holding_days]["close"]

    return ((exit_price - entry_price) / entry_price) * 100


def calculate_performance_metrics(returns: List[float]) -> Dict[str, float]:
    """
    전략 성과 지표 계산

    Args:
        returns: 수익률 리스트 (%)

    Returns:
        Dict: 성과 지표
            - total_trades: 총 거래 수
            - win_rate: 승률 (%)
            - avg_return: 평균 수익률 (%)
            - total_return: 누적 수익률 (%)
            - max_return: 최대 수익률 (%)
            - max_loss: 최대 손실률 (%)
            - sharpe_ratio: 샤프 비율
            - max_drawdown: 최대 낙폭 (MDD, %)
    """
    if not returns:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "avg_return": 0.0,
            "total_return": 0.0,
            "max_return": 0.0,
            "max_loss": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0
        }

    returns_array = np.array(returns)

    # 1. 기본 지표
    total_trades = len(returns)
    win_rate = (np.sum(returns_array > 0) / total_trades) * 100
    avg_return = np.mean(returns_array)
    total_return = np.sum(returns_array)
    max_return = np.max(returns_array)
    max_loss = np.min(returns_array)

    # 2. 샤프 비율 (무위험 이자율 0% 가정)
    if np.std(returns_array) > 0:
        sharpe_ratio = (avg_return / np.std(returns_array)) * np.sqrt(252)  # 연율화
    else:
        sharpe_ratio = 0.0

    # 3. MDD (Maximum Drawdown)
    cumulative_returns = np.cumsum(returns_array)
    running_max = np.maximum.accumulate(cumulative_returns)
    drawdown = running_max - cumulative_returns
    max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0.0

    return {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 2),
        "avg_return": round(avg_return, 2),
        "total_return": round(total_return, 2),
        "max_return": round(max_return, 2),
        "max_loss": round(max_loss, 2),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "max_drawdown": round(max_drawdown, 2)
    }


async def backtest_ai_strategy(
    symbol: str,
    symbol_name: str,
    start_date: datetime,
    end_date: datetime,
    holding_days: int = 5,
    use_ensemble: bool = True
) -> Dict[str, Any]:
    """
    AI 분석 기반 매매 전략 백테스트

    Args:
        symbol: 종목 코드
        symbol_name: 종목명
        start_date: 백테스트 시작일
        end_date: 백테스트 종료일
        holding_days: 보유 기간 (기본: 5일)
        use_ensemble: 앙상블 사용 여부 (기본: True)

    Returns:
        Dict: 백테스트 결과
            - symbol: 종목 코드
            - symbol_name: 종목명
            - period: 백테스트 기간
            - strategy: 전략명
            - trades: 거래 내역 리스트
            - performance: 성과 지표
            - signal_analysis: 신호별 성과 분석
    """
    print(f"\n{'='*60}")
    print(f"📊 백테스트 시작: {symbol_name} ({symbol})")
    print(f"   기간: {start_date.date()} ~ {end_date.date()}")
    print(f"   보유기간: {holding_days}일")
    print(f"   전략: {'AI Ensemble' if use_ensemble else 'GPT-4 Single'}")
    print(f"{'='*60}\n")

    # 1. 전체 기간 데이터 조회 (백테스트 기간 + 기술적 지표 계산용 60일)
    total_days = (end_date - start_date).days + 60 + holding_days
    ohlcv_data = await get_daily_ohlcv(symbol, days=total_days)

    if len(ohlcv_data) < 60:
        raise ValueError(f"데이터 부족: {len(ohlcv_data)}일 (최소 60일 필요)")

    print(f"✅ OHLCV 데이터 조회 완료: {len(ohlcv_data)}일")

    # 2. 백테스트 시작 인덱스 찾기
    start_index = None
    for i, data in enumerate(ohlcv_data):
        data_date = datetime.strptime(data["date"], "%Y%m%d")
        if data_date >= start_date:
            start_index = i
            break

    if start_index is None or start_index < 60:
        raise ValueError("백테스트 시작일이 데이터 범위를 벗어났습니다.")

    # 3. 거래 시뮬레이션
    trades = []
    signal_returns = {"buy": [], "sell": [], "hold": []}

    for i in range(start_index, len(ohlcv_data) - holding_days):
        # 현재 시점까지의 데이터로 분석 (미래 데이터 사용 금지!)
        current_ohlcv = ohlcv_data[:i + 1]
        current_date = datetime.strptime(current_ohlcv[-1]["date"], "%Y%m%d")

        # 백테스트 종료일 초과 시 중단
        if current_date > end_date:
            break

        # 기술적 지표 계산
        try:
            indicators = calculate_all_indicators(current_ohlcv, include_advanced=True)
        except Exception as e:
            print(f"⚠️ 지표 계산 실패 ({current_date.date()}): {str(e)}")
            continue

        # 재무 데이터 및 투자자 동향 (실제로는 과거 시점 데이터가 필요하지만, 여기서는 최신 데이터 사용)
        try:
            financial_data = await get_financial_ratio(symbol)
            investor_data = await get_investor_trend(symbol)
        except Exception as e:
            print(f"⚠️ 재무/투자자 데이터 조회 실패: {str(e)}")
            financial_data = {}
            investor_data = {}

        # 가짜 뉴스 데이터 (백테스트에서는 실제 뉴스 없음)
        news_data = []

        # AI 분석 실행
        try:
            if use_ensemble:
                ai_result = await analyze_with_ensemble(
                    symbol, symbol_name, indicators, news_data, financial_data, investor_data
                )
            else:
                # 단일 모델 분석은 ai_analyzer.py 사용
                from ai_analyzer import analyze_stock
                ai_result = await analyze_stock(
                    symbol, symbol_name, indicators, news_data, financial_data, investor_data
                )
        except Exception as e:
            print(f"⚠️ AI 분석 실패 ({current_date.date()}): {str(e)}")
            continue

        # 투자 신호
        signal = ai_result.get("recommendation", "hold")

        # 미래 수익률 계산 (실제 거래 시뮬레이션)
        forward_return = calculate_forward_return(ohlcv_data, i, holding_days)

        if forward_return is None:
            continue

        # 거래 기록
        trade = {
            "date": current_ohlcv[-1]["date"],
            "entry_price": current_ohlcv[-1]["close"],
            "signal": signal,
            "evaluation_score": ai_result.get("evaluation_score", 50),
            "forward_return": forward_return,
            "profit": forward_return > 0
        }

        trades.append(trade)
        signal_returns[signal].append(forward_return)

        # 진행 상황 출력 (10거래마다)
        if len(trades) % 10 == 0:
            print(f"   진행: {len(trades)}개 거래 분석 완료...")

    # 4. 성과 분석
    print(f"\n✅ 백테스트 완료: 총 {len(trades)}개 거래")

    # 전체 성과
    all_returns = [t["forward_return"] for t in trades]
    overall_performance = calculate_performance_metrics(all_returns)

    # 신호별 성과
    signal_analysis = {}
    for signal, returns in signal_returns.items():
        if returns:
            signal_analysis[signal] = calculate_performance_metrics(returns)
        else:
            signal_analysis[signal] = {
                "total_trades": 0,
                "win_rate": 0.0,
                "avg_return": 0.0
            }

    # 5. 결과 출력
    print(f"\n{'='*60}")
    print(f"📊 백테스트 결과 요약")
    print(f"{'='*60}")
    print(f"📈 전체 성과:")
    print(f"   - 총 거래: {overall_performance['total_trades']}회")
    print(f"   - 승률: {overall_performance['win_rate']}%")
    print(f"   - 평균 수익률: {overall_performance['avg_return']:+.2f}%")
    print(f"   - 누적 수익률: {overall_performance['total_return']:+.2f}%")
    print(f"   - 샤프 비율: {overall_performance['sharpe_ratio']:.2f}")
    print(f"   - MDD: {overall_performance['max_drawdown']:.2f}%")

    print(f"\n📊 신호별 성과:")
    for signal, perf in signal_analysis.items():
        if perf["total_trades"] > 0:
            print(f"   [{signal.upper()}] 거래: {perf['total_trades']}회, "
                  f"승률: {perf['win_rate']}%, "
                  f"평균 수익률: {perf['avg_return']:+.2f}%")

    print(f"{'='*60}\n")

    return {
        "symbol": symbol,
        "symbol_name": symbol_name,
        "period": {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d")
        },
        "strategy": "AI Ensemble" if use_ensemble else "GPT-4 Single",
        "holding_days": holding_days,
        "trades": trades,
        "performance": overall_performance,
        "signal_analysis": signal_analysis
    }


async def compare_strategies(
    symbol: str,
    symbol_name: str,
    start_date: datetime,
    end_date: datetime
) -> Dict[str, Any]:
    """
    여러 전략 비교 백테스트

    비교 대상:
    - AI Ensemble (GPT-4 + Claude)
    - GPT-4 Single
    - Buy & Hold (기준선)

    Returns:
        Dict: 전략별 성과 비교 결과
    """
    print(f"\n{'='*80}")
    print(f"🔬 전략 비교 백테스트: {symbol_name} ({symbol})")
    print(f"{'='*80}\n")

    # 1. AI Ensemble 백테스트
    print("📊 [1/3] AI Ensemble 백테스트...")
    try:
        ensemble_result = await backtest_ai_strategy(
            symbol, symbol_name, start_date, end_date, holding_days=5, use_ensemble=True
        )
    except Exception as e:
        print(f"❌ AI Ensemble 백테스트 실패: {str(e)}")
        ensemble_result = None

    await asyncio.sleep(2)  # API Rate Limit 회피

    # 2. GPT-4 Single 백테스트
    print("\n📊 [2/3] GPT-4 Single 백테스트...")
    try:
        gpt4_result = await backtest_ai_strategy(
            symbol, symbol_name, start_date, end_date, holding_days=5, use_ensemble=False
        )
    except Exception as e:
        print(f"❌ GPT-4 Single 백테스트 실패: {str(e)}")
        gpt4_result = None

    # 3. Buy & Hold 백테스트 (기준선)
    print("\n📊 [3/3] Buy & Hold 기준선 계산...")
    ohlcv_data = await get_daily_ohlcv(symbol, days=(end_date - start_date).days + 60)

    start_index = None
    end_index = None
    for i, data in enumerate(ohlcv_data):
        data_date = datetime.strptime(data["date"], "%Y%m%d")
        if data_date >= start_date and start_index is None:
            start_index = i
        if data_date >= end_date:
            end_index = i
            break

    if start_index and end_index:
        buy_hold_return = ((ohlcv_data[end_index]["close"] - ohlcv_data[start_index]["close"]) /
                           ohlcv_data[start_index]["close"]) * 100
    else:
        buy_hold_return = 0.0

    print(f"✅ Buy & Hold 수익률: {buy_hold_return:+.2f}%")

    # 4. 결과 비교
    print(f"\n{'='*80}")
    print(f"📊 전략 비교 결과")
    print(f"{'='*80}")

    comparison = {
        "symbol": symbol,
        "symbol_name": symbol_name,
        "period": {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d")
        },
        "strategies": {}
    }

    if ensemble_result:
        comparison["strategies"]["AI Ensemble"] = ensemble_result["performance"]
        print(f"✅ [AI Ensemble] 수익률: {ensemble_result['performance']['total_return']:+.2f}%, "
              f"승률: {ensemble_result['performance']['win_rate']:.1f}%, "
              f"샤프: {ensemble_result['performance']['sharpe_ratio']:.2f}")

    if gpt4_result:
        comparison["strategies"]["GPT-4 Single"] = gpt4_result["performance"]
        print(f"✅ [GPT-4 Single] 수익률: {gpt4_result['performance']['total_return']:+.2f}%, "
              f"승률: {gpt4_result['performance']['win_rate']:.1f}%, "
              f"샤프: {gpt4_result['performance']['sharpe_ratio']:.2f}")

    comparison["strategies"]["Buy & Hold"] = {"total_return": round(buy_hold_return, 2)}
    print(f"✅ [Buy & Hold] 수익률: {buy_hold_return:+.2f}%")

    print(f"{'='*80}\n")

    return comparison


# 메인 실행 예시
async def main():
    """백테스트 실행 예시"""
    # 삼성전자 3개월 백테스트
    result = await backtest_ai_strategy(
        symbol="005930",
        symbol_name="삼성전자",
        start_date=datetime(2024, 7, 1),
        end_date=datetime(2024, 10, 1),
        holding_days=5,
        use_ensemble=True
    )

    # 전략 비교
    # comparison = await compare_strategies(
    #     symbol="005930",
    #     symbol_name="삼성전자",
    #     start_date=datetime(2024, 7, 1),
    #     end_date=datetime(2024, 10, 1)
    # )


if __name__ == "__main__":
    asyncio.run(main())
