/**
 * Redis Pub/Sub 메시지 브로커
 * KIS WebSocket에서 받은 실시간 시세를 Redis를 통해 브로드캐스트
 * Socket.IO 서버에서 구독하여 클라이언트에게 전달
 */

import { createClient, RedisClientType } from 'redis';
import dotenv from 'dotenv';

dotenv.config();

interface RealtimeStockData {
  symbol: string;
  price: number;
  change: number;
  change_rate: number;
  volume: number;
  timestamp: string;
}

export class RedisPubSub {
  private publisherClient: RedisClientType | null = null;
  private subscriberClient: RedisClientType | null = null;
  private redisUrl: string;
  private messageHandlers: Map<string, Set<(data: RealtimeStockData) => void>> = new Map();

  constructor() {
    this.redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
  }

  /**
   * Redis 연결
   */
  async connect(): Promise<void> {
    try {
      console.log('📡 [Redis Pub/Sub] 연결 시작...');
      console.log(`   URL: ${this.redisUrl}`);

      // Publisher 클라이언트 (메시지 발행용)
      this.publisherClient = createClient({
        url: this.redisUrl,
      });

      this.publisherClient.on('error', (err) => {
        console.error('❌ [Redis Publisher] 에러:', err);
      });

      await this.publisherClient.connect();
      console.log('✅ [Redis Publisher] 연결 완료');

      // Subscriber 클라이언트 (메시지 구독용)
      // Redis Pub/Sub는 별도의 클라이언트 필요
      this.subscriberClient = createClient({
        url: this.redisUrl,
      });

      this.subscriberClient.on('error', (err) => {
        console.error('❌ [Redis Subscriber] 에러:', err);
      });

      await this.subscriberClient.connect();
      console.log('✅ [Redis Subscriber] 연결 완료');

    } catch (error) {
      console.error('❌ [Redis Pub/Sub] 연결 실패:', error);
      throw error;
    }
  }

  /**
   * 실시간 주가 데이터 발행
   * @param channel 채널명 (예: stock:005930)
   * @param data 주가 데이터
   */
  async publish(channel: string, data: RealtimeStockData): Promise<void> {
    if (!this.publisherClient) {
      console.error('[Redis Pub/Sub] Publisher가 연결되지 않았습니다.');
      return;
    }

    try {
      const message = JSON.stringify(data);
      await this.publisherClient.publish(channel, message);

      // console.log(`📤 [Redis] 발행: ${channel} → ${data.symbol} ${data.price.toLocaleString()}원`);
    } catch (error) {
      console.error(`[Redis Pub/Sub] 발행 실패 (${channel}):`, error);
    }
  }

  /**
   * 채널 구독
   * @param channel 채널명 (예: stock:005930 또는 stock:* 패턴)
   * @param handler 메시지 수신 시 호출될 콜백
   */
  async subscribe(channel: string, handler: (data: RealtimeStockData) => void): Promise<void> {
    if (!this.subscriberClient) {
      console.error('[Redis Pub/Sub] Subscriber가 연결되지 않았습니다.');
      return;
    }

    try {
      // 채널별 핸들러 저장
      if (!this.messageHandlers.has(channel)) {
        this.messageHandlers.set(channel, new Set());
      }
      this.messageHandlers.get(channel)!.add(handler);

      // 패턴 매칭 구독 (예: stock:*)
      if (channel.includes('*')) {
        await this.subscriberClient.pSubscribe(channel, (message, matchedChannel) => {
          this.handleMessage(matchedChannel, message);
        });
        console.log(`✅ [Redis] 패턴 구독: ${channel}`);
      } else {
        // 정확한 채널 구독
        await this.subscriberClient.subscribe(channel, (message) => {
          this.handleMessage(channel, message);
        });
        console.log(`✅ [Redis] 채널 구독: ${channel}`);
      }

    } catch (error) {
      console.error(`[Redis Pub/Sub] 구독 실패 (${channel}):`, error);
    }
  }

  /**
   * 메시지 처리
   */
  private handleMessage(channel: string, message: string): void {
    try {
      const data: RealtimeStockData = JSON.parse(message);

      // 채널에 등록된 모든 핸들러 호출
      const handlers = this.messageHandlers.get(channel);
      if (handlers) {
        handlers.forEach((handler) => handler(data));
      }

      // 패턴 매칭 핸들러도 호출 (예: stock:* 구독자)
      this.messageHandlers.forEach((handlers, pattern) => {
        if (pattern.includes('*') && this.matchPattern(pattern, channel)) {
          handlers.forEach((handler) => handler(data));
        }
      });

      // console.log(`📥 [Redis] 수신: ${channel} → ${data.symbol} ${data.price.toLocaleString()}원`);

    } catch (error) {
      console.error('[Redis Pub/Sub] 메시지 파싱 오류:', error);
    }
  }

