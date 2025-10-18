/**
 * Watchlist Store - 관심 종목 관리
 * Zustand를 사용한 전역 상태 관리
 */
import { create } from 'zustand';
import { supabase } from '../lib/supabase';

interface WatchlistItem {
  id: string;
  user_id: string;
  symbol: string;
  symbol_name: string;
  created_at: string;
}

interface WatchlistState {
  items: WatchlistItem[];
  loading: boolean;
  error: string | null;

  // Actions
  fetchWatchlist: (userId: string) => Promise<void>;
  addToWatchlist: (userId: string, symbol: string, name: string) => Promise<void>;
  removeFromWatchlist: (id: string) => Promise<void>;
  clearError: () => void;
}

export const useWatchlistStore = create<WatchlistState>((set) => ({
  items: [],
  loading: false,
  error: null,

  /**
   * 관심 종목 조회
   */
  fetchWatchlist: async (userId: string) => {
    try {
      set({ loading: true, error: null });

      const { data, error } = await supabase
        .from('watchlist')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: false });

      if (error) throw error;

      set({ items: data || [], loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  /**
   * 관심 종목 추가
   */
  addToWatchlist: async (userId: string, symbol: string, symbolName: string) => {
    try {
      set({ loading: true, error: null });

      // 이미 등록된 종목인지 확인
      const { data: existing } = await supabase
        .from('watchlist')
        .select('*')
        .eq('user_id', userId)
        .eq('symbol', symbol)
        .maybeSingle();

      if (existing) {
        throw new Error('이미 관심 종목에 등록된 종목입니다.');
      }

      const { error } = await supabase
        .from('watchlist')
        .insert({
          user_id: userId,
          symbol,
          symbol_name: symbolName,
        });

      if (error) throw error;

      // 관심 종목 다시 로드
      await useWatchlistStore.getState().fetchWatchlist(userId);
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  /**
   * 관심 종목 삭제
   */
  removeFromWatchlist: async (id: string) => {
    try {
      set({ loading: true, error: null });

      const { error } = await supabase
        .from('watchlist')
        .delete()
        .eq('id', id);

      if (error) throw error;

      // 상태 업데이트
      set((state) => ({
        items: state.items.filter((item) => item.id !== id),
        loading: false,
      }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  /**
   * 에러 초기화
   */
  clearError: () => set({ error: null }),
}));
