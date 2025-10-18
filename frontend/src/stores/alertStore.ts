/**
 * Alert Store - 알림 상태 관리
 * Phase 2.4: Zustand를 사용한 알림 전역 상태 관리
 */

import { create } from 'zustand';
import type { Alert, UserAlertSettings } from '../lib/alertRules';
import { DEFAULT_ALERT_SETTINGS } from '../lib/alertRules';
import type { TTSConfig } from '../lib/tts';
import { DEFAULT_TTS_CONFIG } from '../lib/tts';

interface AlertState {
  // 알림 목록
  alerts: Alert[];
  unreadCount: number;

  // 알림 설정
  alertSettings: UserAlertSettings;
  ttsConfig: TTSConfig;

  // Actions
  addAlert: (alert: Alert) => void;
  markAsRead: (alertId: string) => void;
  markAllAsRead: () => void;
  removeAlert: (alertId: string) => void;
  clearAllAlerts: () => void;

  // 설정 업데이트
  updateAlertSettings: (settings: UserAlertSettings) => void;
  updateTTSConfig: (config: TTSConfig) => void;

  // 읽지 않은 알림 가져오기
  getUnreadAlerts: () => Alert[];

  // 알림 통계
  getAlertStats: () => {
    total: number;
    unread: number;
    byType: Record<string, number>;
    bySeverity: Record<string, number>;
  };
}

export const useAlertStore = create<AlertState>((set, get) => ({
  alerts: [],
  unreadCount: 0,
  alertSettings: DEFAULT_ALERT_SETTINGS,
  ttsConfig: DEFAULT_TTS_CONFIG,

  /**
   * 알림 추가
   */
  addAlert: (alert: Alert) => {
    set((state) => {
      const newAlerts = [alert, ...state.alerts]; // 최신 알림이 위로
      const newUnreadCount = newAlerts.filter((a) => !a.isRead).length;

      return {
        alerts: newAlerts,
        unreadCount: newUnreadCount,
      };
    });

    console.log('[AlertStore] 알림 추가:', alert);
  },

  /**
   * 알림을 읽음으로 표시
   */
  markAsRead: (alertId: string) => {
    set((state) => {
      const updatedAlerts = state.alerts.map((alert) =>
        alert.id === alertId ? { ...alert, isRead: true } : alert
      );
      const newUnreadCount = updatedAlerts.filter((a) => !a.isRead).length;

      return {
        alerts: updatedAlerts,
        unreadCount: newUnreadCount,
      };
    });
  },

  /**
   * 모든 알림을 읽음으로 표시
   */
  markAllAsRead: () => {
    set((state) => ({
      alerts: state.alerts.map((alert) => ({ ...alert, isRead: true })),
      unreadCount: 0,
    }));

    console.log('[AlertStore] 모든 알림을 읽음으로 표시');
  },

  /**
   * 알림 삭제
   */
  removeAlert: (alertId: string) => {
    set((state) => {
      const updatedAlerts = state.alerts.filter((alert) => alert.id !== alertId);
      const newUnreadCount = updatedAlerts.filter((a) => !a.isRead).length;

      return {
        alerts: updatedAlerts,
        unreadCount: newUnreadCount,
      };
    });
  },

  /**
   * 모든 알림 삭제
   */
  clearAllAlerts: () => {
    set({
      alerts: [],
      unreadCount: 0,
    });

    console.log('[AlertStore] 모든 알림 삭제');
  },

  /**
   * 알림 설정 업데이트
   */
  updateAlertSettings: (settings: UserAlertSettings) => {
    set({ alertSettings: settings });
    console.log('[AlertStore] 알림 설정 업데이트:', settings);
  },

  /**
   * TTS 설정 업데이트
   */
  updateTTSConfig: (config: TTSConfig) => {
    set({ ttsConfig: config });
    console.log('[AlertStore] TTS 설정 업데이트:', config);
  },

  /**
   * 읽지 않은 알림 가져오기
   */
  getUnreadAlerts: () => {
    return get().alerts.filter((alert) => !alert.isRead);
  },

  /**
   * 알림 통계
   */
  getAlertStats: () => {
    const { alerts } = get();

    const total = alerts.length;
    const unread = alerts.filter((a) => !a.isRead).length;

    const byType: Record<string, number> = {};
    const bySeverity: Record<string, number> = {};

    alerts.forEach((alert) => {
      // 타입별 카운트
      byType[alert.type] = (byType[alert.type] || 0) + 1;

      // 심각도별 카운트
      bySeverity[alert.severity] = (bySeverity[alert.severity] || 0) + 1;
    });

    return {
      total,
      unread,
      byType,
      bySeverity,
    };
  },
}));
