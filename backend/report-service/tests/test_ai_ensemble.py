"""
ai_ensemble.py 단위 테스트

총 8개 테스트:
1. get_openai_client() - 클라이언트 생성
2. get_anthropic_client() - 클라이언트 생성
3. analyze_news_trend() - 뉴스 트렌드 분석
4. analyze_news_trend() - 뉴스 없음
5. ensemble_vote() - GPT4 + Claude 결과 통합
6. ensemble_vote() - 단일 모델 결과
7. analyze_with_ensemble() - Mock 테스트 (GPT4만)
8. analyze_with_ensemble() - Mock 테스트 (Claude 폴백)
"""
import pytest
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
from ai_ensemble import (
    get_openai_client,
    get_anthropic_client,
    analyze_news_trend,
    ensemble_vote,
    analyze_with_ensemble
)


@pytest.mark.unit
class TestAIClients:
    """AI 클라이언트 생성 테스트"""

    @patch('ai_ensemble.os.getenv')
    def test_get_openai_client(self, mock_getenv):
        """1. get_openai_client() - 클라이언트 생성"""
        mock_getenv.return_value = "test_openai_key"

        client = get_openai_client()

        # 클라이언트 객체 반환 확인
        assert client is not None
        mock_getenv.assert_called_with("OPENAI_API_KEY")

    @patch('ai_ensemble.os.getenv')
    def test_get_anthropic_client(self, mock_getenv):
        """2. get_anthropic_client() - 클라이언트 생성"""
        mock_getenv.return_value = "test_claude_key"

        client = get_anthropic_client()

        # 클라이언트 객체 반환 확인
        assert client is not None
        mock_getenv.assert_called_with("CLAUDE_API_KEY")


@pytest.mark.unit
class TestNewsTrendAnalysis:
    """뉴스 트렌드 분석 테스트"""

    def test_analyze_news_trend_with_news(self):
        """3. analyze_news_trend() - 뉴스 트렌드 분석"""
        news_data = [
            {
                "title": "긍정적인 뉴스 1",
                "sentiment_score": 0.8,
                "impact_score": 0.7
            },
            {
                "title": "긍정적인 뉴스 2",
                "sentiment_score": 0.6,
                "impact_score": 0.5
            },
            {
                "title": "부정적인 뉴스",
                "sentiment_score": -0.5,
                "impact_score": 0.8
            }
        ]

        result = analyze_news_trend(news_data)

        # 뉴스 트렌드 분석 결과 검증
        assert "positive_count" in result
        assert "negative_count" in result
        assert "neutral_count" in result
        assert "avg_sentiment" in result
        assert "avg_impact" in result
        assert "trend" in result

        # 긍정 뉴스 2개, 부정 뉴스 1개
        assert result["positive_count"] >= 1
        assert result["negative_count"] >= 1

    def test_analyze_news_trend_no_news(self):
        """4. analyze_news_trend() - 뉴스 없음"""
        news_data = []

        result = analyze_news_trend(news_data)

        # 뉴스 없을 때 기본값
        assert result["positive_count"] == 0
        assert result["negative_count"] == 0
        assert result["neutral_count"] == 0
        assert result["trend"] == "neutral"


