"""
KIS API 고급 데이터 조회 모듈
- 호가 (매수/매도 10호가)
- 체결 (실시간 체결가)
- 공매도 (공매도 잔고 비율)
- 프로그램 매매 (외국인/기관 프로그램 순매수)
"""
import os
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# KIS 토큰 관리는 kis_data.py에서 통합 관리
from kis_data import get_access_token

# KIS API 설정
KIS_BASE_URL = "https://openapi.koreainvestment.com:9443"
KIS_APP_KEY = os.getenv("KIS_APP_KEY")
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET")


async def get_order_book(symbol: str) -> Dict[str, Any]:
    """
    호가 조회 (매수/매도 10호가)

    Args:
        symbol: 종목 코드 (6자리)

    Returns:
        Dict: 호가 정보
            - ask_prices: 매도 호가 리스트 (10개) [높은 가격부터]
            - ask_volumes: 매도 잔량 리스트 (10개)
            - bid_prices: 매수 호가 리스트 (10개) [높은 가격부터]
            - bid_volumes: 매수 잔량 리스트 (10개)
            - total_ask_volume: 총 매도 잔량
            - total_bid_volume: 총 매수 잔량
            - timestamp: 조회 시간
    """
    token = await get_access_token()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "authorization": f"Bearer {token}",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET,
                "tr_id": "FHKST01010200"  # 국내주식 호가 조회
            },
            params={
                "FID_COND_MRKT_DIV_CODE": "J",  # 시장 분류 (J: 주식)
                "FID_INPUT_ISCD": symbol        # 종목 코드
            }
        )

        if response.status_code != 200:
            raise Exception(f"KIS API 호가 조회 실패: {response.status_code} {response.text}")

        data = response.json()

        if data.get("rt_cd") != "0":
            error_msg = data.get("msg1", "알 수 없는 오류")
            raise Exception(f"KIS API 오류: {error_msg}")

        output1 = data.get("output1", {})
        output2 = data.get("output2", {})

        # 매도 호가 (10호가)
        ask_prices = []
        ask_volumes = []
        for i in range(1, 11):
            price_key = f"askp{i}"
            volume_key = f"askp_rsqn{i}"
            if output1.get(price_key):
                ask_prices.append(float(output1[price_key]))
                ask_volumes.append(int(output1.get(volume_key, 0)))

        # 매수 호가 (10호가)
        bid_prices = []
        bid_volumes = []
        for i in range(1, 11):
            price_key = f"bidp{i}"
            volume_key = f"bidp_rsqn{i}"
            if output1.get(price_key):
                bid_prices.append(float(output1[price_key]))
                bid_volumes.append(int(output1.get(volume_key, 0)))

        # 총 매도/매수 잔량
        total_ask_volume = int(output2.get("total_askp_rsqn", 0))
        total_bid_volume = int(output2.get("total_bidp_rsqn", 0))

        result = {
            "ask_prices": ask_prices,
            "ask_volumes": ask_volumes,
            "bid_prices": bid_prices,
            "bid_volumes": bid_volumes,
            "total_ask_volume": total_ask_volume,
            "total_bid_volume": total_bid_volume,
            "timestamp": datetime.now().isoformat()
        }

        print(f"✅ {symbol} 호가 조회: 매도 {total_ask_volume:,}주 / 매수 {total_bid_volume:,}주")
        return result


async def get_execution_data(symbol: str) -> Dict[str, Any]:
    """
    체결 데이터 조회 (실시간 체결가, 체결량)

    Args:
        symbol: 종목 코드 (6자리)

    Returns:
        Dict: 체결 정보
            - current_price: 현재 체결가
            - change_rate: 등락률 (%)
            - volume: 누적 거래량
            - transaction_volume: 체결량 (최근 체결)
            - timestamp: 조회 시간
    """
    token = await get_access_token()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-ccnl",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "authorization": f"Bearer {token}",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET,
                "tr_id": "FHKST01010300"  # 국내주식 체결 조회
            },
            params={
                "FID_COND_MRKT_DIV_CODE": "J",  # 시장 분류 (J: 주식)
                "FID_INPUT_ISCD": symbol        # 종목 코드
            }
        )

        if response.status_code != 200:
            raise Exception(f"KIS API 체결 조회 실패: {response.status_code} {response.text}")

        data = response.json()

        if data.get("rt_cd") != "0":
            error_msg = data.get("msg1", "알 수 없는 오류")
            raise Exception(f"KIS API 오류: {error_msg}")

        output = data.get("output", [])

        if not output:
            raise Exception("체결 데이터 없음")

        # 최근 체결 (첫 번째 데이터)
        latest = output[0]

        result = {
            "current_price": float(latest.get("stck_prpr", 0)),         # 현재가
            "change_rate": float(latest.get("prdy_ctrt", 0)),           # 등락률
            "volume": int(latest.get("acml_vol", 0)),                   # 누적 거래량
            "transaction_volume": int(latest.get("cntg_vol", 0)),       # 체결량
            "timestamp": datetime.now().isoformat()
        }

        print(f"✅ {symbol} 체결: {result['current_price']:,}원 ({result['change_rate']:+.2f}%), "
              f"체결량: {result['transaction_volume']:,}주")
        return result


