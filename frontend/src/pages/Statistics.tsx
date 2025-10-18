import { useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { usePortfolioStore } from '../stores/portfolioStore';
import { useRealtimePrice } from '../hooks/useRealtimePrice';
import { useInitialStockPrices } from '../hooks/useInitialStockPrices';
import {
  getProfitColor,
  formatProfitRate,
  formatCurrency,
  type PortfolioWithProfit,
} from '../lib/profitCalculator';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

// 차트 색상
const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'];

export default function Statistics() {
  const { user, signOut } = useAuthStore();
  const {
    items: portfolioItems,
    loading,
    fetchPortfolio,
    getPortfolioWithProfit,
    getPortfolioStats,
  } = usePortfolioStore();
  const navigate = useNavigate();

  // 실시간 시세 통합 (Phase 2.2.2)
  const portfolioSymbols = useMemo(() => portfolioItems.map((item: { symbol: string }) => item.symbol), [portfolioItems]);
  const { isConnected } = useRealtimePrice({
    autoConnect: true,
    autoSubscribe: true,
    symbols: portfolioSymbols,
  });

  // 초기 시세 조회
  useInitialStockPrices({
    symbols: portfolioSymbols,
    enabled: portfolioSymbols.length > 0,
  });

  // 포트폴리오 로드
  useEffect(() => {
    if (user) {
      fetchPortfolio(user.id);
    }
  }, [user, fetchPortfolio]);

  // 실시간 수익률 계산 (Phase 2.2.2)
  const portfolioWithProfit = useMemo(() => getPortfolioWithProfit(), [portfolioItems, isConnected]);
  const portfolioStats = useMemo(() => getPortfolioStats(), [portfolioItems, isConnected]);

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
            <h1 className="text-2xl font-bold text-gray-900">📊 수익률 통계</h1>
            <p className="text-lg text-gray-600">{user?.email}</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => navigate('/dashboard')} className="btn btn-secondary">
              대시보드
            </button>
            <button onClick={() => navigate('/portfolio')} className="btn btn-secondary">
              보유 종목
            </button>
            <button onClick={handleSignOut} className="btn btn-danger">
              로그아웃
            </button>
          </div>
        </div>
      </div>

      {/* 메인 콘텐츠 */}
      <div className="max-w-6xl mx-auto space-y-6">
        {/* 전체 포트폴리오 요약 */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold">💰 전체 포트폴리오</h2>
            {isConnected && (
              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                실시간 연동 중
              </span>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-lg text-gray-600">총 투자금액</div>
              <div className="text-2xl font-bold text-gray-900">
                {formatCurrency(portfolioStats.totalInvestment)}원
              </div>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-lg text-gray-600 flex items-center gap-1">
                총 평가금액
                {isConnected && <span className="text-xs text-blue-500">(실시간)</span>}
              </div>
              <div className="text-2xl font-bold text-blue-600">
                {formatCurrency(portfolioStats.totalEvaluation)}원
              </div>
            </div>
            <div className={`p-4 rounded-lg ${portfolioStats.totalProfit >= 0 ? 'bg-red-50' : 'bg-blue-50'}`}>
              <div className="text-lg text-gray-600 flex items-center gap-1">
                총 평가손익
                {isConnected && <span className="text-xs text-gray-500">(실시간)</span>}
              </div>
              <div className={`text-2xl font-bold ${getProfitColor(portfolioStats.totalProfit)}`}>
                {portfolioStats.totalProfit >= 0 ? '+' : ''}
                {formatCurrency(portfolioStats.totalProfit)}원
              </div>
            </div>
            <div className={`p-4 rounded-lg ${portfolioStats.profitRate >= 0 ? 'bg-red-50' : 'bg-blue-50'}`}>
              <div className="text-lg text-gray-600 flex items-center gap-1">
                수익률
                {isConnected && <span className="text-xs text-gray-500">(실시간)</span>}
              </div>
              <div className={`text-3xl font-bold ${getProfitColor(portfolioStats.profitRate)}`}>
                {formatProfitRate(portfolioStats.profitRate)}
              </div>
            </div>
          </div>
        </div>

        {/* 종목별 수익률 */}
        <div className="card">
          <h2 className="text-2xl font-bold mb-4">📈 종목별 수익률</h2>
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-lg text-gray-600">로딩 중...</p>
            </div>
          ) : portfolioWithProfit.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-xl text-gray-600">보유 종목이 없습니다.</p>
              <button
                onClick={() => navigate('/portfolio')}
                className="btn btn-primary mt-4"
              >
                종목 추가하기
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-lg font-bold">종목</th>
                    <th className="px-4 py-3 text-right text-lg font-bold">보유수량</th>
                    <th className="px-4 py-3 text-right text-lg font-bold">평균단가</th>
                    <th className="px-4 py-3 text-right text-lg font-bold">현재가</th>
                    <th className="px-4 py-3 text-right text-lg font-bold">투자금액</th>
                    <th className="px-4 py-3 text-right text-lg font-bold">평가금액</th>
                    <th className="px-4 py-3 text-right text-lg font-bold">평가손익</th>
                    <th className="px-4 py-3 text-right text-lg font-bold">수익률</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {portfolioWithProfit.map((stock: PortfolioWithProfit) => (
                    <tr key={stock.symbol} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <div className="font-bold text-lg">{stock.symbol_name}</div>
                        <div className="text-sm text-gray-500">{stock.symbol}</div>
                      </td>
                      <td className="px-4 py-3 text-right text-lg">
                        {formatCurrency(stock.qty)}주
                      </td>
                      <td className="px-4 py-3 text-right text-lg">
                        {formatCurrency(stock.avg_price)}원
                      </td>
                      <td className="px-4 py-3 text-right text-lg font-bold">
                        {stock.currentPrice ? formatCurrency(stock.currentPrice) : '-'}원
                      </td>
                      <td className="px-4 py-3 text-right text-lg">
                        {formatCurrency(stock.investment)}원
                      </td>
                      <td className="px-4 py-3 text-right text-lg font-bold text-blue-600">
                        {formatCurrency(stock.evaluation)}원
                      </td>
                      <td className={`px-4 py-3 text-right text-lg font-bold ${getProfitColor(stock.profit)}`}>
                        {stock.profit >= 0 ? '+' : ''}
                        {formatCurrency(stock.profit)}원
                      </td>
                      <td className={`px-4 py-3 text-right text-xl font-bold ${getProfitColor(stock.profitRate)}`}>
                        {formatProfitRate(stock.profitRate)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* 수익률 바 차트 (Phase 2.2.2) */}
        {portfolioWithProfit.length > 0 && (
          <div className="card">
            <h2 className="text-2xl font-bold mb-4">📊 종목별 수익률 차트</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={portfolioWithProfit}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="symbol" />
                <YAxis />
                <Tooltip
                  formatter={(value: number) => `${value.toFixed(2)}%`}
                  labelFormatter={(label) => `${label}`}
                />
                <Legend />
                <Bar dataKey="profitRate" name="수익률 (%)" fill="#3B82F6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* 종목별 비중 파이 차트 (Phase 2.2.2) */}
        {portfolioWithProfit.length > 0 && (
          <div className="card">
            <h2 className="text-2xl font-bold mb-4">🥧 종목별 투자 비중</h2>
            <ResponsiveContainer width="100%" height={400}>
              <PieChart>
                <Pie
                  data={portfolioWithProfit}
                  dataKey="investment"
                  nameKey="symbol_name"
                  cx="50%"
                  cy="50%"
                  outerRadius={120}
                  label={(entry: any) => `${entry.symbol_name}: ${((entry.investment / portfolioStats.totalInvestment) * 100).toFixed(1)}%`}
                >
                  {portfolioWithProfit.map((_entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number) => `${formatCurrency(value)}원`}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
