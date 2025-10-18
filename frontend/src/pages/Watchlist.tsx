import { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useWatchlistStore } from '../stores/watchlistStore';
import { useRealtimePrice } from '../hooks/useRealtimePrice';
import { useInitialStockPrices } from '../hooks/useInitialStockPrices';
import { usePriceStore, formatPrice, formatChangeRate, getChangeRateColor } from '../stores/priceStore';
import StockAutocomplete from '../components/StockAutocomplete';

export default function Watchlist() {
  const { user, signOut } = useAuthStore();
  const { items, loading, error, fetchWatchlist, addToWatchlist, removeFromWatchlist, clearError } = useWatchlistStore();
  const navigate = useNavigate();

  // 실시간 시세 통합
  const { getPrice } = usePriceStore();
  const watchlistSymbols = useMemo(() => items.map((item) => item.symbol), [items]);
  const { isConnected } = useRealtimePrice({
    autoConnect: true,
    autoSubscribe: true,
    symbols: watchlistSymbols,
  });

  // 초기 시세 조회 (거래 시간 외 또는 WebSocket 연결 전)
  useInitialStockPrices({
    symbols: watchlistSymbols,
    enabled: watchlistSymbols.length > 0,
  });

  // 추가 폼 상태
  const [isAdding, setIsAdding] = useState(false);
  const [symbol, setSymbol] = useState('');
  const [name, setName] = useState('');

  // 관심 종목 로드
  useEffect(() => {
    if (user) {
      fetchWatchlist(user.id);
    }
  }, [user, fetchWatchlist]);

  const handleAddToWatchlist = async () => {
    if (!user) return;

    try {
      clearError();
      await addToWatchlist(user.id, symbol, name);
      setIsAdding(false);
      resetForm();
      alert('관심 종목이 추가되었습니다.');
    } catch (err) {
      console.error('관심 종목 추가 실패:', err);
    }
  };

  const handleRemoveFromWatchlist = async (id: string, stockName: string) => {
    if (!confirm(`${stockName}을(를) 관심 종목에서 삭제하시겠습니까?`)) return;

    try {
      clearError();
      await removeFromWatchlist(id);
      alert('관심 종목에서 삭제되었습니다.');
    } catch (err) {
      console.error('관심 종목 삭제 실패:', err);
    }
  };

  const resetForm = () => {
    setSymbol('');
    setName('');
    setIsAdding(false);
  };

  const handleSignOut = async () => {
    await signOut();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      {/* 헤더 */}
      <div className="max-w-6xl mx-auto mb-6">
        <div className="bg-white rounded-lg shadow-md p-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">⭐ 관심 종목 관리</h1>
            <p className="text-lg text-gray-600">{user?.email}</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => navigate('/dashboard')} className="btn btn-secondary">
              대시보드
            </button>
            <button onClick={() => navigate('/portfolio')} className="btn btn-secondary">
              보유 종목
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
      <div className="max-w-6xl mx-auto space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* 관심 종목 요약 */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold">📊 관심 종목 요약</h2>
            {isConnected && (
              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                실시간 연동 중
              </span>
            )}
          </div>
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-lg text-gray-600">관심 종목 수</div>
            <div className="text-3xl font-bold text-blue-600">{items.length}개</div>
          </div>
        </div>

        {/* 종목 추가 버튼 */}
        {!isAdding && (
          <div className="card">
            <button onClick={() => setIsAdding(true)} className="btn btn-primary w-full">
              ➕ 관심 종목 추가
            </button>
          </div>
        )}

        {/* 종목 추가 폼 */}
        {isAdding && (
          <div className="card">
            <h2 className="text-2xl font-bold mb-4">➕ 관심 종목 추가</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-lg font-medium text-gray-700 mb-2">
                  종목 검색
                </label>
                <StockAutocomplete
                  onSelect={(stock) => {
                    setSymbol(stock.symbol);
                    setName(stock.name);
                  }}
                  placeholder="종목코드 또는 종목명 입력 (예: 삼성전자, 005930)"
                  autoFocus={isAdding}
                />
                {symbol && name && (
                  <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="text-sm text-blue-700">선택된 종목:</div>
                    <div className="text-lg font-bold text-blue-900">
                      {name} ({symbol})
                    </div>
                  </div>
                )}
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleAddToWatchlist}
                  disabled={loading || !symbol || !name}
                  className="btn btn-primary flex-1"
                >
                  {loading ? '추가 중...' : '추가'}
                </button>
                <button onClick={resetForm} className="btn btn-secondary flex-1">
                  취소
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 관심 종목 목록 */}
        <div className="card">
          <h2 className="text-2xl font-bold mb-4">⭐ 관심 종목 목록</h2>
          {loading && items.length === 0 ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-lg text-gray-600">로딩 중...</p>
            </div>
          ) : items.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-xl text-gray-600">관심 종목이 없습니다.</p>
              <p className="text-lg text-gray-500 mt-2">종목을 추가해보세요!</p>
            </div>
          ) : (
            <div className="space-y-4">
              {items.map((item) => {
                const priceData = getPrice(item.symbol);

                return (
                  <div key={item.id} className="bg-gray-50 p-4 rounded-lg hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <h3 className="text-xl font-bold text-gray-900">
                            {item.symbol_name}
                          </h3>
                          <span className="text-sm text-gray-500">({item.symbol})</span>
                        </div>
                        <p className="text-sm text-gray-500 mt-1">
                          등록일: {new Date(item.created_at).toLocaleDateString('ko-KR')}
                        </p>

                        {/* 실시간 시세 표시 */}
                        {priceData ? (
                          <div className="mt-2 flex items-center gap-4">
                            <div>
                              <div className="text-xs text-gray-600">현재가</div>
                              <div className="text-2xl font-bold text-gray-900">
                                {formatPrice(priceData.price)}원
                              </div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-600">등락</div>
                              <div className={`text-lg font-bold ${getChangeRateColor(priceData.change_rate)}`}>
                                {priceData.change > 0 ? '▲' : priceData.change < 0 ? '▼' : '─'} {formatPrice(Math.abs(priceData.change))}원
                              </div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-600">등락률</div>
                              <div className={`text-lg font-bold ${getChangeRateColor(priceData.change_rate)}`}>
                                {formatChangeRate(priceData.change_rate)}
                              </div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-600">거래량</div>
                              <div className="text-sm text-gray-700">
                                {priceData.volume.toLocaleString()}
                              </div>
                            </div>
                            {isConnected && (
                              <div className="ml-auto">
                                <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                                  실시간
                                </span>
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="mt-2 text-sm text-gray-400 italic">
                            실시간 시세 대기 중...
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => handleRemoveFromWatchlist(item.id, item.symbol_name)}
                        className="btn btn-danger ml-4"
                      >
                        삭제
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
