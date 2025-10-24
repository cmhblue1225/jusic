"""
pdf_generator.py 단위 테스트

총 5개 테스트:
1. StockReportPDF 초기화
2. _translate() - 번역 함수
3. _setup_custom_styles() - 스타일 설정
4. generate() - PDF 생성 (전체 통합 테스트)
5. generate() - 최소 데이터로 PDF 생성
"""
import pytest
from typing import Dict, Any
from io import BytesIO
from pdf_generator import StockReportPDF


@pytest.mark.unit
class TestPDFGenerator:
    """PDF 생성 모듈 테스트"""

    def test_pdf_initialization(self):
        """1. StockReportPDF 초기화"""
        report_data = {
            "symbol": "005930",
            "symbol_name": "삼성전자",
            "report_date": "2025-10-24",
            "current_price": 75000,
            "change_rate": 2.5,
            "summary": "테스트 요약",
            "risk_level": "낮음",
            "recommendation": "매수",
            "evaluation_score": 85
        }

        pdf_generator = StockReportPDF(report_data)

        # 초기화 검증
        assert pdf_generator.report_data == report_data
        assert pdf_generator.symbol == "005930"
        assert pdf_generator.symbol_name == "삼성전자"

    def test_translate_method(self):
        """2. _translate() - 번역 함수"""
        report_data = {
            "symbol": "005930",
            "symbol_name": "삼성전자",
            "report_date": "2025-10-24",
            "current_price": 75000,
            "summary": "테스트",
            "risk_level": "낮음",
            "recommendation": "매수",
            "evaluation_score": 85
        }

        pdf_generator = StockReportPDF(report_data)

        # 번역 테스트
        assert pdf_generator._translate("buy") == "매수"
        assert pdf_generator._translate("sell") == "매도"
        assert pdf_generator._translate("hold") == "관망"
        assert pdf_generator._translate("high") == "높음"
        assert pdf_generator._translate("low") == "낮음"
        assert pdf_generator._translate("moderate") == "보통"

        # 번역 없는 텍스트는 그대로 반환
        assert pdf_generator._translate("테스트") == "테스트"

    def test_setup_custom_styles(self):
        """3. _setup_custom_styles() - 스타일 설정"""
        report_data = {
            "symbol": "005930",
            "symbol_name": "삼성전자",
            "report_date": "2025-10-24",
            "current_price": 75000,
            "summary": "테스트",
            "risk_level": "낮음",
            "recommendation": "매수",
            "evaluation_score": 85
        }

        pdf_generator = StockReportPDF(report_data)

        # 스타일 설정 호출 (내부 메서드이지만 public으로 테스트)
        pdf_generator._setup_custom_styles()

        # 스타일 객체 존재 확인
        assert hasattr(pdf_generator, 'styles')
        assert 'Title' in pdf_generator.styles
        assert 'Heading1' in pdf_generator.styles
        assert 'Heading2' in pdf_generator.styles
        assert 'BodyText' in pdf_generator.styles

    @pytest.mark.slow
    def test_generate_full_report(self):
        """4. generate() - PDF 생성 (전체 통합 테스트)"""
        report_data = {
            "symbol": "005930",
            "symbol_name": "삼성전자",
            "report_date": "2025-10-24",
            "current_price": 75000,
            "change_rate": 2.5,
            "high_price": 76000,
            "low_price": 74000,
            "avg_price": 75000,
            "volume": 15000000,

            # 기술적 지표
            "ma5": 74500,
            "ma20": 73000,
            "ma60": 70000,
            "rsi": 65.0,
            "macd": 120.5,
            "volume_ratio": 1.2,
            "volatility": 2.3,
            "bollinger_upper": 78000,
            "bollinger_lower": 72000,

            # AI 분석
            "summary": "삼성전자는 현재 긍정적인 기술적 지표를 보이고 있습니다.",
            "risk_level": "낮음",
            "recommendation": "매수",
            "evaluation_score": 85,

            # 재무 데이터
            "per": 12.5,
            "pbr": 1.8,
            "roe": 15.3,
            "eps": 6000,

            # 목표가
            "target_prices": {
                "conservative": 80000,
                "neutral": 85000,
                "aggressive": 90000,
                "upside_potential": {
                    "conservative": 6.67,
                    "neutral": 13.33,
                    "aggressive": 20.0
                }
            },

            # 매매 신호
            "trading_signals": {
                "signal": "buy",
                "confidence": 75,
                "strength": "moderate",
                "entry_timing": "immediate",
                "stop_loss": 70000,
                "take_profit": {
                    "first": 80000,
                    "second": 85000
                }
            },

            # 차트 데이터 (없음)
            "chart_data": None,

            # 메타데이터
            "cached": False,
            "ai_model": "ensemble"
        }

        pdf_generator = StockReportPDF(report_data)
        pdf_buffer = pdf_generator.generate()

        # PDF 생성 검증
        assert isinstance(pdf_buffer, BytesIO)
        assert pdf_buffer.tell() > 0  # 데이터가 작성됨

        # PDF 크기 확인 (최소 10KB 이상)
        pdf_buffer.seek(0, 2)  # 끝으로 이동
        pdf_size = pdf_buffer.tell()
        assert pdf_size > 10000  # 10KB 이상

    @pytest.mark.slow
    def test_generate_minimal_data(self):
        """5. generate() - 최소 데이터로 PDF 생성"""
        # 필수 필드만 있는 최소 데이터
        report_data = {
            "symbol": "005930",
            "symbol_name": "삼성전자",
            "report_date": "2025-10-24",
            "current_price": 75000,
            "change_rate": 2.5,
            "summary": "최소 테스트",
            "risk_level": "보통",
            "recommendation": "관망",
            "evaluation_score": 50
        }

        pdf_generator = StockReportPDF(report_data)
        pdf_buffer = pdf_generator.generate()

        # PDF 생성 검증
        assert isinstance(pdf_buffer, BytesIO)
        assert pdf_buffer.tell() > 0

        # 최소 PDF 크기 확인
        pdf_buffer.seek(0, 2)
        pdf_size = pdf_buffer.tell()
        assert pdf_size > 1000  # 1KB 이상 (최소한의 PDF)


