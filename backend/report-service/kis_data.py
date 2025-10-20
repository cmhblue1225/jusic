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


# =============================================================================
# 🔥 Phase 1.2: 추가 KIS API 엔드포인트 (7개)
# =============================================================================

async def get_analyst_opinion(symbol: str) -> Dict[str, Any]:
    """
    증권사 투자의견 조회 (TR_ID: FHKST663300C0)

    Args:
        symbol: 종목 코드 (6자리)

    Returns:
        Dict: 투자의견 정보
            - buy_count: 매수 의견 개수
            - hold_count: 중립 의견 개수
            - sell_count: 매도 의견 개수
            - avg_target_price: 평균 목표가
            - total_count: 총 의견 개수
    """
    token = await get_access_token()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/invest-opinion",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "authorization": f"Bearer {token}",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET,
                "tr_id": "FHKST663300C0"
            },
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": symbol
            }
        )

        if response.status_code != 200:
            print(f"⚠️ 투자의견 조회 실패: {response.status_code}")
            return {"buy_count": 0, "hold_count": 0, "sell_count": 0, "avg_target_price": None, "total_count": 0}

        data = response.json()

        if data.get("rt_cd") != "0":
            print(f"⚠️ KIS API 오류: {data.get('msg1', '알 수 없는 오류')}")
            return {"buy_count": 0, "hold_count": 0, "sell_count": 0, "avg_target_price": None, "total_count": 0}

        output = data.get("output", [])

        if not output:
            return {"buy_count": 0, "hold_count": 0, "sell_count": 0, "avg_target_price": None, "total_count": 0}

        buy_count = 0
        hold_count = 0
        sell_count = 0
        target_prices = []

        for item in output:
            opinion = item.get("stck_invt_opnn", "").strip()
            target_price = item.get("stck_stdt_prpr", "")

            if "매수" in opinion or "BUY" in opinion.upper():
                buy_count += 1
            elif "중립" in opinion or "HOLD" in opinion.upper():
                hold_count += 1
            elif "매도" in opinion or "SELL" in opinion.upper():
                sell_count += 1

            if target_price and target_price.strip():
                try:
                    target_prices.append(float(target_price.replace(",", "")))
                except:
                    pass

        avg_target = sum(target_prices) / len(target_prices) if target_prices else None
        total = buy_count + hold_count + sell_count

        result = {
            "buy_count": buy_count,
            "hold_count": hold_count,
            "sell_count": sell_count,
            "avg_target_price": int(avg_target) if avg_target else None,
            "total_count": total
        }

        print(f"✅ {symbol} 투자의견: 매수={buy_count}, 중립={hold_count}, 매도={sell_count}, 평균목표가={result['avg_target_price']:,}원" if avg_target else f"✅ {symbol} 투자의견: 매수={buy_count}, 중립={hold_count}, 매도={sell_count}")
        return result


async def get_sector_info(symbol: str) -> Dict[str, Any]:
    """
    업종 정보 조회 (종목 기본 조회 API 활용)
    
    Args:
        symbol: 종목 코드 (6자리)
    
    Returns:
        Dict: 업종 정보
            - sector_name: 업종명
            - sector_code: 업종 코드
    """
    token = await get_access_token()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/search-stock-info",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "authorization": f"Bearer {token}",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET,
                "tr_id": "CTPF1002R"
            },
            params={
                "PDNO": symbol,
                "PRDT_TYPE_CD": "300"
            }
        )
        
        if response.status_code != 200:
            print(f"⚠️ 종목 정보 조회 실패: {response.status_code}")
            return {"sector_name": None, "sector_code": None}
        
        data = response.json()
        
        if data.get("rt_cd") != "0":
            return {"sector_name": None, "sector_code": None}
        
        output = data.get("output", {})
        
        result = {
            "sector_name": output.get("std_idst_clsf_cd_name", "미분류"),
            "sector_code": output.get("std_idst_clsf_cd", "")
        }
        
        print(f"✅ {symbol} 업종: {result['sector_name']}")
        return result


