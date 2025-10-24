"""
Pytest 공통 설정 및 픽스처
"""
import pytest
from typing import Dict, List, Any
from datetime import datetime, timedelta


# ========== 테스트 데이터 픽스처 ==========

@pytest.fixture
def sample_ohlcv_data() -> List[Dict[str, Any]]:
    """
    테스트용 OHLCV 데이터 (60일치)
    """
    data = []
    base_price = 10000
    base_date = datetime.now() - timedelta(days=60)

    for i in range(60):
        date_str = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        price = base_price + (i * 100) + ((i % 10) * 50)

        data.append({
            "date": date_str,
            "open": price - 50,
            "high": price + 100,
            "low": price - 100,
            "close": price,
            "volume": 1000000 + (i * 10000)
        })

    return data


@pytest.fixture
def sample_indicators() -> Dict[str, Any]:
    """
    테스트용 기술적 지표 데이터
    """
    return {
        "current_price": 15000,
        "change_rate": 2.5,
        "high": 15500,
        "low": 14800,
        "avg": 15150,
        "volume": 1500000,

        # 기본 지표
        "ma5": 14900,
        "ma20": 14500,
        "ma60": 14000,
        "volume_ratio": 1.2,
        "volatility": 2.3,
        "bollinger_upper": 15800,
        "bollinger_lower": 14200,

        # 고급 지표
        "rsi": 65.0,
        "macd": 120.5,
        "macd_signal": 100.3,
        "macd_histogram": 20.2,
        "stochastic_k": 75.0,
        "stochastic_d": 70.0,
        "williams_r": -30.0,
        "cci": 110.0,
        "adx": 25.0,
        "obv": 50000000,
        "mfi": 60.0,
        "vwap": 15100,
        "atr": 300.0,
        "keltner_upper": 15700,
        "keltner_middle": 15000,
        "keltner_lower": 14300
    }


@pytest.fixture
def sample_financial_data() -> Dict[str, Any]:
    """
    테스트용 재무 데이터
    """
    return {
        "per": 12.5,
        "pbr": 1.8,
        "roe": 15.3,
        "dividend_yield": 2.5,
        "eps": 1200,
        "bps": 8333,
        "operating_margin": 12.0,
        "net_margin": 8.5,
        "debt_ratio": 45.0
    }


@pytest.fixture
def sample_analyst_opinion() -> Dict[str, Any]:
    """
    테스트용 애널리스트 의견
    """
    return {
        "buy_count": 8,
        "hold_count": 3,
        "sell_count": 1,
        "avg_target_price": 18000,
        "total_count": 12
    }


@pytest.fixture
def sample_sector_relative() -> Dict[str, Any]:
    """
    테스트용 업종 상대 평가
    """
    return {
        "sector_avg_change_rate": 1.5,
        "relative_strength": 1.67,
        "sector_rank_pct": 75,
        "outperformance": 1.0,
        "sample_size": 50,
        "sector_avg_volume_ratio": 1.0,
        "sector_avg_per": 15.0,
        "sector_avg_pbr": 2.0
    }


@pytest.fixture
def sample_market_context() -> Dict[str, Any]:
    """
    테스트용 시장 맥락
    """
    return {
        "market_trend": "bullish",
        "market_strength": 75,
        "market_sentiment": "긍정적",
        "kospi": {
            "value": 2650,
            "change_rate": 0.8,
            "momentum": "상승"
        },
        "kosdaq": {
            "value": 850,
            "change_rate": 1.2,
            "momentum": "상승"
        },
        "volatility_level": "medium",
        "volatility_value": 15.5,
        "market_breadth": "positive",
        "market_breadth_pct": 65
    }


@pytest.fixture
def sample_target_prices() -> Dict[str, Any]:
    """
    테스트용 목표가
    """
    return {
        "conservative": 16000,
        "neutral": 18000,
        "aggressive": 20000,
        "current_price": 15000,
        "upside_potential": {
            "conservative": 6.67,
            "neutral": 20.0,
            "aggressive": 33.33
        },
        "methods": {
            "per_based": 17500,
            "pbr_based": 18000,
            "analyst_avg": 18000,
            "technical_resistance": 16500
        },
        "market_adjustment_factor": 1.0
    }


@pytest.fixture
def sample_risk_scores() -> Dict[str, Any]:
    """
    테스트용 위험도 점수
    """
    return {
        "short_term": {"score": 35},
        "mid_term": {"score": 40},
        "long_term": {"score": 45}
    }


# ========== Mock 픽스처 ==========

@pytest.fixture
def mock_supabase(mocker):
    """
    Supabase 클라이언트 Mock
    """
    mock_client = mocker.MagicMock()
    return mock_client


@pytest.fixture
def mock_redis(mocker):
    """
    Redis 클라이언트 Mock
    """
    mock_client = mocker.MagicMock()
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    return mock_client


@pytest.fixture
def mock_openai_client(mocker):
    """
    OpenAI 클라이언트 Mock
    """
    mock_client = mocker.MagicMock()
    return mock_client


@pytest.fixture
def mock_claude_client(mocker):
    """
    Claude 클라이언트 Mock
    """
    mock_client = mocker.MagicMock()
    return mock_client
