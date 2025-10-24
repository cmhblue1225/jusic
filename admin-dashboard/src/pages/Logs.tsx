import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileText, Download, Filter } from 'lucide-react';
import { adminApi } from '@/lib/adminApi';
import type { AdminActivityLog } from '@/types';

export default function Logs() {
  const [actionFilter, setActionFilter] = useState('');
  const [timeRange, setTimeRange] = useState(24);

  const { data: logs, isLoading } = useQuery({
    queryKey: ['admin-activity-logs', actionFilter, timeRange],
    queryFn: () =>
      adminApi.getAdminActivityLogs({
        action: actionFilter || undefined,
        hours: timeRange,
        limit: 100,
      }),
  });

  const { data: logStats } = useQuery({
    queryKey: ['log-statistics', timeRange],
    queryFn: () => adminApi.getLogStatistics(timeRange),
  });

  const { data: availableActions } = useQuery({
    queryKey: ['available-actions'],
    queryFn: () => adminApi.getAvailableActions(),
  });

  const handleExport = async (format: 'json' | 'csv') => {
    try {
      const data = await adminApi.exportLogs(timeRange, format);

      if (format === 'json') {
        const blob = new Blob([JSON.stringify(data.data, null, 2)], {
          type: 'application/json',
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `admin-logs-${new Date().toISOString()}.json`;
        a.click();
      } else {
        const blob = new Blob([data.data], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `admin-logs-${new Date().toISOString()}.csv`;
        a.click();
      }

      alert('로그가 다운로드되었습니다.');
    } catch (error) {
      alert('로그 내보내기 실패: ' + error);
    }
  };

  const getActionBadgeColor = (action: string) => {
    if (action.includes('delete') || action.includes('suspend')) return 'badge-danger';
    if (action.includes('create') || action.includes('activate')) return 'badge-success';
    if (action.includes('update')) return 'badge-warning';
    return 'badge-info';
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">활동 로그</h1>
          <p className="text-gray-600 mt-2">관리자 활동 내역을 조회하고 감사하세요</p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleExport('json')}
            className="btn btn-secondary btn-sm flex items-center space-x-2"
          >
            <Download className="w-4 h-4" />
            <span>JSON</span>
          </button>
          <button
            onClick={() => handleExport('csv')}
            className="btn btn-secondary btn-sm flex items-center space-x-2"
          >
            <Download className="w-4 h-4" />
            <span>CSV</span>
          </button>
        </div>
      </div>

      {/* 로그 통계 */}
      {logStats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card">
            <p className="text-sm text-gray-600">총 로그</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">{logStats.total_logs}</p>
            <p className="text-xs text-gray-500 mt-1">최근 {timeRange}시간</p>
          </div>

          <div className="card">
            <p className="text-sm text-gray-600">액션 유형</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              {Object.keys(logStats.actions_count).length}
            </p>
            <p className="text-xs text-gray-500 mt-1">고유 액션</p>
          </div>

          <div className="card">
            <p className="text-sm text-gray-600">활성 관리자</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">{logStats.top_admins.length}</p>
            <p className="text-xs text-gray-500 mt-1">활동 중</p>
          </div>
        </div>
      )}

      {/* 필터 */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">액션 필터</label>
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="input"
            >
              <option value="">전체</option>
              {availableActions?.actions.map((action) => (
                <option key={action} value={action}>
                  {availableActions.descriptions[action] || action}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">시간 범위</label>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(Number(e.target.value))}
              className="input"
            >
              <option value={1}>최근 1시간</option>
              <option value={6}>최근 6시간</option>
              <option value={24}>최근 24시간</option>
              <option value={72}>최근 3일</option>
              <option value={168}>최근 7일</option>
            </select>
          </div>
        </div>
      </div>

      {/* 로그 테이블 */}
      <div className="card">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="text-gray-500 mt-4">로딩 중...</p>
          </div>
        ) : logs && logs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>시간</th>
                  <th>관리자</th>
                  <th>액션</th>
                  <th>대상</th>
                  <th>상세</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log: AdminActivityLog) => (
                  <tr key={log.id}>
                    <td className="text-sm text-gray-600">
                      {new Date(log.created_at).toLocaleString('ko-KR')}
                    </td>
                    <td className="text-sm font-medium text-gray-900">
                      {log.admin_email || log.admin_id}
                    </td>
                    <td>
                      <span className={`badge ${getActionBadgeColor(log.action)}`}>
                        {availableActions?.descriptions[log.action] || log.action}
                      </span>
                    </td>
                    <td className="text-sm text-gray-600">
                      {log.target_type && log.target_id ? (
                        <span>
                          {log.target_type}: {log.target_id.slice(0, 8)}...
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="text-sm text-gray-600">
                      {log.details ? (
                        <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                          {JSON.stringify(log.details).slice(0, 50)}...
                        </code>
                      ) : (
                        '-'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">로그가 없습니다</p>
          </div>
        )}

        {logs && logs.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-600">총 {logs.length}개의 로그</p>
          </div>
        )}
      </div>
    </div>
  );
}
