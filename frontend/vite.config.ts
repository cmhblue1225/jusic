import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  preview: {
    allowedHosts: [
      'frontend-production-7c4d.up.railway.app',
      'jusik.minhyuk.kr',
      '.railway.app', // 모든 Railway 서브도메인 허용
    ],
  },
})
