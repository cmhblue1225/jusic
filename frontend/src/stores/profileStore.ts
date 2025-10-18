/**
 * Profile Store - 사용자 프로필 관리
 * Zustand를 사용한 전역 상태 관리
 */
import { create } from 'zustand';
import { supabase } from '../lib/supabase';

interface UserProfile {
  id: string;
  email: string;
  name: string | null;
  settings: {
    tts_enabled: boolean;
    tts_speed: number;
    tts_volume: number;
    auto_tts_threshold: number;
    theme: 'light' | 'dark';
    font_size: 'normal' | 'large' | 'extra-large';
    high_contrast: boolean;
  };
  created_at: string;
  updated_at: string;
}

interface ProfileState {
  profile: UserProfile | null;
  loading: boolean;
  error: string | null;

  // Actions
  fetchProfile: (userId: string) => Promise<void>;
  updateProfile: (userId: string, updates: Partial<UserProfile>) => Promise<void>;
  updateSettings: (userId: string, settings: Partial<UserProfile['settings']>) => Promise<void>;
  clearError: () => void;
}

export const useProfileStore = create<ProfileState>((set, get) => ({
  profile: null,
  loading: false,
  error: null,

  /**
   * 프로필 조회
   */
  fetchProfile: async (userId: string) => {
    try {
      set({ loading: true, error: null });

      const { data, error } = await supabase
        .from('users')
        .select('*')
        .eq('id', userId)
        .single();

      if (error) throw error;

      set({ profile: data, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  /**
   * 프로필 업데이트 (이름 등)
   */
  updateProfile: async (userId: string, updates: Partial<UserProfile>) => {
    try {
      set({ loading: true, error: null });

      const { data, error } = await supabase
        .from('users')
        .update({
          ...updates,
          updated_at: new Date().toISOString(),
        })
        .eq('id', userId)
        .select()
        .single();

      if (error) throw error;

      set({ profile: data, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  /**
   * 설정 업데이트 (TTS, 테마 등)
   */
  updateSettings: async (userId: string, settings: Partial<UserProfile['settings']>) => {
    try {
      set({ loading: true, error: null });

      const currentProfile = get().profile;
      if (!currentProfile) {
        throw new Error('프로필을 먼저 로드해주세요.');
      }

      const newSettings = {
        ...currentProfile.settings,
        ...settings,
      };

      const { data, error } = await supabase
        .from('users')
        .update({
          settings: newSettings,
          updated_at: new Date().toISOString(),
        })
        .eq('id', userId)
        .select()
        .single();

      if (error) throw error;

      set({ profile: data, loading: false });

      // 테마 설정이 변경된 경우 body 클래스 업데이트
      if (settings.theme || settings.font_size || settings.high_contrast) {
        applyThemeSettings(data.settings);
      }
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  /**
   * 에러 초기화
   */
  clearError: () => set({ error: null }),
}));

/**
 * 테마 설정을 body에 적용
 */
function applyThemeSettings(settings: UserProfile['settings']) {
  const body = document.body;

  // 폰트 크기
  body.classList.remove('large-font', 'extra-large-font');
  if (settings.font_size === 'large') {
    body.classList.add('large-font');
  } else if (settings.font_size === 'extra-large') {
    body.classList.add('extra-large-font');
  }

  // 고대비 모드
  if (settings.high_contrast) {
    body.classList.add('high-contrast');
  } else {
    body.classList.remove('high-contrast');
  }

  // 다크 모드 (필요시 추가)
  if (settings.theme === 'dark') {
    body.classList.add('dark');
  } else {
    body.classList.remove('dark');
  }
}
