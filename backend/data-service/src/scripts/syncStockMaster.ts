/**
 * 종목 마스터 데이터 동기화 스크립트
 * KIS API에서 전체 종목 정보를 가져와 Supabase에 저장
 */
import { createClient } from '@supabase/supabase-js';
import { KISApiClient } from '../lib/kisApi';
import dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.join(__dirname, '../../../../.env') });

const supabaseUrl = process.env.VITE_SUPABASE_URL!;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_KEY!;
const kisAppKey = process.env.KIS_APP_KEY!;
const kisAppSecret = process.env.KIS_APP_SECRET!;

if (!supabaseUrl || !supabaseServiceKey) {
  throw new Error('VITE_SUPABASE_URL 및 SUPABASE_SERVICE_KEY 환경변수가 필요합니다.');
}

if (!kisAppKey || !kisAppSecret) {
  throw new Error('KIS_APP_KEY 및 KIS_APP_SECRET 환경변수가 필요합니다.');
}

const supabase = createClient(supabaseUrl, supabaseServiceKey);

async function syncStockMaster() {
  console.log('='.repeat(60));
  console.log('📊 종목 마스터 데이터 동기화 시작');
  console.log('='.repeat(60));

  try {
    // 1. KIS API로부터 전체 종목 정보 가져오기
    const kisClient = new KISApiClient(kisAppKey, kisAppSecret);
    const stocks = await kisClient.getAllStocks();

    console.log(`\n✅ 총 ${stocks.length}개 종목 조회 완료`);

    if (stocks.length === 0) {
      console.warn('⚠️  조회된 종목이 없습니다. API 설정을 확인하세요.');
      return;
    }

    // 2. Supabase에 upsert (없으면 추가, 있으면 업데이트)
    console.log('\n📤 Supabase에 데이터 저장 중...');

    const batchSize = 1000;
    let successCount = 0;
    let errorCount = 0;

    for (let i = 0; i < stocks.length; i += batchSize) {
      const batch = stocks.slice(i, i + batchSize);

      const { data, error } = await supabase
        .from('stock_master')
        .upsert(
          batch.map(stock => ({
            symbol: stock.symbol,
            name: stock.name,
            market: stock.market,
            sector: stock.sector,
            listed_shares: stock.listed_shares?.toString(),
            last_updated: new Date().toISOString(),
          })),
          { onConflict: 'symbol' }
        );

      if (error) {
        console.error(`❌ 배치 ${i / batchSize + 1} 저장 실패:`, error.message);
        errorCount += batch.length;
      } else {
        successCount += batch.length;
        console.log(`   배치 ${i / batchSize + 1}/${Math.ceil(stocks.length / batchSize)}: ${batch.length}개 저장 완료`);
      }
    }

    // 3. 결과 요약
    console.log('\n' + '='.repeat(60));
    console.log('📊 동기화 완료');
    console.log('='.repeat(60));
    console.log(`✅ 성공: ${successCount}개`);
    console.log(`❌ 실패: ${errorCount}개`);
    console.log(`📅 동기화 시간: ${new Date().toLocaleString('ko-KR')}`);

    // 4. 샘플 데이터 출력
    console.log('\n📋 샘플 데이터 (처음 5개):');
    stocks.slice(0, 5).forEach((stock, idx) => {
      console.log(`   ${idx + 1}. [${stock.symbol}] ${stock.name} (${stock.market})`);
    });

  } catch (error: any) {
    console.error('\n❌ 동기화 실패:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

// 실행
syncStockMaster();
