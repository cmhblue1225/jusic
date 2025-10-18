/**
 * 데이터 서비스 - 종목 검색 API
 */
import express, { Request, Response } from 'express';
import cors from 'cors';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.join(__dirname, '../../../.env') });

const app = express();
const PORT = process.env.DATA_SERVICE_PORT || 3003;

// Supabase 클라이언트
const supabase = createClient(
  process.env.VITE_SUPABASE_URL!,
  process.env.VITE_SUPABASE_ANON_KEY!
);

// 미들웨어
app.use(cors());
app.use(express.json());

/**
 * 종목 검색 API
 * GET /api/stocks/search?q=검색어&limit=10
 */
app.get('/api/stocks/search', async (req: Request, res: Response) => {
  try {
    const { q, limit = '10' } = req.query;

    if (!q || typeof q !== 'string') {
      return res.status(400).json({
        error: '검색어(q)가 필요합니다.',
      });
    }

    const searchQuery = q.trim();
    const limitNum = Math.min(parseInt(limit as string, 10) || 10, 50);

    // 검색 쿼리: 종목코드 또는 종목명으로 검색
    const { data, error } = await supabase
      .from('stock_master')
      .select('symbol, name, market')
      .or(`symbol.ilike.%${searchQuery}%,name.ilike.%${searchQuery}%`)
      .order('symbol', { ascending: true })
      .limit(limitNum);

    if (error) {
      console.error('종목 검색 실패:', error);
      return res.status(500).json({
        error: '종목 검색 중 오류가 발생했습니다.',
      });
    }

    res.json({
      success: true,
      query: searchQuery,
      count: data?.length || 0,
      results: data || [],
    });
  } catch (error: any) {
    console.error('종목 검색 API 오류:', error);
    res.status(500).json({
      error: '서버 오류가 발생했습니다.',
    });
  }
});

/**
 * 종목 상세 조회 API
 * GET /api/stocks/:symbol
 */
app.get('/api/stocks/:symbol', async (req: Request, res: Response) => {
  try {
    const { symbol } = req.params;

    if (!/^\d{6}$/.test(symbol)) {
      return res.status(400).json({
        error: '유효하지 않은 종목코드입니다. (6자리 숫자 필요)',
      });
    }

    const { data, error } = await supabase
      .from('stock_master')
      .select('*')
      .eq('symbol', symbol)
      .single();

    if (error) {
      if (error.code === 'PGRST116') {
        return res.status(404).json({
          error: '종목을 찾을 수 없습니다.',
        });
      }
      console.error('종목 조회 실패:', error);
      return res.status(500).json({
        error: '종목 조회 중 오류가 발생했습니다.',
      });
    }

    res.json({
      success: true,
      stock: data,
    });
  } catch (error: any) {
    console.error('종목 상세 조회 API 오류:', error);
    res.status(500).json({
      error: '서버 오류가 발생했습니다.',
    });
  }
});

/**
 * 헬스 체크
 */
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'OK',
    service: 'data-service',
    timestamp: new Date().toISOString(),
  });
});

app.listen(PORT, () => {
  console.log(`🚀 데이터 서비스가 포트 ${PORT}에서 실행 중입니다.`);
  console.log(`   - 종목 검색: http://localhost:${PORT}/api/stocks/search?q=삼성`);
  console.log(`   - 종목 상세: http://localhost:${PORT}/api/stocks/:symbol`);
  console.log(`   - 헬스 체크: http://localhost:${PORT}/health`);
});
