/**
 * 실시간 주가 자동 갱신 Hook
 * 1초마다 HTTP 폴링으로 가격 업데이트
 */
import { useEffect, useRef } from 'react';
import { usePriceStore } from '../stores/priceStore';

export function useRealtimePrices(symbols: string[], enabled: boolean = true) {
  const { fetchPrices } = usePriceStore();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // 종목이 없거나 비활성화 시 중단
    if (!enabled || symbols.length === 0) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    // 즉시 1회 실행
    fetchPrices(symbols);

    // 1초마다 자동 갱신
    intervalRef.current = setInterval(() => {
      fetchPrices(symbols);
    }, 1000);

    // cleanup
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [symbols.join(','), enabled, fetchPrices]); // symbols 배열 의존성

  return usePriceStore();
}
