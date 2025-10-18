/**
 * 한국투자증권 REST API 클라이언트 (Backend Proxy)
 * CORS 문제 해결을 위해 백엔드 API를 통해 KIS API 호출
 */

const STREAM_SERVICE_URL = 'http://localhost:3001';

export interface StockQuote {
  symbol: string;
  name?: string;
  price: number;
  change: number;
  change_rate: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  prev_close?: number;
  timestamp?: string;
}

class KisApiClient {
  /**
   * 복수 종목 현재가 일괄 조회
   * @param symbols 종목코드 배열
   */
  async getMultipleStockPrices(symbols: string[]): Promise<Map<string, StockQuote>> {
    const results = new Map<string, StockQuote>();

    if (symbols.length === 0) {
      return results;
    }

    try {
      console.log(`[KIS API] ${symbols.length}개 종목 시세 조회 요청...`);

      const response = await fetch(`${STREAM_SERVICE_URL}/api/stocks/prices`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbols: symbols,
        }),
      });

      if (!response.ok) {
        throw new Error(`백엔드 API 호출 실패: ${response.status}`);
      }

      const data = await response.json();

      if (data.success && data.data) {
        for (const stock of data.data) {
          results.set(stock.symbol, {
            symbol: stock.symbol,
            name: stock.name,
            price: stock.price,
            change: stock.change,
            change_rate: stock.change_rate,
            volume: stock.volume,
            high: stock.high,
            low: stock.low,
            open: stock.open,
            prev_close: stock.prev_close,
            timestamp: stock.timestamp,
          });
        }

        console.log(`[KIS API] ${results.size}개 종목 시세 조회 완료`);
      }

      if (data.errors && data.errors.length > 0) {
        console.warn(`[KIS API] 일부 종목 조회 실패:`, data.errors);
      }

      return results;

    } catch (error) {
      console.error('[KIS API] 복수 종목 현재가 조회 실패:', error);
      return results; // 빈 Map 반환
    }
  }
}

// 싱글톤 인스턴스
export const kisApiClient = new KisApiClient();