async def get_credit_balance_trend(symbol: str, days: int = 5) -> List[Dict]:
    """
    신용잔고 일별 추이 (TR_ID: FHPST04760000)
    
    Args:
        symbol: 종목 코드
        days: 조회 일수 (기본 5일)
    
    Returns:
        List[Dict]: 일별 신용잔고 데이터
    """
    token = await get_access_token()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/daily-credit-balance",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "authorization": f"Bearer {token}",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET,
                "tr_id": "FHPST04760000"
            },
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": symbol,
                "fid_input_date_1": (datetime.now() - timedelta(days=days+5)).strftime("%Y%m%d"),
                "fid_input_date_2": datetime.now().strftime("%Y%m%d")
            }
        )
        
        if response.status_code != 200:
            print(f"⚠️ 신용잔고 조회 실패: {response.status_code}")
            return []
        
        data = response.json()
        
        if data.get("rt_cd") != "0":
            return []
        
        output = data.get("output", [])
        
        result = []
        for item in output[:days]:
            result.append({
                "date": item.get("stck_bsop_date"),
                "credit_balance": int(item.get("crdt_ord_blce", "0").replace(",", "")) if item.get("crdt_ord_blce") else 0
            })
        
        print(f"✅ {symbol} 신용잔고 추이: {len(result)}일")
        return result


async def get_short_selling_trend(symbol: str, days: int = 5) -> List[Dict]:
    """
    공매도 일별 추이 (TR_ID: FHPST04830000)
    
    Args:
        symbol: 종목 코드
        days: 조회 일수
    
    Returns:
        List[Dict]: 일별 공매도 데이터
    """
    token = await get_access_token()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/daily-short-sale",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "authorization": f"Bearer {token}",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET,
                "tr_id": "FHPST04830000"
            },
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": symbol,
                "fid_input_date_1": (datetime.now() - timedelta(days=days+5)).strftime("%Y%m%d"),
                "fid_input_date_2": datetime.now().strftime("%Y%m%d")
            }
        )
        
        if response.status_code != 200:
            print(f"⚠️ 공매도 조회 실패: {response.status_code}")
            return []
        
        data = response.json()
        
        if data.get("rt_cd") != "0":
            return []
        
        output = data.get("output", [])
        
        result = []
        for item in output[:days]:
            result.append({
                "date": item.get("stck_bsop_date"),
                "short_balance": int(item.get("ssts_ord_blce", "0").replace(",", "")) if item.get("ssts_ord_blce") else 0
            })
        
        print(f"✅ {symbol} 공매도 추이: {len(result)}일")
        return result


async def get_program_trading_trend(symbol: str, days: int = 5) -> List[Dict]:
    """
    프로그램매매 추이 (TR_ID: FHPPG04650201)
    
    Args:
        symbol: 종목 코드
        days: 조회 일수
    
    Returns:
        List[Dict]: 일별 프로그램매매 데이터
    """
    token = await get_access_token()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/program-trade-by-stock-daily",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "authorization": f"Bearer {token}",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET,
                "tr_id": "FHPPG04650201"
            },
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": symbol,
                "fid_input_date_1": (datetime.now() - timedelta(days=days+5)).strftime("%Y%m%d"),
                "fid_input_date_2": datetime.now().strftime("%Y%m%d")
            }
        )
        
        if response.status_code != 200:
            print(f"⚠️ 프로그램매매 조회 실패: {response.status_code}")
            return []
        
        data = response.json()
        
        if data.get("rt_cd") != "0":
            return []
        
        output = data.get("output", [])
        
        result = []
        for item in output[:days]:
            result.append({
                "date": item.get("stck_bsop_date"),
                "program_net_buy": int(item.get("stck_prpr", "0").replace(",", "")) if item.get("stck_prpr") else 0
            })
        
        print(f"✅ {symbol} 프로그램매매 추이: {len(result)}일")
        return result


