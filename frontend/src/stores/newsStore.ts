/**
 * News Store - 뉴스 관리
 * Zustand를 사용한 전역 상태 관리
 */
import { create } from 'zustand';
import { supabase } from '../lib/supabase';

export interface NewsItem {
  id: string;
  source: string;
  title: string;
  content: string;
  url: string;
  related_symbols: string[];
  published_at: string;
  summary: string | null;
  sentiment_score: number | null; // -1 ~ 1
  impact_score: number | null; // 0 ~ 1
  recommended_action: string | null; // buy, sell, hold
  created_at: string;
}

interface NewsState {
  items: NewsItem[];
  loading: boolean;
  error: string | null;
  selectedSymbol: string | null; // 필터링용 종목 선택

  // Actions
  fetchNews: (userId?: string, limit?: number) => Promise<void>;
  fetchNewsBySymbol: (symbol: string) => Promise<void>;
  clearFilter: () => void;
  clearError: () => void;
}

export const useNewsStore = create<NewsState>((set) => ({
  items: [],
  loading: false,
  error: null,
  selectedSymbol: null,

  /**
   * 사용자 관련 뉴스 조회 (보유 종목 + 관심 종목)
   */
  fetchNews: async (userId?: string, limit = 100) => {
    try {
      set({ loading: true, error: null, selectedSymbol: null });

      // userId가 없으면 전체 뉴스 조회
      if (!userId) {
        const { data, error } = await supabase
          .from('news')
          .select('*')
          .order('published_at', { ascending: false })
          .limit(limit);

        if (error) throw error;
        set({ items: data || [], loading: false });
        return;
      }

      // 1. 사용자의 보유 종목 조회
      const { data: portfolioData } = await supabase
        .from('portfolios')
        .select('symbol')
        .eq('user_id', userId);

      // 2. 사용자의 관심 종목 조회
      const { data: watchlistData } = await supabase
        .from('watchlist')
        .select('symbol')
        .eq('user_id', userId);

      // 3. 종목 코드 추출 (중복 제거)
      const portfolioSymbols = portfolioData?.map((p) => p.symbol) || [];
      const watchlistSymbols = watchlistData?.map((w) => w.symbol) || [];
      const userSymbols = [...new Set([...portfolioSymbols, ...watchlistSymbols])];

      // 종목이 없으면 빈 배열 반환
      if (userSymbols.length === 0) {
        set({ items: [], loading: false });
        return;
      }

      // 4. 사용자 관련 종목의 뉴스만 조회
      const { data, error } = await supabase
        .from('news')
        .select('*')
        .overlaps('related_symbols', userSymbols) // 배열 겹침 체크
        .order('published_at', { ascending: false })
        .limit(limit);

      if (error) throw error;

      set({ items: data || [], loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  /**
   * 특정 종목 관련 뉴스 조회
   */
  fetchNewsBySymbol: async (symbol: string) => {
    try {
      set({ loading: true, error: null, selectedSymbol: symbol });

      const { data, error } = await supabase
        .from('news')
        .select('*')
        .contains('related_symbols', [symbol])
        .order('published_at', { ascending: false })
        .limit(50);

      if (error) throw error;

      set({ items: data || [], loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  /**
   * 필터 초기화
   */
  clearFilter: () => {
    set({ selectedSymbol: null });
  },

  /**
   * 에러 초기화
   */
  clearError: () => set({ error: null }),
}));
