/**
 * 실시간 시세 커스텀 훅
 * Socket.IO와 priceStore를 통합하여 실시간 시세 관리
 */

import { useEffect, useRef } from 'react';
import { socketService } from '../lib/socket';
import { usePriceStore, type RealtimeStockData } from '../stores/priceStore';
import { useAuthStore } from '../stores/authStore';

export interface UseRealtimePriceOptions {
  /**
   * 자동 연결 여부 (기본값: true)
   */
  autoConnect?: boolean;

  /**
   * 자동 구독 여부 (기본값: true)
   * false일 경우 수동으로 subscribe() 호출 필요
   */
  autoSubscribe?: boolean;

  /**
   * 구독할 종목 코드 배열
   */
  symbols?: string[];
}

/**
 * 실시간 시세 훅
 */
export const useRealtimePrice = (options: UseRealtimePriceOptions = {}) => {
  const { autoConnect = true, autoSubscribe = true, symbols = [] } = options;

  const { session } = useAuthStore();
  const {
    isConnected,
    setConnected,
    updatePrice,
    addSubscribedSymbol,
    removeSubscribedSymbol,
    clearSubscribedSymbols,
    subscribedSymbols,
  } = usePriceStore();

  const isInitialized = useRef(false);

  /**
   * WebSocket 연결
   */
  useEffect(() => {
    if (!autoConnect || !session?.access_token) {
      return;
    }

    if (isInitialized.current) {
      return;
    }

    console.log('[useRealtimePrice] WebSocket 연결 시작...');

    // Socket.IO 연결
    socketService.connect(session.access_token);

    // 실시간 시세 업데이트 리스너 등록
    socketService.onStockUpdate((data) => {
      console.log('[useRealtimePrice] 시세 업데이트:', data);
      updatePrice(data);
    });

    // 연결 상태 감지
    const checkConnection = setInterval(() => {
      const connected = socketService.isConnected();
      setConnected(connected);

      if (!connected && isInitialized.current) {
        console.warn('[useRealtimePrice] WebSocket 연결 끊김');
      }
    }, 1000);

    isInitialized.current = true;

    // Cleanup
    return () => {
      clearInterval(checkConnection);
      socketService.offStockUpdate();
    };
  }, [autoConnect, session, setConnected, updatePrice]);

  /**
   * 자동 구독
   */
  useEffect(() => {
    if (!autoSubscribe || !isConnected || symbols.length === 0) {
      return;
    }

    console.log('[useRealtimePrice] 자동 구독:', symbols);

    // 구독
    socketService.subscribe(symbols);

    // 구독 목록에 추가
    symbols.forEach((symbol) => {
      addSubscribedSymbol(symbol);
    });

    // Cleanup: 구독 해제
    return () => {
      socketService.unsubscribe(symbols);
      symbols.forEach((symbol) => {
        removeSubscribedSymbol(symbol);
      });
    };
  }, [autoSubscribe, isConnected, symbols, addSubscribedSymbol, removeSubscribedSymbol]);

  /**
   * 수동 구독
   */
  const subscribe = (symbolsToSubscribe: string[]) => {
    if (!isConnected) {
      console.warn('[useRealtimePrice] WebSocket이 연결되어 있지 않습니다.');
      return;
    }

    socketService.subscribe(symbolsToSubscribe);
    symbolsToSubscribe.forEach((symbol) => {
      addSubscribedSymbol(symbol);
    });
  };

  /**
   * 수동 구독 해제
   */
  const unsubscribe = (symbolsToUnsubscribe: string[]) => {
    if (!isConnected) {
      console.warn('[useRealtimePrice] WebSocket이 연결되어 있지 않습니다.');
      return;
    }

    socketService.unsubscribe(symbolsToUnsubscribe);
    symbolsToUnsubscribe.forEach((symbol) => {
      removeSubscribedSymbol(symbol);
    });
  };

  /**
   * 연결 해제
   */
  const disconnect = () => {
    socketService.disconnect();
    clearSubscribedSymbols();
    setConnected(false);
    isInitialized.current = false;
  };

  return {
    isConnected,
    subscribedSymbols: Array.from(subscribedSymbols),
    subscribe,
    unsubscribe,
    disconnect,
  };
};

/**
 * 단일 종목 실시간 시세 훅
 */
export const useStockPrice = (symbol: string) => {
  const { getPrice, getPriceHistory } = usePriceStore();
  const { isConnected, subscribe, unsubscribe } = useRealtimePrice({
    autoConnect: true,
    autoSubscribe: false,
  });

  // 해당 종목 구독
  useEffect(() => {
    if (!isConnected || !symbol) return;

    subscribe([symbol]);

    return () => {
      unsubscribe([symbol]);
    };
  }, [isConnected, symbol, subscribe, unsubscribe]);

  const price = getPrice(symbol);
  const history = getPriceHistory(symbol);

  return {
    price,
    history,
    isConnected,
  };
};