async def get_institutional_flow_estimate(symbol: str) -> Dict[str, Any]:
    """
    기관/외인 매매 가집계 (TR_ID: FHPTJ04400000)
    당일 누적 순매수 데이터
    
    Args:
        symbol: 종목 코드
    
    Returns:
        Dict: 당일 누적 매매 데이터
            - foreign_net_buy_amt: 외국인 순매수금액
            - institution_net_buy_amt: 기관 순매수금액
    """
    token = await get_access_token()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/foreign-institution-total",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "authorization": f"Bearer {token}",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET,
                "tr_id": "FHPTJ04400000"
            },
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": symbol,
                "fid_input_date_1": datetime.now().strftime("%Y%m%d")
            }
        )
        
        if response.status_code != 200:
            print(f"⚠️ 매매 가집계 조회 실패: {response.status_code}")
            return {"foreign_net_buy_amt": 0, "institution_net_buy_amt": 0}
        
        data = response.json()
        
        if data.get("rt_cd") != "0":
            return {"foreign_net_buy_amt": 0, "institution_net_buy_amt": 0}
        
        output = data.get("output", {})
        
        result = {
            "foreign_net_buy_amt": float(output.get("frgn_ntby_tr_pbmn", "0").replace(",", "")) if output.get("frgn_ntby_tr_pbmn") else 0,
            "institution_net_buy_amt": float(output.get("orgn_ntby_tr_pbmn", "0").replace(",", "")) if output.get("orgn_ntby_tr_pbmn") else 0
        }
        
        print(f"✅ {symbol} 당일 매매: 외국인={result['foreign_net_buy_amt']/1e8:.1f}억, 기관={result['institution_net_buy_amt']/1e8:.1f}억")
        return result


async def get_index_price(index_code: str) -> Dict[str, Any]:
    """
    업종 지수 조회 (TR_ID: FHPUP02100000)
    
    Args:
        index_code: 지수 코드 (예: 0001=코스피, 1001=코스닥)
    
    Returns:
        Dict: 지수 정보
            - index_value: 지수 값
            - change_rate: 등락률
    """
    token = await get_access_token()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-index-price",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "authorization": f"Bearer {token}",
                "appkey": KIS_APP_KEY,
                "appsecret": KIS_APP_SECRET,
                "tr_id": "FHPUP02100000"
            },
            params={
                "fid_cond_mrkt_div_code": "U",
                "fid_input_iscd": index_code
            }
        )
        
        if response.status_code != 200:
            print(f"⚠️ 지수 조회 실패: {response.status_code}")
            return {"index_value": 0, "change_rate": 0}
        
        data = response.json()
        
        if data.get("rt_cd") != "0":
            return {"index_value": 0, "change_rate": 0}
        
        output = data.get("output", {})
        
        result = {
            "index_value": float(output.get("bstp_nmix_prpr", "0").replace(",", "")) if output.get("bstp_nmix_prpr") else 0,
            "change_rate": float(output.get("bstp_nmix_prdy_ctrt", "0")) if output.get("bstp_nmix_prdy_ctrt") else 0
        }
        
        print(f"✅ 지수 {index_code}: {result['index_value']:.2f} ({result['change_rate']:+.2f}%)")
        return result