@pytest.mark.unit
class TestEnsembleVote:
    """앙상블 투표 테스트"""

    def test_ensemble_vote_multiple_models(self):
        """5. ensemble_vote() - GPT4 + Claude 결과 통합"""
        results = [
            {
                "model": "gpt-4",
                "summary": "GPT4 요약",
                "risk_level": "낮음",
                "recommendation": "매수",
                "evaluation_score": 80
            },
            {
                "model": "claude",
                "summary": "Claude 요약",
                "risk_level": "보통",
                "recommendation": "매수",
                "evaluation_score": 75
            }
        ]

        result = ensemble_vote(results)

        # 앙상블 결과 검증
        assert "summary" in result
        assert "risk_level" in result
        assert "recommendation" in result
        assert "evaluation_score" in result
        assert "model_agreement" in result
        assert "confidence_score" in result

        # 두 모델 모두 매수 → 매수 권고
        assert result["recommendation"] == "매수"

        # 평가 점수는 평균
        assert result["evaluation_score"] == pytest.approx(77.5, rel=0.1)

    def test_ensemble_vote_single_model(self):
        """6. ensemble_vote() - 단일 모델 결과"""
        results = [
            {
                "model": "gpt-4",
                "summary": "GPT4 요약",
                "risk_level": "낮음",
                "recommendation": "매수",
                "evaluation_score": 80
            }
        ]

        result = ensemble_vote(results)

        # 단일 모델 결과 그대로 반환
        assert result["summary"] == "GPT4 요약"
        assert result["recommendation"] == "매수"
        assert result["evaluation_score"] == 80


@pytest.mark.asyncio
@pytest.mark.unit
class TestAnalyzeWithEnsemble:
    """앙상블 분석 통합 테스트 (Mock)"""

    @patch('ai_ensemble.analyze_with_gpt4')
    async def test_analyze_with_ensemble_gpt4_only(
        self,
        mock_gpt4,
        sample_indicators,
        sample_financial_data,
        sample_market_context
    ):
        """7. analyze_with_ensemble() - Mock 테스트 (GPT4만)"""
        # GPT4 응답 Mock
        mock_gpt4.return_value = {
            "model": "gpt-4",
            "summary": "테스트 요약",
            "risk_level": "낮음",
            "recommendation": "매수",
            "evaluation_score": 85,
            "investment_strategy": "단기 매수 전략",
            "risk_factors": "낮은 위험",
            "catalysts": "긍정적 요인",
            "target_price_range": "15000~20000",
            "time_horizon": "short_term"
        }

        # analyze_with_ensemble 호출
        result = await analyze_with_ensemble(
            symbol="005930",
            symbol_name="삼성전자",
            indicators=sample_indicators,
            news_data=[],
            financial_data=sample_financial_data,
            market_context=sample_market_context
        )

        # 결과 검증
        assert result is not None
        assert "summary" in result
        assert "risk_level" in result
        assert "recommendation" in result
        assert result["recommendation"] in ["매수", "매도", "관망", "보유"]

        # GPT4 호출 확인
        mock_gpt4.assert_called_once()

    @patch('ai_ensemble.analyze_with_claude')
    @patch('ai_ensemble.analyze_with_gpt4')
    async def test_analyze_with_ensemble_claude_fallback(
        self,
        mock_gpt4,
        mock_claude,
        sample_indicators,
        sample_financial_data,
        sample_market_context
    ):
        """8. analyze_with_ensemble() - Mock 테스트 (Claude 폴백)"""
        # GPT4 실패 시뮬레이션
        mock_gpt4.side_effect = Exception("GPT4 API 실패")

        # Claude 응답 Mock
        mock_claude.return_value = {
            "model": "claude",
            "summary": "Claude 요약",
            "risk_level": "보통",
            "recommendation": "보유",
            "evaluation_score": 70,
            "investment_strategy": "중기 보유 전략",
            "risk_factors": "중간 위험",
            "catalysts": "중립적 요인",
            "target_price_range": "14000~18000",
            "time_horizon": "medium_term"
        }

        # analyze_with_ensemble 호출
        result = await analyze_with_ensemble(
            symbol="005930",
            symbol_name="삼성전자",
            indicators=sample_indicators,
            news_data=[],
            financial_data=sample_financial_data,
            market_context=sample_market_context
        )

        # 결과 검증
        assert result is not None
        assert "summary" in result
        assert result["recommendation"] in ["매수", "매도", "관망", "보유"]

        # GPT4 실패 후 Claude 호출 확인
        mock_gpt4.assert_called_once()
        mock_claude.assert_called_once()
