/**
 * 종목 자동완성 컴포넌트
 * 종목코드 또는 종목명으로 검색 가능
 */
import { useState, useEffect, useRef } from 'react';
import { supabase } from '../lib/supabase';

interface Stock {
  symbol: string;
  name: string;
  market: string;
}

interface StockAutocompleteProps {
  onSelect: (stock: Stock) => void;
  placeholder?: string;
  className?: string;
  autoFocus?: boolean;
}

export default function StockAutocomplete({
  onSelect,
  placeholder = '종목코드 또는 종목명을 입력하세요',
  className = '',
  autoFocus = false,
}: StockAutocompleteProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  // 검색 API 호출 (디바운스 적용)
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (query.trim().length < 1) {
        setResults([]);
        setShowResults(false);
        return;
      }

      setLoading(true);
      try {
        const { data, error } = await supabase
          .from('stock_master')
          .select('symbol, name, market')
          .or(`symbol.ilike.%${query}%,name.ilike.%${query}%`)
          .order('symbol', { ascending: true })
          .limit(10);

        if (error) throw error;

        setResults(data || []);
        setShowResults(true);
        setSelectedIndex(-1);
      } catch (error) {
        console.error('종목 검색 실패:', error);
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300); // 300ms 디바운스

    return () => clearTimeout(timer);
  }, [query]);

  // 외부 클릭 시 결과 닫기
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        resultsRef.current &&
        !resultsRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setShowResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 키보드 네비게이션
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showResults) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev =>
          prev < results.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => (prev > 0 ? prev - 1 : -1));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handleSelect(results[selectedIndex]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setShowResults(false);
        break;
    }
  };

  const handleSelect = (stock: Stock) => {
    onSelect(stock);
    setQuery('');
    setShowResults(false);
    setSelectedIndex(-1);
  };

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => query && setShowResults(true)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        autoFocus={autoFocus}
        className={`input ${className}`}
      />

      {/* 로딩 인디케이터 */}
      {loading && (
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
        </div>
      )}

      {/* 검색 결과 드롭다운 */}
      {showResults && results.length > 0 && (
        <div
          ref={resultsRef}
          className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-80 overflow-y-auto"
        >
          {results.map((stock, index) => (
            <button
              key={stock.symbol}
              onClick={() => handleSelect(stock)}
              className={`
                w-full px-4 py-3 text-left hover:bg-blue-50 transition-colors
                flex justify-between items-center
                ${index === selectedIndex ? 'bg-blue-50' : ''}
                ${index === 0 ? 'rounded-t-lg' : ''}
                ${index === results.length - 1 ? 'rounded-b-lg' : 'border-b border-gray-100'}
              `}
            >
              <div>
                <div className="font-bold text-lg text-gray-900">{stock.name}</div>
                <div className="text-sm text-gray-500">{stock.symbol}</div>
              </div>
              <div className="text-sm font-medium text-blue-600">
                {stock.market}
              </div>
            </button>
          ))}
        </div>
      )}

      {/* 검색 결과 없음 */}
      {showResults && !loading && query && results.length === 0 && (
        <div
          ref={resultsRef}
          className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg p-4 text-center text-gray-500"
        >
          검색 결과가 없습니다.
        </div>
      )}
    </div>
  );
}