# 🔥 Phase 4.1: 업종 상대 평가
async def get_sector_relative_analysis(symbol: str, sector_code: str) -> Dict[str, Any]:
    """
    업종 상대 평가 - 동일 업종 내 다른 종목들과 비교

    Args:
        symbol: 기준 종목 코드
        sector_code: 업종 코드

    Returns:
        Dict: 업종 상대 평가 결과
            - sector_avg_change_rate: 업종 평균 등락률 (%)
            - relative_strength: 상대 강도 (기준 종목 등락률 / 업종 평균 등락률)
            - sector_rank_pct: 업종 내 등락률 순위 백분위 (0~100, 높을수록 상위)
            - sector_avg_volume_ratio: 업종 평균 거래량 비율
            - sector_avg_per: 업종 평균 PER
            - sector_avg_pbr: 업종 평균 PBR
            - outperformance: 업종 대비 초과 수익률 (%)
            - sample_size: 분석에 사용된 종목 수
    """
    from lib.supabase import supabase
    import asyncio

    try:
        # 1. Supabase에서 동일 업종 종목 조회 (최대 30개, 시가총액 상위 기준)
        # Note: stock_master 테이블에 sector 컬럼이 없다면, 이 로직은 작동하지 않음
        # 대신 sector_code를 활용한 매핑 테이블이 필요할 수 있음

        # 일단 sector_name을 기준으로 조회 (sector_code는 KIS API 고유 값이므로 stock_master에 없을 수 있음)
        sector_info = await get_sector_info(symbol)
        sector_name = sector_info.get("sector_name", "")

        if not sector_name or sector_name == "미분류":
            print(f"⚠️ {symbol} 업종 정보 없음, 상대 평가 불가")
            return {
                "sector_avg_change_rate": 0,
                "relative_strength": 1.0,
                "sector_rank_pct": 50,
                "sector_avg_volume_ratio": 1.0,
                "sector_avg_per": 0,
                "sector_avg_pbr": 0,
                "outperformance": 0,
                "sample_size": 0
            }

        # 2. 동일 업종 종목 리스트 조회 (Supabase에서 sector 컬럼이 있다고 가정)
        # 실제로는 stock_master 테이블 구조를 확인해야 함
        # 여기서는 간단히 sector_name이 일치하는 종목들을 조회한다고 가정

        # 임시: 업종명으로 검색 (실제로는 sector 컬럼 필요)
        # stock_master에 sector 컬럼이 없으므로, 별도 매핑 테이블 또는 KIS API 활용 필요
        # 현재는 간단한 구현을 위해 시가총액 상위 30개 종목만 샘플링

        # 실제 구현: KIS API에는 업종별 종목 리스트 API가 없으므로,
        # Supabase에 업종 매핑 테이블을 추가하거나, 전체 종목을 순회하며 sector_info를 조회해야 함
        # 성능을 위해 캐싱 필요

        # 🔥 간단한 구현: 기준 종목의 현재가 데이터만 조회하여 업종 평균 대비 성과 계산
        # (실제로는 업종 내 모든 종목 데이터가 필요하지만, 현재는 간소화)

        # 기준 종목 데이터 조회
        base_stock = await get_current_price(symbol)

        # 임시: 업종 평균을 코스피/코스닥 지수로 대체 (실제로는 업종 지수 필요)
        # KIS API에는 업종 지수 조회 API가 있을 수 있음 (확인 필요)

        # 간단한 구현: 코스피 지수를 업종 평균으로 가정
        market_index = await get_market_index()
        kospi_change = market_index.get("kospi_change_rate", 0)

        stock_change_rate = base_stock.get("change_rate", 0)

        # 상대 강도 계산
        relative_strength = stock_change_rate / kospi_change if kospi_change != 0 else 1.0

        # 초과 수익률
        outperformance = stock_change_rate - kospi_change

        result = {
            "sector_avg_change_rate": kospi_change,  # 실제로는 업종 평균 등락률
            "relative_strength": round(relative_strength, 2),
            "sector_rank_pct": 50,  # 실제로는 업종 내 순위 백분위 계산 필요
            "sector_avg_volume_ratio": 1.0,  # 실제로는 업종 평균 거래량 비율 계산 필요
            "sector_avg_per": 0,  # 실제로는 업종 평균 PER 계산 필요
            "sector_avg_pbr": 0,  # 실제로는 업종 평균 PBR 계산 필요
            "outperformance": round(outperformance, 2),
            "sample_size": 1,  # 현재는 기준 종목만 사용
            "note": "현재는 코스피 지수 대비 상대 성과 (실제 업종 평균은 추후 구현)"
        }

        print(f"✅ {symbol} 업종 상대 평가: 상대강도 {relative_strength:.2f}, 초과수익률 {outperformance:+.2f}%")
        return result

    except Exception as e:
        print(f"❌ 업종 상대 평가 오류 ({symbol}): {str(e)}")
        return {
            "sector_avg_change_rate": 0,
            "relative_strength": 1.0,
            "sector_rank_pct": 50,
            "sector_avg_volume_ratio": 1.0,
            "sector_avg_per": 0,
            "sector_avg_pbr": 0,
            "outperformance": 0,
            "sample_size": 0,
            "error": str(e)
        }


