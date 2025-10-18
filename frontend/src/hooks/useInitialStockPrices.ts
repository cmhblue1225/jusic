/**
 * 초기 주식 시세 조회 훅
 * 거래 시간 외 또는 WebSocket 연결 전에 최신 종가를 표시하기 위함
 */

import { useEffect, useState } from 'react';
import { kisApiClient } from '../lib/kisApi';
import { usePriceStore } from '../stores/priceStore';

export interface UseInitialStockPricesOptions {
  symbols: string[];
  enabled?: boolean;
}

export const useInitialStockPrices = (options: UseInitialStockPricesOptions) => {
  const { symbols, enabled = true } = options;
  const { updatePrice } = usePriceStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled || symbols.length === 0) {
      return;
    }

    const fetchInitialPrices = async () => {
      setLoading(true);
      setError(null);

      try {
        console.log(`[useInitialStockPrices] ${symbols.length}개 종목 초기 시세 조회 시작...`);

        const quotes = await kisApiClient.getMultipleStockPrices(symbols);

        console.log(`[useInitialStockPrices] ${quotes.size}개 종목 시세 조회 완료`);

        // priceStore에 초기 시세 저장
        quotes.forEach((quote, symbol) => {
          updatePrice({
            symbol,
            price: quote.price,
            change: quote.change,
            change_rate: quote.change_rate,
            volume: quote.volume,
            timestamp: new Date().toISOString(),
          });
        });

        setLoading(false);
      } catch (err) {
        console.error('[useInitialStockPrices] 초기 시세 조회 실패:', err);
        setError(err instanceof Error ? err.message : '시세 조회 실패');
        setLoading(false);
      }
    };

    fetchInitialPrices();
  }, [symbols.join(','), enabled, updatePrice]);

  return {
    loading,
    error,
  };
};
