/**
 * Socket.IO 서버
 * 프론트엔드 클라이언트에게 실시간 주가 데이터 전송
 * Redis Pub/Sub에서 데이터를 구독하여 팬아웃 (Fan-out)
 */

import { Server as SocketIOServer } from 'socket.io';
import { Server as HttpServer } from 'http';
import { redisPubSub } from './redis-pubsub';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

interface ClientSubscription {
  userId: string;
  symbols: Set<string>;
}

export class StreamServer {
  private io: SocketIOServer;
  private supabase;
  private clientSubscriptions: Map<string, ClientSubscription> = new Map();

  constructor(httpServer: HttpServer) {
    // Socket.IO 서버 초기화
    this.io = new SocketIOServer(httpServer, {
      cors: {
        origin: process.env.FRONTEND_URL || 'http://localhost:5173',
        methods: ['GET', 'POST'],
        credentials: true,
      },
    });

    // Supabase 클라이언트 (JWT 토큰 검증용)
    this.supabase = createClient(
      process.env.SUPABASE_URL || '',
      process.env.SUPABASE_ANON_KEY || ''
    );

    this.setupEventHandlers();
  }

  /**
   * Socket.IO 이벤트 핸들러 설정
   */
  private setupEventHandlers(): void {
    this.io.on('connection', async (socket) => {
      console.log(`🔌 [Socket.IO] 클라이언트 연결: ${socket.id}`);

      // 인증 토큰 검증
      const token = socket.handshake.auth.token;
      if (!token) {
        console.error(`❌ [Socket.IO] 인증 토큰 없음: ${socket.id}`);
        socket.disconnect();
        return;
      }

      // JWT 토큰 검증
      const { data: { user }, error } = await this.supabase.auth.getUser(token);
      if (error || !user) {
        console.error(`❌ [Socket.IO] 토큰 검증 실패: ${socket.id}`, error?.message);
        socket.disconnect();
        return;
      }

      console.log(`✅ [Socket.IO] 인증 완료: ${user.email} (${socket.id})`);

      // 클라이언트 구독 정보 저장
      this.clientSubscriptions.set(socket.id, {
        userId: user.id,
        symbols: new Set(),
      });

      // 이벤트 리스너 등록
      socket.on('subscribe', (symbols: string[]) => {
        this.handleSubscribe(socket, user.id, symbols);
      });

      socket.on('unsubscribe', (symbols: string[]) => {
        this.handleUnsubscribe(socket, symbols);
      });

      socket.on('disconnect', () => {
        this.handleDisconnect(socket);
      });

      // 연결 즉시 사용자의 보유 종목 + 관심 종목 자동 구독
      await this.autoSubscribeUserStocks(socket, user.id, token);
    });
  }

  /**
   * 사용자의 보유 종목 + 관심 종목 자동 구독
   */
  private async autoSubscribeUserStocks(socket: any, userId: string, token: string): Promise<void> {
    try {
      console.log(`[Socket.IO] 자동 구독 시작: ${userId} (${socket.id})`);

      // JWT 토큰으로 인증된 Supabase 클라이언트 생성
      const authedSupabase = createClient(
        process.env.SUPABASE_URL || '',
        process.env.SUPABASE_ANON_KEY || '',
        {
          global: {
            headers: {
              Authorization: `Bearer ${token}`
            }
          }
        }
      );

      // 1. 보유 종목 조회
      const { data: portfolioStocks, error: portfolioError } = await authedSupabase
        .from('portfolios')
        .select('symbol')
        .eq('user_id', userId);

      if (portfolioError) {
        console.error('[Socket.IO] 보유 종목 조회 실패:', portfolioError);
      } else {
        console.log(`[Socket.IO] 보유 종목 조회 성공: ${portfolioStocks?.length || 0}개`);
      }

      // 2. 관심 종목 조회
      const { data: watchlistStocks, error: watchlistError } = await authedSupabase
        .from('watchlist')
        .select('symbol')
        .eq('user_id', userId);

      if (watchlistError) {
        console.error('[Socket.IO] 관심 종목 조회 실패:', watchlistError);
      } else {
        console.log(`[Socket.IO] 관심 종목 조회 성공: ${watchlistStocks?.length || 0}개`);
      }

      // 3. 중복 제거 후 구독
      const allSymbols = new Set<string>();

      portfolioStocks?.forEach((stock: any) => {
        allSymbols.add(stock.symbol);
      });

      watchlistStocks?.forEach((stock: any) => {
        allSymbols.add(stock.symbol);
      });

      console.log(`[Socket.IO] 총 구독 대상 종목: ${allSymbols.size}개`, Array.from(allSymbols));

      if (allSymbols.size > 0) {
        const symbols = Array.from(allSymbols);
        await this.handleSubscribe(socket, userId, symbols);
        console.log(`✅ [Socket.IO] 자동 구독 완료: ${symbols.length}개 종목 (${socket.id})`);
      } else {
        console.log(`[Socket.IO] 구독할 종목이 없습니다 (${socket.id})`);
      }

    } catch (error) {
      console.error('[Socket.IO] 자동 구독 실패:', error);
    }
  }

