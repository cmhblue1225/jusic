/**
 * ToastContainer - 토스트 알림 컨테이너
 * Phase 2.4.2: 실시간 알림 Toast UI
 */

import { useEffect, useState } from 'react';
import { useAlertStore } from '../stores/alertStore';
import Toast from './Toast';
import type { Alert } from '../lib/alertRules';

export default function ToastContainer() {
  const { alerts, markAsRead } = useAlertStore();
  const [activeToasts, setActiveToasts] = useState<Alert[]>([]);

  // 새 알림 구독 및 필터링
  useEffect(() => {
    // 읽지 않은 알림만 가져오기
    const unreadAlerts = alerts.filter((alert) => !alert.isRead);

    // 최신 3개만 표시 (최대 3개 제한)
    const latestAlerts = unreadAlerts.slice(-3);

    setActiveToasts(latestAlerts);
  }, [alerts]);

  const handleClose = (alertId: string) => {
    // 활성 토스트에서 제거
    setActiveToasts((prev) => prev.filter((alert) => alert.id !== alertId));

    // 스토어에서 읽음으로 표시
    markAsRead(alertId);
  };

  // 활성 토스트가 없으면 렌더링하지 않음
  if (activeToasts.length === 0) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 pointer-events-none">
      {/* 토스트 스택 (아래에서 위로) */}
      <div className="flex flex-col-reverse gap-3 pointer-events-auto">
        {activeToasts.map((alert) => (
          <Toast key={alert.id} alert={alert} onClose={() => handleClose(alert.id)} />
        ))}
      </div>
    </div>
  );
}
