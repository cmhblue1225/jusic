import { useQuery } from '@tanstack/react-query';
import { Users, Activity, Database, TrendingUp, AlertCircle } from 'lucide-react';
import { adminApi } from '@/lib/adminApi';

// 통계 카드 컴포넌트
function StatCard({
  title,
  value,
  change,
  icon: Icon,
  color,
}: {
  title: string;
  value: string | number;
  change?: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}) {
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
          {change && <p className="text-sm text-gray-500 mt-1">{change}</p>}
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-8 h-8 text-white" />
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  // 메트릭 요약 조회
  const { data: metricsSummary } = useQuery({
    queryKey: ['metrics-summary'],
    queryFn: () => adminApi.getMetricsSummary(24),
    refetchInterval: 60000, // 1분마다 갱신
  });

  // 서비스 헬스 조회
  const { data: servicesHealth } = useQuery({
    queryKey: ['services-health'],
    queryFn: () => adminApi.getServicesHealth(),
    refetchInterval: 30000, // 30초마다 갱신
  });

  // DB 통계 조회
  const { data: dbStats } = useQuery({
    queryKey: ['database-statistics'],
    queryFn: () => adminApi.getDatabaseStatistics(),
  });

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">대시보드</h1>
        <p className="text-gray-600 mt-2">시스템 전체 상태를 한눈에 확인하세요</p>
      </div>

      {/* 통계 카드 그리드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="전체 사용자"
          value={metricsSummary?.user_statistics.total_users || 0}
          icon={Users}
          color="bg-blue-500"
        />
        <StatCard
          title="보유 종목"
          value={metricsSummary?.user_statistics.total_portfolios || 0}
          icon={TrendingUp}
          color="bg-green-500"
        />
        <StatCard
          title="생성된 레포트"
          value={metricsSummary?.user_statistics.total_reports || 0}
          icon={Activity}
          color="bg-purple-500"
        />
        <StatCard
          title="DB 테이블"
          value={dbStats ? Object.keys(dbStats.users).length : 12}
          icon={Database}
          color="bg-orange-500"
        />
      </div>

      {/* 서비스 상태 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 서비스 헬스 */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">서비스 상태</h2>
          {servicesHealth ? (
            <div className="space-y-3">
              {/* 전체 상태 */}
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium text-gray-900">전체 상태</span>
                <span
                  className={`badge ${
                    servicesHealth.overall_status === 'healthy'
                      ? 'badge-success'
                      : servicesHealth.overall_status === 'warning'
                      ? 'badge-warning'
                      : 'badge-danger'
                  }`}
                >
                  {servicesHealth.overall_status === 'healthy'
                    ? '정상'
                    : servicesHealth.overall_status === 'warning'
                    ? '경고'
                    : '위험'}
                </span>
              </div>

              {/* 서비스별 상태 */}
              {servicesHealth.services?.map((service: any) => (
                <div key={service.name} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        service.status === 'online'
                          ? 'bg-green-500'
                          : service.status === 'degraded'
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      }`}
                    />
                    <span className="text-sm font-medium text-gray-700">{service.description}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-gray-500">
                      {service.response_time_ms ? `${service.response_time_ms}ms` : '-'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
              <p className="text-sm text-gray-500 mt-2">로딩 중...</p>
            </div>
          )}
        </div>

        {/* 시스템 메트릭 */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">시스템 메트릭</h2>
          {metricsSummary ? (
            <div className="space-y-4">
              {/* 평균 응답 시간 */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">평균 응답 시간</span>
                  <span className="text-sm text-gray-900 font-mono">
                    {servicesHealth?.avg_response_time_ms?.toFixed(0) || 0}ms
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      (servicesHealth?.avg_response_time_ms || 0) < 200
                        ? 'bg-green-500'
                        : (servicesHealth?.avg_response_time_ms || 0) < 500
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{
                      width: `${Math.min((servicesHealth?.avg_response_time_ms || 0) / 10, 100)}%`,
                    }}
                  />
                </div>
              </div>

              {/* 비즈니스 메트릭 */}
              {metricsSummary.business_metrics && Object.keys(metricsSummary.business_metrics).length > 0 ? (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-gray-700">오늘의 비즈니스 지표</h3>
                  {Object.entries(metricsSummary.business_metrics).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between text-sm">
                      <span className="text-gray-600 capitalize">{key.replace(/_/g, ' ')}</span>
                      <span className="font-medium text-gray-900">{value}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-4">
                  <AlertCircle className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">오늘 수집된 비즈니스 메트릭이 없습니다</p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
              <p className="text-sm text-gray-500 mt-2">로딩 중...</p>
            </div>
          )}
        </div>
      </div>

      {/* 데이터베이스 통계 */}
      {dbStats && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">데이터베이스 통계</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <p className="text-sm text-gray-600">사용자</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{dbStats.users?.total || 0}</p>
              <p className="text-xs text-gray-500 mt-1">관리자: {dbStats.users?.admins || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">포트폴리오</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{dbStats.portfolios?.total || 0}</p>
              <p className="text-xs text-gray-500 mt-1">관심종목: {dbStats.portfolios?.watchlist || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">레포트</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{dbStats.reports?.total || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">뉴스</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{dbStats.news?.total || 0}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
