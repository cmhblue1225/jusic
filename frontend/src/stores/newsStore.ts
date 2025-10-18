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
  fetchNews: (limit?: number) => Promise<void>;
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
   * 전체 뉴스 조회 (최신순)
   */
  fetchNews: async (limit = 50) => {
    try {
      set({ loading: true, error: null, selectedSymbol: null });

      const { data, error } = await supabase
        .from('news')
        .select('*')
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
