/**
 * ReportCard Component
 * 종목 레포트 카드 (결과 표시)
 */
import type { StockReport } from '../stores/reportStore';

interface ReportCardProps {
  report: StockReport;
  onClose?: () => void;
}

export default function ReportCard({ report, onClose }: ReportCardProps) {
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
  const formatNumber = (num: number | null) => {
    if (num === null) return 'N/A';
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
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            ✕
          </button>
        )}
      </div>

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

      {/* AI 평가 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