async def get_short_selling(symbol: str) -> Dict[str, Any]:
    """
    공매도 잔고 비율 조회

    Args:
        symbol: 종목 코드 (6자리)

    Returns:
        Dict: 공매도 정보
            - short_ratio: 공매도 잔고 비율 (%)
            - short_volume: 공매도 잔고 (주)
            - listed_shares: 상장 주식수
            - timestamp: 조회 시간
    """
    token = await get_access_token()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "authorization": f"Bearer {token}",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET,
                "tr_id": "FHKST03010100"  # 국내주식 기간별시세
            },
            params={
                "FID_COND_MRKT_DIV_CODE": "J",  # 시장 분류
                "FID_INPUT_ISCD": symbol,       # 종목 코드
                "FID_INPUT_DATE_1": (datetime.now() - timedelta(days=30)).strftime("%Y%m%d"),
                "FID_INPUT_DATE_2": datetime.now().strftime("%Y%m%d"),
                "FID_PERIOD_DIV_CODE": "D",     # 일봉
                "FID_ORG_ADJ_PRC": "0"          # 수정주가 미적용
            }
        )

        if response.status_code != 200:
            raise Exception(f"KIS API 공매도 조회 실패: {response.status_code} {response.text}")

        data = response.json()

        if data.get("rt_cd") != "0":
            error_msg = data.get("msg1", "알 수 없는 오류")
            raise Exception(f"KIS API 오류: {error_msg}")

        # 주의: KIS API는 공매도 데이터를 직접 제공하지 않을 수 있음
        # 실제 공매도 데이터는 금융감독원 API 또는 별도 API 필요
        # 여기서는 구조만 제공

        result = {
            "short_ratio": 0.0,      # 실제 API 연동 필요
            "short_volume": 0,       # 실제 API 연동 필요
            "listed_shares": 0,      # 실제 API 연동 필요
            "timestamp": datetime.now().isoformat(),
            "note": "공매도 데이터는 금융감독원 API 연동 필요"
        }

        print(f"⚠️ {symbol} 공매도: KIS API는 공매도 데이터를 직접 제공하지 않음 (금융감독원 API 필요)")
        return result


async def get_program_trading(symbol: str) -> Dict[str, Any]:
    """
    프로그램 매매 동향 조회 (외국인/기관 프로그램 순매수)

    Args:
        symbol: 종목 코드 (6자리)

    Returns:
        Dict: 프로그램 매매 정보
            - foreign_program_net_buy: 외국인 프로그램 순매수 (주)
            - institution_program_net_buy: 기관 프로그램 순매수 (주)
            - timestamp: 조회 시간
    """
    token = await get_access_token()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "authorization": f"Bearer {token}",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET,
                "tr_id": "FHKST03010100"
            },
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol,
                "FID_INPUT_DATE_1": (datetime.now() - timedelta(days=5)).strftime("%Y%m%d"),
                "FID_INPUT_DATE_2": datetime.now().strftime("%Y%m%d"),
                "FID_PERIOD_DIV_CODE": "D",
                "FID_ORG_ADJ_PRC": "0"
            }
        )

        if response.status_code != 200:
            raise Exception(f"KIS API 프로그램 매매 조회 실패: {response.status_code} {response.text}")

        data = response.json()

        if data.get("rt_cd") != "0":
            error_msg = data.get("msg1", "알 수 없는 오류")
            raise Exception(f"KIS API 오류: {error_msg}")

        # 주의: KIS API는 프로그램 매매 데이터를 직접 제공하지 않을 수 있음
        # 실제 데이터는 증권사별 API 또는 별도 API 필요
        # 여기서는 구조만 제공

        result = {
            "foreign_program_net_buy": 0,      # 실제 API 연동 필요
            "institution_program_net_buy": 0,  # 실제 API 연동 필요
            "timestamp": datetime.now().isoformat(),
            "note": "프로그램 매매 데이터는 별도 API 연동 필요"
        }

        print(f"⚠️ {symbol} 프로그램 매매: KIS API는 직접 제공하지 않음 (증권사별 API 필요)")
        return result


async def get_advanced_stock_data(symbol: str) -> Dict[str, Any]:
    """
    고급 주식 데이터 종합 조회

    Args:
        symbol: 종목 코드 (6자리)

    Returns:
        Dict: 고급 데이터 종합
            - order_book: 호가 정보
            - execution: 체결 정보
            - short_selling: 공매도 정보
            - program_trading: 프로그램 매매 정보
    """
    print(f"\n🔍 고급 데이터 조회 시작: {symbol}")

    try:
        # 호가
        order_book = await get_order_book(symbol)
    except Exception as e:
        print(f"⚠️ 호가 조회 실패: {str(e)}")
        order_book = {}

    try:
        # 체결
        execution = await get_execution_data(symbol)
    except Exception as e:
        print(f"⚠️ 체결 조회 실패: {str(e)}")
        execution = {}

    try:
        # 공매도 (주의: 실제 API 연동 필요)
        short_selling = await get_short_selling(symbol)
    except Exception as e:
        print(f"⚠️ 공매도 조회 실패: {str(e)}")
        short_selling = {}

    try:
        # 프로그램 매매 (주의: 실제 API 연동 필요)
        program_trading = await get_program_trading(symbol)
    except Exception as e:
        print(f"⚠️ 프로그램 매매 조회 실패: {str(e)}")
        program_trading = {}

    result = {
        "symbol": symbol,
        "order_book": order_book,
        "execution": execution,
        "short_selling": short_selling,
        "program_trading": program_trading,
        "timestamp": datetime.now().isoformat()
    }

    print(f"✅ 고급 데이터 조회 완료: {symbol}\n")
    return result


# 테스트용 메인 함수
async def main():
    """고급 데이터 조회 테스트"""
    from dotenv import load_dotenv
    load_dotenv()

    # 삼성전자 고급 데이터 조회
    data = await get_advanced_stock_data("005930")

    print("\n📊 고급 데이터 조회 결과:")
    print(f"호가: {data['order_book']}")
    print(f"체결: {data['execution']}")
    print(f"공매도: {data['short_selling']}")
    print(f"프로그램: {data['program_trading']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
