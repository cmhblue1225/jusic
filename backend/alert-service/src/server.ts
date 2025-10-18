import express from 'express';
import cors from 'cors';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

// Supabase 클라이언트
const supabase = createClient(
  process.env.SUPABASE_URL || '',
  process.env.SUPABASE_SERVICE_KEY || ''
);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'alert-service' });
});

// 알림 생성
app.post('/alerts', async (req, res) => {
  const { user_id, type, title, message, params } = req.body;

  try {
    const { data, error } = await supabase
      .table('alerts')
      .insert({
        user_id,
        type,
        title,
        message,
        params,
      })
      .select()
      .single();

    if (error) throw error;

    // TODO: Web Push 또는 FCM으로 푸시 알림 발송

    res.json({ success: true, alert: data });
  } catch (error) {
    console.error('Alert creation error:', error);
    res.status(500).json({ error: 'Failed to create alert' });
  }
});

// 알림 규칙 평가 (주기적으로 실행)
async function evaluateAlertRules() {
  console.log('[Alert Evaluation] 알림 규칙 평가 시작...');

  try {
    // 활성화된 알림 규칙 조회
    const { data: rules, error } = await supabase
      .table('alert_rules')
      .select('*')
      .eq('is_active', true);

    if (error) throw error;

    for (const rule of rules || []) {
      // 규칙 타입별 처리
      if (rule.rule_type === 'price_threshold') {
        await checkPriceThreshold(rule);
      } else if (rule.rule_type === 'volume_spike') {
        await checkVolumeSpike(rule);
      } else if (rule.rule_type === 'news_impact') {
        await checkNewsImpact(rule);
      }
    }
  } catch (error) {
    console.error('Alert evaluation error:', error);
  }

  console.log('[Alert Evaluation] 완료\n');
}

async function checkPriceThreshold(rule: any) {
  // 가격 변동 임계값 체크
  const { symbol, threshold } = rule.conditions;

  const { data: latestPrice } = await supabase
    .table('stock_prices')
    .select('*')
    .eq('symbol', symbol)
    .order('timestamp', { ascending: false })
    .limit(1)
    .single();

  if (latestPrice && Math.abs(latestPrice.change_rate) >= threshold) {
    // 알림 생성
    await supabase.table('alerts').insert({
      user_id: rule.user_id,
      type: 'price_change',
      title: `${symbol} 가격 변동 알림`,
      message: `${symbol} 종목이 ${latestPrice.change_rate.toFixed(2)}% ${
        latestPrice.change_rate > 0 ? '상승' : '하락'
      }했습니다.`,
      params: { symbol, price: latestPrice.price, change_rate: latestPrice.change_rate },
    });
  }
}

async function checkVolumeSpike(rule: any) {
  // 거래량 급증 체크 (실제 구현 필요)
  console.log('Volume spike check:', rule);
}

async function checkNewsImpact(rule: any) {
  // 뉴스 영향도 체크
  const { impact_threshold } = rule.conditions;

  const { data: news } = await supabase
    .table('news')
    .select('*')
    .gte('impact_score', impact_threshold)
    .order('created_at', { ascending: false })
    .limit(5);

  // 사용자 관심 종목과 매칭
  const { data: watchlist } = await supabase
    .table('watchlist')
    .select('symbol')
    .eq('user_id', rule.user_id);

  const userSymbols = watchlist?.map((w) => w.symbol) || [];

  for (const article of news || []) {
    const hasMatch = article.related_symbols?.some((s: string) => userSymbols.includes(s));

    if (hasMatch) {
      await supabase.table('alerts').insert({
        user_id: rule.user_id,
        type: 'news',
        title: `중요 뉴스 알림`,
        message: article.title,
        params: { news_id: article.id, symbols: article.related_symbols },
      });
    }
  }
}

// 30초마다 알림 규칙 평가
setInterval(evaluateAlertRules, 30000);

const PORT = process.env.PORT || 3004;

app.listen(PORT, () => {
  console.log(`🔔 Alert Service running on port ${PORT}`);
});
