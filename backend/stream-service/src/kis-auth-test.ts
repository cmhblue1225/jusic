/**
 * 한국투자증권 API 토큰 발급 직접 테스트
 * 다양한 형식으로 시도해봅니다.
 */
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const APP_KEY = process.env.KIS_APP_KEY || '';
const APP_SECRET = process.env.KIS_APP_SECRET || '';
const BASE_URL = process.env.KIS_BASE_URL || '';

async function testTokenRequest1() {
  console.log('\n🔍 테스트 1: 기본 형식 (appkey/appsecret)');
  console.log('─'.repeat(50));

  try {
    const response = await axios.post(`${BASE_URL}/oauth2/tokenP`, {
      grant_type: 'client_credentials',
      appkey: APP_KEY,
      appsecret: APP_SECRET,
    }, {
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 10000,
    });

    console.log('✅ 성공!');
    console.log('응답:', response.data);
    return true;
  } catch (error: any) {
    console.log('❌ 실패:', error.response?.data || error.message);
    return false;
  }
}

async function testTokenRequest2() {
  console.log('\n🔍 테스트 2: 대문자 형식 (appKey/appSecret)');
  console.log('─'.repeat(50));

  try {
    const response = await axios.post(`${BASE_URL}/oauth2/tokenP`, {
      grant_type: 'client_credentials',
      appKey: APP_KEY,
      appSecret: APP_SECRET,
    }, {
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 10000,
    });

    console.log('✅ 성공!');
    console.log('응답:', response.data);
    return true;
  } catch (error: any) {
    console.log('❌ 실패:', error.response?.data || error.message);
    return false;
  }
}

async function testTokenRequest3() {
  console.log('\n🔍 테스트 3: JSON 문자열 형식');
  console.log('─'.repeat(50));

  try {
    const body = JSON.stringify({
      grant_type: 'client_credentials',
      appkey: APP_KEY,
      appsecret: APP_SECRET,
    });

    const response = await axios.post(`${BASE_URL}/oauth2/tokenP`, body, {
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
      },
      timeout: 10000,
    });

    console.log('✅ 성공!');
    console.log('응답:', response.data);
    return true;
  } catch (error: any) {
    console.log('❌ 실패:', error.response?.data || error.message);
    return false;
  }
}

async function testTokenRequest4() {
  console.log('\n🔍 테스트 4: 헤더에 key 포함');
  console.log('─'.repeat(50));

  try {
    const response = await axios.post(`${BASE_URL}/oauth2/tokenP`, {
      grant_type: 'client_credentials',
    }, {
      headers: {
        'Content-Type': 'application/json',
        'appkey': APP_KEY,
        'appsecret': APP_SECRET,
      },
      timeout: 10000,
    });

    console.log('✅ 성공!');
    console.log('응답:', response.data);
    return true;
  } catch (error: any) {
    console.log('❌ 실패:', error.response?.data || error.message);
    return false;
  }
}

async function testTokenRequest5() {
  console.log('\n🔍 테스트 5: URL에 key 포함 (Query String)');
  console.log('─'.repeat(50));

  try {
    const response = await axios.post(
      `${BASE_URL}/oauth2/tokenP?grant_type=client_credentials&appkey=${APP_KEY}&appsecret=${APP_SECRET}`,
      {},
      {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 10000,
      }
    );

    console.log('✅ 성공!');
    console.log('응답:', response.data);
    return true;
  } catch (error: any) {
    console.log('❌ 실패:', error.response?.data || error.message);
    return false;
  }
}

async function main() {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🔐 한국투자증권 토큰 발급 테스트');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`\nBase URL: ${BASE_URL}`);
  console.log(`APP_KEY: ${APP_KEY.substring(0, 10)}...`);
  console.log(`APP_SECRET: ${APP_SECRET.substring(0, 10)}...`);

  const tests = [
    testTokenRequest1,
    testTokenRequest2,
    testTokenRequest3,
    testTokenRequest4,
    testTokenRequest5,
  ];

  for (const test of tests) {
    const success = await test();
    if (success) {
      console.log('\n✅ 성공한 방식을 찾았습니다!');
      break;
    }
    // 다음 테스트 전 잠시 대기
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('테스트 완료');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
}

main();
