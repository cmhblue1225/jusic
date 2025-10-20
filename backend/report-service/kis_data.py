"""
KIS API 데이터 조회 모듈
- 1일 주가 데이터 (OHLCV) 조회
- OAuth 토큰 관리
"""
import os
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# KIS API 설정
KIS_BASE_URL = "https://openapi.koreainvestment.com:9443"
KIS_APP_KEY = os.getenv("KIS_APP_KEY")
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET")

# 토큰 캐시 (메모리)
_token_cache: Dict[str, Any] = {}


async def get_access_token() -> str:
    """
    KIS API OAuth 토큰 발급 (캐시 사용)

    Returns:
        str: Access Token
    """
    global _token_cache

    # 캐시된 토큰이 있고, 아직 유효하면 재사용
    if _token_cache.get("token") and _token_cache.get("expires_at"):
        if datetime.now() < _token_cache["expires_at"]:
            print("✅ 캐시된 KIS 토큰 사용")
            return _token_cache["token"]

    # 새 토큰 발급
    print("🔄 KIS API 토큰 발급 중...")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KIS_BASE_URL}/oauth2/tokenP",
            json={
                "grant_type": "client_credentials",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET
            },
            headers={"Content-Type": "application/json"}
        )

        if response.status_code != 200:
            raise Exception(f"KIS 토큰 발급 실패: {response.status_code} {response.text}")

        data = response.json()
        token = data["access_token"]
        expires_in = data.get("expires_in", 86400)  # 기본 24시간

        # 캐시 저장 (만료 5분 전까지 유효하게 설정)
        _token_cache = {
            "token": token,
            "expires_at": datetime.now() + timedelta(seconds=expires_in - 300)
        }

        print(f"✅ KIS 토큰 발급 완료 (유효기간: {expires_in // 3600}시간)")
        return token


async def get_daily_ohlcv(symbol: str, days: int = 60) -> List[Dict[str, Any]]:
    """
    일별 주가 데이터 조회 (OHLCV)

    Args:
        symbol: 종목 코드 (6자리, 예: '005930')
        days: 조회 기간 (기본: 60일 - 이평선 60일 계산용)

    Returns:
        List[Dict]: 일별 OHLCV 데이터
            - date: 날짜 (YYYYMMDD)
            - open: 시가
            - high: 고가
            - low: 저가
            - close: 종가
            - volume: 거래량
    """
    token = await get_access_token()

    # 조회 시작일 계산 (영업일 기준 여유있게 +20일)
    start_date = (datetime.now() - timedelta(days=days + 20)).strftime("%Y%m%d")
    end_date = datetime.now().strftime("%Y%m%d")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "authorization": f"Bearer {token}",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET,
                "tr_id": "FHKST03010100"  # 국내주식 기간별시세(일/주/월/년)
            },
            params={
                "FID_COND_MRKT_DIV_CODE": "J",  # 시장 분류 (J: 주식)
                "FID_INPUT_ISCD": symbol,       # 종목 코드
                "FID_INPUT_DATE_1": start_date, # 시작일
                "FID_INPUT_DATE_2": end_date,   # 종료일
                "FID_PERIOD_DIV_CODE": "D",     # 기간 분류 (D: 일봉)
                "FID_ORG_ADJ_PRC": "0"          # 수정주가 (0: 미적용)
            }
        )

        if response.status_code != 200:
            raise Exception(f"KIS API 주가 조회 실패: {response.status_code} {response.text}")

        data = response.json()

        if data.get("rt_cd") != "0":
            error_msg = data.get("msg1", "알 수 없는 오류")
            raise Exception(f"KIS API 오류: {error_msg}")

        output2 = data.get("output2", [])

        # 데이터 변환
        ohlcv_data = []
        for item in output2:
            ohlcv_data.append({
                "date": item["stck_bsop_date"],                    # 날짜
                "open": float(item["stck_oprc"]),                  # 시가
                "high": float(item["stck_hgpr"]),                  # 고가
                "low": float(item["stck_lwpr"]),                   # 저가
                "close": float(item["stck_clpr"]),                 # 종가
                "volume": int(item["acml_vol"])                    # 거래량
            })

        # 날짜 오름차순 정렬
        ohlcv_data.sort(key=lambda x: x["date"])

        print(f"✅ {symbol} 주가 데이터 {len(ohlcv_data)}일 조회 완료")
        return ohlcv_data


async def get_current_price(symbol: str) -> Dict[str, Any]:
    """
    현재가 조회

    Args:
        symbol: 종목 코드 (6자리)

    Returns:
        Dict: 현재가 정보
            - price: 현재가
            - change_rate: 등락률 (%)
            - high: 고가
            - low: 저가
            - volume: 거래량
    """
    token = await get_access_token()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "authorization": f"Bearer {token}",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET,
                "tr_id": "FHKST01010100"  # 주식현재가 시세
            },
            params={
                "FID_COND_MRKT_DIV_CODE": "J",  # 시장 분류 (J: 주식)
                "FID_INPUT_ISCD": symbol        # 종목 코드
            }
        )

        if response.status_code != 200:
            raise Exception(f"KIS API 현재가 조회 실패: {response.status_code} {response.text}")

        data = response.json()

        if data.get("rt_cd") != "0":
            error_msg = data.get("msg1", "알 수 없는 오류")
            raise Exception(f"KIS API 오류: {error_msg}")

        output = data.get("output", {})

        result = {
            "price": float(output["stck_prpr"]),                   # 현재가
            "change_rate": float(output["prdy_ctrt"]),             # 등락률
            "high": float(output["stck_hgpr"]),                    # 고가
            "low": float(output["stck_lwpr"]),                     # 저가
            "volume": int(output["acml_vol"])                      # 거래량
        }

        print(f"✅ {symbol} 현재가: {result['price']:,}원 ({result['change_rate']:+.2f}%)")
        return result


