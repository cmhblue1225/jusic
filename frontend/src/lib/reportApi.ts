/**
 * Report API Client
 * Report Service와 통신하는 API 클라이언트
 */
import type { StockReport } from '../stores/reportStore';
import { supabase } from './supabase';

const REPORT_SERVICE_URL = import.meta.env.VITE_REPORT_SERVICE_URL || 'https://report-service-production-4a2b.up.railway.app';

/**
 * 레포트 생성 요청
 */
export async function generateReport(symbol: string, symbolName: string): Promise<StockReport> {
  try {
    // JWT 토큰 가져오기 (Supabase Auth)
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;

    const response = await fetch(`${REPORT_SERVICE_URL}/api/reports/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
      },
      body: JSON.stringify({
        symbol,
        symbol_name: symbolName,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '레포트 생성에 실패했습니다');
    }

    const report: StockReport = await response.json();
    return report;
  } catch (error) {
    console.error('[Report API] 레포트 생성 실패:', error);
    throw error;
  }
}

/**
 * 북마크 목록 조회
 */
export async function getBookmarks(): Promise<StockReport[]> {
  try {
    // JWT 토큰 가져오기
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;

    if (!token) {
      throw new Error('로그인이 필요합니다');
    }

    const response = await fetch(`${REPORT_SERVICE_URL}/api/reports/bookmarks`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '북마크 조회에 실패했습니다');
    }

    const data = await response.json();
    return data.bookmarks || [];
  } catch (error) {
    console.error('[Report API] 북마크 조회 실패:', error);
    throw error;
  }
}

/**
 * 북마크 삭제
 */
export async function deleteBookmark(bookmarkId: string): Promise<void> {
  try {
    // JWT 토큰 가져오기
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;

    if (!token) {
      throw new Error('로그인이 필요합니다');
    }

    const response = await fetch(`${REPORT_SERVICE_URL}/api/reports/bookmarks/${bookmarkId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '북마크 삭제에 실패했습니다');
    }
  } catch (error) {
    console.error('[Report API] 북마크 삭제 실패:', error);
    throw error;
  }
}
/**
 * 레포트 북마크 저장
 */
export async function bookmarkReport(symbol: string, symbolName: string): Promise<{ message: string; bookmark_id: string | null }> {
  try {
    // JWT 토큰 가져오기
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;

    if (!token) {
      throw new Error('로그인이 필요합니다');
    }

    const response = await fetch(`${REPORT_SERVICE_URL}/api/reports/bookmark`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        symbol,
        symbol_name: symbolName,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '북마크 저장에 실패했습니다');
    }

    return await response.json();
  } catch (error) {
    console.error('[Report API] 북마크 저장 실패:', error);
    throw error;
  }
}

/**
 * 레포트 PDF 다운로드
 */
export async function exportReportToPDF(symbol: string, symbolName: string): Promise<void> {
  try {
    // JWT 토큰 가져오기
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;

    const response = await fetch(`${REPORT_SERVICE_URL}/api/reports/export-pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
      },
      body: JSON.stringify({
        symbol,
        symbol_name: symbolName,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'PDF 생성에 실패했습니다');
    }

    // PDF 파일 다운로드
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;

    // 파일명 생성 (예: 삼성전자_레포트_2025-10-21.pdf)
    const today = new Date().toISOString().slice(0, 10);
    a.download = `${symbolName}_레포트_${today}.pdf`;

    document.body.appendChild(a);
    a.click();

    // 정리
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    console.error('[Report API] PDF 다운로드 실패:', error);
    throw error;
  }
}
