/**
 * 공통 타입 정의
 */

export interface User {
  id: string;
  email: string;
  name?: string;
  settings: UserSettings;
  created_at: string;
  updated_at: string;
}

export interface UserSettings {
  tts_enabled: boolean;
  tts_speed: number;
  tts_volume: number;
  auto_tts_threshold: number;
  theme: 'light' | 'dark';
  font_size: 'normal' | 'large' | 'extra-large';
  high_contrast: boolean;
}

export interface Portfolio {
  id: string;
  user_id: string;
  symbol: string;
  symbol_name?: string;
  avg_price: number;
  qty: number;
  created_at: string;
  updated_at: string;
}

export interface Watchlist {
  id: string;
  user_id: string;
  symbol: string;
  symbol_name?: string;
  created_at: string;
}

export interface News {
  id: string;
  source: string;
  title: string;
  content?: string;
  url?: string;
  published_at: string;
  summary?: string;
  sentiment_score?: number; // -1 ~ 1
  impact_score?: number; // 0 ~ 1
  recommended_action?: 'buy' | 'sell' | 'hold';
  related_symbols?: string[];
  created_at: string;
}

export interface Alert {
  id: string;
  user_id: string;
  type: 'price_change' | 'news' | 'system';
  title: string;
  message: string;
  params?: Record<string, any>;
  status: 'unread' | 'read' | 'archived';
  created_at: string;
}

export interface StockPrice {
  id: string;
  symbol: string;
  price: number;
  change_rate?: number;
  volume?: number;
  high?: number;
  low?: number;
  open?: number;
  timestamp: string;
}

export interface AlertRule {
  id: string;
  user_id: string;
  rule_type: 'price_threshold' | 'volume_spike' | 'news_impact';
  conditions: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BacktestResult {
  id: string;
  user_id: string;
  strategy_name: string;
  params?: Record<string, any>;
  results?: {
    cagr?: number;
    mdd?: number;
    sharpe_ratio?: number;
    win_rate?: number;
  };
  created_at: string;
}
