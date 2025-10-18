import { useState } from 'react';
import { NewsItem } from '../stores/newsStore';

interface NewsCardProps {
  news: NewsItem;
  onReadAloud?: (text: string) => void;
}

export default function NewsCard({ news, onReadAloud }: NewsCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // 감성 점수 색상 결정
  const getSentimentColor = (score: number | null) => {
    if (score === null) return 'text-gray-500';
    if (score > 0.3) return 'text-blue-600';
    if (score < -0.3) return 'text-red-600';
    return 'text-gray-600';
  };

  // 감성 점수 텍스트
  const getSentimentText = (score: number | null) => {
    if (score === null) return '분석 중';
    if (score > 0.5) return '매우 긍정';
    if (score > 0.2) return '긍정';
    if (score > -0.2) return '중립';
    if (score > -0.5) return '부정';
    return '매우 부정';
  };

  // 영향도 색상
  const getImpactColor = (score: number | null) => {
    if (score === null) return 'bg-gray-100 text-gray-600';
    if (score > 0.7) return 'bg-red-100 text-red-700';
    if (score > 0.4) return 'bg-orange-100 text-orange-700';
    return 'bg-blue-100 text-blue-700';
  };

  // 권고 액션 색상
  const getActionColor = (action: string | null) => {
    if (!action) return 'bg-gray-100 text-gray-600';
    if (action === 'buy') return 'bg-green-100 text-green-700';
    if (action === 'sell') return 'bg-red-100 text-red-700';
    return 'bg-yellow-100 text-yellow-700';
  };

  // 권고 액션 텍스트
  const getActionText = (action: string | null) => {
    if (!action) return '대기';
    if (action === 'buy') return '매수';
    if (action === 'sell') return '매도';
    return '보유';
  };

  // TTS 음성 읽기
  const handleReadAloud = () => {
    if (onReadAloud) {
      const text = `${news.title}. ${news.summary || news.content.slice(0, 200)}`;
      onReadAloud(text);
    }
  };

  return (
    <div className="card hover:shadow-lg transition-shadow duration-200">
      {/* 헤더 */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
              {news.source}
            </span>
            <span className="text-xs text-gray-500">
              {new Date(news.published_at).toLocaleString('ko-KR', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>
          <h3 className="text-lg font-bold text-gray-900 mb-2 leading-snug">
            {news.title}
          </h3>
        </div>

        {/* TTS 버튼 */}
        {onReadAloud && (
          <button
            onClick={handleReadAloud}
            className="ml-3 p-2 hover:bg-gray-100 rounded-full transition-colors"
            title="음성으로 듣기"
          >
            🔊
          </button>
        )}
      </div>

      {/* AI 분석 결과 */}
      {news.summary && (
        <div className="bg-blue-50 border-l-4 border-blue-500 p-3 mb-3 rounded">
          <div className="text-sm font-semibold text-blue-900 mb-1">
            📋 AI 요약
          </div>
          <p className="text-sm text-blue-800 leading-relaxed">{news.summary}</p>
        </div>
      )}

      {/* 분석 지표 */}
      <div className="flex flex-wrap gap-2 mb-3">
        {/* 감성 점수 */}
        {news.sentiment_score !== null && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">감성:</span>
            <span className={`text-sm font-bold ${getSentimentColor(news.sentiment_score)}`}>
              {getSentimentText(news.sentiment_score)}
            </span>
          </div>
        )}

        {/* 영향도 */}
        {news.impact_score !== null && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">영향도:</span>
            <span className={`text-xs px-2 py-1 rounded font-bold ${getImpactColor(news.impact_score)}`}>
              {(news.impact_score * 100).toFixed(0)}%
            </span>
          </div>
        )}

        {/* 권고 액션 */}
        {news.recommended_action && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">권고:</span>
            <span className={`text-xs px-2 py-1 rounded font-bold ${getActionColor(news.recommended_action)}`}>
              {getActionText(news.recommended_action)}
            </span>
          </div>
        )}
      </div>

      {/* 관련 종목 */}
      {news.related_symbols && news.related_symbols.length > 0 && (
        <div className="mb-3">
          <div className="flex flex-wrap gap-2">
            {news.related_symbols.map((symbol) => (
              <span
                key={symbol}
                className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded font-medium"
              >
                {symbol}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 본문 미리보기/전체보기 */}
      <div className="mb-3">
        <p className={`text-sm text-gray-700 leading-relaxed ${!isExpanded && 'line-clamp-3'}`}>
          {news.content}
        </p>
        {news.content.length > 150 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-xs text-blue-600 hover:text-blue-800 font-medium mt-2"
          >
            {isExpanded ? '접기' : '더보기'}
          </button>
        )}
      </div>

      {/* 원문 링크 */}
      <div className="pt-3 border-t border-gray-200">
        <a
          href={news.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-blue-600 hover:text-blue-800 font-medium inline-flex items-center gap-1"
        >
          원문 보기 →
        </a>
      </div>
    </div>
  );
}
