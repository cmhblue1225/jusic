import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useNewsStore } from '../stores/newsStore';
import { useWatchlistStore } from '../stores/watchlistStore';
import { useAlertStore } from '../stores/alertStore';
import NewsCard from '../components/NewsCard';

export default function News() {
  const { user, signOut } = useAuthStore();
  const { items: news, loading, error, fetchNews, fetchNewsBySymbol, selectedSymbol, clearFilter, clearError } = useNewsStore();
  const { items: watchlist } = useWatchlistStore();
  const { ttsConfig } = useAlertStore();
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'impact'>('date'); // 정렬 기준

  // 뉴스 로드
  useEffect(() => {
    fetchNews();
  }, [fetchNews]);

  // 관심 종목 로드
  useEffect(() => {
    if (user) {
      useWatchlistStore.getState().fetchWatchlist(user.id);
    }
  }, [user]);

  const handleSignOut = async () => {
    await signOut();
    navigate('/login');
  };

  // 종목 필터링
  const handleSymbolFilter = (symbol: string) => {
    if (symbol === selectedSymbol) {
      clearFilter();
      fetchNews();
    } else {
      fetchNewsBySymbol(symbol);
    }
  };

  // TTS 음성 읽기
  const handleReadAloud = (text: string) => {
    if (!ttsConfig.enabled) {
      alert('TTS가 비활성화되어 있습니다. 프로필 설정에서 활성화해주세요.');
      return;
    }

    // Web Speech API 사용
    if ('speechSynthesis' in window) {
      // 기존 음성 중지
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'ko-KR';
      utterance.rate = ttsConfig.rate;
      utterance.volume = ttsConfig.volume;
      utterance.pitch = 1.0;

      window.speechSynthesis.speak(utterance);
    } else {
      alert('브라우저가 음성 합성을 지원하지 않습니다.');
    }
  };

  // 검색 필터링
  const filteredNews = news.filter((item) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      item.title.toLowerCase().includes(term) ||
      item.content.toLowerCase().includes(term) ||
      item.summary?.toLowerCase().includes(term) ||
      item.related_symbols.some((symbol) => symbol.toLowerCase().includes(term))
    );
  });

  // 정렬 (Phase 2.3.3)
  const sortedNews = [...filteredNews].sort((a, b) => {
    if (sortBy === 'date') {
      // 최신순 정렬
      return new Date(b.published_at).getTime() - new Date(a.published_at).getTime();
    } else {
      // 영향도순 정렬 (impact_score가 null인 경우 0으로 처리)
      const impactA = a.impact_score ?? 0;
      const impactB = b.impact_score ?? 0;
      return impactB - impactA;
    }
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      {/* 헤더 */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="bg-white rounded-lg shadow-md p-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">📰 뉴스 센터</h1>
            <p className="text-lg text-gray-600">{user?.email}</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => navigate('/dashboard')} className="btn btn-secondary">
              대시보드
            </button>
            <button onClick={() => navigate('/portfolio')} className="btn btn-secondary">
              보유 종목
            </button>
            <button onClick={() => navigate('/watchlist')} className="btn btn-secondary">
              관심 종목
            </button>
            <button onClick={() => navigate('/profile')} className="btn btn-secondary">
              프로필 설정
            </button>
            <button onClick={handleSignOut} className="btn btn-danger">
              로그아웃
            </button>
          </div>
        </div>
      </div>

      {/* 메인 콘텐츠 */}
      <div className="max-w-7xl mx-auto space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex justify-between items-center">
            <span>{error}</span>
            <button onClick={clearError} className="text-red-900 hover:text-red-700 font-bold">
              ✕
            </button>
          </div>
        )}

        {/* 필터 및 검색 */}
        <div className="card">
          <div className="mb-4">
            <h2 className="text-xl font-bold mb-3">🔍 필터 및 검색</h2>

            {/* 검색바 */}
            <div className="mb-4">
              <input
                type="text"
                placeholder="뉴스 제목, 내용, 종목 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input w-full"
              />
            </div>

            {/* 정렬 옵션 (Phase 2.3.3) */}
            <div className="mb-4">
              <div className="text-sm text-gray-600 mb-2">정렬:</div>
              <div className="flex gap-2">
                <button
                  onClick={() => setSortBy('date')}
                  className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                    sortBy === 'date'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  📅 최신순
                </button>
                <button
                  onClick={() => setSortBy('impact')}
                  className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                    sortBy === 'impact'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  🔥 영향도순
                </button>
              </div>
            </div>

            {/* 관심 종목 필터 */}
            {watchlist.length > 0 && (
              <div>
                <div className="text-sm text-gray-600 mb-2">관심 종목 필터:</div>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => {
                      clearFilter();
                      fetchNews();
                    }}
                    className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                      !selectedSymbol
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    전체
                  </button>
                  {watchlist.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleSymbolFilter(item.symbol)}
                      className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                        selectedSymbol === item.symbol
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      {item.symbol_name} ({item.symbol})
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* 뉴스 통계 */}
          <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-200">
            <div className="bg-blue-50 p-3 rounded-lg">
              <div className="text-sm text-gray-600">전체 뉴스</div>
              <div className="text-2xl font-bold text-blue-600">{news.length}건</div>
            </div>
            <div className="bg-green-50 p-3 rounded-lg">
              <div className="text-sm text-gray-600">표시 중</div>
              <div className="text-2xl font-bold text-green-600">{filteredNews.length}건</div>
            </div>
            <div className="bg-purple-50 p-3 rounded-lg">
              <div className="text-sm text-gray-600">TTS 상태</div>
              <div className="text-lg font-bold text-purple-600">
                {ttsConfig.enabled ? '🔊 활성' : '🔇 비활성'}
              </div>
            </div>
          </div>
        </div>

        {/* 뉴스 목록 */}
        <div className="card">
          <h2 className="text-2xl font-bold mb-4">
            {selectedSymbol ? `📊 ${selectedSymbol} 관련 뉴스` : '📰 전체 뉴스'}
          </h2>

          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-lg text-gray-600">로딩 중...</p>
            </div>
          ) : sortedNews.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-xl text-gray-600">
                {searchTerm || selectedSymbol ? '검색 결과가 없습니다.' : '뉴스가 없습니다.'}
              </p>
              <p className="text-lg text-gray-500 mt-2">
                {selectedSymbol && '다른 종목을 선택하거나 전체를 확인해보세요.'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {sortedNews.map((newsItem) => (
                <NewsCard key={newsItem.id} news={newsItem} onReadAloud={handleReadAloud} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
