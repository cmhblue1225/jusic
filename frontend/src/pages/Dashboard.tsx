import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { supabase } from '../lib/supabase';
import { useRealtimePrice } from '../hooks/useRealtimePrice';
import { useInitialStockPrices } from '../hooks/useInitialStockPrices';
import { usePriceStore, formatPrice, formatChangeRate, getChangeRateColor } from '../stores/priceStore';

interface StockSymbol {
  symbol: string;
  symbol_name?: string;
}

export default function Dashboard() {
  const { user, signOut } = useAuthStore();
  const navigate = useNavigate();
  const [newsCount, setNewsCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [userSymbols, setUserSymbols] = useState<string[]>([]);
  const [stockNames, setStockNames] = useState<Map<string, string>>(new Map());
  const [showAllStocks, setShowAllStocks] = useState(false);

  const { getPrice } = usePriceStore();
  const { isConnected, subscribedSymbols } = useRealtimePrice({
    autoConnect: true,
    autoSubscribe: true,
    symbols: userSymbols,
  });

  // 초기 시세 조회 (거래 시간 외 또는 WebSocket 연결 전)
  useInitialStockPrices({
    symbols: userSymbols,
    enabled: userSymbols.length > 0,
  });

  // 사용자의 포트폴리오 + 관심종목 가져오기
  useEffect(() => {
    async function fetchUserStocks() {
      if (!user) return;

      const [portfolioResult, watchlistResult, newsResult] = await Promise.all([
        supabase.from('portfolios').select('symbol, symbol_name').eq('user_id', user.id),
        supabase.from('watchlist').select('symbol, symbol_name').eq('user_id', user.id),
        supabase.from('news').select('id', { count: 'exact', head: true }),
      ]);

      // 뉴스 개수
      if (!newsResult.error) {
        setNewsCount(newsResult.count || 0);
      }

      // 포트폴리오 + 관심종목 합치기
      const portfolioStocks: StockSymbol[] = portfolioResult.data || [];
      const watchlistStocks: StockSymbol[] = watchlistResult.data || [];

      const allStocks = [...portfolioStocks, ...watchlistStocks];
      const uniqueSymbols = Array.from(new Set(allStocks.map((s) => s.symbol)));

      // 종목명 매핑
      const names = new Map<string, string>();
      allStocks.forEach((stock) => {
        if (stock.symbol_name && !names.has(stock.symbol)) {
          names.set(stock.symbol, stock.symbol_name);
        }
      });

      setUserSymbols(uniqueSymbols);
      setStockNames(names);
      setLoading(false);
    }

    fetchUserStocks();
  }, [user]);

  const handleSignOut = async () => {
    await signOut();
    navigate('/login');
  };

  const handleGoToProfile = () => {
    navigate('/profile');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      {/* 헤더 */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="bg-white rounded-lg shadow-md p-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              📈 실시간 트레이딩 인텔리전스 플랫폼
            </h1>
            <p className="text-lg text-gray-600">
              환영합니다, {user?.user_metadata?.name || user?.email}님!
            </p>
            {/* WebSocket 연결 상태 */}
            <div className="flex items-center gap-2 mt-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
              <span className="text-sm text-gray-600">
                {isConnected ? '실시간 시세 연결됨' : '실시간 시세 연결 끊김'}
              </span>
              {subscribedSymbols.length > 0 && (
                <span className="text-xs text-gray-500">
                  ({subscribedSymbols.length}개 종목 구독 중)
                </span>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={handleGoToProfile} className="btn btn-secondary">
              ⚙️ 프로필 설정
            </button>
            <button onClick={handleSignOut} className="btn btn-secondary">
              로그아웃
            </button>
          </div>
        </div>
      </div>

      {/* 메인 콘텐츠 */}
      <div className="max-w-7xl mx-auto">
        <div className="card">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-blue-50 p-6 rounded-lg">
              <div className="text-3xl font-bold text-blue-600">✅</div>
              <div className="text-lg font-medium mt-2">Supabase 연결</div>
            </div>

            <div className="bg-green-50 p-6 rounded-lg">
              <div className="text-3xl font-bold text-green-600">
                {loading ? '...' : newsCount}
              </div>
              <div className="text-lg font-medium mt-2">뉴스 데이터</div>
            </div>

            <div className="bg-purple-50 p-6 rounded-lg">
              <div className="text-3xl font-bold text-purple-600">
                {isConnected ? '✅' : '⚠️'}
              </div>
              <div className="text-lg font-medium mt-2">실시간 시세</div>
            </div>
          </div>

          {/* 실시간 시세 섹션 */}
          {userSymbols.length > 0 && (
            <div className="mb-8 bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg">
              <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                📊 실시간 시세
                {isConnected && (
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                    LIVE
                  </span>
                )}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {(showAllStocks ? userSymbols : userSymbols.slice(0, 6)).map((symbol) => {
                  const priceData = getPrice(symbol);
                  const stockName = stockNames.get(symbol) || symbol;

                  return (
                    <div key={symbol} className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="font-medium text-gray-900">{stockName}</div>
                          <div className="text-xs text-gray-500">{symbol}</div>
                        </div>
                        {priceData && (
                          <div className={`text-xs px-2 py-1 rounded ${
                            priceData.change_rate > 0 ? 'bg-red-50 text-red-600' :
                            priceData.change_rate < 0 ? 'bg-blue-50 text-blue-600' :
                            'bg-gray-50 text-gray-600'
                          }`}>
                            {formatChangeRate(priceData.change_rate)}
                          </div>
                        )}
                      </div>

                      {priceData ? (
                        <div className="space-y-1">
                          <div className="text-2xl font-bold text-gray-900">
                            {formatPrice(priceData.price)}원
                          </div>
                          <div className={`text-sm ${getChangeRateColor(priceData.change_rate)}`}>
                            {priceData.change > 0 ? '▲' : priceData.change < 0 ? '▼' : '─'} {formatPrice(Math.abs(priceData.change))}원
                          </div>
                          <div className="text-xs text-gray-500">
                            {new Date(priceData.updatedAt).toLocaleTimeString('ko-KR')}
                          </div>
                        </div>
                      ) : (
                        <div className="text-sm text-gray-400">시세 대기 중...</div>
                      )}
                    </div>
                  );
                })}
              </div>
              {userSymbols.length > 6 && (
                <div className="mt-4 text-center">
                  <button
                    onClick={() => setShowAllStocks(!showAllStocks)}
                    className="px-6 py-2 bg-white text-indigo-600 rounded-lg shadow-sm hover:shadow-md transition-all font-medium"
                  >
                    {showAllStocks ? '접기 ▲' : `더보기 ▼ (${userSymbols.length - 6}개 종목)`}
                  </button>
                </div>
              )}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <button onClick={() => navigate('/portfolio')} className="btn btn-primary">
                💼 보유 종목 관리
              </button>
              <button onClick={() => navigate('/watchlist')} className="btn btn-primary">
                ⭐ 관심 종목 관리
              </button>
              <button onClick={() => navigate('/news')} className="btn btn-primary">
                📰 뉴스 센터
              </button>
              <button onClick={() => navigate('/statistics')} className="btn btn-primary">
                📊 수익률 통계
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