  /**
   * 종목 구독 처리
   */
  private async handleSubscribe(socket: any, userId: string, symbols: string[]): Promise<void> {
    const subscription = this.clientSubscriptions.get(socket.id);
    if (!subscription) {
      console.error(`[Socket.IO] 구독 정보 없음: ${socket.id}`);
      return;
    }

    try {
      const newSymbols: string[] = [];

      symbols.forEach((symbol) => {
        const paddedSymbol = symbol.padStart(6, '0');

        // 이미 구독 중인 종목인지 확인
        if (!subscription.symbols.has(paddedSymbol)) {
          subscription.symbols.add(paddedSymbol);
          newSymbols.push(paddedSymbol);
        }
      });

      if (newSymbols.length === 0) {
        console.log(`[Socket.IO] 이미 구독 중인 종목들입니다: ${socket.id}`);
        return;
      }

      // Redis에서 각 종목별 실시간 시세 구독
      for (const symbol of newSymbols) {
        const channel = `stock:${symbol}`;

        await redisPubSub.subscribe(channel, (data) => {
          // 해당 종목을 구독한 클라이언트에게만 전송
          const clientSubscription = this.clientSubscriptions.get(socket.id);
          if (clientSubscription && clientSubscription.symbols.has(symbol)) {
            socket.emit('stock:update', data);
          }
        });
      }

      console.log(`✅ [Socket.IO] 종목 구독: ${newSymbols.join(', ')} (${socket.id})`);

      // 최신 가격 즉시 전송 (캐시에서 조회)
      const latestPrices = await redisPubSub.getLatestPrices(newSymbols);
      latestPrices.forEach((data, symbol) => {
        socket.emit('stock:update', data);
      });

    } catch (error) {
      console.error('[Socket.IO] 구독 처리 실패:', error);
    }
  }

  /**
   * 종목 구독 해지 처리
   */
  private async handleUnsubscribe(socket: any, symbols: string[]): Promise<void> {
    const subscription = this.clientSubscriptions.get(socket.id);
    if (!subscription) {
      console.error(`[Socket.IO] 구독 정보 없음: ${socket.id}`);
      return;
    }

    try {
      symbols.forEach((symbol) => {
        const paddedSymbol = symbol.padStart(6, '0');
        subscription.symbols.delete(paddedSymbol);
      });

      console.log(`❌ [Socket.IO] 종목 구독 해지: ${symbols.join(', ')} (${socket.id})`);

    } catch (error) {
      console.error('[Socket.IO] 구독 해지 실패:', error);
    }
  }

  /**
   * 클라이언트 연결 종료 처리
   */
  private handleDisconnect(socket: any): void {
    console.log(`🔌 [Socket.IO] 클라이언트 연결 종료: ${socket.id}`);

    // 구독 정보 삭제
    this.clientSubscriptions.delete(socket.id);
  }

  /**
   * 특정 사용자에게 메시지 전송
   */
  emitToUser(userId: string, event: string, data: any): void {
    // 해당 사용자의 모든 소켓 찾기
    this.clientSubscriptions.forEach((subscription, socketId) => {
      if (subscription.userId === userId) {
        this.io.to(socketId).emit(event, data);
      }
    });
  }

  /**
   * 전체 클라이언트에게 브로드캐스트
   */
  broadcast(event: string, data: any): void {
    this.io.emit(event, data);
  }

  /**
   * 서버 시작
   */
  async start(): Promise<void> {
    console.log('🚀 [Socket.IO] 서버 시작...');

    // Redis Pub/Sub 연결
    if (!redisPubSub.isConnected()) {
      await redisPubSub.connect();
    }

    console.log('✅ [Socket.IO] 서버 준비 완료');
  }

  /**
   * 서버 종료
   */
  async shutdown(): Promise<void> {
    console.log('🔌 [Socket.IO] 서버 종료 중...');

    // 모든 클라이언트 연결 종료
    this.io.disconnectSockets();
    this.clientSubscriptions.clear();

    // Redis 연결 종료
    await redisPubSub.disconnect();

    console.log('✅ [Socket.IO] 서버 종료 완료');
  }
}
