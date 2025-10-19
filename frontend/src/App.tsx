import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import { useAlertStore } from './stores/alertStore';
import { monitoringService } from './services/monitoring';
import ToastContainer from './components/ToastContainer';
import Login from './pages/Login';
import SignUp from './pages/SignUp';
import Dashboard from './pages/Dashboard';
import Profile from './pages/Profile';
import Portfolio from './pages/Portfolio';
import Watchlist from './pages/Watchlist';
import Statistics from './pages/Statistics';
import News from './pages/News';
import Report from './pages/Report';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  const { initialize, user } = useAuthStore();
  const { alertSettings, ttsConfig, addAlert } = useAlertStore();

  // 앱 시작 시 세션 복원
  useEffect(() => {
    initialize();
  }, [initialize]);

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

        {/* 기본 리다이렉트 */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>

      {/* 전역 Toast 알림 컨테이너 (모든 페이지에서 표시) */}
      <ToastContainer />
    </BrowserRouter>
  );
}

export default App;
