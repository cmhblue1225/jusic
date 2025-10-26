import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { signIn, loading, error, clearError } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    try {
      await signIn(email, password);
      navigate('/dashboard');
    } catch (err) {
      console.error('로그인 실패:', err);
    }
  };

  const handleTestLogin = async () => {
    clearError();

    try {
      await signIn('test@test.com', 'test1234');
      navigate('/dashboard');
    } catch (err) {
      console.error('테스트 계정 로그인 실패:', err);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="card max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            📈 트레이딩 인텔리전스
          </h1>
          <p className="text-xl text-gray-600">로그인</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-lg font-medium text-gray-700 mb-2">
              이메일
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
              placeholder="email@example.com"
              required
              autoComplete="email"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-lg font-medium text-gray-700 mb-2">
              비밀번호
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
              placeholder="비밀번호를 입력하세요"
              required
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary w-full text-xl"
          >
            {loading ? '로그인 중...' : '로그인'}
          </button>

          {/* 테스트 계정 로그인 버튼 */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">또는</span>
            </div>
          </div>

          <button
            type="button"
            onClick={handleTestLogin}
            disabled={loading}
            className="w-full text-lg px-6 py-3 border-2 border-blue-600 text-blue-600 rounded-lg font-medium hover:bg-blue-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? '로그인 중...' : '🚀 테스트 계정으로 체험하기'}
          </button>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800 text-center">
              <strong>💡 테스트 계정 정보</strong>
              <br />
              ID: test@test.com / PW: test1234
            </p>
          </div>

          <div className="text-center">
            <p className="text-lg text-gray-600">
              계정이 없으신가요?{' '}
              <Link to="/signup" className="text-blue-600 hover:text-blue-700 font-medium">
                회원가입
              </Link>
            </p>
          </div>

          {/* 관리자 페이지 이동 버튼 */}
          <div className="pt-4 border-t border-gray-200">
            <a
              href="https://admin-dashboard-production-1909.up.railway.app/login"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center w-full text-base px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors"
            >
              🛡️ 관리자 페이지로 이동
            </a>
            <p className="text-xs text-gray-500 text-center mt-2">
              관리자 권한이 필요합니다
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
