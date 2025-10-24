import axios, { AxiosInstance } from 'axios';
import type {
  User,
  ServiceStatus,
  ServiceDetail,
  SystemMetric,
  BusinessMetric,
  AdminActivityLog,
  TableStatistics,
  MetricSummary,
  PaginationParams,
  FilterParams,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_ADMIN_API_URL || 'http://localhost:8000';

class AdminApi {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 요청 인터셉터: JWT 토큰 자동 추가
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 응답 인터셉터: 에러 처리
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          console.error('인증 만료 또는 실패');
          // 인증 실패 시 로그인 페이지로 리디렉션 (authStore에서 처리)
        }
        return Promise.reject(error);
      }
    );
  }

  private getToken(): string | null {
    // Supabase 세션에서 JWT 토큰 가져오기
    // Supabase v2는 sb-{project-ref}-auth-token 키를 사용
    const keys = Object.keys(localStorage).filter(key => key.startsWith('sb-') && key.endsWith('-auth-token'));

    if (keys.length > 0) {
      try {
        const session = localStorage.getItem(keys[0]);
        if (session) {
          const parsed = JSON.parse(session);
          return parsed.access_token || null;
        }
      } catch {
        return null;
      }
    }
    return null;
  }

  // 사용자 관리 API
  async getUsers(params?: PaginationParams & FilterParams): Promise<User[]> {
    const { data } = await this.client.get('/api/admin/users', { params });
    return data;
  }

  async getUser(userId: string): Promise<User> {
    const { data } = await this.client.get(`/api/admin/users/${userId}`);
    return data;
  }

  async updateUser(userId: string, updates: { name?: string; role?: string }): Promise<User> {
    const { data } = await this.client.patch(`/api/admin/users/${userId}`, updates);
    return data;
  }

  async suspendUser(userId: string): Promise<{ message: string; user_id: string }> {
    const { data } = await this.client.post(`/api/admin/users/${userId}/suspend`);
    return data;
  }

  async activateUser(userId: string): Promise<{ message: string; user_id: string }> {
    const { data } = await this.client.post(`/api/admin/users/${userId}/activate`);
    return data;
  }

  async deleteUser(userId: string): Promise<{ message: string; user_id: string; email: string }> {
    const { data } = await this.client.delete(`/api/admin/users/${userId}`);
    return data;
  }

  async getUserActivity(userId: string, params?: PaginationParams): Promise<any> {
    const { data } = await this.client.get(`/api/admin/users/${userId}/activity`, { params });
    return data;
  }

  // 서비스 모니터링 API
  async getServices(): Promise<ServiceStatus[]> {
    const { data } = await this.client.get('/api/admin/services');
    return data;
  }

  async getServiceDetail(serviceName: string): Promise<ServiceDetail> {
    const { data } = await this.client.get(`/api/admin/services/${serviceName}`);
    return data;
  }

  async getServicesHealth(): Promise<any> {
    const { data } = await this.client.get('/api/admin/services/health');
    return data;
  }

  async restartService(serviceName: string): Promise<{ message: string }> {
    const { data } = await this.client.post(`/api/admin/services/${serviceName}/restart`);
    return data;
  }

  // 메트릭 API
  async getSystemMetrics(params?: FilterParams): Promise<SystemMetric[]> {
    const { data } = await this.client.get('/api/admin/metrics/system', { params });
    return data;
  }

  async getBusinessMetrics(params?: FilterParams): Promise<BusinessMetric[]> {
    const { data } = await this.client.get('/api/admin/metrics/business', { params });
    return data;
  }

  async getMetricsSummary(hours: number = 24): Promise<MetricSummary> {
    const { data } = await this.client.get('/api/admin/metrics/summary', {
      params: { hours },
    });
    return data;
  }

  async getMetricTimeseries(metricName: string, hours: number = 24): Promise<any> {
    const { data } = await this.client.get(`/api/admin/metrics/timeseries/${metricName}`, {
      params: { hours },
    });
    return data;
  }

  // 데이터베이스 API
  async getDatabaseTables(): Promise<TableStatistics[]> {
    const { data } = await this.client.get('/api/admin/database/tables');
    return data;
  }

  async getTableDetail(tableName: string): Promise<any> {
    const { data } = await this.client.get(`/api/admin/database/tables/${tableName}`);
    return data;
  }

  async getDatabaseHealth(): Promise<any> {
    const { data } = await this.client.get('/api/admin/database/health');
    return data;
  }

  async getDatabaseStatistics(): Promise<any> {
    const { data } = await this.client.get('/api/admin/database/statistics');
    return data;
  }

  async executeQuery(query: string, description?: string): Promise<any> {
    const { data } = await this.client.post('/api/admin/database/query', {
      query,
      description,
    });
    return data;
  }

  // 로그 API
  async getAdminActivityLogs(params?: PaginationParams & FilterParams): Promise<AdminActivityLog[]> {
    const { data } = await this.client.get('/api/admin/logs/admin-activity', { params });
    return data;
  }

  async getLogStatistics(hours: number = 24): Promise<any> {
    const { data } = await this.client.get('/api/admin/logs/statistics', {
      params: { hours },
    });
    return data;
  }

  async getAvailableActions(): Promise<{ actions: string[]; descriptions: Record<string, string> }> {
    const { data } = await this.client.get('/api/admin/logs/actions');
    return data;
  }

  async exportLogs(hours: number = 24, format: 'json' | 'csv' = 'json'): Promise<any> {
    const { data } = await this.client.get('/api/admin/logs/export', {
      params: { hours, format },
    });
    return data;
  }

  // 뉴스 크롤러 제어 API
  async pauseNewsCrawler(): Promise<{ status: string; message: string }> {
    const { data } = await this.client.post('/api/admin/services/news-crawler/pause');
    return data;
  }

  async resumeNewsCrawler(): Promise<{ status: string; message: string }> {
    const { data } = await this.client.post('/api/admin/services/news-crawler/resume');
    return data;
  }

  async getNewsCrawlerStatus(): Promise<{
    status: string;
    state: number;
    jobs: Array<{ id: string; name: string; next_run_time: string | null }>;
    ai_analysis_enabled: boolean;
  }> {
    const { data } = await this.client.get('/api/admin/services/news-crawler/scheduler-status');
    return data;
  }

  // 캐시 관리 API
  async getCachedReports(): Promise<{
    cached_reports: Array<{
      symbol: string;
      report_date: string;
      cache_key: string;
      ttl_seconds: number;
      ttl_minutes: number;
    }>;
    total: number;
  }> {
    const { data } = await this.client.get('/api/admin/database/cache/reports');
    return data;
  }

  async deleteCachedReport(symbol: string, reportDate: string): Promise<{
    message: string;
    symbol: string;
    report_date: string;
  }> {
    const { data } = await this.client.delete(`/api/admin/database/cache/reports/${symbol}/${reportDate}`);
    return data;
  }
}

export const adminApi = new AdminApi();
