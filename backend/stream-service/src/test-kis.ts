/**
 * 한국투자증권 API 테스트 스크립트
 *
 * 실행 방법:
 * cd backend/stream-service
 * npx tsx src/test-kis.ts
 */
import { kisApi } from './kis-api.js';

async function main() {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🚀 한국투자증권 API 테스트');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  // 1. API 연결 테스트
  console.log('📝 1단계: API 연결 테스트');
  console.log('─'.repeat(50));
  const isConnected = await kisApi.testConnection();

  if (!isConnected) {
    console.error('\n❌ API 연결 실패. .env 파일의 KIS API 키를 확인하세요.\n');
    process.exit(1);
  }

  console.log('\n');

  // 2. 복수 종목 조회 테스트
  console.log('📝 2단계: 복수 종목 조회 테스트');
  console.log('─'.repeat(50));

  const testSymbols = ['005930', '000660', '035420', '035720', '207940'];
  console.log(`종목: ${testSymbols.join(', ')}\n`);

  try {
    const prices = await kisApi.getBatchPrices(testSymbols);

    console.log('✅ 조회 결과:\n');

    prices.forEach((stock, index) => {
      const arrow = stock.change_rate > 0 ? '▲' : stock.change_rate < 0 ? '▼' : '─';
      const color = stock.change_rate > 0 ? '\x1b[31m' : stock.change_rate < 0 ? '\x1b[34m' : '\x1b[0m';
      const reset = '\x1b[0m';

      console.log(`${index + 1}. ${stock.name} (${stock.symbol})`);
      console.log(`   현재가: ${stock.price.toLocaleString()}원`);
      console.log(`   ${color}${arrow} ${stock.change.toLocaleString()}원 (${stock.change_rate > 0 ? '+' : ''}${stock.change_rate}%)${reset}`);
      console.log(`   거래량: ${stock.volume.toLocaleString()}주`);
      console.log(`   고가: ${stock.high.toLocaleString()}원 | 저가: ${stock.low.toLocaleString()}원`);
      console.log('');
    });
  } catch (error: any) {
    console.error('❌ 복수 종목 조회 실패:', error.message);
  }

  // 3. 호가 조회 테스트
  console.log('📝 3단계: 호가 조회 테스트 (삼성전자)');
  console.log('─'.repeat(50));

  try {
    const orderbook = await kisApi.getOrderbook('005930');

    console.log('✅ 호가 조회 결과:\n');
    console.log('매도 호가 (높은 가격순):');
    orderbook.asks.slice(0, 5).forEach((ask, i) => {
      console.log(`  ${5 - i}. ${ask.price.toLocaleString()}원 | ${ask.qty.toLocaleString()}주`);
    });

    console.log('\n─ 현재가 ─\n');

    console.log('매수 호가 (낮은 가격순):');
    orderbook.bids.slice(0, 5).forEach((bid, i) => {
      console.log(`  ${i + 1}. ${bid.price.toLocaleString()}원 | ${bid.qty.toLocaleString()}주`);
    });

    console.log('');
  } catch (error: any) {
    console.error('❌ 호가 조회 실패:', error.message);
  }

  // 4. 실시간 구독 테스트 (5초간)
  console.log('📝 4단계: 실시간 시세 구독 테스트 (5초간)');
  console.log('─'.repeat(50));

  const unsubscribe = kisApi.subscribeRealtime(['005930', '000660'], (stock) => {
    const arrow = stock.change_rate > 0 ? '▲' : stock.change_rate < 0 ? '▼' : '─';
    const color = stock.change_rate > 0 ? '\x1b[31m' : stock.change_rate < 0 ? '\x1b[34m' : '\x1b[0m';
    const reset = '\x1b[0m';

    console.log(
      `[${new Date().toLocaleTimeString()}] ${stock.name} ` +
      `${color}${stock.price.toLocaleString()}원 ${arrow} ${stock.change_rate > 0 ? '+' : ''}${stock.change_rate}%${reset}`
    );
  }, 2000);  // 2초마다 순환 조회

  // 5초 후 구독 해제
  setTimeout(() => {
    unsubscribe();
    console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('✅ 모든 테스트 완료!');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
    process.exit(0);
  }, 5000);
}

main().catch((error) => {
  console.error('\n❌ 테스트 실행 중 오류 발생:', error);
  process.exit(1);
});