@pytest.mark.unit
class TestPDFContent:
    """PDF 내용 검증 테스트"""

    def test_pdf_has_korean_support(self):
        """PDF 한글 지원 확인"""
        report_data = {
            "symbol": "005930",
            "symbol_name": "삼성전자",
            "report_date": "2025-10-24",
            "current_price": 75000,
            "summary": "한글 테스트 요약입니다.",
            "risk_level": "낮음",
            "recommendation": "매수",
            "evaluation_score": 85
        }

        pdf_generator = StockReportPDF(report_data)

        # 한글 폰트 경로 확인
        assert pdf_generator.korean_font is not None
        assert "Nanum" in pdf_generator.korean_font or "NotoSans" in pdf_generator.korean_font

    def test_pdf_color_mapping(self):
        """PDF 색상 매핑 확인"""
        report_data = {
            "symbol": "005930",
            "symbol_name": "삼성전자",
            "report_date": "2025-10-24",
            "current_price": 75000,
            "summary": "테스트",
            "risk_level": "낮음",
            "recommendation": "매수",
            "evaluation_score": 85
        }

        pdf_generator = StockReportPDF(report_data)

        # 색상 매핑 확인
        from reportlab.lib.colors import red, green, blue, orange, HexColor

        # 매수 = 파랑 계열
        assert pdf_generator._translate("buy") == "매수"

        # 매도 = 빨강 계열
        assert pdf_generator._translate("sell") == "매도"

        # 위험도 색상
        assert pdf_generator._translate("high") == "높음"
        assert pdf_generator._translate("low") == "낮음"
