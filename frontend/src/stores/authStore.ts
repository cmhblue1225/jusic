/**
 * Auth Store - 인증 상태 관리
 * Zustand를 사용한 전역 상태 관리
 */
import { create } from 'zustand';
import { supabase } from '../lib/supabase';
import type { User, Session } from '@supabase/supabase-js';

interface AuthState {
  user: User | null;
  session: Session | null;
  loading: boolean;
  error: string | null;

  // Actions
  signUp: (email: string, password: string, name: string) => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  initialize: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  session: null,
  loading: true,
  error: null,

  /**
   * 회원가입
   */
  signUp: async (email: string, password: string, name: string) => {
    try {
      set({ loading: true, error: null });

      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            name,
          },
        },
      });

      if (error) throw error;

      // 프로필 자동 생성
      if (data.user) {
        const { error: profileError } = await supabase
          .from('users')
          .insert({
            id: data.user.id,
            email: data.user.email,
            name,
            settings: {
              tts_enabled: true,
              tts_speed: 0.9,
              tts_volume: 1.0,
              auto_tts_threshold: 0.8,
              theme: 'light',
              font_size: 'large',
              high_contrast: false,
            },
          });

        if (profileError) {
          console.error('프로필 생성 실패:', profileError);
        }
      }

      set({ user: data.user, session: data.session, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  /**
   * 로그인
   */
  signIn: async (email: string, password: string) => {
    try {
      set({ loading: true, error: null });

      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) throw error;

      set({ user: data.user, session: data.session, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  /**
   * 로그아웃
   */
  signOut: async () => {
    try {
      set({ loading: true, error: null });

      const { error } = await supabase.auth.signOut();

      if (error) throw error;

      set({ user: null, session: null, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  /**
   * 초기화 (세션 복원)
   */
  initialize: async () => {
    try {
      set({ loading: true });

      const { data: { session }, error } = await supabase.auth.getSession();

      if (error) throw error;

      set({ user: session?.user ?? null, session, loading: false });

      // Auth 상태 변경 리스너 등록
      supabase.auth.onAuthStateChange((_event, session) => {
        set({ user: session?.user ?? null, session });
      });
    } catch (error: any) {
      console.error('Auth 초기화 실패:', error);
      set({ loading: false });
    }
  },

  /**
   * 에러 초기화
   */
  clearError: () => set({ error: null }),
}));
