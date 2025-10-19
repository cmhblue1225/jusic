/**
 * Report Page
 * 종목 레포트 생성 및 조회 페이지
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useReportStore } from '../stores/reportStore';
import { generateReport } from '../lib/reportApi';
import StockAutocomplete from '../components/StockAutocomplete';
import ReportCard from '../components/ReportCard';

export default function Report() {
  const navigate = useNavigate();
  const { currentReport, loading, error, setCurrentReport, setLoading, setError, clearError } = useReportStore();

  const [selectedSymbol, setSelectedSymbol] = useState('');
  const [selectedName, setSelectedName] = useState('');

  // 레포트 생성
  const handleGenerateReport = async () => {
    if (!selectedSymbol || !selectedName) {
      setError('종목을 선택해주세요');
      return;
    }

    clearError();
    setLoading(true);

    try {
      const report = await generateReport(selectedSymbol, selectedName);
      setCurrentReport(report);
    } catch (err) {
      console.error('[Report] 레포트 생성 실패:', err);
      setError(err instanceof Error ? err.message : '레포트 생성에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  // 레포트 닫기
  const handleCloseReport = () => {
    setCurrentReport(null);
    setSelectedSymbol('');
    setSelectedName('');
    clearError();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      {/* 헤더 */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="bg-white rounded-lg shadow-md p-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">📊 종목 레포트</h1>
            <p className="text-gray-600">AI 기반 종합 분석 레포트</p>
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="btn btn-secondary"
          >
            ← 대시보드로
          </button>
        </div>
      </div>

      {/* 메인 콘텐츠 */}
      <div className="max-w-7xl mx-auto">
        {!currentReport ? (
          /* 레포트 생성 폼 */
          <div className="card">
            <h2 className="text-xl font-bold mb-4">종목 검색</h2>

            <div className="space-y-4">
              {/* 종목 검색 */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  종목 검색 (종목코드 또는 종목명)
                </label>
                <StockAutocomplete
                  onSelect={(stock) => {
                    setSelectedSymbol(stock.symbol);
                    setSelectedName(stock.name);
                    clearError();
                  }}
                  placeholder="예: 삼성전자, 005930"
                  autoFocus={true}
                />
              </div>

              {/* 선택된 종목 표시 */}
              {selectedSymbol && selectedName && (
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-sm text-blue-700 mb-1">선택된 종목</div>
                  <div className="text-lg font-bold text-blue-900">
                    {selectedName} ({selectedSymbol})
                  </div>
                </div>
              )}

              {/* 에러 메시지 */}
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                  ⚠️ {error}
                </div>
              )}

              {/* 안내 메시지 */}
              <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                <h3 className="font-bold text-yellow-900 mb-2">📋 레포트 포함 내용</h3>
                <ul className="list-disc list-inside space-y-1 text-sm text-yellow-800">
                  <li>당일 주가 데이터 (현재가, 고가, 저가, 거래량)</li>
                  <li>기술적 지표 (이동평균선, 볼린저 밴드, 거래량 비율, 변동성)</li>
                  <li>관련 뉴스 분석 (최근 1일)</li>
                  <li>AI 종합 분석 (위험도, 투자 권고, 평가 점수)</li>
                </ul>
                <p className="text-xs text-yellow-700 mt-2">
                  ⚡ 레포트는 캐싱되어 빠르게 조회됩니다 (장 마감 시간 기준)
                </p>
              </div>

              {/* 레포트 생성 버튼 */}
              <button
                onClick={handleGenerateReport}
                disabled={!selectedSymbol || !selectedName || loading}
                className="btn btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
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
                    레포트 생성 중... (최대 10초 소요)
                  </span>
                ) : (
                  '🤖 AI 레포트 생성'
                )}
              </button>
            </div>
          </div>
        ) : (
          /* 레포트 결과 표시 */
          <ReportCard report={currentReport} onClose={handleCloseReport} />
        )}
      </div>
    </div>
  );
}
