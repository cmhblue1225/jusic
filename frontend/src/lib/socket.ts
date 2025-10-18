/**
 * Socket.IO 클라이언트
 * Stream Service와 실시간 WebSocket 연결
 */

import { io, Socket } from 'socket.io-client';
import type { RealtimeStockData } from '../stores/priceStore';

const STREAM_SERVICE_URL = import.meta.env.VITE_STREAM_SERVICE_URL || 'http://localhost:3001';

export class SocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 5000; // 5초

  /**
   * WebSocket 연결
   * @param token JWT 인증 토큰
   */
  connect(token: string): void {
    if (this.socket?.connected) {
      console.log('[Socket.IO] 이미 연결되어 있습니다.');
      return;
    }

    console.log('[Socket.IO] 연결 시작...', STREAM_SERVICE_URL);

    this.socket = io(STREAM_SERVICE_URL, {
      auth: {
        token,
      },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
    });

    this.setupEventListeners();
  }

  /**
   * 이벤트 리스너 설정
   */
  private setupEventListeners(): void {
    if (!this.socket) return;

    // 연결 성공
    this.socket.on('connect', () => {
      console.log('✅ [Socket.IO] 연결 성공:', this.socket?.id);
      this.reconnectAttempts = 0;
    });

    // 연결 오류
    this.socket.on('connect_error', (error) => {
      console.error('❌ [Socket.IO] 연결 오류:', error.message);
      this.reconnectAttempts++;

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('[Socket.IO] 최대 재연결 시도 횟수 초과');
        this.disconnect();
      }
    });

    // 연결 종료
    this.socket.on('disconnect', (reason) => {
      console.log('[Socket.IO] 연결 종료:', reason);

      if (reason === 'io server disconnect') {
        // 서버에서 연결을 끊은 경우 재연결
        console.log('[Socket.IO] 서버에서 연결을 끊음. 재연결 시도...');
        this.socket?.connect();
      }
    });

    // 재연결 시도
    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`[Socket.IO] 재연결 시도 ${attemptNumber}/${this.maxReconnectAttempts}...`);
    });

    // 재연결 성공
    this.socket.on('reconnect', (attemptNumber) => {
      console.log(`✅ [Socket.IO] 재연결 성공 (시도 횟수: ${attemptNumber})`);
      this.reconnectAttempts = 0;
    });

    // 재연결 실패
    this.socket.on('reconnect_failed', () => {
      console.error('❌ [Socket.IO] 재연결 실패');
    });
  }

  /**
   * 실시간 주가 업데이트 리스너 등록
   * @param callback 주가 업데이트 시 호출될 콜백
   */
  onStockUpdate(callback: (data: RealtimeStockData) => void): void {
    if (!this.socket) {
      console.warn('[Socket.IO] 소켓이 연결되어 있지 않습니다.');
      return;
    }

    this.socket.on('stock:update', (data: RealtimeStockData) => {
      callback(data);
    });
  }

  /**
   * 실시간 주가 업데이트 리스너 제거
   */
  offStockUpdate(): void {
    if (!this.socket) return;
    this.socket.off('stock:update');
  }

  /**
   * 종목 구독
   * @param symbols 종목코드 배열
   */
  subscribe(symbols: string[]): void {
    if (!this.socket?.connected) {
      console.warn('[Socket.IO] 소켓이 연결되어 있지 않습니다.');
      return;
    }

    console.log('[Socket.IO] 종목 구독:', symbols);
    this.socket.emit('subscribe', symbols);
  }

  /**
   * 종목 구독 해제
   * @param symbols 종목코드 배열
   */
  unsubscribe(symbols: string[]): void {
    if (!this.socket?.connected) {
      console.warn('[Socket.IO] 소켓이 연결되어 있지 않습니다.');
      return;
    }

    console.log('[Socket.IO] 종목 구독 해제:', symbols);
    this.socket.emit('unsubscribe', symbols);
  }

  /**
   * 연결 상태 확인
   */
  isConnected(): boolean {
    return this.socket?.connected ?? false;
  }

  /**
   * 연결 종료
   */
  disconnect(): void {
    if (this.socket) {
      console.log('[Socket.IO] 연결 종료');
      this.socket.disconnect();
      this.socket = null;
    }
  }

  /**
   * Socket.IO 인스턴스 반환 (고급 사용)
   */
  getSocket(): Socket | null {
    return this.socket;
  }
}

// 싱글톤 인스턴스
export const socketService = new SocketService();
