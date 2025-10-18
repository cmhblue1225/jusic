/**
 * 한국투자증권 Open API 클라이언트
 * https://apiportal.koreainvestment.com/
 */
import axios, { AxiosInstance } from 'axios';
import dotenv from 'dotenv';

dotenv.config();

interface KISTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

interface StockPrice {
  symbol: string;
  price: number;
  change_rate: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  timestamp: string;
}

class KISApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;
  private tokenExpiry: number = 0;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.KIS_BASE_URL || 'https://openapi.koreainvestment.com:9443',
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
      },
    });
  }

  /**
   * 접근 토큰 발급
   */
  private async getAccessToken(): Promise<string> {
    // 토큰이 유효하면 재사용
    if (this.accessToken && Date.now() < this.tokenExpiry) {
      return this.accessToken;
    }

    try {
      const response = await this.client.post<KISTokenResponse>('/oauth2/tokenP', {
        grant_type: 'client_credentials',
        appkey: process.env.KIS_APP_KEY,
        appsecret: process.env.KIS_APP_SECRET,
      });

      this.accessToken = response.data.access_token;
      // 토큰 만료 시간 (발급 후 24시간)
      this.tokenExpiry = Date.now() + response.data.expires_in * 1000;

      console.log('✅ KIS API 토큰 발급 완료');
      return this.accessToken;
    } catch (error) {
      console.error('❌ KIS API 토큰 발급 실패:', error);
      throw error;
    }
  }

  /**
   * 현재가 조회
   * @param symbol 종목 코드 (예: 005930)
   */
  async getCurrentPrice(symbol: string): Promise<StockPrice> {
    const token = await this.getAccessToken();

    try {
      const response = await this.client.get('/uapi/domestic-stock/v1/quotations/inquire-price', {
        headers: {
          authorization: `Bearer ${token}`,
          appkey: process.env.KIS_APP_KEY,
          appsecret: process.env.KIS_APP_SECRET,
          tr_id: 'FHKST01010100', // 주식현재가 시세
        },
        params: {
          FID_COND_MRKT_DIV_CODE: 'J', // J: 주식
          FID_INPUT_ISCD: symbol,
        },
      });

      const data = response.data.output;

      return {
        symbol,
        price: parseFloat(data.stck_prpr), // 현재가
        change_rate: parseFloat(data.prdy_ctrt), // 전일 대비율
        volume: parseInt(data.acml_vol), // 누적 거래량
        high: parseFloat(data.stck_hgpr), // 최고가
        low: parseFloat(data.stck_lwpr), // 최저가
        open: parseFloat(data.stck_oprc), // 시가
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      console.error(`❌ 현재가 조회 실패 (${symbol}):`, error);
      throw error;
    }
  }

  /**
   * 복수 종목 현재가 일괄 조회
   */
  async getBatchPrices(symbols: string[]): Promise<StockPrice[]> {
    const promises = symbols.map((symbol) => this.getCurrentPrice(symbol));
    return Promise.all(promises);
  }

  /**
   * 호가 조회
   * @param symbol 종목 코드
   */
  async getOrderbook(symbol: string) {
    const token = await this.getAccessToken();

    try {
      const response = await this.client.get('/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn', {
        headers: {
          authorization: `Bearer ${token}`,
          appkey: process.env.KIS_APP_KEY,
          appsecret: process.env.KIS_APP_SECRET,
          tr_id: 'FHKST01010200', // 주식호가
        },
        params: {
          FID_COND_MRKT_DIV_CODE: 'J',
          FID_INPUT_ISCD: symbol,
        },
      });

      return response.data.output;
    } catch (error) {
      console.error(`❌ 호가 조회 실패 (${symbol}):`, error);
      throw error;
    }
  }

  /**
   * 체결가 조회
   * @param symbol 종목 코드
   */
  async getExecution(symbol: string) {
    const token = await this.getAccessToken();

    try {
      const response = await this.client.get('/uapi/domestic-stock/v1/quotations/inquire-ccnl', {
        headers: {
          authorization: `Bearer ${token}`,
          appkey: process.env.KIS_APP_KEY,
          appsecret: process.env.KIS_APP_SECRET,
          tr_id: 'FHKST01010300', // 주식체결가
        },
        params: {
          FID_COND_MRKT_DIV_CODE: 'J',
          FID_INPUT_ISCD: symbol,
        },
      });

      return response.data.output;
    } catch (error) {
      console.error(`❌ 체결가 조회 실패 (${symbol}):`, error);
      throw error;
    }
  }

  /**
   * WebSocket 실시간 시세 구독
   * (한국투자증권 WebSocket 연동은 별도 구현 필요)
   */
  subscribeRealtime(symbols: string[], callback: (data: StockPrice) => void) {
    console.log('📡 WebSocket 실시간 시세 구독:', symbols);
    // TODO: WebSocket 연동 구현
    // 현재는 폴링 방식으로 대체
    const interval = setInterval(async () => {
      for (const symbol of symbols) {
        try {
          const price = await this.getCurrentPrice(symbol);
          callback(price);
        } catch (error) {
          console.error(`실시간 시세 조회 오류 (${symbol}):`, error);
        }
      }
    }, 1000); // 1초마다 조회 (API 제한 주의)

    return () => clearInterval(interval);
  }
}

export const kisApi = new KISApiClient();
