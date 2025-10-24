import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import * as Sentry from '@sentry/react'
import './index.css'
import App from './App.tsx'

// Sentry 에러 추적 초기화
const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN

if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    environment: import.meta.env.MODE,  // development, production
    integrations: [
      Sentry.browserTracingIntegration(),  // 페이지 로딩 추적
      Sentry.replayIntegration({  // 세션 리플레이 (에러 발생 시 사용자 행동 녹화)
        maskAllText: true,  // 개인정보 보호
        blockAllMedia: true,
      }),
    ],
    tracesSampleRate: 0.1,  // 10% 성능 추적
    replaysSessionSampleRate: 0.1,  // 10% 세션 리플레이
    replaysOnErrorSampleRate: 1.0,  // 에러 발생 시 100% 리플레이

    // 에러 필터링 (중복 에러 최소화)
    beforeSend(event, hint) {
      // Console 에러는 제외
      if (hint.originalException && typeof hint.originalException === 'string') {
        if (hint.originalException.includes('ResizeObserver') ||
            hint.originalException.includes('Non-Error')) {
          return null
        }
      }
      return event
    },
  })
  console.log('✅ Sentry 초기화 완료 (Frontend)')
} else {
  console.warn('⚠️  VITE_SENTRY_DSN 환경 변수 없음 - Sentry 비활성화')
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