  /**
   * 패턴 매칭 (간단한 * 와일드카드 지원)
   */
  private matchPattern(pattern: string, channel: string): boolean {
    const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
    return regex.test(channel);
  }

  /**
   * 채널 구독 해지
   * @param channel 채널명
   */
  async unsubscribe(channel: string): Promise<void> {
    if (!this.subscriberClient) {
      console.error('[Redis Pub/Sub] Subscriber가 연결되지 않았습니다.');
      return;
    }

    try {
      if (channel.includes('*')) {
        await this.subscriberClient.pUnsubscribe(channel);
      } else {
        await this.subscriberClient.unsubscribe(channel);
      }

      this.messageHandlers.delete(channel);
      console.log(`❌ [Redis] 구독 해지: ${channel}`);

    } catch (error) {
      console.error(`[Redis Pub/Sub] 구독 해지 실패 (${channel}):`, error);
    }
  }

  /**
   * 특정 종목의 최신 가격 조회 (캐시에서)
   * @param symbol 종목코드
   */
  async getLatestPrice(symbol: string): Promise<RealtimeStockData | null> {
    if (!this.publisherClient) {
      console.error('[Redis Pub/Sub] Publisher가 연결되지 않았습니다.');
      return null;
    }

    try {
      const key = `latest:stock:${symbol}`;
      const data = await this.publisherClient.get(key);

      if (data) {
        return JSON.parse(data);
      }

      return null;
    } catch (error) {
      console.error(`[Redis Pub/Sub] 최신 가격 조회 실패 (${symbol}):`, error);
      return null;
    }
  }

  /**
   * 최신 가격 캐싱 (Redis에 저장)
   * @param symbol 종목코드
   * @param data 주가 데이터
   * @param ttl TTL (초 단위, 기본값: 300초 = 5분)
   */
  async setLatestPrice(symbol: string, data: RealtimeStockData, ttl: number = 300): Promise<void> {
    if (!this.publisherClient) {
      console.error('[Redis Pub/Sub] Publisher가 연결되지 않았습니다.');
      return;
    }

    try {
      const key = `latest:stock:${symbol}`;
      const value = JSON.stringify(data);

      await this.publisherClient.setEx(key, ttl, value);
      // console.log(`💾 [Redis] 최신 가격 캐싱: ${symbol} → ${data.price.toLocaleString()}원 (TTL: ${ttl}초)`);

    } catch (error) {
      console.error(`[Redis Pub/Sub] 최신 가격 캐싱 실패 (${symbol}):`, error);
    }
  }

  /**
   * 복수 종목의 최신 가격 일괄 조회
   * @param symbols 종목코드 배열
   */
  async getLatestPrices(symbols: string[]): Promise<Map<string, RealtimeStockData>> {
    const result = new Map<string, RealtimeStockData>();

    if (!this.publisherClient) {
      console.error('[Redis Pub/Sub] Publisher가 연결되지 않았습니다.');
      return result;
    }

    try {
      const keys = symbols.map(symbol => `latest:stock:${symbol}`);
      const values = await this.publisherClient.mGet(keys);

      values.forEach((value, index) => {
        if (value) {
          const data = JSON.parse(value);
          result.set(symbols[index], data);
        }
      });

      console.log(`📊 [Redis] 복수 종목 조회 완료: ${result.size}/${symbols.length}개`);
      return result;

    } catch (error) {
      console.error('[Redis Pub/Sub] 복수 종목 조회 실패:', error);
      return result;
    }
  }

  /**
   * Redis 연결 종료
   */
  async disconnect(): Promise<void> {
    try {
      if (this.publisherClient) {
        await this.publisherClient.quit();
        this.publisherClient = null;
        console.log('🔌 [Redis Publisher] 연결 종료');
      }

      if (this.subscriberClient) {
        await this.subscriberClient.quit();
        this.subscriberClient = null;
        console.log('🔌 [Redis Subscriber] 연결 종료');
      }

      this.messageHandlers.clear();

    } catch (error) {
      console.error('[Redis Pub/Sub] 연결 종료 실패:', error);
    }
  }

  /**
   * 연결 상태 확인
   */
  isConnected(): boolean {
    return (
      this.publisherClient !== null &&
      this.publisherClient.isOpen &&
      this.subscriberClient !== null &&
      this.subscriberClient.isOpen
    );
  }
}

// 싱글톤 인스턴스
export const redisPubSub = new RedisPubSub();
