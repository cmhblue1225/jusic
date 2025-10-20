import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      // tslib을 외부 모듈로 처리하지 않고 번들에 포함
      external: [],
    },
    // CommonJS 의존성 최적화
    commonjsOptions: {
      include: [/node_modules/],
      transformMixedEsModules: true,
    },
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
