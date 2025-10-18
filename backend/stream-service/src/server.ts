/**
 * Stream Service 메인 서버
 * KIS WebSocket → Redis Pub/Sub → Socket.IO → Frontend
 * 실시간 주가 데이터 스트리밍 파이프라인
 */

import express from 'express';
import { createServer } from 'http';
import cors from 'cors';
import dotenv from 'dotenv';
import { kisWebSocket } from './kis-websocket.js';
import { redisPubSub } from './redis-pubsub.js';
import { StreamServer } from './socketio-server.js';
import { kisApi } from './kis-api.js';

dotenv.config();

const app = express();
const httpServer = createServer(app);

app.use(cors());
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'stream-service',
    components: {
      kis_websocket: kisWebSocket.isConnected(),
      redis_pubsub: redisPubSub.isConnected(),
    },
  });
});

// KIS API 프록시 엔드포인트: 복수 종목 현재가 조회
app.post('/api/stocks/prices', async (req, res) => {
  try {
    const { symbols } = req.body;

    if (!symbols || !Array.isArray(symbols)) {
      return res.status(400).json({ error: 'symbols array is required' });
    }

    console.log(`[API] 복수 종목 현재가 조회: ${symbols.length}개`);

    const results: any[] = [];
    const errors: any[] = [];

    for (const symbol of symbols) {
      try {
        const price = await kisApi.getCurrentPrice(symbol);
        results.push(price);

        // Rate limit: 50ms 대기
        await new Promise(resolve => setTimeout(resolve, 50));
      } catch (error: any) {
        console.error(`[API] ${symbol} 조회 실패:`, error.message);
        errors.push({ symbol, error: error.message });
      }
    }

    res.json({
      success: true,
      count: results.length,
      data: results,
      errors: errors.length > 0 ? errors : undefined,
    });
  } catch (error: any) {
    console.error('[API] 복수 종목 현재가 조회 실패:', error);
    res.status(500).json({ error: error.message });
  }
});

// Socket.IO 서버 초기화
const streamServer = new StreamServer(httpServer);

const PORT = process.env.PORT || process.env.STREAM_SERVICE_PORT || 3001;

/**
 * 서버 시작
 */
async function startServer() {
  try {
    console.log('🚀 [Stream Service] 시작 중...');

    // 1. Redis Pub/Sub 연결
    await redisPubSub.connect();

    // 2. KIS WebSocket 연결
    await kisWebSocket.connect();

    // 3. KIS WebSocket에서 수신한 데이터를 Redis로 발행
    // (실제 구독은 사용자가 연결될 때 동적으로 처리)

    // 4. Socket.IO 서버 시작
    await streamServer.start();

    // 5. HTTP 서버 시작
    httpServer.listen(PORT, () => {
      console.log(`✅ [Stream Service] 서버 실행 중: http://localhost:${PORT}`);
      console.log(`   KIS WebSocket: ${kisWebSocket.isConnected() ? '연결됨' : '연결 안 됨'}`);
      console.log(`   Redis Pub/Sub: ${redisPubSub.isConnected() ? '연결됨' : '연결 안 됨'}`);
    });

    // 테스트용 종목 구독 (삼성전자)
    if (process.env.NODE_ENV !== 'production') {
      // WebSocket 연결 완료 대기 (최대 10초)
      let retries = 0;
      const maxRetries = 20;  // 10초 (500ms x 20)

      const waitForConnection = setInterval(() => {
        if (kisWebSocket.isConnected()) {
          clearInterval(waitForConnection);

          console.log('📊 [테스트] 삼성전자(005930) 실시간 시세 구독 시작...');

          // KIS WebSocket에서 실시간 시세 수신
          kisWebSocket.onRealtimePrice('005930', async (data) => {
            // Redis로 발행 (팬아웃)
            await redisPubSub.publish(`stock:${data.symbol}`, {
              symbol: data.symbol,
              price: data.price,
              change: data.change,
              change_rate: data.change_rate,
              volume: data.volume,
              timestamp: data.timestamp,
            });

            // 최신 가격 캐싱
            await redisPubSub.setLatestPrice(data.symbol, {
              symbol: data.symbol,
              price: data.price,
              change: data.change,
              change_rate: data.change_rate,
              volume: data.volume,
              timestamp: data.timestamp,
            });
          });

          // KIS WebSocket 구독 시작
          kisWebSocket.subscribeStock('005930');

        } else {
          retries++;
          if (retries >= maxRetries) {
            clearInterval(waitForConnection);
            console.error('❌ [테스트] WebSocket 연결 타임아웃');
          }
        }
      }, 500);
    }

  } catch (error) {
    console.error('❌ [Stream Service] 시작 실패:', error);
    process.exit(1);
  }
}

/**
 * 서버 종료 처리
 */
async function shutdown() {
  console.log('🔌 [Stream Service] 종료 중...');

  try {
    // 1. KIS WebSocket 연결 종료
    kisWebSocket.disconnect();

    // 2. Socket.IO 서버 종료
    await streamServer.shutdown();

    // 3. Redis 연결 종료
    await redisPubSub.disconnect();

    // 4. HTTP 서버 종료
    httpServer.close(() => {
      console.log('✅ [Stream Service] 서버 종료 완료');
      process.exit(0);
    });

  } catch (error) {
    console.error('❌ [Stream Service] 종료 중 오류:', error);
    process.exit(1);
  }
}

// 종료 시그널 처리
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

// 서버 시작
startServer();
