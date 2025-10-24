import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Server, RefreshCw, CheckCircle, XCircle, AlertTriangle, Pause, Play } from 'lucide-react';
import { adminApi } from '@/lib/adminApi';
import type { ServiceStatus } from '@/types';
import toast from 'react-hot-toast';

export default function Services() {
  const queryClient = useQueryClient();

  const { data: servicesHealth, refetch, isLoading } = useQuery({
    queryKey: ['services-health'],
    queryFn: () => adminApi.getServicesHealth(),
    refetchInterval: 30000, // 30초마다 자동 갱신
  });

  // 뉴스 크롤러 스케줄러 상태 조회
  const { data: crawlerStatus } = useQuery({
    queryKey: ['news-crawler-status'],
    queryFn: () => adminApi.getNewsCrawlerStatus(),
    refetchInterval: 10000, // 10초마다 갱신
  });

  // 일시중지
  const pauseMutation = useMutation({
    mutationFn: () => adminApi.pauseNewsCrawler(),
    onSuccess: (data) => {
      toast.success(data.message || '뉴스 크롤러가 일시중지되었습니다');
      queryClient.invalidateQueries({ queryKey: ['news-crawler-status'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || '일시중지 실패');
    },
  });

  // 재개
  const resumeMutation = useMutation({
    mutationFn: () => adminApi.resumeNewsCrawler(),
    onSuccess: (data) => {
      toast.success(data.message || '뉴스 크롤러가 재개되었습니다');
      queryClient.invalidateQueries({ queryKey: ['news-crawler-status'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || '재개 실패');
    },
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'degraded':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'offline':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Server className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'online':
        return <span className="badge badge-success">정상</span>;
      case 'degraded':
        return <span className="badge badge-warning">저하</span>;
      case 'offline':
        return <span className="badge badge-danger">오프라인</span>;
      default:
        return <span className="badge">알 수 없음</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">서비스 모니터링</h1>
          <p className="text-gray-600 mt-2">Railway 배포 서비스의 상태를 실시간으로 확인하세요</p>
        </div>
        <button
          onClick={() => refetch()}
          className="btn btn-primary flex items-center space-x-2"
          disabled={isLoading}
        >
          <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>새로고침</span>
        </button>
      </div>

      {/* 전체 상태 요약 */}
      {servicesHealth && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="card">
            <p className="text-sm text-gray-600">전체 상태</p>
            <p className="text-2xl font-bold text-gray-900 mt-2 capitalize">
              {servicesHealth.overall_status === 'healthy'
                ? '정상'
                : servicesHealth.overall_status === 'warning'
                ? '경고'
                : '위험'}
            </p>
            <span
              className={`badge mt-3 ${
                servicesHealth.overall_status === 'healthy'
                  ? 'badge-success'
                  : servicesHealth.overall_status === 'warning'
                  ? 'badge-warning'
                  : 'badge-danger'
              }`}
            >
              {servicesHealth.overall_status}
            </span>
          </div>

          <div className="card">
            <p className="text-sm text-gray-600">온라인 서비스</p>
            <p className="text-2xl font-bold text-green-600 mt-2">{servicesHealth.online}</p>
            <p className="text-xs text-gray-500 mt-3">/ {servicesHealth.total_services} 서비스</p>
          </div>

          <div className="card">
            <p className="text-sm text-gray-600">저하 서비스</p>
            <p className="text-2xl font-bold text-yellow-600 mt-2">{servicesHealth.degraded}</p>
            <p className="text-xs text-gray-500 mt-3">성능 저하 중</p>
          </div>

          <div className="card">
            <p className="text-sm text-gray-600">오프라인 서비스</p>
            <p className="text-2xl font-bold text-red-600 mt-2">{servicesHealth.offline}</p>
            <p className="text-xs text-gray-500 mt-3">응답 없음</p>
          </div>
        </div>
      )}

      {/* 서비스 목록 */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">서비스 상세</h2>

        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="text-gray-500 mt-4">서비스 상태 확인 중...</p>
          </div>
        ) : servicesHealth?.services && servicesHealth.services.length > 0 ? (
          <div className="space-y-4">
            {servicesHealth.services.map((service: ServiceStatus) => (
              <div
                key={service.name}
                className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(service.status)}
                      <h3 className="text-lg font-semibold text-gray-900">{service.description}</h3>
                      {getStatusBadge(service.status)}
                    </div>

                    <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-4">
                      <div>
                        <p className="text-xs text-gray-500">서비스 이름</p>
                        <p className="text-sm font-medium text-gray-900 mt-1">{service.name}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">응답 시간</p>
                        <p className="text-sm font-medium text-gray-900 mt-1">
                          {service.response_time_ms ? `${service.response_time_ms}ms` : '-'}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">마지막 확인</p>
                        <p className="text-sm font-medium text-gray-900 mt-1">
                          {new Date(service.last_checked).toLocaleTimeString('ko-KR')}
                        </p>
                      </div>
                    </div>

                    {service.error_message && (
                      <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-sm text-red-800">
                          <strong>에러:</strong> {service.error_message}
                        </p>
                      </div>
                    )}

                    <div className="mt-4">
                      <p className="text-xs text-gray-500">URL</p>
                      <p className="text-sm text-gray-700 font-mono mt-1 break-all">{service.url}</p>
                    </div>

                    {/* 뉴스 크롤러 제어 버튼 */}
                    {service.name === 'news-crawler' && crawlerStatus && (
                      <div className="mt-6 pt-4 border-t border-gray-200">
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <p className="text-sm font-semibold text-gray-900">스케줄러 제어</p>
                            <p className="text-xs text-gray-500 mt-1">
                              상태:{' '}
                              <span
                                className={`font-medium ${
                                  crawlerStatus.status === 'running'
                                    ? 'text-green-600'
                                    : crawlerStatus.status === 'paused'
                                    ? 'text-yellow-600'
                                    : 'text-gray-600'
                                }`}
                              >
                                {crawlerStatus.status === 'running'
                                  ? '실행 중'
                                  : crawlerStatus.status === 'paused'
                                  ? '일시중지됨'
                                  : '정지됨'}
                              </span>
                            </p>
                          </div>
                          <div className="flex space-x-2">
                            {crawlerStatus.status === 'running' ? (
                              <button
                                onClick={() => pauseMutation.mutate()}
                                disabled={pauseMutation.isPending}
                                className="btn btn-sm flex items-center space-x-2 bg-yellow-600 text-white hover:bg-yellow-700"
                              >
                                <Pause className="w-4 h-4" />
                                <span>{pauseMutation.isPending ? '일시중지 중...' : '일시중지'}</span>
                              </button>
                            ) : (
                              <button
                                onClick={() => resumeMutation.mutate()}
                                disabled={resumeMutation.isPending}
                                className="btn btn-sm flex items-center space-x-2 bg-green-600 text-white hover:bg-green-700"
                              >
                                <Play className="w-4 h-4" />
                                <span>{resumeMutation.isPending ? '재개 중...' : '재개'}</span>
                              </button>
                            )}
                          </div>
                        </div>

                        {/* Job 정보 */}
                        {crawlerStatus.jobs && crawlerStatus.jobs.length > 0 && (
                          <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                            <p className="text-xs font-medium text-gray-700 mb-2">실행 스케줄</p>
                            {crawlerStatus.jobs.map((job) => (
                              <div key={job.id} className="text-xs text-gray-600">
                                <p>
                                  <strong>{job.name}</strong>
                                </p>
                                {job.next_run_time && (
                                  <p className="text-gray-500 mt-1">
                                    다음 실행:{' '}
                                    {new Date(job.next_run_time).toLocaleString('ko-KR', {
                                      month: 'short',
                                      day: 'numeric',
                                      hour: '2-digit',
                                      minute: '2-digit',
                                    })}
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Server className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">서비스 정보를 불러올 수 없습니다</p>
          </div>
        )}

        {servicesHealth && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="flex items-center justify-between text-sm text-gray-600">
              <span>평균 응답 시간: {servicesHealth.avg_response_time_ms?.toFixed(0) || 0}ms</span>
              <span>마지막 업데이트: {new Date(servicesHealth.checked_at).toLocaleString('ko-KR')}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
