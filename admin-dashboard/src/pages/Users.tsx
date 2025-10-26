import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, Trash2, Ban, CheckCircle } from 'lucide-react';
import { adminApi } from '@/lib/adminApi';
import type { User } from '@/types';

export default function Users() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');

  // 사용자 목록 조회
  const { data: users, isLoading } = useQuery({
    queryKey: ['users', search, roleFilter],
    queryFn: () =>
      adminApi.getUsers({
        search: search || undefined,
        role: roleFilter || undefined,
        limit: 100,
      }),
  });

  // 사용자 정지 mutation
  const suspendMutation = useMutation({
    mutationFn: (userId: string) => adminApi.suspendUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      alert('사용자가 정지되었습니다.');
    },
  });

  // 사용자 활성화 mutation
  const activateMutation = useMutation({
    mutationFn: (userId: string) => adminApi.activateUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      alert('사용자가 활성화되었습니다.');
    },
  });

  // 사용자 삭제 mutation
  const deleteMutation = useMutation({
    mutationFn: (userId: string) => adminApi.deleteUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      alert('사용자가 삭제되었습니다.');
    },
  });

  const handleSuspend = (user: User) => {
    if (confirm(`${user.email} 사용자를 정지하시겠습니까?`)) {
      suspendMutation.mutate(user.id);
    }
  };

  const handleActivate = (user: User) => {
    if (confirm(`${user.email} 사용자를 활성화하시겠습니까?`)) {
      activateMutation.mutate(user.id);
    }
  };

  const handleDelete = (user: User) => {
    if (
      confirm(
        `${user.email} 사용자를 삭제하시겠습니까?\n\n⚠️ 이 작업은 되돌릴 수 없으며, 사용자의 모든 데이터(포트폴리오, 관심종목, 레포트 등)가 함께 삭제됩니다.`
      )
    ) {
      deleteMutation.mutate(user.id);
    }
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">사용자 관리</h1>
        <p className="text-gray-600 mt-2">전체 사용자 계정을 관리하고 권한을 제어하세요</p>
      </div>

      {/* 검색 및 필터 */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* 검색 */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">검색</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="이메일 또는 이름 검색..."
                className="input pl-10"
              />
            </div>
          </div>

          {/* 역할 필터 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">역할</label>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="input"
            >
              <option value="">전체</option>
              <option value="user">일반 사용자</option>
              <option value="admin">관리자</option>
              <option value="superadmin">슈퍼관리자</option>
            </select>
          </div>
        </div>
      </div>

      {/* 사용자 테이블 */}
      <div className="card">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="text-gray-500 mt-4">로딩 중...</p>
          </div>
        ) : users && users.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>이메일</th>
                  <th>이름</th>
                  <th>역할</th>
                  <th>상태</th>
                  <th>가입일</th>
                  <th className="text-right">작업</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user: User) => {
                  const isSuspended = user.settings?.suspended === true;

                  return (
                    <tr key={user.id}>
                      <td className="font-medium text-gray-900">{user.email}</td>
                      <td className="text-gray-600">{user.name || '-'}</td>
                      <td>
                        <span
                          className={`badge ${
                            user.role === 'superadmin'
                              ? 'badge-danger'
                              : user.role === 'admin'
                              ? 'badge-warning'
                              : 'badge-info'
                          }`}
                        >
                          {user.role === 'superadmin'
                            ? '슈퍼관리자'
                            : user.role === 'admin'
                            ? '관리자'
                            : '일반 사용자'}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${isSuspended ? 'badge-danger' : 'badge-success'}`}>
                          {isSuspended ? '정지' : '활성'}
                        </span>
                      </td>
                      <td className="text-gray-600 text-sm">
                        {new Date(user.created_at).toLocaleDateString('ko-KR')}
                      </td>
                      <td>
                        <div className="flex items-center justify-end space-x-2">
                          {isSuspended ? (
                            <button
                              onClick={() => handleActivate(user)}
                              className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                              title="활성화"
                            >
                              <CheckCircle className="w-5 h-5" />
                            </button>
                          ) : (
                            <button
                              onClick={() => handleSuspend(user)}
                              className="p-2 text-yellow-600 hover:bg-yellow-50 rounded-lg transition-colors"
                              title="정지"
                            >
                              <Ban className="w-5 h-5" />
                            </button>
                          )}

                          <button
                            onClick={() => handleDelete(user)}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="삭제"
                            disabled={user.role === 'superadmin'}
                          >
                            <Trash2 className="w-5 h-5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-500">사용자가 없습니다</p>
          </div>
        )}

        {users && users.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-600">총 {users.length}명의 사용자</p>
          </div>
        )}
      </div>
    </div>
  );
}
