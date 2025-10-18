/**
 * 한국투자증권 WebSocket 클라이언트
 * 실시간 시세 및 체결가 스트리밍
 *
 * WebSocket 엔드포인트: ws://ops.koreainvestment.com:21000
 * 주요 TR_ID:
 * - H0STCNT0: 국내주식 실시간체결가 (실전/모의 동일)
 * - H0STASP0: 국내주식 실시간호가 (실전/모의 동일)
 */

import WebSocket from 'ws';
import axios from 'axios';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config();

interface ApprovalKeyResponse {
  approval_key: string;
}

interface WebSocketMessage {
  header: {
    tr_id: string;
    tr_key: string;
  };
  body: {
    rt_cd: string;  // 응답코드
    msg_cd: string; // 메시지코드
    msg1: string;   // 메시지
    output?: any;   // 출력 데이터
  };
}

interface RealtimePrice {
  symbol: string;           // 종목코드
  name?: string;            // 종목명
  price: number;            // 현재가
  change: number;           // 전일 대비
  change_rate: number;      // 등락률 (%)
  volume: number;           // 거래량
  timestamp: string;        // 시각
}

interface ApprovalKeyCache {
  approval_key: string;
  expiresAt: string;
}

export class KISWebSocketClient {
  private ws: WebSocket | null = null;
  private appKey: string;
  private appSecret: string;
  private approvalKey: string | null = null;
  private approvalKeyExpiry: Date | null = null;
  private approvalKeyCachePath: string;
  private wsUrl = 'ws://ops.koreainvestment.com:21000';
  private baseURL: string;
  private reconnectInterval: number = 5000;  // 재연결 간격 (5초)
  private reconnectTimer: NodeJS.Timeout | null = null;
  private isConnecting: boolean = false;
  private subscribedSymbols: Set<string> = new Set();
  private messageHandlers: Map<string, (data: RealtimePrice) => void> = new Map();

  constructor() {
    this.appKey = process.env.KIS_APP_KEY || '';
    this.appSecret = process.env.KIS_APP_SECRET || '';
    this.baseURL = process.env.KIS_BASE_URL || 'https://openapivts.koreainvestment.com:29443';
    this.approvalKeyCachePath = path.join(__dirname, '../../.kis-approval-key-cache.json');

    // 캐시된 approval key 로드
    this.loadApprovalKeyFromCache();
  }

  /**
   * 캐시에서 approval key 로드
   */
  private loadApprovalKeyFromCache(): void {
    try {
      if (fs.existsSync(this.approvalKeyCachePath)) {
        const cached: ApprovalKeyCache = JSON.parse(
          fs.readFileSync(this.approvalKeyCachePath, 'utf-8')
        );

        const expiresAt = new Date(cached.expiresAt);

        // approval key가 아직 유효하면 재사용 (24시간 유효)
        if (expiresAt > new Date()) {
          this.approvalKey = cached.approval_key;
          this.approvalKeyExpiry = expiresAt;
          console.log('캐시된 KIS Approval Key 로드 완료:', {
            expires_at: this.approvalKeyExpiry.toLocaleString('ko-KR'),
          });
        } else {
          console.log('캐시된 Approval Key가 만료되었습니다. 새로 발급합니다.');
          fs.unlinkSync(this.approvalKeyCachePath);
        }
      }
    } catch (error) {
      console.warn('Approval Key 캐시 로드 실패:', error);
    }
  }

  /**
   * Approval Key를 파일에 저장
   */
  private saveApprovalKeyToCache(): void {
    try {
      const cache: ApprovalKeyCache = {
        approval_key: this.approvalKey!,
        expiresAt: this.approvalKeyExpiry!.toISOString(),
      };
      fs.writeFileSync(this.approvalKeyCachePath, JSON.stringify(cache, null, 2));
      console.log('Approval Key가 캐시 파일에 저장되었습니다.');
    } catch (error) {
      console.warn('Approval Key 캐시 저장 실패:', error);
    }
  }

  /**
   * WebSocket 접속키 (Approval Key) 발급
   * POST /oauth2/Approval
   */
  private async getApprovalKey(): Promise<string> {
    // approval key가 유효하면 재사용
    if (this.approvalKey && this.approvalKeyExpiry && this.approvalKeyExpiry > new Date()) {
      console.log('기존 Approval Key 재사용 (만료:', this.approvalKeyExpiry.toLocaleString('ko-KR'), ')');
      return this.approvalKey;
    }

    try {
      console.log('새로운 KIS Approval Key 발급 요청...');
      const response = await axios.post<ApprovalKeyResponse>(
        `${this.baseURL}/oauth2/Approval`,
        {
          grant_type: 'client_credentials',
          appkey: this.appKey,
          secretkey: this.appSecret,  // secretkey = appsecret (동일)
        },
        {
          headers: {
            'Content-Type': 'application/json; charset=utf-8',
          },
        }
      );

      this.approvalKey = response.data.approval_key;

      // approval key 만료 시간 (24시간, 안전하게 23시간으로 설정)
      const expiresInMs = 23 * 60 * 60 * 1000;
      this.approvalKeyExpiry = new Date(Date.now() + expiresInMs);

      console.log('✅ KIS Approval Key 발급 완료:', {
        expires_at: this.approvalKeyExpiry.toLocaleString('ko-KR'),
      });

      // approval key를 파일에 저장
      this.saveApprovalKeyToCache();

      return this.approvalKey!;
    } catch (error: any) {
      console.error('❌ KIS Approval Key 발급 실패:', error.response?.data || error.message);
      throw new Error('KIS Approval Key 발급 실패');
    }
  }

