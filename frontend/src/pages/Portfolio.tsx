import { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { usePortfolioStore } from '../stores/portfolioStore';
import { useRealtimePrice } from '../hooks/useRealtimePrice';
import { useInitialStockPrices } from '../hooks/useInitialStockPrices';
import { usePriceStore, formatPrice, formatChangeRate, getChangeRateColor } from '../stores/priceStore';
import StockAutocomplete from '../components/StockAutocomplete';

export default function Portfolio() {
  const { user, signOut } = useAuthStore();
  const {
    items,
    loading,
    error,
    fetchPortfolio,
    addStock,
    updateStock,
    deleteStock,
    clearError,
    getPortfolioWithProfit,
    getPortfolioStats,
  } = usePortfolioStore();
  const navigate = useNavigate();

  // 실시간 시세 통합
  const portfolioSymbols = useMemo(() => items.map((item) => item.symbol), [items]);
  const { isConnected } = useRealtimePrice({
    autoConnect: true,
    autoSubscribe: true,
    symbols: portfolioSymbols,
  });

  // 초기 시세 조회 (거래 시간 외 또는 WebSocket 연결 전)
  useInitialStockPrices({
    symbols: portfolioSymbols,
    enabled: portfolioSymbols.length > 0,
  });

  // 실시간 평가금액이 계산된 포트폴리오 (Phase 2.2.1)
  const portfolioWithProfit = useMemo(() => getPortfolioWithProfit(), [items, isConnected]);
  const portfolioStats = useMemo(() => getPortfolioStats(), [items, isConnected]);

  // 추가/수정 폼 상태
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [symbol, setSymbol] = useState('');
  const [name, setName] = useState('');
  const [quantity, setQuantity] = useState(0);
  const [avgPrice, setAvgPrice] = useState(0);

  // 정렬 상태 (Phase 2.2.2)
  type SortKey = 'name' | 'qty' | 'avgPrice' | 'currentPrice' | 'investment' | 'evaluation' | 'profit' | 'profitRate';
  type SortOrder = 'asc' | 'desc';
  const [sortKey, setSortKey] = useState<SortKey>('profitRate');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  // 정렬된 포트폴리오 (Phase 2.2.2)
  const sortedPortfolio = useMemo(() => {
    const sorted = [...portfolioWithProfit];
    sorted.sort((a, b) => {
      let aVal: number | string = 0;
      let bVal: number | string = 0;

      switch (sortKey) {
        case 'name':
          aVal = a.symbol_name;
          bVal = b.symbol_name;
          break;
        case 'qty':
          aVal = a.qty;
          bVal = b.qty;
          break;
        case 'avgPrice':
          aVal = a.avg_price;
          bVal = b.avg_price;
          break;
        case 'currentPrice':
          aVal = a.currentPrice || 0;
          bVal = b.currentPrice || 0;
          break;
        case 'investment':
          aVal = a.investment;
          bVal = b.investment;
          break;
        case 'evaluation':
          aVal = a.evaluation;
          bVal = b.evaluation;
          break;
        case 'profit':
          aVal = a.profit;
          bVal = b.profit;
          break;
        case 'profitRate':
          aVal = a.profitRate;
          bVal = b.profitRate;
          break;
      }

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }

      return sortOrder === 'asc' ? (aVal as number) - (bVal as number) : (bVal as number) - (aVal as number);
    });

    return sorted;
  }, [portfolioWithProfit, sortKey, sortOrder]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('desc');
    }
  };

  // 포트폴리오 로드
  useEffect(() => {
    if (user) {
      fetchPortfolio(user.id);
    }
  }, [user, fetchPortfolio]);

  const handleAddStock = async () => {
    if (!user) return;

    try {
      clearError();
      await addStock(user.id, symbol, name, quantity, avgPrice);
      setIsAdding(false);
      resetForm();
      alert('종목이 추가되었습니다.');
    } catch (err) {
      console.error('종목 추가 실패:', err);
    }
  };

  const handleUpdateStock = async () => {
    if (!editingId) return;

    try {
      clearError();
      await updateStock(editingId, quantity, avgPrice);
      setEditingId(null);
      resetForm();
      alert('종목이 수정되었습니다.');
    } catch (err) {
      console.error('종목 수정 실패:', err);
    }
  };

  const handleDeleteStock = async (id: string, stockName: string) => {
    if (!confirm(`${stockName}을(를) 삭제하시겠습니까?`)) return;

    try {
      clearError();
      await deleteStock(id);
      alert('종목이 삭제되었습니다.');
    } catch (err) {
      console.error('종목 삭제 실패:', err);
    }
  };

  const startEdit = (item: PortfolioItem) => {
    setEditingId(item.id);
    setSymbol(item.symbol);
    setName(item.symbol_name);
    setQuantity(item.qty);
    setAvgPrice(item.avg_price);
    setIsAdding(false);
  };

  const resetForm = () => {
    setSymbol('');
    setName('');
    setQuantity(0);
    setAvgPrice(0);
    setIsAdding(false);
    setEditingId(null);
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
            <h1 className="text-2xl font-bold text-gray-900">💼 보유 종목 관리</h1>
            <p className="text-lg text-gray-600">{user?.email}</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => navigate('/dashboard')} className="btn btn-secondary">
              대시보드
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

        {/* 포트폴리오 요약 */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold">📊 포트폴리오 요약</h2>
            {isConnected && (
              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                실시간 연동 중
              </span>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">보유 종목 수</div>
              <div className="text-2xl font-bold text-blue-600">{items.length}개</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">총 투자금액</div>
              <div className="text-2xl font-bold text-green-600">
                {formatPrice(portfolioStats.totalInvestment)}원
              </div>
            </div>
            <div className="bg-indigo-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600 flex items-center gap-1">
                평가금액
                {isConnected && <span className="text-xs text-indigo-500">(실시간)</span>}
              </div>
              <div className="text-2xl font-bold text-indigo-600">
                {formatPrice(portfolioStats.totalEvaluation)}원
              </div>
            </div>
            <div className={`p-4 rounded-lg ${
              portfolioStats.totalProfit > 0 ? 'bg-red-50' :
              portfolioStats.totalProfit < 0 ? 'bg-blue-50' :
              'bg-gray-50'
            }`}>
              <div className="text-sm text-gray-600 flex items-center gap-1">
                평가손익
                {isConnected && <span className="text-xs text-gray-500">(실시간)</span>}
              </div>
              <div className={`text-2xl font-bold ${
                portfolioStats.totalProfit > 0 ? 'text-red-600' :
                portfolioStats.totalProfit < 0 ? 'text-blue-600' :
                'text-gray-600'
              }`}>
                {portfolioStats.totalProfit > 0 ? '+' : ''}
                {formatPrice(portfolioStats.totalProfit)}원
              </div>
              <div className={`text-sm mt-1 ${
                portfolioStats.totalProfit > 0 ? 'text-red-600' :
                portfolioStats.totalProfit < 0 ? 'text-blue-600' :
                'text-gray-600'
              }`}>
                {portfolioStats.profitRate > 0 ? '+' : ''}
                {portfolioStats.profitRate.toFixed(2)}%
              </div>
            </div>
          </div>
        </div>

        {/* 종목 추가 버튼 */}
        {!isAdding && !editingId && (
          <div className="card">
            <button onClick={() => setIsAdding(true)} className="btn btn-primary w-full">
              ➕ 종목 추가
            </button>
          </div>
        )}

        {/* 종목 추가/수정 폼 */}
        {(isAdding || editingId) && (
          <div className="card">
            <h2 className="text-2xl font-bold mb-4">
              {editingId ? '📝 종목 수정' : '➕ 종목 추가'}
            </h2>
            <div className="space-y-4">
              {!editingId ? (
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
              ) : (
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="text-sm text-gray-600">수정 중인 종목:</div>
                  <div className="text-xl font-bold text-gray-900">
                    {name} ({symbol})
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-lg font-medium text-gray-700 mb-2">
                    보유 수량
                  </label>
                  <input
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(Number(e.target.value))}
                    className="input"
                    placeholder="10"
                    min="0"
                  />
                </div>
                <div>
                  <label className="block text-lg font-medium text-gray-700 mb-2">
                    평균 단가
                  </label>
                  <input
                    type="number"
                    value={avgPrice}
                    onChange={(e) => setAvgPrice(Number(e.target.value))}
                    className="input"
                    placeholder="70000"
                    min="0"
                  />
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={editingId ? handleUpdateStock : handleAddStock}
                  disabled={loading || !symbol || !name || quantity <= 0 || avgPrice <= 0}
                  className="btn btn-primary flex-1"
                >
                  {loading ? '처리 중...' : editingId ? '수정' : '추가'}
                </button>
                <button onClick={resetForm} className="btn btn-secondary flex-1">
                  취소
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 보유 종목 목록 */}
        <div className="card">
          <h2 className="text-2xl font-bold mb-4">📈 보유 종목 목록</h2>
          {loading && items.length === 0 ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-lg text-gray-600">로딩 중...</p>
            </div>
          ) : items.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-xl text-gray-600">보유 종목이 없습니다.</p>
              <p className="text-lg text-gray-500 mt-2">종목을 추가해보세요!</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th
                      className="px-4 py-3 text-left text-sm font-bold text-gray-700 cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('name')}
                    >
                      종목명 {sortKey === 'name' && (sortOrder === 'asc' ? '▲' : '▼')}
                    </th>
                    <th
                      className="px-4 py-3 text-right text-sm font-bold text-gray-700 cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('qty')}
                    >
                      보유수량 {sortKey === 'qty' && (sortOrder === 'asc' ? '▲' : '▼')}
                    </th>
                    <th
                      className="px-4 py-3 text-right text-sm font-bold text-gray-700 cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('avgPrice')}
                    >
                      평균단가 {sortKey === 'avgPrice' && (sortOrder === 'asc' ? '▲' : '▼')}
                    </th>
                    <th
                      className="px-4 py-3 text-right text-sm font-bold text-gray-700 cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('currentPrice')}
                    >
                      현재가 {sortKey === 'currentPrice' && (sortOrder === 'asc' ? '▲' : '▼')}
                      {isConnected && <div className="text-xs text-green-600 font-normal">(실시간)</div>}
                    </th>
                    <th
                      className="px-4 py-3 text-right text-sm font-bold text-gray-700 cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('investment')}
                    >
                      투자금액 {sortKey === 'investment' && (sortOrder === 'asc' ? '▲' : '▼')}
                    </th>
                    <th
                      className="px-4 py-3 text-right text-sm font-bold text-gray-700 cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('evaluation')}
                    >
                      평가금액 {sortKey === 'evaluation' && (sortOrder === 'asc' ? '▲' : '▼')}
                      {isConnected && <div className="text-xs text-green-600 font-normal">(실시간)</div>}
                    </th>
                    <th
                      className="px-4 py-3 text-right text-sm font-bold text-gray-700 cursor-pointer hover:bg-gray-100"
                      onClick={() => handleSort('profitRate')}
                    >
                      손익률 {sortKey === 'profitRate' && (sortOrder === 'asc' ? '▲' : '▼')}
                      {isConnected && <div className="text-xs text-green-600 font-normal">(실시간)</div>}
                    </th>
                    <th className="px-4 py-3 text-center text-sm font-bold text-gray-700">관리</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {sortedPortfolio.map((item) => {
                    const { getPrice } = usePriceStore.getState();
                    const priceData = getPrice(item.symbol);

                    return (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div className="font-medium text-gray-900">{item.symbol_name}</div>
                          <div className="text-xs text-gray-500">{item.symbol}</div>
                        </td>
                        <td className="px-4 py-3 text-right">{item.qty.toLocaleString()}주</td>
                        <td className="px-4 py-3 text-right">{formatPrice(item.avg_price)}원</td>
                        <td className="px-4 py-3 text-right">
                          {item.currentPrice ? (
                            <div>
                              <div className="font-medium">{formatPrice(item.currentPrice)}원</div>
                              {priceData && (
                                <div className={`text-xs ${getChangeRateColor(priceData.change_rate)}`}>
                                  {formatChangeRate(priceData.change_rate)}
                                </div>
                              )}
                            </div>
                          ) : (
                            <div className="text-gray-400 text-sm">대기 중</div>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right">{formatPrice(item.investment)}원</td>
                        <td className="px-4 py-3 text-right font-medium">
                          {formatPrice(item.evaluation)}원
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className={`font-bold ${
                            item.profit > 0 ? 'text-red-600' :
                            item.profit < 0 ? 'text-blue-600' :
                            'text-gray-600'
                          }`}>
                            {item.profit > 0 ? '+' : ''}{formatPrice(item.profit)}원
                          </div>
                          <div className={`text-xs ${
                            item.profit > 0 ? 'text-red-600' :
                            item.profit < 0 ? 'text-blue-600' :
                            'text-gray-600'
                          }`}>
                            {item.profitRate > 0 ? '+' : ''}{item.profitRate.toFixed(2)}%
                          </div>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <div className="flex gap-2 justify-center">
                            <button
                              onClick={() => startEdit(item)}
                              className="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm"
                            >
                              수정
                            </button>
                            <button
                              onClick={() => handleDeleteStock(item.id, item.symbol_name)}
                              className="px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 text-sm"
                            >
                              삭제
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
