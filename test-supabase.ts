/**
 * Supabase 연결 테스트
 */
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const supabaseUrl = process.env.VITE_SUPABASE_URL || '';
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY || '';

console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('🔍 Supabase 연결 테스트');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

console.log(`URL: ${supabaseUrl}`);
console.log(`Key: ${supabaseKey.substring(0, 20)}...\n`);

const supabase = createClient(supabaseUrl, supabaseKey);

async function testConnection() {
  try {
    // 1. 테이블 목록 조회
    console.log('📝 1단계: 테이블 목록 조회');
    console.log('─'.repeat(50));

    const { data: tables, error: tablesError } = await supabase
      .from('news')
      .select('id')
      .limit(1);

    if (tablesError) {
      console.error('❌ 테이블 접근 실패:', tablesError.message);
    } else {
      console.log('✅ news 테이블 접근 성공\n');
    }

    // 2. 샘플 뉴스 데이터 조회
    console.log('📝 2단계: 샘플 뉴스 데이터 조회');
    console.log('─'.repeat(50));

    const { data: news, error: newsError } = await supabase
      .from('news')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(3);

    if (newsError) {
      console.error('❌ 뉴스 조회 실패:', newsError.message);
    } else {
      console.log(`✅ ${news?.length || 0}개의 뉴스 조회 성공\n`);

      news?.forEach((item, index) => {
        console.log(`${index + 1}. ${item.title}`);
        console.log(`   출처: ${item.source}`);
        console.log(`   감성: ${item.sentiment_score || 'N/A'}`);
        console.log(`   영향도: ${item.impact_score || 'N/A'}`);
        console.log(`   권고: ${item.recommended_action || 'N/A'}`);
        console.log('');
      });
    }

    // 3. 주가 데이터 조회
    console.log('📝 3단계: 주가 데이터 조회');
    console.log('─'.repeat(50));

    const { data: prices, error: pricesError } = await supabase
      .from('stock_prices')
      .select('*')
      .order('timestamp', { ascending: false })
      .limit(5);

    if (pricesError) {
      console.error('❌ 주가 조회 실패:', pricesError.message);
    } else {
      console.log(`✅ ${prices?.length || 0}개의 주가 데이터 조회 성공\n`);

      prices?.forEach((item, index) => {
        console.log(`${index + 1}. ${item.symbol}`);
        console.log(`   가격: ${Number(item.price).toLocaleString()}원`);
        console.log(`   등락률: ${item.change_rate}%`);
        console.log(`   시간: ${new Date(item.timestamp).toLocaleString('ko-KR')}`);
        console.log('');
      });
    }

    // 4. 뉴스 키워드 조회
    console.log('📝 4단계: 뉴스 키워드 매핑 조회');
    console.log('─'.repeat(50));

    const { data: keywords, error: keywordsError } = await supabase
      .from('news_keywords')
      .select('*')
      .limit(5);

    if (keywordsError) {
      console.error('❌ 키워드 조회 실패:', keywordsError.message);
    } else {
      console.log(`✅ ${keywords?.length || 0}개의 종목 키워드 조회 성공\n`);

      keywords?.forEach((item, index) => {
        console.log(`${index + 1}. ${item.symbol}`);
        console.log(`   키워드: ${item.keywords?.join(', ')}`);
        console.log('');
      });
    }

    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('✅ Supabase 연결 테스트 완료!');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  } catch (error) {
    console.error('\n❌ 테스트 실행 중 오류:', error);
  }
}

testConnection();