  /**
   * WebSocket 연결
   */
  async connect(): Promise<void> {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      console.log('이미 WebSocket에 연결되어 있거나 연결 중입니다.');
      return;
    }

    this.isConnecting = true;

    try {
      // Approval Key 발급
      const approvalKey = await this.getApprovalKey();

      console.log('📡 [KIS WebSocket] 연결 시작...');
      console.log(`   URL: ${this.wsUrl}`);

      this.ws = new WebSocket(this.wsUrl);

      this.ws.on('open', () => {
        console.log('✅ [KIS WebSocket] 연결 완료');
        this.isConnecting = false;

        // 기존 구독 종목 재구독
        if (this.subscribedSymbols.size > 0) {
          console.log(`📡 [KIS WebSocket] 기존 구독 종목 재구독 (${this.subscribedSymbols.size}개)`);
          this.subscribedSymbols.forEach((symbol) => {
            this.subscribeStock(symbol);
          });
        }
      });

      this.ws.on('message', (data: WebSocket.Data) => {
        this.handleMessage(data);
      });

      this.ws.on('error', (error) => {
        console.error('❌ [KIS WebSocket] 에러:', error.message);
        this.isConnecting = false;
      });

      this.ws.on('close', (code, reason) => {
        console.log(`🔌 [KIS WebSocket] 연결 종료 (code: ${code}, reason: ${reason})`);
        this.isConnecting = false;
        this.ws = null;

        // 자동 재연결
        console.log(`🔄 [KIS WebSocket] ${this.reconnectInterval / 1000}초 후 재연결 시도...`);
        this.reconnectTimer = setTimeout(() => {
          this.connect();
        }, this.reconnectInterval);
      });

    } catch (error) {
      console.error('❌ [KIS WebSocket] 연결 실패:', error);
      this.isConnecting = false;
      throw error;
    }
  }

  /**
   * WebSocket 메시지 처리
   */
  private handleMessage(data: WebSocket.Data): void {
    try {
      const message = data.toString('utf-8');

      // JSON 메시지 (PINGPONG, SUBSCRIBE 응답 등)
      if (message.startsWith('{')) {
        const jsonData = JSON.parse(message);

        // PINGPONG은 무시 (heartbeat)
        if (jsonData.header?.tr_id === 'PINGPONG') {
          return;
        }

        // 구독 응답 처리
        if (jsonData.body?.msg_cd === 'OPSP0000' && jsonData.body?.msg1 === 'SUBSCRIBE SUCCESS') {
          console.log(`✅ [KIS WebSocket] 구독 성공: ${jsonData.header?.tr_key}`);
          return;
        }

        // 그 외 JSON 메시지는 로깅
        console.log('[KIS WebSocket] JSON 메시지:', jsonData);
        return;
      }

      // 파이프(|) 구분자로 분리 (실시간 데이터)
      const parts = message.split('|');

      if (parts.length < 2) {
        console.warn('[KIS WebSocket] 잘못된 메시지 형식:', message);
        return;
      }

      const trId = parts[0];  // TR_ID (예: H0STCNT0)
      const trKey = parts[1]; // 종목코드
      const body = parts.slice(2).join('|');  // 실제 데이터

      // TR_ID별 파싱
      if (trId === 'H0STCNT0') {
        // 실시간 체결가
        this.parseRealtimePrice(trKey, body);
      } else if (trId === 'H0STASP0') {
        // 실시간 호가
        this.parseRealtimeOrderbook(trKey, body);
      } else {
        console.log(`[KIS WebSocket] 알 수 없는 TR_ID: ${trId}`);
      }

    } catch (error) {
      console.error('[KIS WebSocket] 메시지 처리 오류:', error);
    }
  }

  /**
   * 실시간 체결가 파싱
   * TR_ID: H0STCNT0
   */
  private parseRealtimePrice(symbol: string, data: string): void {
    try {
      // 체결가 데이터를 '^' 구분자로 분리
      const fields = data.split('^');

      if (fields.length < 50) {
        console.warn(`[KIS WebSocket] 체결가 데이터 필드 부족 (${fields.length})`);
        return;
      }

      // 필드 인덱스는 KIS API 문서 참조 필요
      // 임시로 주요 필드만 파싱
      const realtimePrice: RealtimePrice = {
        symbol: symbol.padStart(6, '0'),
        price: parseFloat(fields[2] || '0'),           // 현재가
        change: parseFloat(fields[4] || '0'),          // 전일대비
        change_rate: parseFloat(fields[5] || '0'),     // 등락률
        volume: parseInt(fields[10] || '0'),           // 체결량
        timestamp: new Date().toISOString(),
      };

      // 구독자에게 데이터 전달
      const handler = this.messageHandlers.get(symbol);
      if (handler) {
        handler(realtimePrice);
      }

      console.log(`📊 [${symbol}] ${realtimePrice.price.toLocaleString()}원 (${realtimePrice.change_rate > 0 ? '+' : ''}${realtimePrice.change_rate}%)`);

    } catch (error) {
      console.error('[KIS WebSocket] 체결가 파싱 오류:', error);
    }
  }

  /**
   * 실시간 호가 파싱
   * TR_ID: H0STASP0
   */
  private parseRealtimeOrderbook(symbol: string, data: string): void {
    try {
      // 호가 데이터 파싱 (필요 시 구현)
      console.log(`📋 [${symbol}] 실시간 호가 수신`);
    } catch (error) {
      console.error('[KIS WebSocket] 호가 파싱 오류:', error);
    }
  }

  /**
   * 종목 구독
   * @param symbol 종목코드 (6자리)
   * @param trId TR_ID (기본값: H0STCNT0 - 실시간체결가)
   */
  subscribeStock(symbol: string, trId: string = 'H0STCNT0'): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('[KIS WebSocket] WebSocket이 연결되어 있지 않습니다. 연결 후 구독하세요.');
      return;
    }

    const paddedSymbol = symbol.padStart(6, '0');

    // 구독 메시지 전송
    // 형식: {"header":{"approval_key":"...","custtype":"P","tr_type":"1","content-type":"utf-8"},"body":{"input":{"tr_id":"H0STCNT0","tr_key":"005930"}}}
    const subscribeMessage = JSON.stringify({
      header: {
        approval_key: this.approvalKey,
        custtype: 'P',      // 개인: P, 법인: B
        tr_type: '1',       // 등록: 1, 해지: 2
        'content-type': 'utf-8',
      },
      body: {
        input: {
          tr_id: trId,
          tr_key: paddedSymbol,
        },
      },
    });

    this.ws.send(subscribeMessage);
    this.subscribedSymbols.add(paddedSymbol);

    console.log(`✅ [KIS WebSocket] 종목 구독: ${paddedSymbol} (TR_ID: ${trId})`);
  }

  /**
   * 종목 구독 해지
   * @param symbol 종목코드 (6자리)
   * @param trId TR_ID
   */
  unsubscribeStock(symbol: string, trId: string = 'H0STCNT0'): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('[KIS WebSocket] WebSocket이 연결되어 있지 않습니다.');
      return;
    }

    const paddedSymbol = symbol.padStart(6, '0');

    // 구독 해지 메시지 전송
    const unsubscribeMessage = JSON.stringify({
      header: {
        approval_key: this.approvalKey,
        custtype: 'P',
        tr_type: '2',       // 해지: 2
        'content-type': 'utf-8',
      },
      body: {
        input: {
          tr_id: trId,
          tr_key: paddedSymbol,
        },
      },
    });

    this.ws.send(unsubscribeMessage);
    this.subscribedSymbols.delete(paddedSymbol);
    this.messageHandlers.delete(paddedSymbol);

    console.log(`❌ [KIS WebSocket] 종목 구독 해지: ${paddedSymbol} (TR_ID: ${trId})`);
  }

  /**
   * 실시간 시세 콜백 등록
   * @param symbol 종목코드
   * @param handler 시세 수신 시 호출될 콜백 함수
   */
  onRealtimePrice(symbol: string, handler: (data: RealtimePrice) => void): void {
    const paddedSymbol = symbol.padStart(6, '0');
    this.messageHandlers.set(paddedSymbol, handler);
  }

  /**
   * WebSocket 연결 종료
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      // 모든 구독 해지
      this.subscribedSymbols.forEach((symbol) => {
        this.unsubscribeStock(symbol);
      });

      this.ws.close();
      this.ws = null;
      console.log('🔌 [KIS WebSocket] 연결 종료');
    }

    this.subscribedSymbols.clear();
    this.messageHandlers.clear();
  }

  /**
   * 연결 상태 확인
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// 싱글톤 인스턴스
export const kisWebSocket = new KISWebSocketClient();
