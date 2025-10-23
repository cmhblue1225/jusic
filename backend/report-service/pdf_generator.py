"""
PDF Report Generator
전문적인 투자 리포트 PDF 생성 모듈
"""
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, List, Optional
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import matplotlib
matplotlib.use('Agg')  # 백엔드에서 GUI 없이 사용
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np

# 한글 폰트 등록
FONTS_DIR = os.path.join(os.path.dirname(__file__), 'fonts')
try:
    pdfmetrics.registerFont(TTFont('NotoSansKR', os.path.join(FONTS_DIR, 'NotoSansKR-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('NotoSansKR-Bold', os.path.join(FONTS_DIR, 'NotoSansKR-Bold.ttf')))
    print("✅ 한글 폰트 등록 완료 (NotoSansKR)")
except Exception as e:
    print(f"⚠️ 한글 폰트 등록 실패: {e}")
    print("   → Helvetica 폰트로 대체됩니다 (한글이 깨질 수 있음)")

# matplotlib 한글 폰트 설정
try:
    import matplotlib.font_manager as fm
    font_path = os.path.join(FONTS_DIR, 'NotoSansKR-Regular.ttf')
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()
    plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지
    print(f"✅ matplotlib 한글 폰트 설정 완료: {font_prop.get_name()}")
except Exception as e:
    print(f"⚠️ matplotlib 한글 폰트 설정 실패: {e}")
    print("   → 차트 한글이 깨질 수 있음")


class StockReportPDF:
    """종목 레포트 PDF 생성 클래스"""

    def __init__(self, report_data: Dict[str, Any]):
        """
        Args:
            report_data: API에서 반환된 레포트 데이터 (dict)
        """
        self.data = report_data
        self.buffer = BytesIO()
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # 스타일 정의
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

        # PDF 요소 리스트
        self.story = []

    def _setup_custom_styles(self):
        """커스텀 스타일 설정"""
        # 제목 스타일
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2563EB'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='NotoSansKR-Bold'
        ))

        # 소제목 스타일
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1F2937'),
            spaceAfter=12,
            fontName='NotoSansKR-Bold'
        ))

        # 본문 스타일
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=16,
            textColor=colors.HexColor('#374151'),
            alignment=TA_JUSTIFY,
            fontName='NotoSansKR'
        ))

        # 강조 텍스트
        self.styles.add(ParagraphStyle(
            name='Highlight',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#2563EB'),
            fontName='Helvetica-Bold'
        ))

    def _create_cover_page(self):
        """커버 페이지 생성"""
        # 로고/제목
        title = Paragraph(
            "📈 트레이딩 인텔리전스 플랫폼",
            self.styles['CustomTitle']
        )
        self.story.append(title)
        self.story.append(Spacer(1, 1*cm))

        # 종목명
        stock_name = Paragraph(
            f"<b>{self.data.get('symbol_name', '')} ({self.data.get('symbol', '')})</b>",
            ParagraphStyle(
                name='StockName',
                fontSize=28,
                textColor=colors.HexColor('#1F2937'),
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
        )
        self.story.append(stock_name)
        self.story.append(Spacer(1, 0.5*cm))

        # 현재가 및 등락률
        current_price = self.data.get('current_price', 0)
        change_rate = self.data.get('change_rate', 0)
        price_color = '#DC2626' if change_rate < 0 else '#16A34A'

        price_text = f"""
        <para align=center>
            <font size=20><b>{current_price:,.0f}원</b></font><br/>
            <font size=16 color="{price_color}"><b>{change_rate:+.2f}%</b></font>
        </para>
        """
        self.story.append(Paragraph(price_text, self.styles['CustomBody']))
        self.story.append(Spacer(1, 2*cm))

        # AI 분석 요약 박스
        summary_data = [
            ['AI 분석 요약', self.data.get('summary', 'N/A')],
            ['투자 권고', self.data.get('recommendation', 'N/A')],
            ['위험도', self.data.get('risk_level', 'N/A')],
            ['평가 점수', f"{self.data.get('evaluation_score', 0)}점"]
        ]

        summary_table = Table(summary_data, colWidths=[4*cm, 10*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#EFF6FF')),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1F2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DBEAFE')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        self.story.append(summary_table)
        self.story.append(Spacer(1, 1*cm))

        # 생성 날짜
        report_date = self.data.get('report_date', datetime.now().strftime('%Y-%m-%d'))
        date_text = Paragraph(
            f"<para align=center><i>레포트 생성일: {report_date}</i></para>",
            self.styles['CustomBody']
        )
        self.story.append(date_text)

        self.story.append(PageBreak())

    def _create_price_chart(self) -> Optional[str]:
        """캔들스틱 차트 생성 (matplotlib → PNG)"""
        chart_data = self.data.get('chart_data', {})
        if not chart_data or not chart_data.get('data'):
            return None

        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])

            # 캔들스틱 데이터
            candles = chart_data['data']
            dates = [item['date'] for item in candles]
            opens = [item['open'] for item in candles]
            highs = [item['high'] for item in candles]
            lows = [item['low'] for item in candles]
            closes = [item['close'] for item in candles]

            # 캔들스틱 차트
            for i in range(len(dates)):
                color = 'red' if closes[i] >= opens[i] else 'blue'
                ax1.plot([i, i], [lows[i], highs[i]], color=color, linewidth=0.5)
                ax1.add_patch(Rectangle(
                    (i - 0.3, min(opens[i], closes[i])),
                    0.6,
                    abs(closes[i] - opens[i]),
                    facecolor=color,
                    edgecolor=color,
                    alpha=0.8
                ))

            # 이동평균선
            ma5_data = chart_data.get('indicators', {}).get('ma5', {}).get('data', [])
            ma20_data = chart_data.get('indicators', {}).get('ma20', {}).get('data', [])

            if ma5_data:
                ma5_values = [item['value'] for item in ma5_data]
                ma5_indices = list(range(len(dates) - len(ma5_values), len(dates)))
                ax1.plot(ma5_indices, ma5_values, label='MA5', color='#FF6B6B', linewidth=1.5)

            if ma20_data:
                ma20_values = [item['value'] for item in ma20_data]
                ma20_indices = list(range(len(dates) - len(ma20_values), len(dates)))
                ax1.plot(ma20_indices, ma20_values, label='MA20', color='#4ECDC4', linewidth=1.5)

            ax1.set_title(f'{self.data.get("symbol_name")} 주가 차트 (60일)', fontsize=14, fontweight='bold')
            ax1.set_ylabel('가격 (원)', fontsize=10)
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)

            # 거래량 차트
            volume_data = chart_data.get('volume_data', [])
            if volume_data:
                volumes = [item['volume'] for item in volume_data]
                colors_vol = ['red' if closes[i] >= opens[i] else 'blue' for i in range(len(volumes))]
                ax2.bar(range(len(volumes)), volumes, color=colors_vol, alpha=0.6)
                ax2.set_ylabel('거래량', fontsize=10)
                ax2.set_xlabel('기간', fontsize=10)
                ax2.grid(True, alpha=0.3)

            plt.tight_layout()

            # PNG로 저장
            chart_path = f'/tmp/price_chart_{self.data.get("symbol")}.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()

            return chart_path
        except Exception as e:
            print(f"⚠️ 차트 생성 실패: {str(e)}")
            return None

    def _create_technical_indicators_chart(self) -> Optional[str]:
        """기술적 지표 차트 생성 (RSI, MACD)"""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6))

            # RSI 차트
            rsi = self.data.get('rsi', 50)
            ax1.axhline(y=70, color='r', linestyle='--', alpha=0.5, label='과매수(70)')
            ax1.axhline(y=30, color='g', linestyle='--', alpha=0.5, label='과매도(30)')
            ax1.axhline(y=rsi, color='blue', linewidth=2, label=f'현재 RSI: {rsi:.2f}')
            ax1.set_ylim(0, 100)
            ax1.set_ylabel('RSI', fontsize=10)
            ax1.set_title('RSI (Relative Strength Index)', fontsize=12, fontweight='bold')
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)

            # MACD 차트
            macd = self.data.get('macd', 0)
            macd_signal = self.data.get('macd_signal', 0)
            macd_histogram = self.data.get('macd_histogram', 0)

            ax2.bar([0], [macd_histogram], color='gray', alpha=0.5, label='Histogram')
            ax2.axhline(y=macd, color='blue', linewidth=2, label=f'MACD: {macd:.2f}')
            ax2.axhline(y=macd_signal, color='red', linewidth=2, label=f'Signal: {macd_signal:.2f}')
            ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax2.set_ylabel('MACD', fontsize=10)
            ax2.set_title('MACD (Moving Average Convergence Divergence)', fontsize=12, fontweight='bold')
            ax2.legend(loc='upper left')
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()

            chart_path = f'/tmp/technical_chart_{self.data.get("symbol")}.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()

            return chart_path
        except Exception as e:
            print(f"⚠️ 기술적 지표 차트 생성 실패: {str(e)}")
            return None

    def _add_financial_data(self):
        """재무 데이터 섹션"""
        self.story.append(Paragraph("재무 분석", self.styles['CustomHeading']))
        self.story.append(Spacer(1, 0.5*cm))

        financial_data = [
            ['지표', '값'],
            ['PER (주가수익비율)', f"{self.data.get('per', 'N/A')}"],
            ['PBR (주가순자산비율)', f"{self.data.get('pbr', 'N/A')}"],
            ['ROE (자기자본이익률)', f"{self.data.get('roe', 'N/A')}%"],
            ['배당수익률', f"{self.data.get('dividend_yield', 'N/A')}%"],
            ['EPS (주당순이익)', f"{self.data.get('eps', 'N/A')}원"],
            ['BPS (주당순자산)', f"{self.data.get('bps', 'N/A')}원"],
            ['영업이익률', f"{self.data.get('operating_margin', 'N/A')}%"],
            ['순이익률', f"{self.data.get('net_margin', 'N/A')}%"],
            ['부채비율', f"{self.data.get('debt_ratio', 'N/A')}%"],
        ]

        financial_table = Table(financial_data, colWidths=[7*cm, 7*cm])
        financial_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DBEAFE')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ]))
        self.story.append(financial_table)
        self.story.append(Spacer(1, 1*cm))

    def _add_target_prices(self):
        """목표가 및 투자 전략 섹션"""
        self.story.append(Paragraph("목표가 및 투자 전략", self.styles['CustomHeading']))
        self.story.append(Spacer(1, 0.5*cm))

        target_prices = self.data.get('target_prices', {})

        # 목표가 테이블
        target_data = [
            ['시나리오', '목표가', '상승 여력'],
            [
                '보수적',
                f"{target_prices.get('conservative', 'N/A'):,}원" if target_prices.get('conservative') else 'N/A',
                f"{target_prices.get('upside_potential', {}).get('conservative', 'N/A')}%"
            ],
            [
                '중립적',
                f"{target_prices.get('neutral', 'N/A'):,}원" if target_prices.get('neutral') else 'N/A',
                f"{target_prices.get('upside_potential', {}).get('neutral', 'N/A')}%"
            ],
            [
                '공격적',
                f"{target_prices.get('aggressive', 'N/A'):,}원" if target_prices.get('aggressive') else 'N/A',
                f"{target_prices.get('upside_potential', {}).get('aggressive', 'N/A')}%"
            ],
        ]

        target_table = Table(target_data, colWidths=[4.5*cm, 4.5*cm, 4.5*cm])
        target_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D1FAE5')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ]))
        self.story.append(target_table)
        self.story.append(Spacer(1, 0.5*cm))

        # 갭 분석 경고
        gap_analysis = target_prices.get('gap_analysis', {})
        if gap_analysis:
            warning = gap_analysis.get('warning', {})
            gap_text = f"""
            <para>
                <b>현재가 vs 목표가 분석:</b><br/>
                갭: {gap_analysis.get('gap_percent', 0):+.1f}%<br/>
                {warning.get('message', '')}
            </para>
            """
            self.story.append(Paragraph(gap_text, self.styles['CustomBody']))
            self.story.append(Spacer(1, 1*cm))

        # 타임프레임별 전략
        strategies = self.data.get('investment_strategies', {})
        if strategies:
            self.story.append(Paragraph("타임프레임별 투자 전략", self.styles['CustomHeading']))
            self.story.append(Spacer(1, 0.3*cm))

            for key, label in [('short_term', '단기'), ('medium_term', '중기'), ('long_term', '장기')]:
                strategy = strategies.get(key, {})
                if strategy:
                    strategy_text = f"""
                    <para>
                        <b>{label} ({strategy.get('timeframe', '')})</b><br/>
                        전망: {strategy.get('outlook', 'N/A')}<br/>
                        주요 요인: {strategy.get('key_factors', 'N/A')}<br/>
                        목표가: {strategy.get('target_price', 'N/A'):,}원
                    </para>
                    """
                    self.story.append(Paragraph(strategy_text, self.styles['CustomBody']))
                    self.story.append(Spacer(1, 0.3*cm))

    def _add_trading_signals(self):
        """매매 타이밍 신호 섹션"""
        self.story.append(PageBreak())
        self.story.append(Paragraph("매매 타이밍 신호", self.styles['CustomHeading']))
        self.story.append(Spacer(1, 0.5*cm))

        signals = self.data.get('trading_signals', {})

        signal_data = [
            ['항목', '값'],
            ['매매 신호', signals.get('signal', 'N/A').upper()],
            ['신뢰도', f"{signals.get('confidence', 0)}%"],
            ['강도', signals.get('strength', 'N/A')],
            ['진입 타이밍', signals.get('entry_timing', 'N/A')],
            ['포지션 크기', signals.get('position_size', 'N/A')],
        ]

        signal_table = Table(signal_data, colWidths=[7*cm, 7*cm])
        signal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F59E0B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#FDE68A')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ]))
        self.story.append(signal_table)
        self.story.append(Spacer(1, 0.5*cm))

        # 종합 위험도
        comp_risk = signals.get('comprehensive_risk', {})
        if comp_risk:
            risk_text = f"""
            <para>
                <b>종합 위험도:</b> {comp_risk.get('risk_level', 'N/A')} ({comp_risk.get('risk_score', 0):.1f}점)<br/>
                <b>위험 요인:</b><br/>
                {' / '.join(comp_risk.get('risk_factors', []))}
            </para>
            """
            self.story.append(Paragraph(risk_text, self.styles['CustomBody']))

    def _add_footer(self):
        """푸터 (면책 조항)"""
        self.story.append(PageBreak())

        disclaimer = f"""
        <para align=center>
            <b>면책 조항</b><br/><br/>
            본 레포트는 투자 참고 자료로만 제공되며, 투자 권유 또는 특정 종목의 매수/매도를 권장하는 것이 아닙니다.<br/>
            모든 투자 결정은 투자자 본인의 판단과 책임 하에 이루어져야 하며,<br/>
            투자로 인한 손실에 대해서는 본 플랫폼이 책임지지 않습니다.<br/><br/>
            <i>생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}</i><br/>
            <i>제공: 트레이딩 인텔리전스 플랫폼 (jusik.minhyuk.kr)</i>
        </para>
        """
        self.story.append(Paragraph(disclaimer, self.styles['CustomBody']))

    def generate(self) -> BytesIO:
        """PDF 생성 및 반환"""
        print(f"📄 PDF 생성 시작: {self.data.get('symbol_name')} ({self.data.get('symbol')})")

        # 1. 커버 페이지
        self._create_cover_page()

        # 2. 주가 차트
        price_chart_path = self._create_price_chart()
        if price_chart_path:
            self.story.append(Paragraph("주가 및 거래량 분석", self.styles['CustomHeading']))
            self.story.append(Spacer(1, 0.5*cm))
            img = Image(price_chart_path, width=15*cm, height=10*cm)
            self.story.append(img)
            self.story.append(Spacer(1, 1*cm))

        # 3. 기술적 지표 차트
        tech_chart_path = self._create_technical_indicators_chart()
        if tech_chart_path:
            self.story.append(Paragraph("기술적 지표", self.styles['CustomHeading']))
            self.story.append(Spacer(1, 0.5*cm))
            img = Image(tech_chart_path, width=15*cm, height=8*cm)
            self.story.append(img)
            self.story.append(Spacer(1, 1*cm))

        # 4. 재무 데이터
        self.story.append(PageBreak())
        self._add_financial_data()

        # 5. 목표가 및 투자 전략
        self._add_target_prices()

        # 6. 매매 타이밍 신호
        self._add_trading_signals()

        # 7. 푸터
        self._add_footer()

        # PDF 빌드
        self.doc.build(self.story)

        # BytesIO 버퍼 반환
        self.buffer.seek(0)
        print(f"✅ PDF 생성 완료: {len(self.buffer.getvalue())} bytes")
        return self.buffer
