import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      // tslib을 외부 모듈로 처리하지 않고 번들에 포함
      external: [],
      output: {
        // 수동 청크 분리 (Code Splitting)
        manualChunks: {
          // React 생태계 (150KB)
          'vendor-react': [
            'react',
            'react-dom',
            'react-router-dom',
          ],
          // 차트 라이브러리 (Report 페이지에서만 로드) (200KB)
          'vendor-charts': [
            'recharts',
          ],
          // Supabase (100KB)
          'vendor-supabase': [
            '@supabase/supabase-js',
          ],
          // React Query + Zustand (50KB)
          'vendor-state': [
            '@tanstack/react-query',
            'zustand',
          ],
          // Socket.IO Client (70KB)
          'vendor-socket': [
            'socket.io-client',
          ],
          // Sentry (50KB)
          'vendor-sentry': [
            '@sentry/react',
          ],
        },
        // 청크 파일명 패턴 (캐시 무효화 최적화)
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
      },
    },
    // CommonJS 의존성 최적화
    commonjsOptions: {
      include: [/node_modules/],
      transformMixedEsModules: true,
    },
    // 청크 크기 경고 임계값 (500KB)
    chunkSizeWarningLimit: 500,
  },
  optimizeDeps: {
    // tslib 사전 번들링
    include: ['tslib'],
  },
  preview: {
    allowedHosts: [
      'frontend-production-7c4d.up.railway.app',
      'jusik.minhyuk.kr',
      '.railway.app', // 모든 Railway 서브도메인 허용
    ],
  },
})
