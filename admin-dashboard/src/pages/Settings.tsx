import { useAuthStore } from '@/stores/authStore';
import { User, Shield, Bell, Palette } from 'lucide-react';

export default function Settings() {
  const { user } = useAuthStore();

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">설정</h1>
        <p className="text-gray-600 mt-2">관리자 계정 및 시스템 설정</p>
      </div>

      {/* 프로필 정보 */}
      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <User className="w-6 h-6 text-primary-600" />
          <h2 className="text-xl font-semibold text-gray-900">프로필 정보</h2>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">이메일</label>
            <input
              type="email"
              value={user?.email || ''}
              disabled
              className="input bg-gray-50 cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">이름</label>
            <input
              type="text"
              value={user?.name || ''}
              disabled
              className="input bg-gray-50 cursor-not-allowed"
              placeholder="설정되지 않음"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">역할</label>
            <span
              className={`badge ${
                user?.role === 'superadmin'
                  ? 'badge-danger'
                  : user?.role === 'admin'
                  ? 'badge-warning'
                  : 'badge-info'
              }`}
            >
              {user?.role === 'superadmin'
                ? '슈퍼관리자'
                : user?.role === 'admin'
                ? '관리자'
                : '일반 사용자'}
            </span>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">가입일</label>
            <p className="text-gray-900">
              {user?.created_at ? new Date(user.created_at).toLocaleString('ko-KR') : '-'}
            </p>
          </div>
        </div>
      </div>

      {/* 보안 설정 */}
      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <Shield className="w-6 h-6 text-primary-600" />
          <h2 className="text-xl font-semibold text-gray-900">보안 설정</h2>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">2단계 인증 (2FA)</p>
              <p className="text-sm text-gray-500 mt-1">추가 보안 레이어로 계정을 보호하세요</p>
            </div>
            <span className="badge badge-warning">준비 중</span>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">세션 타임아웃</p>
              <p className="text-sm text-gray-500 mt-1">비활성 시 자동 로그아웃 시간</p>
            </div>
            <span className="text-sm text-gray-700">24시간</span>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">IP 화이트리스트</p>
              <p className="text-sm text-gray-500 mt-1">허용된 IP에서만 접근 가능</p>
            </div>
            <span className="badge badge-warning">준비 중</span>
          </div>
        </div>
      </div>

      {/* 알림 설정 */}
      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <Bell className="w-6 h-6 text-primary-600" />
          <h2 className="text-xl font-semibold text-gray-900">알림 설정</h2>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">시스템 에러 알림</p>
              <p className="text-sm text-gray-500 mt-1">서비스 오류 발생 시 즉시 알림</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">사용자 활동 알림</p>
              <p className="text-sm text-gray-500 mt-1">신규 가입, 대량 데이터 변경 등</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">일일 리포트</p>
              <p className="text-sm text-gray-500 mt-1">매일 시스템 통계 요약 이메일</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>
        </div>
      </div>

      {/* 시스템 정보 */}
      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <Palette className="w-6 h-6 text-primary-600" />
          <h2 className="text-xl font-semibold text-gray-900">시스템 정보</h2>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600">버전</p>
            <p className="text-gray-900 font-medium mt-1">1.0.0</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">환경</p>
            <p className="text-gray-900 font-medium mt-1">
              {import.meta.env.DEV ? 'Development' : 'Production'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">API URL</p>
            <p className="text-gray-900 font-medium mt-1 text-xs break-all">
              {import.meta.env.VITE_ADMIN_API_URL || 'http://localhost:8000'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Supabase</p>
            <p className="text-gray-900 font-medium mt-1 text-xs break-all">
              {import.meta.env.VITE_SUPABASE_URL || '-'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