async def get_financial_ratio(symbol: str) -> Dict[str, Any]:
    """
    재무비율 조회 (PER, PBR, ROE, 배당수익률 등)

    Args:
        symbol: 종목 코드 (6자리)

    Returns:
        Dict: 재무비율 정보
            - per: PER (주가수익비율)
            - pbr: PBR (주가순자산비율)
            - roe: ROE (자기자본이익률, %)
            - dividend_yield: 배당수익률 (%)
            - eps: EPS (주당순이익)
            - bps: BPS (주당순자산)
            - operating_margin: 영업이익률 (%)
            - net_margin: 순이익률 (%)
            - debt_ratio: 부채비율 (%)
    """
    token = await get_access_token()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{KIS_BASE_URL}/uapi/domestic-stock/v1/finance/financial-ratio",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "authorization": f"Bearer {token}",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET,
                "tr_id": "FHKST66430300"  # 국내주식 재무비율
            },
            params={
                "FID_DIV_CLS_CODE": "0",    # 분류 (0: 전체)
                "fid_cond_mrkt_div_code": "J",  # 시장 분류 (J: 주식)
                "fid_input_iscd": symbol    # 종목 코드
            }
        )

        if response.status_code != 200:
            raise Exception(f"KIS API 재무비율 조회 실패: {response.status_code} {response.text}")

        data = response.json()

        if data.get("rt_cd") != "0":
            error_msg = data.get("msg1", "알 수 없는 오류")
            raise Exception(f"KIS API 오류: {error_msg}")

        output = data.get("output", {})

        # output이 list인 경우 첫 번째 요소 사용
        if isinstance(output, list):
            output = output[0] if output else {}

        # 안전한 float 변환 (빈 문자열이나 None 처리)
        def safe_float(value, default=None):
            try:
                return float(value) if value and str(value).strip() else default
            except (ValueError, TypeError):
                return default

        result = {
            "per": safe_float(output.get("per")),                          # PER
            "pbr": safe_float(output.get("pbr")),                          # PBR
            "roe": safe_float(output.get("roe")),                          # ROE (%)
            "dividend_yield": safe_float(output.get("per_xstk_yldd")),     # 배당수익률 (%)
            "eps": safe_float(output.get("eps")),                          # EPS (주당순이익)
            "bps": safe_float(output.get("bps")),                          # BPS (주당순자산)
            "operating_margin": safe_float(output.get("bsop_prfi_inrt")), # 영업이익률 (%)
            "net_margin": safe_float(output.get("ntin_inrt")),            # 순이익률 (%)
            "debt_ratio": safe_float(output.get("debt_rate"))             # 부채비율 (%)
        }

        print(f"✅ {symbol} 재무비율: PER={result['per']}, PBR={result['pbr']}, ROE={result['roe']}%")
        return result


async def get_investor_trend(symbol: str) -> Dict[str, Any]:
    """
    투자자별 매매 동향 조회 (외국인, 기관, 개인)

    Args:
        symbol: 종목 코드 (6자리)

    Returns:
        Dict: 투자자별 매매 동향
            - foreign_net_buy: 외국인 순매수 (주)
            - foreign_net_buy_amt: 외국인 순매수금액 (원)
            - institution_net_buy: 기관 순매수 (주)
            - institution_net_buy_amt: 기관 순매수금액 (원)
            - individual_net_buy: 개인 순매수 (주)
            - individual_net_buy_amt: 개인 순매수금액 (원)
    """
    token = await get_access_token()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-investor",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "authorization": f"Bearer {token}",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET,
                "tr_id": "FHKST01010900"  # 주식현재가 투자자
            },
            params={
                "FID_COND_MRKT_DIV_CODE": "J",  # 시장 분류 (J: 주식)
                "FID_INPUT_ISCD": symbol        # 종목 코드
            }
        )

        if response.status_code != 200:
            raise Exception(f"KIS API 투자자 동향 조회 실패: {response.status_code} {response.text}")

        data = response.json()

        if data.get("rt_cd") != "0":
            error_msg = data.get("msg1", "알 수 없는 오류")
            raise Exception(f"KIS API 오류: {error_msg}")

        output = data.get("output", {})

        # output이 list인 경우 첫 번째 요소 사용
        if isinstance(output, list):
            output = output[0] if output else {}

        # 안전한 int/float 변환
        def safe_int(value, default=0):
            try:
                return int(value) if value and str(value).strip() else default
            except (ValueError, TypeError):
                return default

        def safe_float(value, default=0.0):
            try:
                return float(value) if value and str(value).strip() else default
            except (ValueError, TypeError):
                return default

        result = {
            "foreign_net_buy": safe_int(output.get("frgn_ntby_qty")),          # 외국인 순매수량
            "foreign_net_buy_amt": safe_float(output.get("frgn_ntby_tr_pbmn")), # 외국인 순매수금액
            "institution_net_buy": safe_int(output.get("orgn_ntby_qty")),      # 기관 순매수량
            "institution_net_buy_amt": safe_float(output.get("orgn_ntby_tr_pbmn")), # 기관 순매수금액
            "individual_net_buy": safe_int(output.get("prsn_ntby_qty")),       # 개인 순매수량
            "individual_net_buy_amt": safe_float(output.get("prsn_ntby_tr_pbmn"))  # 개인 순매수금액
        }

        print(f"✅ {symbol} 투자자 동향: 외국인={result['foreign_net_buy']:+,}주, 기관={result['institution_net_buy']:+,}주")
        return result
