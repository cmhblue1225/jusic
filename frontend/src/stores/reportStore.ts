/**
 * Report Store - 종목 레포트 상태 관리
 */
import { create } from 'zustand';

export interface StockReport {
  // 기본 정보
  symbol: string;
  symbol_name: string;
  report_date: string;

  // 주가 데이터
  current_price: number;
  change_rate: number;
  high_price: number;
  low_price: number;
  avg_price: number;
  volume: number;

  // 기술적 지표
  ma5: number | null;
  ma20: number | null;
  ma60: number | null;
  volume_ratio: number | null;
  volatility: number | null;
  bollinger_upper: number | null;
  bollinger_lower: number | null;

  // AI 분석 결과
  summary: string;
  risk_level: 'low' | 'medium' | 'high';
  recommendation: 'buy' | 'sell' | 'hold';
  evaluation_score: number;

  // 관련 뉴스
  related_news_count: number;

  // 메타데이터
  cached: boolean;
}

interface ReportState {
  // 상태
  currentReport: StockReport | null;
  bookmarks: StockReport[];
  loading: boolean;
  error: string | null;

  // 액션
  setCurrentReport: (report: StockReport | null) => void;
  setBookmarks: (bookmarks: StockReport[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useReportStore = create<ReportState>((set) => ({
  // 초기 상태
  currentReport: null,
  bookmarks: [],
  loading: false,
  error: null,

  // 액션
  setCurrentReport: (report) => set({ currentReport: report }),
  setBookmarks: (bookmarks) => set({ bookmarks }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));
