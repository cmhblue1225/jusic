import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useProfileStore } from '../stores/profileStore';
import { useAlertStore } from '../stores/alertStore';
import { speak, cancel as cancelTTS } from '../lib/tts';
import { ttsService } from '../lib/tts';

export default function Profile() {
  const { user, signOut } = useAuthStore();
  const { profile, loading, error, fetchProfile, updateProfile, updateSettings, clearError } = useProfileStore();
  const { alertSettings, updateAlertSettings, updateTTSConfig } = useAlertStore();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [ttsSpeed, setTtsSpeed] = useState(0.9);
  const [ttsVolume, setTtsVolume] = useState(1.0);
  const [autoTtsThreshold, setAutoTtsThreshold] = useState(0.8);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [fontSize, setFontSize] = useState<'normal' | 'large' | 'extra-large'>('large');
  const [highContrast, setHighContrast] = useState(false);

  // Phase 2.4: 알림 설정 (Alert Rules)
  const [priceChangeEnabled, setPriceChangeEnabled] = useState(true);
  const [priceChangeThreshold, setPriceChangeThreshold] = useState(3.0);
  const [volumeEnabled, setVolumeEnabled] = useState(true);
  const [volumeThreshold, setVolumeThreshold] = useState(2.0);
  const [marketHoursOnly, setMarketHoursOnly] = useState(true);

  // 프로필 로드
  useEffect(() => {
    if (user) {
      fetchProfile(user.id);
    }
  }, [user, fetchProfile]);

  // 프로필 데이터를 폼에 반영
  useEffect(() => {
    if (profile) {
      setName(profile.name || '');
      setTtsEnabled(profile.settings.tts_enabled);
      setTtsSpeed(profile.settings.tts_speed);
      setTtsVolume(profile.settings.tts_volume);
      setAutoTtsThreshold(profile.settings.auto_tts_threshold);
      setTheme(profile.settings.theme);
      setFontSize(profile.settings.font_size);
      setHighContrast(profile.settings.high_contrast);
    }
  }, [profile]);

  // Phase 2.4: 알림 설정 로드
  useEffect(() => {
    setPriceChangeEnabled(alertSettings.priceChangeEnabled);
    setPriceChangeThreshold(alertSettings.priceChangeThreshold);
    setVolumeEnabled(alertSettings.volumeEnabled);
    setVolumeThreshold(alertSettings.volumeThreshold);
    setMarketHoursOnly(alertSettings.marketHoursOnly);
  }, [alertSettings]);

  const handleSaveProfile = async () => {
    if (!user) return;

    try {
      clearError();
      await updateProfile(user.id, { name });
      alert('프로필이 저장되었습니다.');
    } catch (err) {
      console.error('프로필 저장 실패:', err);
    }
  };

  const handleSaveSettings = async () => {
    if (!user) return;

    try {
      clearError();
      await updateSettings(user.id, {
        tts_enabled: ttsEnabled,
        tts_speed: ttsSpeed,
        tts_volume: ttsVolume,
        auto_tts_threshold: autoTtsThreshold,
        theme,
        font_size: fontSize,
        high_contrast: highContrast,
      });
      alert('설정이 저장되었습니다.');
    } catch (err) {
      console.error('설정 저장 실패:', err);
    }
  };

  const handleTTSTest = () => {
    cancelTTS();
    speak('음성 읽기 테스트입니다. 삼성전자가 3% 상승했습니다.', {
      rate: ttsSpeed,
      volume: ttsVolume,
    });
  };

  // Phase 2.4: 알림 설정 저장
  const handleSaveAlertSettings = () => {
    updateAlertSettings({
      priceChangeEnabled,
      priceChangeThreshold,
      newsEnabled: false, // Phase 2.3 완성 후 활성화
      newsThreshold: 0.7,
      volumeEnabled,
      volumeThreshold,
      marketHoursOnly,
    });

    updateTTSConfig({
      enabled: ttsEnabled,
      rate: ttsSpeed,
      pitch: 1.0,
      volume: ttsVolume,
      lang: 'ko-KR',
      autoPlayThreshold: autoTtsThreshold,
    });

    alert('알림 설정이 저장되었습니다.');
  };

  // Phase 2.4: TTS 테스트 (새로운 TTS 서비스 사용)
  const handleTTSTestNew = async () => {
    try {
      await ttsService.speakTestMessage({
        enabled: true,
        rate: ttsSpeed,
        pitch: 1.0,
        volume: ttsVolume,
        lang: 'ko-KR',
        autoPlayThreshold: autoTtsThreshold,
      });
    } catch (error) {
      console.error('[Profile] TTS 테스트 오류:', error);
    }
  };

  const handleSignOut = async () => {
    await signOut();
    navigate('/login');
  };

  if (loading && !profile) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="card">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-xl text-gray-600">로딩 중...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      {/* 헤더 */}
      <div className="max-w-4xl mx-auto mb-6">
        <div className="bg-white rounded-lg shadow-md p-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">⚙️ 프로필 설정</h1>
            <p className="text-lg text-gray-600">{user?.email}</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => navigate('/dashboard')} className="btn btn-secondary">
              대시보드
            </button>
            <button onClick={handleSignOut} className="btn btn-danger">
              로그아웃
            </button>
          </div>
        </div>
      </div>

      {/* 메인 콘텐츠 */}
      <div className="max-w-4xl mx-auto space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* 프로필 정보 */}
        <div className="card">
          <h2 className="text-2xl font-bold mb-4">👤 프로필 정보</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-lg font-medium text-gray-700 mb-2">이름</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input"
                placeholder="이름을 입력하세요"
              />
            </div>
            <button onClick={handleSaveProfile} disabled={loading} className="btn btn-primary">
              {loading ? '저장 중...' : '프로필 저장'}
            </button>
          </div>
        </div>

        {/* TTS 설정 */}
        <div className="card">
          <h2 className="text-2xl font-bold mb-4">🔊 음성 읽기 (TTS) 설정</h2>
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="tts-enabled"
                checked={ttsEnabled}
                onChange={(e) => setTtsEnabled(e.target.checked)}
                className="w-6 h-6 mr-3"
              />
              <label htmlFor="tts-enabled" className="text-lg font-medium">
                음성 읽기 활성화
              </label>
            </div>

            <div>
              <label className="block text-lg font-medium text-gray-700 mb-2">
                읽기 속도: {ttsSpeed.toFixed(1)}x
              </label>
              <input
                type="range"
                min="0.5"
                max="2.0"
                step="0.1"
                value={ttsSpeed}
                onChange={(e) => setTtsSpeed(parseFloat(e.target.value))}
                className="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            <div>
              <label className="block text-lg font-medium text-gray-700 mb-2">
                볼륨: {Math.round(ttsVolume * 100)}%
              </label>
              <input
                type="range"
                min="0"
                max="1.0"
                step="0.1"
                value={ttsVolume}
                onChange={(e) => setTtsVolume(parseFloat(e.target.value))}
                className="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            <div>
              <label className="block text-lg font-medium text-gray-700 mb-2">
                자동 읽기 임계값: {Math.round(autoTtsThreshold * 100)}%
              </label>
              <input
                type="range"
                min="0"
                max="1.0"
                step="0.1"
                value={autoTtsThreshold}
                onChange={(e) => setAutoTtsThreshold(parseFloat(e.target.value))}
                className="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <p className="text-sm text-gray-600 mt-1">
                뉴스 영향도가 이 값 이상일 때 자동으로 읽습니다
              </p>
            </div>

            <div className="flex gap-2">
              <button onClick={handleTTSTest} className="btn btn-secondary flex-1">
                🔊 음성 테스트 (기존)
              </button>
              <button onClick={handleTTSTestNew} className="btn btn-secondary flex-1">
                🔊 음성 테스트 (큐 방식)
              </button>
            </div>
          </div>
        </div>

        {/* Phase 2.4: 알림 설정 */}
        <div className="card">
          <h2 className="text-2xl font-bold mb-4">🔔 실시간 알림 설정</h2>
          <div className="space-y-4">
            {/* 가격 변동 알림 */}
            <div className="bg-gray-50 p-4 rounded-lg space-y-3">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="price-change-enabled"
                  checked={priceChangeEnabled}
                  onChange={(e) => setPriceChangeEnabled(e.target.checked)}
                  className="w-6 h-6 mr-3"
                />
                <label htmlFor="price-change-enabled" className="text-lg font-medium">
                  가격 변동 알림
                </label>
              </div>
              <div>
                <label className="block text-lg font-medium text-gray-700 mb-2">
                  가격 변동 임계값: {priceChangeThreshold.toFixed(1)}%
                </label>
                <input
                  type="range"
                  min="1.0"
                  max="10.0"
                  step="0.5"
                  value={priceChangeThreshold}
                  onChange={(e) => setPriceChangeThreshold(parseFloat(e.target.value))}
                  disabled={!priceChangeEnabled}
                  className="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer disabled:opacity-50"
                />
                <p className="text-sm text-gray-600 mt-1">
                  주가가 이 비율 이상 변동하면 알림을 받습니다
                </p>
              </div>
            </div>

            {/* 거래량 급증 알림 */}
            <div className="bg-gray-50 p-4 rounded-lg space-y-3">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="volume-enabled"
                  checked={volumeEnabled}
                  onChange={(e) => setVolumeEnabled(e.target.checked)}
                  className="w-6 h-6 mr-3"
                />
                <label htmlFor="volume-enabled" className="text-lg font-medium">
                  거래량 급증 알림
                </label>
              </div>
              <div>
                <label className="block text-lg font-medium text-gray-700 mb-2">
                  거래량 급증 배수: {volumeThreshold.toFixed(1)}배
                </label>
                <input
                  type="range"
                  min="1.5"
                  max="5.0"
                  step="0.5"
                  value={volumeThreshold}
                  onChange={(e) => setVolumeThreshold(parseFloat(e.target.value))}
                  disabled={!volumeEnabled}
                  className="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer disabled:opacity-50"
                />
                <p className="text-sm text-gray-600 mt-1">
                  평균 거래량의 이 배수 이상일 때 알림을 받습니다
                </p>
              </div>
            </div>

            {/* 장중만 알림 */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="market-hours-only"
                checked={marketHoursOnly}
                onChange={(e) => setMarketHoursOnly(e.target.checked)}
                className="w-6 h-6 mr-3"
              />
              <label htmlFor="market-hours-only" className="text-lg font-medium">
                장중만 알림 (평일 09:00~15:30)
              </label>
            </div>

            <button onClick={handleSaveAlertSettings} className="btn btn-primary w-full">
              알림 설정 저장
            </button>

            <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
              <p className="text-sm text-blue-800">
                💡 <strong>알림 메시지 차이:</strong><br />
                • <strong>보유 종목</strong>: "삼성전자 보유 종목 알림. 3.5% 상승했습니다. 현재가 70,000원, 수익률 +5.2%"<br />
                • <strong>관심 종목</strong>: "카카오 관심 종목 알림. 3.5% 상승했습니다. 현재가 50,000원"
              </p>
            </div>
          </div>
        </div>

        {/* 화면 표시 설정 */}
        <div className="card">
          <h2 className="text-2xl font-bold mb-4">🎨 화면 표시 설정</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-lg font-medium text-gray-700 mb-2">테마</label>
              <select
                value={theme}
                onChange={(e) => setTheme(e.target.value as 'light' | 'dark')}
                className="input"
              >
                <option value="light">라이트 모드</option>
                <option value="dark">다크 모드</option>
              </select>
            </div>

            <div>
              <label className="block text-lg font-medium text-gray-700 mb-2">글꼴 크기</label>
              <select
                value={fontSize}
                onChange={(e) => setFontSize(e.target.value as any)}
                className="input"
              >
                <option value="normal">보통 (18px)</option>
                <option value="large">크게 (20px)</option>
                <option value="extra-large">매우 크게 (24px)</option>
              </select>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="high-contrast"
                checked={highContrast}
                onChange={(e) => setHighContrast(e.target.checked)}
                className="w-6 h-6 mr-3"
              />
              <label htmlFor="high-contrast" className="text-lg font-medium">
                고대비 모드 (흑백)
              </label>
            </div>
          </div>
        </div>

        {/* 설정 저장 */}
        <div className="card">
          <button onClick={handleSaveSettings} disabled={loading} className="btn btn-primary w-full">
            {loading ? '저장 중...' : '모든 설정 저장'}
          </button>
        </div>
      </div>
    </div>
  );
}
