/**
 * 실시간 시세 상태 관리 Store
 * Socket.IO를 통해 받은 실시간 주가 데이터 관리
 */

import { create } from 'zustand';

// 실시간 주가 데이터 인터페이스
export interface RealtimeStockData {
  symbol: string;
  price: number;
  change: number;
  change_rate: number;
  volume: number;
  timestamp: string;
}

export interface StockPrice extends RealtimeStockData {
  // 추가 계산 필드
  prevPrice?: number; // 이전 가격 (등락 애니메이션용)
  updatedAt: Date;    // 마지막 업데이트 시각
}

interface PriceHistory {
  timestamp: string;
  price: number;
  volume: number;
}

interface PriceStoreState {
  // 종목별 실시간 시세 (key: symbol)
  prices: Map<string, StockPrice>;

  // 종목별 히스토리 (최근 100개)
  history: Map<string, PriceHistory[]>;

  // WebSocket 연결 상태
  isConnected: boolean;

  // 구독 중인 종목 목록
  subscribedSymbols: Set<string>;

  // HTTP 폴링 상태
  loading: boolean;
  error: string | null;

  // Actions
  setConnected: (connected: boolean) => void;
  updatePrice: (data: RealtimeStockData) => void;
  getPrice: (symbol: string) => StockPrice | undefined;
  getPriceHistory: (symbol: string) => PriceHistory[];
  clearPrices: () => void;
  addSubscribedSymbol: (symbol: string) => void;
  removeSubscribedSymbol: (symbol: string) => void;
  clearSubscribedSymbols: () => void;

  // HTTP 폴링 (WebSocket 대체용)
  fetchPrices: (symbols: string[]) => Promise<void>;
  clearError: () => void;
}

const MAX_HISTORY_LENGTH = 100;

const STREAM_SERVICE_URL = import.meta.env.VITE_STREAM_SERVICE_URL || 'http://localhost:3001';

export const usePriceStore = create<PriceStoreState>((set, get) => ({
  prices: new Map(),
  history: new Map(),
  isConnected: false,
  subscribedSymbols: new Set(),
  loading: false,
  error: null,

  setConnected: (connected) => {
    set({ isConnected: connected });
  },

  updatePrice: (data) => {
    const { prices, history } = get();

    // 이전 가격 저장 (애니메이션용)
    const prevPrice = prices.get(data.symbol)?.price;

    // 새 가격 정보
    const newPrice: StockPrice = {
      ...data,
      prevPrice,
      updatedAt: new Date(),
    };

    // 가격 업데이트
    const newPrices = new Map(prices);
    newPrices.set(data.symbol, newPrice);

    // 히스토리 업데이트
    const symbolHistory = history.get(data.symbol) || [];
    const newHistoryEntry: PriceHistory = {
      timestamp: data.timestamp,
      price: data.price,
      volume: data.volume,
    };

    const updatedHistory = [...symbolHistory, newHistoryEntry];

    // 최근 100개만 유지
    if (updatedHistory.length > MAX_HISTORY_LENGTH) {
      updatedHistory.shift();
    }

    const newHistory = new Map(history);
    newHistory.set(data.symbol, updatedHistory);

    set({
      prices: newPrices,
      history: newHistory,
    });
  },

  getPrice: (symbol) => {
    return get().prices.get(symbol);
  },

  getPriceHistory: (symbol) => {
    return get().history.get(symbol) || [];
  },

  clearPrices: () => {
    set({
      prices: new Map(),
      history: new Map(),
    });
  },

  addSubscribedSymbol: (symbol) => {
    const { subscribedSymbols } = get();
    const newSymbols = new Set(subscribedSymbols);
    newSymbols.add(symbol);
    set({ subscribedSymbols: newSymbols });
  },

  removeSubscribedSymbol: (symbol) => {
    const { subscribedSymbols } = get();
    const newSymbols = new Set(subscribedSymbols);
    newSymbols.delete(symbol);
    set({ subscribedSymbols: newSymbols });
  },

  clearSubscribedSymbols: () => {
    set({ subscribedSymbols: new Set() });
  },

  /**
   * HTTP 폴링 방식 가격 조회 (WebSocket 대체용)
   */
  fetchPrices: async (symbols: string[]) => {
    if (symbols.length === 0) return;

    try {
      set({ loading: true, error: null });

      const response = await fetch(`${STREAM_SERVICE_URL}/api/stocks/prices`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbols }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const result = await response.json();

      if (result.success && result.data) {
        // 각 가격 데이터를 updatePrice로 처리
        result.data.forEach((priceData: RealtimeStockData) => {
          get().updatePrice(priceData);
        });
      }

      set({ loading: false });
    } catch (error: any) {
      console.error('[Price Store] HTTP 폴링 실패:', error);
      set({ error: error.message, loading: false });
    }
  },

  clearError: () => {
    set({ error: null });
  },
}));

/**
 * 가격 변동 방향
 */
export const getPriceDirection = (price: StockPrice): 'up' | 'down' | 'neutral' => {
  if (!price.prevPrice) return 'neutral';
  if (price.price > price.prevPrice) return 'up';
  if (price.price < price.prevPrice) return 'down';
  return 'neutral';
};

/**
 * 등락률 색상
 */
export const getChangeRateColor = (changeRate: number): string => {
  if (changeRate > 0) return 'text-red-600'; // 상승 (빨강)
  if (changeRate < 0) return 'text-blue-600'; // 하락 (파랑)
  return 'text-gray-600'; // 보합
};

/**
 * 등락률 표시 텍스트
 */
export const formatChangeRate = (changeRate: number): string => {
  const sign = changeRate > 0 ? '+' : '';
  return `${sign}${changeRate.toFixed(2)}%`;
};

/**
 * 가격 포맷 (천 단위 구분)
 */
export const formatPrice = (price: number): string => {
  return price.toLocaleString('ko-KR');
};

/**
 * 거래량 포맷 (천 단위 축약)
 */
export const formatVolume = (volume: number): string => {
  if (volume >= 1000000) {
    return `${(volume / 1000000).toFixed(1)}M`;
  } else if (volume >= 1000) {
    return `${(volume / 1000).toFixed(1)}K`;
  }
  return volume.toLocaleString('ko-KR');
};
