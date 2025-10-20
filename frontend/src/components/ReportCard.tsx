/**
 * ReportCard Component
 * 종목 레포트 카드 (결과 표시)
 */
import { useState } from 'react';
import type { StockReport } from '../stores/reportStore';
import { useAuthStore } from '../stores/authStore';
import { useReportStore } from '../stores/reportStore';
import { bookmarkReport } from '../lib/reportApi';
import PriceChart from './PriceChart';
import FinancialChart from './FinancialChart';

interface ReportCardProps {
  report: StockReport;
  onClose?: () => void;
}

export default function ReportCard({ report, onClose }: ReportCardProps) {
  const { user } = useAuthStore();
  const { bookmarks, addBookmark } = useReportStore();
  const [isBookmarking, setIsBookmarking] = useState(false);
  const [bookmarkError, setBookmarkError] = useState<string | null>(null);

  // 이미 북마크되어 있는지 확인
  const isBookmarked = bookmarks.some(
    b => b.symbol === report.symbol && b.report_date === report.report_date
  );

  // 북마크 저장 핸들러
  const handleBookmark = async () => {
    if (!user) {
      setBookmarkError('로그인이 필요합니다');
      return;
    }

    if (isBookmarked) {
      setBookmarkError('이미 북마크에 저장되어 있습니다');
      return;
    }

    setIsBookmarking(true);
    setBookmarkError(null);

    try {
      const result = await bookmarkReport(report.symbol, report.symbol_name);

      // 북마크 목록에 추가 (ID 포함)
      addBookmark({
        ...report,
        id: result.bookmark_id || undefined
      });

      alert(result.message || '북마크에 저장되었습니다');
    } catch (error) {
      console.error('[ReportCard] 북마크 저장 실패:', error);
      setBookmarkError(error instanceof Error ? error.message : '북마크 저장에 실패했습니다');
    } finally {
      setIsBookmarking(false);
    }
  };

  // 위험도별 색상
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low':
        return 'bg-green-100 text-green-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'high':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // 권고별 색상
  const getRecommendationColor = (rec: string) => {
    switch (rec) {
      case 'buy':
        return 'bg-blue-100 text-blue-800';
      case 'sell':
        return 'bg-red-100 text-red-800';
      case 'hold':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // 위험도 한글
  const getRiskLabel = (level: string) => {
    switch (level) {
      case 'low':
        return '낮음';
      case 'medium':
        return '보통';
      case 'high':
        return '높음';
      default:
        return '알 수 없음';
    }
  };

  // 권고 한글
  const getRecommendationLabel = (rec: string) => {
    switch (rec) {
      case 'buy':
        return '매수';
      case 'sell':
        return '매도';
      case 'hold':
        return '관망';
      default:
        return '알 수 없음';
    }
  };

  // 숫자 포맷팅
  const formatNumber = (num: number | null | undefined) => {
    if (num === null || num === undefined) return 'N/A';
    return num.toLocaleString('ko-KR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 space-y-6">
      {/* 헤더 */}
      <div className="flex justify-between items-start border-b pb-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            {report.symbol_name} ({report.symbol})
          </h2>
          <p className="text-sm text-gray-500">레포트 생성일: {report.report_date}</p>
          {report.cached && (
            <span className="inline-block mt-2 px-2 py-1 bg-green-100 text-green-700 text-xs rounded">
              ⚡ 캐시 데이터
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* 북마크 버튼 (로그인 사용자만) */}
          {user && (
            <button
              onClick={handleBookmark}
              disabled={isBookmarking || isBookmarked}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                isBookmarked
                  ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                  : 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
              } disabled:opacity-50`}
              title={isBookmarked ? '이미 북마크됨' : '북마크에 저장'}
            >
              {isBookmarking ? (
                <span className="flex items-center">
                  <svg className="animate-spin h-4 w-4 mr-1" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  저장 중...
                </span>
              ) : isBookmarked ? (
                <>⭐ 저장됨</>
              ) : (
                <>📌 북마크 저장</>
              )}
            </button>
          )}
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* 북마크 에러 메시지 */}
      {bookmarkError && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          ⚠️ {bookmarkError}
        </div>
      )}

      {/* AI 요약 */}
      <div className="bg-blue-50 p-4 rounded-lg">
        <h3 className="font-bold text-lg mb-2 text-blue-900">📊 AI 종합 분석</h3>
        <p className="text-gray-700 leading-relaxed">{report.summary}</p>
      </div>

      {/* 주가 정보 */}
      <div>
        <h3 className="font-bold text-lg mb-3">💰 주가 정보</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-sm text-gray-600">현재가</div>
            <div className="text-xl font-bold">{formatNumber(report.current_price)}원</div>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-sm text-gray-600">등락률</div>
            <div className={`text-xl font-bold ${report.change_rate >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
              {report.change_rate >= 0 ? '▲' : '▼'} {Math.abs(report.change_rate)}%
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-sm text-gray-600">고가 / 저가</div>
            <div className="text-sm font-semibold">
              {formatNumber(report.high_price)} / {formatNumber(report.low_price)}
            </div>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-sm text-gray-600">거래량</div>
            <div className="text-sm font-semibold">{formatNumber(report.volume)}</div>
          </div>
        </div>
      </div>

      {/* 기술적 지표 */}
      <div>
        <h3 className="font-bold text-lg mb-3">📈 기술적 지표</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-sm text-gray-600">5일 이동평균</div>
            <div className="text-lg font-semibold">{formatNumber(report.ma5)}</div>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-sm text-gray-600">20일 이동평균</div>
            <div className="text-lg font-semibold">{formatNumber(report.ma20)}</div>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-sm text-gray-600">60일 이동평균</div>
            <div className="text-lg font-semibold">{formatNumber(report.ma60)}</div>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-sm text-gray-600">거래량 비율</div>
            <div className="text-lg font-semibold">{formatNumber(report.volume_ratio)}배</div>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-sm text-gray-600">변동성</div>
            <div className="text-lg font-semibold">{formatNumber(report.volatility)}</div>
          </div>
          <div className="bg-gray-50 p-3 rounded">
            <div className="text-sm text-gray-600">볼린저 밴드</div>
            <div className="text-sm font-semibold">
              {formatNumber(report.bollinger_upper)} / {formatNumber(report.bollinger_lower)}
            </div>
          </div>
        </div>
      </div>

      {/* 주가 차트 (신규) */}
      <PriceChart
        currentPrice={report.current_price}
        ma5={report.ma5}
        ma20={report.ma20}
        ma60={report.ma60}
        high={report.high_price}
        low={report.low_price}
        symbolName={report.symbol_name}
      />

      {/* 재무비율 (신규) */}
      {(report.per || report.pbr || report.roe) && (
        <div>
          <h3 className="font-bold text-lg mb-3">💰 재무비율</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-indigo-50 p-3 rounded">
              <div className="text-sm text-indigo-700">PER (주가수익비율)</div>
              <div className="text-lg font-semibold text-indigo-900">{formatNumber(report.per)}</div>
            </div>
            <div className="bg-indigo-50 p-3 rounded">
              <div className="text-sm text-indigo-700">PBR (주가순자산비율)</div>
              <div className="text-lg font-semibold text-indigo-900">{formatNumber(report.pbr)}</div>
            </div>
            <div className="bg-indigo-50 p-3 rounded">
              <div className="text-sm text-indigo-700">ROE (자기자본이익률)</div>
              <div className="text-lg font-semibold text-indigo-900">{formatNumber(report.roe)}%</div>
            </div>
            <div className="bg-indigo-50 p-3 rounded">
              <div className="text-sm text-indigo-700">배당수익률</div>
              <div className="text-lg font-semibold text-indigo-900">{formatNumber(report.dividend_yield)}%</div>
            </div>
            <div className="bg-indigo-50 p-3 rounded">
              <div className="text-sm text-indigo-700">EPS (주당순이익)</div>
              <div className="text-sm font-semibold text-indigo-900">{formatNumber(report.eps)}원</div>
            </div>
            <div className="bg-indigo-50 p-3 rounded">
              <div className="text-sm text-indigo-700">BPS (주당순자산)</div>
              <div className="text-sm font-semibold text-indigo-900">{formatNumber(report.bps)}원</div>
            </div>
            <div className="bg-indigo-50 p-3 rounded">
              <div className="text-sm text-indigo-700">영업이익률</div>
              <div className="text-lg font-semibold text-indigo-900">{formatNumber(report.operating_margin)}%</div>
            </div>
            <div className="bg-indigo-50 p-3 rounded">
              <div className="text-sm text-indigo-700">부채비율</div>
              <div className="text-lg font-semibold text-indigo-900">{formatNumber(report.debt_ratio)}%</div>
            </div>
          </div>

          {/* 재무비율 차트 */}
          <FinancialChart
            per={report.per}
            pbr={report.pbr}
            roe={report.roe}
            symbolName={report.symbol_name}
          />
        </div>
      )}

      {/* 투자자 동향 (신규) */}
      {(report.foreign_net_buy !== null && report.foreign_net_buy !== undefined) && (
        <div>
          <h3 className="font-bold text-lg mb-3">📊 투자자 매매 동향</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <div className="text-sm text-blue-700 mb-2">외국인</div>
              <div className={`text-xl font-bold ${(report.foreign_net_buy || 0) >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
                {(report.foreign_net_buy || 0) >= 0 ? '▲' : '▼'} {Math.abs(report.foreign_net_buy || 0).toLocaleString()}주
              </div>
              <div className="text-xs text-gray-600 mt-1">
                {((report.foreign_net_buy_amt || 0) / 100000000).toFixed(1)}억원
              </div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <div className="text-sm text-green-700 mb-2">기관</div>
              <div className={`text-xl font-bold ${(report.institution_net_buy || 0) >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
                {(report.institution_net_buy || 0) >= 0 ? '▲' : '▼'} {Math.abs(report.institution_net_buy || 0).toLocaleString()}주
              </div>
              <div className="text-xs text-gray-600 mt-1">
                {((report.institution_net_buy_amt || 0) / 100000000).toFixed(1)}억원
              </div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
              <div className="text-sm text-purple-700 mb-2">개인</div>
              <div className={`text-xl font-bold ${(report.individual_net_buy || 0) >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
                {(report.individual_net_buy || 0) >= 0 ? '▲' : '▼'} {Math.abs(report.individual_net_buy || 0).toLocaleString()}주
              </div>
              <div className="text-xs text-gray-600 mt-1">
                {((report.individual_net_buy_amt || 0) / 100000000).toFixed(1)}억원
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI 평가 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg">
          <div className="text-sm text-purple-700 mb-1">위험도</div>
          <div className={`inline-block px-3 py-1 rounded font-bold ${getRiskColor(report.risk_level)}`}>
            {getRiskLabel(report.risk_level)}
          </div>
        </div>
        <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 p-4 rounded-lg">
          <div className="text-sm text-indigo-700 mb-1">투자 권고</div>
          <div className={`inline-block px-3 py-1 rounded font-bold ${getRecommendationColor(report.recommendation)}`}>
            {getRecommendationLabel(report.recommendation)}
          </div>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg">
          <div className="text-sm text-green-700 mb-1">평가 점수</div>
          <div className="text-2xl font-bold text-green-800">{report.evaluation_score}점</div>
        </div>
        {report.target_price_range && (
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg">
            <div className="text-sm text-blue-700 mb-1">목표 주가</div>
            <div className="text-lg font-bold text-blue-800">{report.target_price_range}원</div>
          </div>
        )}
      </div>

      {/* GPT-4 고급 분석 섹션 (신규) - 항상 표시 */}
      <div className="bg-gradient-to-br from-slate-50 to-slate-100 p-6 rounded-lg border-2 border-slate-200">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-2xl">🤖</span>
          <h3 className="text-xl font-bold text-slate-900">GPT-4 심화 분석</h3>
          <span className="px-2 py-1 bg-blue-500 text-white text-xs rounded-full font-medium">AI Premium</span>
        </div>

          <div className="space-y-4">
            {/* 투자 전략 */}
            {report.investment_strategy && (
              <div className="bg-white p-4 rounded-lg border border-slate-200">
                <h4 className="font-bold text-slate-800 mb-2 flex items-center gap-2">
                  <span>💡</span> 투자 전략
                  {report.time_horizon && (
                    <span className="ml-auto px-2 py-1 bg-slate-100 text-slate-700 text-xs rounded">
                      {report.time_horizon === 'short_term' ? '단기 (1~3개월)' :
                       report.time_horizon === 'medium_term' ? '중기 (3~6개월)' :
                       '장기 (6개월 이상)'}
                    </span>
                  )}
                </h4>
                <p className="text-slate-700 text-sm leading-relaxed">{report.investment_strategy}</p>
              </div>
            )}

            {/* 기술적 분석 & 기본적 분석 */}
            {(report.technical_analysis || report.fundamental_analysis) && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {report.technical_analysis && (
                  <div className="bg-white p-4 rounded-lg border border-slate-200">
                    <h4 className="font-bold text-slate-800 mb-2 flex items-center gap-2">
                      <span>📈</span> 기술적 분석
                    </h4>
                    <p className="text-slate-700 text-sm leading-relaxed">{report.technical_analysis}</p>
                  </div>
                )}
                {report.fundamental_analysis && (
                  <div className="bg-white p-4 rounded-lg border border-slate-200">
                    <h4 className="font-bold text-slate-800 mb-2 flex items-center gap-2">
                      <span>💰</span> 기본적 분석
                    </h4>
                    <p className="text-slate-700 text-sm leading-relaxed">{report.fundamental_analysis}</p>
                  </div>
                )}
              </div>
            )}

            {/* 시장 심리 */}
            {report.market_sentiment && (
              <div className="bg-white p-4 rounded-lg border border-slate-200">
                <h4 className="font-bold text-slate-800 mb-2 flex items-center gap-2">
                  <span>📊</span> 시장 심리
                </h4>
                <p className="text-slate-700 text-sm leading-relaxed">{report.market_sentiment}</p>
              </div>
            )}

            {/* 긍정적 촉매 & 리스크 요인 */}
            {(report.catalysts || report.risk_factors) && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {report.catalysts && (
                  <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                    <h4 className="font-bold text-green-800 mb-2 flex items-center gap-2">
                      <span>🚀</span> 긍정적 촉매
                    </h4>
                    <p className="text-green-700 text-sm leading-relaxed whitespace-pre-line">{report.catalysts}</p>
                  </div>
                )}
                {report.risk_factors && (
                  <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                    <h4 className="font-bold text-red-800 mb-2 flex items-center gap-2">
                      <span>⚠️</span> 주요 리스크
                    </h4>
                    <p className="text-red-700 text-sm leading-relaxed whitespace-pre-line">{report.risk_factors}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

      {/* 관련 뉴스 */}
      <div className="bg-yellow-50 p-4 rounded-lg">
        <div className="text-sm text-yellow-800">
          📰 관련 뉴스 {report.related_news_count}개 분석됨
        </div>
      </div>
    </div>
  );
}
