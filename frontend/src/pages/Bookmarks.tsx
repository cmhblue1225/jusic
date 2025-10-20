/**
 * Bookmarks Page
 * 저장된 레포트 북마크 목록 조회 및 관리
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useReportStore } from '../stores/reportStore';
import { getBookmarks, deleteBookmark } from '../lib/reportApi';
import ReportCard from '../components/ReportCard';

export default function Bookmarks() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { bookmarks, setBookmarks, removeBookmark, loading, error, setLoading, setError, clearError } = useReportStore();

  const [selectedReport, setSelectedReport] = useState<typeof bookmarks[0] | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // 북마크 목록 로드
  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    loadBookmarks();
  }, [user, navigate]);

  const loadBookmarks = async () => {
    clearError();
    setLoading(true);

    try {
      const data = await getBookmarks();
      setBookmarks(data);
    } catch (err) {
      console.error('[Bookmarks] 북마크 조회 실패:', err);
      setError(err instanceof Error ? err.message : '북마크 조회에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  // 북마크 삭제
  const handleDelete = async (bookmarkId: string) => {
    if (!bookmarkId) {
      alert('북마크 ID가 없습니다');
      return;
    }

    if (!confirm('이 북마크를 삭제하시겠습니까?')) {
      return;
    }

    setDeletingId(bookmarkId);

    try {
      await deleteBookmark(bookmarkId);
      removeBookmark(bookmarkId);
      alert('북마크가 삭제되었습니다');

      // 현재 선택된 레포트가 삭제된 경우 닫기
      if (selectedReport?.id === bookmarkId) {
        setSelectedReport(null);
      }
    } catch (err) {
      console.error('[Bookmarks] 북마크 삭제 실패:', err);
      alert(err instanceof Error ? err.message : '북마크 삭제에 실패했습니다');
    } finally {
      setDeletingId(null);
    }
  };

  // 레포트 상세 보기
  const handleViewReport = (bookmark: typeof bookmarks[0]) => {
    setSelectedReport(bookmark);
  };

  // 레포트 닫기
  const handleCloseReport = () => {
    setSelectedReport(null);
  };

  // 숫자 포맷팅
  const formatNumber = (num: number | null) => {
    if (num === null) return 'N/A';
    return num.toLocaleString('ko-KR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });
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

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      {/* 헤더 */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="bg-white rounded-lg shadow-md p-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">📌 저장된 레포트</h1>
            <p className="text-gray-600">북마크에 저장한 레포트 목록</p>
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
        {selectedReport ? (
          /* 레포트 상세 보기 */
          <div>
            <button
              onClick={handleCloseReport}
              className="mb-4 btn btn-secondary"
            >
              ← 목록으로
            </button>
            <ReportCard report={selectedReport} onClose={handleCloseReport} />
          </div>
        ) : (
          /* 북마크 목록 */
          <div className="card">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <svg className="animate-spin h-8 w-8 text-blue-600" viewBox="0 0 24 24">
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
                <span className="ml-3 text-gray-600">북마크 로딩 중...</span>
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                ⚠️ {error}
              </div>
            ) : bookmarks.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📭</div>
                <h3 className="text-xl font-bold text-gray-700 mb-2">저장된 북마크가 없습니다</h3>
                <p className="text-gray-500 mb-6">레포트를 생성하고 북마크에 저장해보세요</p>
                <button
                  onClick={() => navigate('/report')}
                  className="btn btn-primary"
                >
                  📊 레포트 생성하기
                </button>
              </div>
            ) : (
              <div>
                <div className="mb-4 flex justify-between items-center">
                  <h2 className="text-xl font-bold">전체 {bookmarks.length}개</h2>
                  <button
                    onClick={loadBookmarks}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    🔄 새로고침
                  </button>
                </div>

                <div className="space-y-4">
                  {bookmarks.map((bookmark) => (
                    <div
                      key={bookmark.id || `${bookmark.symbol}-${bookmark.report_date}`}
                      className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex justify-between items-start">
                        {/* 레포트 정보 */}
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="text-xl font-bold text-gray-900">
                              {bookmark.symbol_name} ({bookmark.symbol})
                            </h3>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${getRecommendationColor(bookmark.recommendation)}`}>
                              {getRecommendationLabel(bookmark.recommendation)}
                            </span>
                          </div>

                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm mb-3">
                            <div>
                              <span className="text-gray-600">현재가: </span>
                              <span className="font-semibold">{formatNumber(bookmark.current_price)}원</span>
                            </div>
                            <div>
                              <span className="text-gray-600">등락률: </span>
                              <span className={`font-semibold ${bookmark.change_rate >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
                                {bookmark.change_rate >= 0 ? '▲' : '▼'} {Math.abs(bookmark.change_rate)}%
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-600">평가 점수: </span>
                              <span className="font-semibold">{bookmark.evaluation_score}점</span>
                            </div>
                            <div>
                              <span className="text-gray-600">생성일: </span>
                              <span className="font-semibold">{bookmark.report_date}</span>
                            </div>
                          </div>

                          <p className="text-sm text-gray-700 line-clamp-2">{bookmark.summary}</p>
                        </div>

                        {/* 액션 버튼 */}
                        <div className="flex flex-col gap-2 ml-4">
                          <button
                            onClick={() => handleViewReport(bookmark)}
                            className="px-4 py-2 bg-blue-100 text-blue-800 rounded-lg font-medium hover:bg-blue-200 transition-colors whitespace-nowrap"
                          >
                            📄 상세보기
                          </button>
                          <button
                            onClick={() => bookmark.id && handleDelete(bookmark.id)}
                            disabled={deletingId === bookmark.id}
                            className="px-4 py-2 bg-red-100 text-red-800 rounded-lg font-medium hover:bg-red-200 transition-colors whitespace-nowrap disabled:opacity-50"
                          >
                            {deletingId === bookmark.id ? '삭제 중...' : '🗑️ 삭제'}
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
