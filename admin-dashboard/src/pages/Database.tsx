import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Database as DatabaseIcon, Table, Activity, Trash2, Clock } from 'lucide-react';
import { adminApi } from '@/lib/adminApi';
import type { TableStatistics } from '@/types';
import toast from 'react-hot-toast';

export default function Database() {
  const queryClient = useQueryClient();

  const { data: tables, isLoading } = useQuery({
    queryKey: ['database-tables'],
    queryFn: () => adminApi.getDatabaseTables(),
  });

  const { data: dbHealth } = useQuery({
    queryKey: ['database-health'],
    queryFn: () => adminApi.getDatabaseHealth(),
    refetchInterval: 60000,
  });

  const { data: dbStats } = useQuery({
    queryKey: ['database-statistics'],
    queryFn: () => adminApi.getDatabaseStatistics(),
  });

  // 캐시 목록 조회
  const { data: cacheData } = useQuery({
    queryKey: ['cached-reports'],
    queryFn: () => adminApi.getCachedReports(),
    refetchInterval: 15000, // 15초마다 갱신
  });

  // 캐시 삭제
  const deleteCacheMutation = useMutation({
    mutationFn: ({ symbol, reportDate }: { symbol: string; reportDate: string }) =>
      adminApi.deleteCachedReport(symbol, reportDate),
    onSuccess: (data) => {
      toast.success(data.message || '캐시가 삭제되었습니다');
      queryClient.invalidateQueries({ queryKey: ['cached-reports'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || '캐시 삭제 실패');
    },
  });

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('ko-KR').format(num);
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">데이터베이스 관리</h1>
        <p className="text-gray-600 mt-2">Supabase PostgreSQL 데이터베이스 상태 및 테이블 정보</p>
      </div>

      {/* DB 헬스 */}
      {dbHealth && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="card">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">DB 상태</p>
              <Activity
                className={`w-5 h-5 ${
                  dbHealth.status === 'healthy' ? 'text-green-500' : 'text-red-500'
                }`}
              />
            </div>
            <p className="text-2xl font-bold text-gray-900 mt-2 capitalize">
              {dbHealth.status === 'healthy' ? '정상' : '비정상'}
            </p>
            <span
              className={`badge mt-3 ${
                dbHealth.status === 'healthy' ? 'badge-success' : 'badge-danger'
              }`}
            >
              {dbHealth.status}
            </span>
          </div>

          <div className="card">
            <p className="text-sm text-gray-600">응답 시간</p>
            <p className="text-2xl font-bold text-gray-900 mt-2">
              {dbHealth.response_time_ms?.toFixed(0) || 0}ms
            </p>
          </div>

          <div className="card">
            <p className="text-sm text-gray-600">전체 테이블</p>
            <p className="text-2xl font-bold text-gray-900 mt-2">{dbHealth.total_tables || 0}</p>
          </div>

          <div className="card">
            <p className="text-sm text-gray-600">전체 레코드</p>
            <p className="text-2xl font-bold text-gray-900 mt-2">
              {formatNumber(dbHealth.total_records || 0)}
            </p>
          </div>
        </div>
      )}

      {/* DB 통계 */}
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
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {dbStats.portfolios?.total || 0}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                관심종목: {dbStats.portfolios?.watchlist || 0}
              </p>
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

      {/* 테이블 목록 */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">테이블 목록</h2>

        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="text-gray-500 mt-4">로딩 중...</p>
          </div>
        ) : tables && tables.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>테이블 이름</th>
                  <th className="text-right">행 수</th>
                  <th>마지막 업데이트</th>
                </tr>
              </thead>
              <tbody>
                {tables.map((table: TableStatistics) => (
                  <tr key={table.table_name}>
                    <td className="flex items-center space-x-2">
                      <Table className="w-4 h-4 text-gray-400" />
                      <span className="font-medium text-gray-900 font-mono">{table.table_name}</span>
                    </td>
                    <td className="text-right font-semibold text-gray-900">
                      {formatNumber(table.row_count)}
                    </td>
                    <td className="text-gray-600 text-sm">
                      {table.last_updated
                        ? new Date(table.last_updated).toLocaleString('ko-KR')
                        : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <DatabaseIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">테이블 정보를 불러올 수 없습니다</p>
          </div>
        )}
      </div>

      {/* 캐시 관리 섹션 */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">레포트 캐시 관리</h2>
            <p className="text-sm text-gray-600 mt-1">Redis에 캐시된 종목 레포트 목록</p>
          </div>
          {cacheData && (
            <span className="badge badge-info">총 {cacheData.total}개 캐시</span>
          )}
        </div>

        {cacheData && cacheData.cached_reports && cacheData.cached_reports.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>종목코드</th>
                  <th>레포트 날짜</th>
                  <th className="text-right">남은 시간 (TTL)</th>
                  <th className="text-right">액션</th>
                </tr>
              </thead>
              <tbody>
                {cacheData.cached_reports.map((cache) => (
                  <tr key={cache.cache_key}>
                    <td className="font-mono font-semibold text-gray-900">{cache.symbol}</td>
                    <td className="text-gray-700">{cache.report_date}</td>
                    <td className="text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <Clock className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-600">
                          {cache.ttl_minutes > 0
                            ? `${cache.ttl_minutes}분 ${cache.ttl_seconds % 60}초`
                            : '만료됨'}
                        </span>
                      </div>
                    </td>
                    <td className="text-right">
                      <button
                        onClick={() => {
                          if (
                            window.confirm(
                              `${cache.symbol} (${cache.report_date}) 캐시를 삭제하시겠습니까?`
                            )
                          ) {
                            deleteCacheMutation.mutate({
                              symbol: cache.symbol,
                              reportDate: cache.report_date,
                            });
                          }
                        }}
                        disabled={deleteCacheMutation.isPending}
                        className="btn btn-sm bg-red-600 text-white hover:bg-red-700 flex items-center space-x-2"
                      >
                        <Trash2 className="w-4 h-4" />
                        <span>{deleteCacheMutation.isPending ? '삭제 중...' : '삭제'}</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <DatabaseIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">캐시된 레포트가 없습니다</p>
          </div>
        )}
      </div>
    </div>
  );
}
