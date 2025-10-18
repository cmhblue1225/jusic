/**
 * Portfolio Store - 보유 종목 관리
 * Zustand를 사용한 전역 상태 관리
 * Phase 2.2.1: priceStore와 연동하여 실시간 수익률 계산
 */
import { create } from 'zustand';
import { supabase } from '../lib/supabase';
import { usePriceStore } from './priceStore';
import type {
  PortfolioItem,
  PortfolioWithProfit,
  ProfitData
} from '../lib/profitCalculator';
import {
  calculatePortfolioWithPrices,
  calculatePortfolioStats,
} from '../lib/profitCalculator';

interface PortfolioState {
  items: PortfolioItem[];
  loading: boolean;
  error: string | null;

  // Actions
  fetchPortfolio: (userId: string) => Promise<void>;
  addStock: (userId: string, symbol: string, name: string, quantity: number, avgPrice: number) => Promise<void>;
  updateStock: (id: string, quantity: number, avgPrice: number) => Promise<void>;
  deleteStock: (id: string) => Promise<void>;
  clearError: () => void;

  // 실시간 수익률 계산 (Phase 2.2.1)
  getPortfolioWithProfit: () => PortfolioWithProfit[];
  getPortfolioStats: () => ProfitData;
}

export const usePortfolioStore = create<PortfolioState>((set) => ({
  items: [],
  loading: false,
  error: null,

  /**
   * 포트폴리오 조회
   */
  fetchPortfolio: async (userId: string) => {
    try {
      set({ loading: true, error: null });

      const { data, error } = await supabase
        .from('portfolios')
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
   * 종목 추가
   */
  addStock: async (userId: string, symbol: string, symbolName: string, quantity: number, avgPrice: number) => {
    try {
      set({ loading: true, error: null });

      // 이미 보유 중인 종목인지 확인
      const { data: existing } = await supabase
        .from('portfolios')
        .select('*')
        .eq('user_id', userId)
        .eq('symbol', symbol)
        .maybeSingle();

      if (existing) {
        // 기존 종목이 있으면 평균 단가 재계산
        const totalQty = existing.qty + quantity;
        const newAvgPrice =
          (existing.avg_price * existing.qty + avgPrice * quantity) / totalQty;

        const { error } = await supabase
          .from('portfolios')
          .update({
            qty: totalQty,
            avg_price: newAvgPrice,
            updated_at: new Date().toISOString(),
          })
          .eq('id', existing.id);

        if (error) throw error;
      } else {
        // 새로운 종목 추가
        const { error } = await supabase
          .from('portfolios')
          .insert({
            user_id: userId,
            symbol,
            symbol_name: symbolName,
            qty: quantity,
            avg_price: avgPrice,
          });

        if (error) throw error;
      }

      // 포트폴리오 다시 로드
      await usePortfolioStore.getState().fetchPortfolio(userId);
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  /**
   * 종목 수정
   */
  updateStock: async (id: string, quantity: number, avgPrice: number) => {
    try {
      set({ loading: true, error: null });

      const { data, error } = await supabase
        .from('portfolios')
        .update({
          qty: quantity,
          avg_price: avgPrice,
          updated_at: new Date().toISOString(),
        })
        .eq('id', id)
        .select()
        .single();

      if (error) throw error;

      // 상태 업데이트
      set((state) => ({
        items: state.items.map((item) =>
          item.id === id ? data : item
        ),
        loading: false,
      }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  /**
   * 종목 삭제
   */
  deleteStock: async (id: string) => {
    try {
      set({ loading: true, error: null });

      const { error } = await supabase
        .from('portfolios')
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

  /**
   * 실시간 시세를 적용한 포트폴리오 조회 (Phase 2.2.1)
   * priceStore에서 실시간 시세를 가져와서 평가금액 및 수익률 계산
   */
  getPortfolioWithProfit: (): PortfolioWithProfit[] => {
    const items: PortfolioItem[] = usePortfolioStore.getState().items;
    const priceStore = usePriceStore.getState();

    // 현재가 Map 생성 (symbol → price)
    const currentPrices = new Map<string, number>();
    items.forEach((item) => {
      const priceData = priceStore.getPrice(item.symbol);
      if (priceData) {
        currentPrices.set(item.symbol, priceData.price);
      }
    });

    // 실시간 시세를 적용한 포트폴리오 계산
    return calculatePortfolioWithPrices(items, currentPrices);
  },

  /**
   * 포트폴리오 전체 통계 (Phase 2.2.1)
   * 총 투자금액, 총 평가금액, 총 손익, 수익률
   */
  getPortfolioStats: () => {
    const portfolioWithProfit = usePortfolioStore.getState().getPortfolioWithProfit();
    return calculatePortfolioStats(portfolioWithProfit);
  },
}));
