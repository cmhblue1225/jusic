import { create } from 'zustand';
import { supabase } from '@/lib/supabase';
import type { User } from '@/types';

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  initialize: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: true,
  error: null,

  initialize: async () => {
    try {
      // Supabase 세션 확인
      const { data: { session } } = await supabase.auth.getSession();

      if (session?.user) {
        // users 테이블에서 사용자 정보 가져오기
        const { data: userData, error } = await supabase
          .from('users')
          .select('*')
          .eq('id', session.user.id)
          .single();

        if (error) throw error;

        // admin 또는 superadmin 권한 확인
        if (userData.role !== 'admin' && userData.role !== 'superadmin') {
          throw new Error('관리자 권한이 필요합니다.');
        }

        set({ user: userData, loading: false, error: null });
      } else {
        set({ user: null, loading: false, error: null });
      }
    } catch (error: any) {
      console.error('세션 초기화 실패:', error);
      set({ user: null, loading: false, error: error.message });
    }
  },

  login: async (email: string, password: string) => {
    try {
      set({ loading: true, error: null });

      // Supabase 로그인
      const { data, error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (signInError) throw signInError;

      if (!data.user) {
        throw new Error('로그인 실패: 사용자 정보를 찾을 수 없습니다.');
      }

      // users 테이블에서 사용자 정보 가져오기
      const { data: userData, error: userError } = await supabase
        .from('users')
        .select('*')
        .eq('id', data.user.id)
        .single();

      if (userError) throw userError;

      // admin 또는 superadmin 권한 확인
      if (userData.role !== 'admin' && userData.role !== 'superadmin') {
        // 권한이 없으면 로그아웃
        await supabase.auth.signOut();
        throw new Error('관리자 권한이 필요합니다. 일반 사용자는 접근할 수 없습니다.');
      }

      set({ user: userData, loading: false, error: null });
    } catch (error: any) {
      console.error('로그인 실패:', error);
      set({ user: null, loading: false, error: error.message });
      throw error;
    }
  },

  logout: async () => {
    try {
      await supabase.auth.signOut();
      set({ user: null, loading: false, error: null });
    } catch (error: any) {
      console.error('로그아웃 실패:', error);
      set({ error: error.message });
    }
  },
}));
