import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart3, TrendingUp, TrendingDown } from 'lucide-react';
import { adminApi } from '@/lib/adminApi';

export default function Metrics() {
  const [timeRange, setTimeRange] = useState(24);

  const { data: metricsSummary } = useQuery({
    queryKey: ['metrics-summary', timeRange],
    queryFn: () => adminApi.getMetricsSummary(timeRange),
    refetchInterval: 60000,
  });

  const { data: systemMetrics } = useQuery({
    queryKey: ['system-metrics', timeRange],
    queryFn: () => adminApi.getSystemMetrics({ hours: timeRange }),
  });

  const { data: businessMetrics } = useQuery({
    queryKey: ['business-metrics'],
    queryFn: () => adminApi.getBusinessMetrics({ days: 30 }),
  });

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">메트릭</h1>
          <p className="text-gray-600 mt-2">시스템 및 비즈니스 지표를 분석하세요</p>
        </div>

        {/* 시간 범위 선택 */}
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(Number(e.target.value))}
          className="input w-auto"
        >
          <option value={1}>최근 1시간</option>
          <option value={6}>최근 6시간</option>
          <option value={24}>최근 24시간</option>
          <option value={72}>최근 3일</option>
          <option value={168}>최근 7일</option>
        </select>
      </div>

      {/* 시스템 메트릭 요약 */}
      {metricsSummary && (
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">시스템 메트릭</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.entries(metricsSummary.system_metrics.avg_latency_by_service).map(
              ([service, latency]) => (
                <div key={service} className="card">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-medium text-gray-600 capitalize">{service}</p>
                    <BarChart3 className="w-5 h-5 text-primary-600" />
                  </div>
                  <p className="text-3xl font-bold text-gray-900">{latency.toFixed(0)}ms</p>
                  <p className="text-xs text-gray-500 mt-1">평균 응답 시간</p>

                  {metricsSummary.system_metrics.avg_error_rate_by_service[service] !==
                    undefined && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <p className="text-xs text-gray-500">에러율</p>
                      <p className="text-sm font-medium text-red-600">
                        {metricsSummary.system_metrics.avg_error_rate_by_service[service].toFixed(
                          2
                        )}
                        %
                      </p>
                    </div>
                  )}
                </div>
              )
            )}
          </div>
        </div>
      )}

      {/* 비즈니스 메트릭 */}
      {businessMetrics && businessMetrics.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">비즈니스 메트릭 (최근 30일)</h2>
          <div className="card">
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>메트릭</th>
                    <th>값</th>
                    <th>날짜</th>
                  </tr>
                </thead>
                <tbody>
                  {businessMetrics.slice(0, 20).map((metric: any) => (
                    <tr key={metric.metric_name + metric.date}>
                      <td className="font-medium text-gray-900 capitalize">
                        {metric.metric_name.replace(/_/g, ' ')}
                      </td>
                      <td className="text-gray-900 font-semibold">{metric.value}</td>
                      <td className="text-gray-600 text-sm">
                        {new Date(metric.date).toLocaleDateString('ko-KR')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* 사용자 통계 */}
      {metricsSummary?.user_statistics && (
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">사용자 통계</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="card">
              <p className="text-sm text-gray-600">전체 사용자</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {metricsSummary.user_statistics.total_users}
              </p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-600">포트폴리오</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {metricsSummary.user_statistics.total_portfolios}
              </p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-600">관심 종목</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {metricsSummary.user_statistics.total_watchlist}
              </p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-600">생성된 레포트</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {metricsSummary.user_statistics.total_reports}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
