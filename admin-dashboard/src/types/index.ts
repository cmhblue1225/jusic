// 사용자 타입
export interface User {
  id: string;
  email: string;
  name?: string;
  role: 'user' | 'admin' | 'superadmin';
  created_at: string;
  updated_at?: string;
  settings?: Record<string, any>;
}

// 서비스 상태
export interface ServiceStatus {
  name: string;
  url: string;
  description: string;
  status: 'online' | 'offline' | 'degraded';
  response_time_ms?: number;
  last_checked: string;
  error_message?: string;
}

// 서비스 상세
export interface ServiceDetail extends ServiceStatus {
  health_data?: Record<string, any>;
  recent_errors: Array<Record<string, any>>;
  uptime_percentage?: number;
}

// 시스템 메트릭
export interface SystemMetric {
  service_name: string;
  metric_type: string;
  value: number;
  unit?: string;
  timestamp: string;
}

// 비즈니스 메트릭
export interface BusinessMetric {
  metric_name: string;
  value: number;
  date: string;
  metadata?: Record<string, any>;
}

// 관리자 활동 로그
export interface AdminActivityLog {
  id: string;
  admin_id: string;
  admin_email?: string;
  action: string;
  target_type?: string;
  target_id?: string;
  details?: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

// 테이블 통계
export interface TableStatistics {
  table_name: string;
  row_count: number;
  size_bytes?: number;
  last_updated?: string;
}

// 메트릭 요약
export interface MetricSummary {
  time_range: {
    start: string;
    end: string;
    hours: number;
  };
  system_metrics: {
    avg_latency_by_service: Record<string, number>;
    avg_error_rate_by_service: Record<string, number>;
  };
  business_metrics: Record<string, number>;
  user_statistics: {
    total_users: number;
    total_portfolios: number;
    total_watchlist: number;
    total_reports: number;
  };
  generated_at: string;
}

// API 응답 타입
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

// 페이지네이션
export interface PaginationParams {
  skip?: number;
  limit?: number;
}

// 필터 파라미터
export interface FilterParams {
  [key: string]: string | number | boolean | undefined;
}
