/**
 * 한국투자증권 OpenAPI 클라이언트
 * 종목 마스터 데이터 및 시세 조회
 */
import axios, { AxiosInstance } from 'axios';
import fs from 'fs';
import path from 'path';

interface KISToken {
  access_token: string;
  token_type: string;
  expires_in: number;
  access_token_token_expired: string;
}

interface KISTokenCache {
  token: KISToken;
  expiresAt: string;
}

interface KISStockMaster {
  rsym: string;           // 실시간 조회 종목코드 (단축코드)
  symb: string;           // 종목코드 (6자리)
  hts_kor_isnm: string;   // 한글 종목명
  w_icod1: string;        // 업종코드
  name_eng: string;       // 영문 종목명
  item_name: string;      // 종목명
  list_shrs: string;      // 상장주식수
}

export class KISApiClient {
  private baseURL = 'https://openapi.koreainvestment.com:9443';
  private client: AxiosInstance;
  private appKey: string;
  private appSecret: string;
  private token: KISToken | null = null;
  private tokenExpiry: Date | null = null;
  private tokenCachePath: string;

  constructor(appKey: string, appSecret: string) {
    this.appKey = appKey;
    this.appSecret = appSecret;
    this.tokenCachePath = path.join(__dirname, '../../.kis-token-cache.json');

    this.client = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
      },
    });

    // 캐시된 토큰 로드
    this.loadTokenFromCache();
  }

  /**
   * 캐시에서 토큰 로드
   */
  private loadTokenFromCache(): void {
    try {
      if (fs.existsSync(this.tokenCachePath)) {
        const cached: KISTokenCache = JSON.parse(
          fs.readFileSync(this.tokenCachePath, 'utf-8')
        );

        const expiresAt = new Date(cached.expiresAt);

        // 토큰이 아직 유효하면 재사용
        if (expiresAt > new Date()) {
          this.token = cached.token;
          this.tokenExpiry = expiresAt;
          console.log('캐시된 KIS API 토큰 로드 완료:', {
            expires_at: this.tokenExpiry.toLocaleString('ko-KR'),
          });
        } else {
          console.log('캐시된 토큰이 만료되었습니다. 새로 발급합니다.');
          fs.unlinkSync(this.tokenCachePath);
        }
      }
    } catch (error) {
      console.warn('토큰 캐시 로드 실패:', error);
    }
  }

  /**
   * 토큰을 파일에 저장
   */
  private saveTokenToCache(): void {
    try {
      const cache: KISTokenCache = {
        token: this.token!,
        expiresAt: this.tokenExpiry!.toISOString(),
      };
      fs.writeFileSync(this.tokenCachePath, JSON.stringify(cache, null, 2));
      console.log('토큰이 캐시 파일에 저장되었습니다.');
    } catch (error) {
      console.warn('토큰 캐시 저장 실패:', error);
    }
  }

  /**
   * OAuth 토큰 발급
   */
  async getAccessToken(): Promise<string> {
    // 토큰이 유효하면 재사용
    if (this.token && this.tokenExpiry && this.tokenExpiry > new Date()) {
      console.log('기존 토큰 재사용 (만료:', this.tokenExpiry.toLocaleString('ko-KR'), ')');
      return this.token.access_token;
    }

    try {
      console.log('새로운 KIS API 토큰 발급 요청...');
      const response = await this.client.post('/oauth2/tokenP', {
        grant_type: 'client_credentials',
        appkey: this.appKey,
        appsecret: this.appSecret,
      });

      this.token = response.data;

      // 만료 시간 설정 (안전하게 10분 일찍 만료 처리)
      const expiresInMs = (this.token!.expires_in - 600) * 1000;
      this.tokenExpiry = new Date(Date.now() + expiresInMs);

      console.log('✅ KIS API 토큰 발급 완료:', {
        expires_at: this.tokenExpiry.toLocaleString('ko-KR'),
      });

      // 토큰을 파일에 저장
      this.saveTokenToCache();

      return this.token!.access_token;
    } catch (error: any) {
      console.error('❌ KIS API 토큰 발급 실패:', error.response?.data || error.message);
      throw new Error('KIS API 토큰 발급 실패');
    }
  }

  /**
   * 한국거래소(KRX)에서 상장 종목 정보 가져오기
   * KIS API 대신 공개 데이터 사용
   */
  async getAllStocksFromKRX(): Promise<Array<{
    symbol: string;
    name: string;
    market: string;
    sector: string | null;
    listed_shares: bigint | null;
  }>> {
    console.log('한국거래소(KRX) 상장 종목 데이터 조회 시작...');

    try {
      // KOSPI 종목 조회
      const kospiResponse = await axios.get('http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd', {
        params: {
          bld: 'dbms/MDC/STAT/standard/MDCSTAT01501',
          mktId: 'STK',  // KOSPI
          trdDd: new Date().toISOString().slice(0, 10).replace(/-/g, ''),
        },
        headers: {
          'User-Agent': 'Mozilla/5.0',
          'Referer': 'http://data.krx.co.kr',
        },
      });

      // KOSDAQ 종목 조회
      const kosdaqResponse = await axios.get('http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd', {
        params: {
          bld: 'dbms/MDC/STAT/standard/MDCSTAT01501',
          mktId: 'KSQ',  // KOSDAQ
          trdDd: new Date().toISOString().slice(0, 10).replace(/-/g, ''),
        },
        headers: {
          'User-Agent': 'Mozilla/5.0',
          'Referer': 'http://data.krx.co.kr',
        },
      });

      const kospiStocks = kospiResponse.data.OutBlock_1 || [];
      const kosdaqStocks = kosdaqResponse.data.OutBlock_1 || [];

      console.log(`KOSPI: ${kospiStocks.length}개, KOSDAQ: ${kosdaqStocks.length}개 종목 조회 완료`);

      const allStocks = [
        ...kospiStocks.map((stock: any) => ({
          symbol: stock.ISU_SRT_CD,
          name: stock.ISU_ABBRV || stock.ISU_NM,
          market: 'KOSPI',
          sector: stock.SECT_TP_NM || null,
          listed_shares: stock.LIST_SHRS ? BigInt(stock.LIST_SHRS.replace(/,/g, '')) : null,
        })),
        ...kosdaqStocks.map((stock: any) => ({
          symbol: stock.ISU_SRT_CD,
          name: stock.ISU_ABBRV || stock.ISU_NM,
          market: 'KOSDAQ',
          sector: stock.SECT_TP_NM || null,
          listed_shares: stock.LIST_SHRS ? BigInt(stock.LIST_SHRS.replace(/,/g, '')) : null,
        })),
      ];

      // 종목코드가 6자리 숫자인 것만 필터링
      return allStocks.filter(stock =>
        stock.symbol &&
        stock.name &&
        /^\d{6}$/.test(stock.symbol)
      );
    } catch (error: any) {
      console.error('KRX 데이터 조회 실패:', error.message);
      throw new Error('KRX 종목 데이터 조회 실패');
    }
  }

  /**
   * 전체 종목 마스터 조회 (KRX 공개 데이터 사용)
   * @deprecated KIS API 종목 마스터 조회는 사용 불가
   */
  async getAllStocks(): Promise<Array<{
    symbol: string;
    name: string;
    market: string;
    sector: string | null;
    listed_shares: bigint | null;
  }>> {
    return this.getAllStocksFromKRX();
  }
}