# 🔥 Phase 4.2: 시장 전체 맥락 분석
async def get_market_context() -> Dict[str, Any]:
    """
    시장 전체 맥락 분석 - 종합적인 시장 상황 파악

    Returns:
        Dict: 시장 맥락 분석 결과
            - market_trend: 시장 추세 ('bullish', 'bearish', 'neutral')
            - market_strength: 시장 강도 (0-100)
            - kospi_momentum: 코스피 모멘텀 지표
            - kosdaq_momentum: 코스닥 모멘텀 지표
            - volatility_level: 변동성 수준 ('low', 'medium', 'high')
            - foreign_flow: 외국인 순매수 추세
            - institutional_flow: 기관 순매수 추세
            - market_breadth: 시장 폭 (상승종목/전체종목 비율)
    """
    import asyncio

    try:
        # 1. 코스피, 코스닥 지수 조회 (병렬)
        kospi_task = get_index_price("0001")  # 코스피
        kosdaq_task = get_index_price("1001")  # 코스닥

        kospi_data, kosdaq_data = await asyncio.gather(kospi_task, kosdaq_task)

        kospi_change = kospi_data.get("change_rate", 0)
        kosdaq_change = kosdaq_data.get("change_rate", 0)

        # 2. 시장 추세 판단 (코스피 + 코스닥 평균)
        avg_market_change = (kospi_change + kosdaq_change) / 2

        if avg_market_change > 0.5:
            market_trend = "bullish"  # 강세장
        elif avg_market_change < -0.5:
            market_trend = "bearish"  # 약세장
        else:
            market_trend = "neutral"  # 중립

        # 3. 시장 강도 계산 (0-100)
        # 등락률 절대값 기준 (0% = 50점, ±2% = 100 or 0점)
        market_strength = 50 + (avg_market_change / 2.0 * 50)
        market_strength = max(0, min(100, market_strength))  # 0-100 범위로 제한

        # 4. 모멘텀 지표 (간단한 구현: 등락률 기준)
        kospi_momentum = "상승" if kospi_change > 0 else "하락" if kospi_change < 0 else "보합"
        kosdaq_momentum = "상승" if kosdaq_change > 0 else "하락" if kosdaq_change < 0 else "보합"

        # 5. 변동성 수준 (등락률 절대값 기준)
        volatility = abs(avg_market_change)
        if volatility < 0.5:
            volatility_level = "low"
        elif volatility < 1.5:
            volatility_level = "medium"
        else:
            volatility_level = "high"

        # 6. 시장 폭 (market breadth) - 간단한 추정
        # 코스피와 코스닥이 모두 상승하면 넓은 시장, 한쪽만 상승하면 좁은 시장
        if kospi_change > 0 and kosdaq_change > 0:
            market_breadth = "broad"  # 광범위한 상승
            breadth_pct = 70  # 약 70% 종목 상승 추정
        elif kospi_change < 0 and kosdaq_change < 0:
            market_breadth = "broad_decline"  # 광범위한 하락
            breadth_pct = 30  # 약 30% 종목 상승 추정
        else:
            market_breadth = "narrow"  # 제한적 (일부만 상승/하락)
            breadth_pct = 50  # 약 50% 종목 상승 추정

        # 7. 시장 심리 (sentiment) 종합
        if market_trend == "bullish" and volatility_level == "low":
            market_sentiment = "안정적 상승세"
        elif market_trend == "bullish" and volatility_level == "high":
            market_sentiment = "과열 우려"
        elif market_trend == "bearish" and volatility_level == "low":
            market_sentiment = "완만한 조정"
        elif market_trend == "bearish" and volatility_level == "high":
            market_sentiment = "급락 국면"
        else:
            market_sentiment = "관망세"

        result = {
            "market_trend": market_trend,
            "market_strength": round(market_strength, 2),
            "market_sentiment": market_sentiment,
            "kospi": {
                "value": kospi_data.get("index_value", 0),
                "change_rate": kospi_change,
                "momentum": kospi_momentum
            },
            "kosdaq": {
                "value": kosdaq_data.get("index_value", 0),
                "change_rate": kosdaq_change,
                "momentum": kosdaq_momentum
            },
            "volatility_level": volatility_level,
            "volatility_value": round(volatility, 2),
            "market_breadth": market_breadth,
            "market_breadth_pct": breadth_pct,
            # 외국인/기관 순매수는 개별 종목 데이터에서 가져오므로 여기서는 생략
            "foreign_flow": "N/A",  # 추후 구현
            "institutional_flow": "N/A"  # 추후 구현
        }

        print(f"✅ 시장 맥락: {market_trend.upper()} (강도: {market_strength:.1f}, 심리: {market_sentiment})")
        return result

    except Exception as e:
        print(f"❌ 시장 맥락 분석 오류: {str(e)}")
        return {
            "market_trend": "neutral",
            "market_strength": 50,
            "market_sentiment": "데이터 부족",
            "kospi": {"value": 0, "change_rate": 0, "momentum": "N/A"},
            "kosdaq": {"value": 0, "change_rate": 0, "momentum": "N/A"},
            "volatility_level": "medium",
            "volatility_value": 0,
            "market_breadth": "neutral",
            "market_breadth_pct": 50,
            "foreign_flow": "N/A",
            "institutional_flow": "N/A",
            "error": str(e)
        }
