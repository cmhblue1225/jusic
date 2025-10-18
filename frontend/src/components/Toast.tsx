import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Alert } from '../lib/alertRules';

interface ToastProps {
  alert: Alert;
  onClose: () => void;
}

export default function Toast({ alert, onClose }: ToastProps) {
  const navigate = useNavigate();

  // 5초 후 자동 사라짐
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, 5000);

    return () => clearTimeout(timer);
  }, [onClose]);

  // 알림 타입별 스타일 설정
  const getTypeConfig = () => {
    switch (alert.type) {
      case 'price_change':
        return {
          icon: '🔔',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-400',
          textColor: 'text-blue-800',
        };
      case 'news':
        return {
          icon: '📰',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-400',
          textColor: 'text-green-800',
        };
      case 'volume':
        return {
          icon: '📊',
          bgColor: 'bg-orange-50',
          borderColor: 'border-orange-400',
          textColor: 'text-orange-800',
        };
      default:
        return {
          icon: '🔔',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-400',
          textColor: 'text-gray-800',
        };
    }
  };

  const config = getTypeConfig();

  const handleClick = () => {
    // 알림 타입별 상세 페이지로 이동
    if (alert.type === 'news') {
      navigate('/news');
    } else {
      navigate('/portfolio');
    }
    onClose();
  };

  return (
    <div
      onClick={handleClick}
      className={`
        ${config.bgColor} ${config.borderColor} ${config.textColor}
        border-l-4 p-4 rounded-lg shadow-lg cursor-pointer
        transition-all duration-300 hover:shadow-xl
        min-w-[320px] max-w-[400px]
        animate-slide-in
      `}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1">
          {/* 아이콘 */}
          <span className="text-2xl flex-shrink-0">{config.icon}</span>

          {/* 내용 */}
          <div className="flex-1 min-w-0">
            {/* 종목명 (종목코드 아님!) */}
            <p className="font-bold text-lg mb-1 truncate">{alert.symbolName}</p>

            {/* 메시지 */}
            <p className="text-sm line-clamp-2">{alert.message}</p>

            {/* 뉴스 요약 (있으면 표시) */}
            {alert.summary && (
              <p className="text-xs mt-1 opacity-80 line-clamp-1">{alert.summary}</p>
            )}
          </div>
        </div>

        {/* 닫기 버튼 */}
        <button
          onClick={(e) => {
            e.stopPropagation(); // 클릭 이벤트 전파 방지 (페이지 이동 X)
            onClose();
          }}
          className="text-gray-500 hover:text-gray-700 transition-colors flex-shrink-0"
          aria-label="알림 닫기"
        >
          <span className="text-xl">✕</span>
        </button>
      </div>
    </div>
  );
}
