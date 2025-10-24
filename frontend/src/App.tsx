import { useEffect, lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import { useAlertStore } from './stores/alertStore';
import { useProfileStore } from './stores/profileStore';
import { monitoringService } from './services/monitoring';
import ToastContainer from './components/ToastContainer';
import ProtectedRoute from './components/ProtectedRoute';

// Eager Loading (로그인 전 필요)
import Login from './pages/Login';
import SignUp from './pages/SignUp';

// Lazy Loading (로그인 후 필요)
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Profile = lazy(() => import('./pages/Profile'));
const Portfolio = lazy(() => import('./pages/Portfolio'));
const Watchlist = lazy(() => import('./pages/Watchlist'));
const Statistics = lazy(() => import('./pages/Statistics'));
const News = lazy(() => import('./pages/News'));
const Report = lazy(() => import('./pages/Report'));
const Bookmarks = lazy(() => import('./pages/Bookmarks'));

function App() {
  const { initialize, user } = useAuthStore();
  const { alertSettings, ttsConfig, addAlert } = useAlertStore();
  const { profile, fetchProfile } = useProfileStore();

  // 앱 시작 시 세션 복원
  useEffect(() => {
    initialize();
  }, [initialize]);

  // 사용자 프로필 로드 (테마/글꼴 설정 적용용)
  useEffect(() => {
    if (user) {
      fetchProfile(user.id);
    }
  }, [user, fetchProfile]);

  // 테마 및 글꼴 크기 전역 적용
  useEffect(() => {
    if (!profile) return;

    const html = document.documentElement;
    const body = document.body;

    // 테마 적용
    if (profile.settings.theme === 'dark') {
      html.classList.add('dark');
      body.style.backgroundColor = '#1a202c';
      body.style.color = '#f7fafc';
    } else {
      html.classList.remove('dark');
      body.style.backgroundColor = '';
      body.style.color = '';
    }

    // 글꼴 크기 적용
    const fontSizeMap = {
      'normal': '18px',
      'large': '20px',
      'extra-large': '24px',
    };
    html.style.fontSize = fontSizeMap[profile.settings.font_size];

    // 고대비 모드 적용
    if (profile.settings.high_contrast) {
      html.classList.add('high-contrast');
      // 고대비 모드용 CSS 변수 설정
      body.style.setProperty('--text-color', '#000000');
      body.style.setProperty('--bg-color', '#ffffff');
      body.style.setProperty('--border-color', '#000000');
    } else {
      html.classList.remove('high-contrast');
      body.style.removeProperty('--text-color');
      body.style.removeProperty('--bg-color');
      body.style.removeProperty('--border-color');
    }

    console.log('[App] 테마 설정 적용:', {
      theme: profile.settings.theme,
      fontSize: profile.settings.font_size,
      highContrast: profile.settings.high_contrast,
    });
  }, [profile]);

  // 전역 모니터링 서비스 시작 (모든 페이지에서 알림 수신)
  useEffect(() => {
    if (!user || !ttsConfig.enabled) {
      // TTS가 비활성화되어 있거나 사용자가 없으면 모니터링 중지
      if (monitoringService.isRunning()) {
        monitoringService.stop();
      }
      return;
    }

    // 모니터링 서비스 시작
    console.log('[App] 전역 모니터링 서비스 시작');
    monitoringService.start(
      user.id,
      alertSettings,
      ttsConfig,
      (alert) => {
        console.log('[App] 알림 수신:', alert);
        addAlert(alert);
      }
    );

    // 언마운트 시 중지
    return () => {
      console.log('[App] 전역 모니터링 서비스 중지');
      monitoringService.stop();
    };
  }, [user, ttsConfig.enabled, alertSettings, ttsConfig, addAlert]);

  return (
    <BrowserRouter>
      <Suspense
        fallback={
          <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
            <div className="text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-xl text-gray-600">로딩 중...</p>
            </div>
          </div>
        }
      >
        <Routes>
        {/* 공개 라우트 */}
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<SignUp />} />

        {/* 보호된 라우트 */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />
        <Route
          path="/portfolio"
          element={
            <ProtectedRoute>
              <Portfolio />
            </ProtectedRoute>
          }
        />
        <Route
          path="/watchlist"
          element={
            <ProtectedRoute>
              <Watchlist />
            </ProtectedRoute>
          }
        />
        <Route
          path="/statistics"
          element={
            <ProtectedRoute>
              <Statistics />
            </ProtectedRoute>
          }
        />
        <Route
          path="/news"
          element={
            <ProtectedRoute>
              <News />
            </ProtectedRoute>
          }
        />
        <Route
          path="/report"
          element={
            <ProtectedRoute>
              <Report />
            </ProtectedRoute>
          }
        />
        <Route
          path="/bookmarks"
          element={
            <ProtectedRoute>
              <Bookmarks />
            </ProtectedRoute>
          }
        />

        {/* 기본 리다이렉트 */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>

      {/* 전역 Toast 알림 컨테이너 (모든 페이지에서 표시) */}
      <ToastContainer />
    </BrowserRouter>
  );
}

export default App;
