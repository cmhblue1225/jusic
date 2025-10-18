/**
 * 한국투자증권 Open API 클라이언트 v2
 * 공식 문서: https://apiportal.koreainvestment.com/
 *
 * 주요 TR_ID:
 * - FHKST01010100: 주식현재가 시세
 * - FHKST01010200: 주식 호가
 * - FHKST01010300: 주식 체결가
 * - FHKST03010100: 주식 일/주/월/년 시세
 */
import axios, { AxiosInstance } from 'axios';
import crypto from 'crypto';
import dotenv from 'dotenv';

dotenv.config();

interface KISTokenResponse {
  access_token: string;
  access_token_token_expired: string;
  token_type: string;
  expires_in: number;
}

interface StockPrice {
  symbol: string;              // 종목코드
  name?: string;               // 종목명
  price: number;               // 현재가
  change: number;              // 전일 대비
  change_rate: number;         // 등락률 (%)
  volume: number;              // 거래량
  high: number;                // 최고가
  low: number;                 // 최저가
  open: number;                // 시가
  prev_close: number;          // 전일 종가
  timestamp: string;
}

interface Orderbook {
  symbol: string;
  asks: Array<{ price: number; qty: number }>;  // 매도 호가
  bids: Array<{ price: number; qty: number }>;  // 매수 호가
  timestamp: string;
}

class KISApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;
  private tokenExpiry: number = 0;
  private appKey: string;
  private appSecret: string;
  private accountNumber: string;
  private accountProductCode: string;

  constructor() {
    this.appKey = process.env.KIS_APP_KEY || '';
    this.appSecret = process.env.KIS_APP_SECRET || '';
    this.accountNumber = process.env.KIS_ACCOUNT_NUMBER || '';
    this.accountProductCode = process.env.KIS_ACCOUNT_PRODUCT_CODE || '01';

    this.client = axios.create({
      baseURL: process.env.KIS_BASE_URL || 'https://openapivts.koreainvestment.com:29443',
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
      },
      timeout: 10000,
    });

    // 요청/응답 로깅
    this.client.interceptors.request.use((config) => {
      console.log(`[KIS API] ${config.method?.toUpperCase()} ${config.url}`);
      return config;
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('[KIS API Error]', error.response?.data || error.message);
        throw error;
      }
    );
  }

  /**
   * 접근 토큰 발급 (OAuth 2.0)
   * POST /oauth2/tokenP
   */
  private async getAccessToken(): Promise<string> {
    // 토큰이 유효하면 재사용 (만료 1분 전까지)
    if (this.accessToken && Date.now() < this.tokenExpiry - 60000) {
      return this.accessToken;
    }

    try {
      console.log('[KIS] 토큰 발급 요청 시작...');
      console.log(`   Base URL: ${this.client.defaults.baseURL}`);

      const response = await this.client.post<KISTokenResponse>('/oauth2/tokenP', {
        grant_type: 'client_credentials',
        appkey: this.appKey,
        appsecret: this.appSecret,
      });

      this.accessToken = response.data.access_token;
      // 토큰 만료 시간 (발급 후 24시간, 하지만 안전하게 23시간으로 설정)
      this.tokenExpiry = Date.now() + 23 * 60 * 60 * 1000;

      console.log('✅ [KIS] 접근 토큰 발급 완료');
      console.log(`   만료 시간: ${new Date(this.tokenExpiry).toLocaleString('ko-KR')}`);

      return this.accessToken;
    } catch (error: any) {
      console.error('❌ [KIS] 토큰 발급 실패:', error.response?.data || error.message);
      throw new Error('KIS API 토큰 발급 실패');
    }
  }

  /**
   * Hashkey 생성 (POST 요청 시 필요)
   */
  private async getHashkey(data: any): Promise<string> {
    try {
      const response = await this.client.post('/uapi/hashkey', data, {
        headers: {
          appkey: this.appKey,
          appsecret: this.appSecret,
        },
      });
      return response.data.HASH;
    } catch (error) {
      console.error('❌ [KIS] Hashkey 생성 실패');
      return '';
    }
  }

  /**
   * 주식 현재가 시세 조회
   * TR_ID: FHKST01010100 (실전투자) / FHKST01010100 (모의투자)
   *
   * @param symbol 종목 코드 (6자리, 예: 005930)
   */
  async getCurrentPrice(symbol: string): Promise<StockPrice> {
    const token = await this.getAccessToken();

    // 종목 코드 6자리 패딩
    const paddedSymbol = symbol.padStart(6, '0');

    try {
      const response = await this.client.get('/uapi/domestic-stock/v1/quotations/inquire-price', {
        headers: {
          'authorization': `Bearer ${token}`,
          'appkey': this.appKey,
          'appsecret': this.appSecret,
          'tr_id': 'FHKST01010100',  // 주식현재가 시세
        },
        params: {
          FID_COND_MRKT_DIV_CODE: 'J',  // J: 주식, ETF, ETN
          FID_INPUT_ISCD: paddedSymbol,
        },
      });

      const output = response.data.output;

      // 응답 데이터 파싱
      return {
        symbol: paddedSymbol,
        name: output.prdt_name,                      // 상품명
        price: parseFloat(output.stck_prpr),          // 주식 현재가
        change: parseFloat(output.prdy_vrss),         // 전일 대비
        change_rate: parseFloat(output.prdy_ctrt),    // 전일 대비율
        volume: parseInt(output.acml_vol),            // 누적 거래량
        high: parseFloat(output.stck_hgpr),           // 최고가
        low: parseFloat(output.stck_lwpr),            // 최저가
        open: parseFloat(output.stck_oprc),           // 시가
        prev_close: parseFloat(output.stck_sdpr),     // 기준가 (전일 종가)
        timestamp: new Date().toISOString(),
      };
    } catch (error: any) {
      console.error(`❌ [KIS] 현재가 조회 실패 (${symbol}):`, error.response?.data?.msg1 || error.message);
      throw error;
    }
  }

  /**
   * 주식 호가 조회
   * TR_ID: FHKST01010200
   */
  async getOrderbook(symbol: string): Promise<Orderbook> {
    const token = await this.getAccessToken();
    const paddedSymbol = symbol.padStart(6, '0');

    try {
      const response = await this.client.get('/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn', {
        headers: {
          'authorization': `Bearer ${token}`,
          'appkey': this.appKey,
          'appsecret': this.appSecret,
          'tr_id': 'FHKST01010200',  // 주식 호가
        },
        params: {
          FID_COND_MRKT_DIV_CODE: 'J',
          FID_INPUT_ISCD: paddedSymbol,
        },
      });

      const output = response.data.output1;

      // 호가 10단계 파싱
      const asks: Array<{ price: number; qty: number }> = [];
      const bids: Array<{ price: number; qty: number }> = [];

      for (let i = 1; i <= 10; i++) {
        const askPrice = parseFloat(output[`askp${i}`]);
        const askQty = parseInt(output[`askp_rsqn${i}`]);
        const bidPrice = parseFloat(output[`bidp${i}`]);
        const bidQty = parseInt(output[`bidp_rsqn${i}`]);

        if (askPrice > 0) asks.push({ price: askPrice, qty: askQty });
        if (bidPrice > 0) bids.push({ price: bidPrice, qty: bidQty });
      }

      return {
        symbol: paddedSymbol,
        asks: asks.reverse(),  // 높은 가격순으로 정렬
        bids,                  // 낮은 가격순으로 정렬
        timestamp: new Date().toISOString(),
      };
    } catch (error: any) {
      console.error(`❌ [KIS] 호가 조회 실패 (${symbol}):`, error.response?.data?.msg1 || error.message);
      throw error;
    }
  }

  /**
   * 복수 종목 현재가 일괄 조회
   */
  async getBatchPrices(symbols: string[]): Promise<StockPrice[]> {
    const results: StockPrice[] = [];

    for (const symbol of symbols) {
      try {
        const price = await this.getCurrentPrice(symbol);
        results.push(price);
        // Rate Limit 방지 (초당 5건 제한 - 모의투자)
        await this.delay(200);  // 200ms 간격
      } catch (error) {
        console.error(`종목 ${symbol} 조회 실패, 스킵`);
      }
    }

    return results;
  }

  /**
   * 딜레이 함수 (Rate Limit 방지)
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 실시간 시세 구독 (폴링 방식)
   * WebSocket은 별도 구현 필요
   */
  subscribeRealtime(symbols: string[], callback: (data: StockPrice) => void, intervalMs: number = 1000) {
    console.log(`📡 [KIS] 실시간 시세 구독 시작 (${symbols.length}개 종목)`);
    console.log(`   종목: ${symbols.join(', ')}`);
    console.log(`   간격: ${intervalMs}ms`);

    let currentIndex = 0;

    const interval = setInterval(async () => {
      // 순환하며 한 번에 하나씩 조회 (Rate Limit 준수)
      const symbol = symbols[currentIndex];

      try {
        const price = await this.getCurrentPrice(symbol);
        callback(price);
      } catch (error) {
        console.error(`[KIS] 실시간 시세 조회 오류 (${symbol})`);
      }

      currentIndex = (currentIndex + 1) % symbols.length;
    }, intervalMs);

    // 구독 해제 함수 반환
    return () => {
      clearInterval(interval);
      console.log('📡 [KIS] 실시간 시세 구독 종료');
    };
  }

  /**
   * API 연결 테스트
   */
  async testConnection(): Promise<boolean> {
    try {
      console.log('🔍 [KIS] API 연결 테스트 시작...');
      const token = await this.getAccessToken();

      if (token) {
        console.log('✅ [KIS] API 연결 성공!');

        // 삼성전자 현재가 조회 테스트
        const testPrice = await this.getCurrentPrice('005930');
        console.log('✅ [KIS] 현재가 조회 테스트 성공:');
        console.log(`   ${testPrice.name} (${testPrice.symbol})`);
        console.log(`   현재가: ${testPrice.price.toLocaleString()}원`);
        console.log(`   등락률: ${testPrice.change_rate > 0 ? '+' : ''}${testPrice.change_rate}%`);

        return true;
      }

      return false;
    } catch (error) {
      console.error('❌ [KIS] API 연결 실패');
      return false;
    }
  }
}

// 싱글톤 인스턴스
export const kisApi = new KISApiClient();
