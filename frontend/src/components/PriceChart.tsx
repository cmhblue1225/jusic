/**
 * PriceChart Component
 * 캔들스틱 차트 + 이동평균선 (60일)
 */
import { useMemo } from 'react';
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface PriceChartProps {
  currentPrice: number;
  ma5?: number | null;
  ma20?: number | null;
  ma60?: number | null;
  high: number;
  low: number;
  symbolName: string;
}

export default function PriceChart({
  currentPrice,
  ma5,
  ma20,
  ma60,
  high,
  low,
  symbolName,
}: PriceChartProps) {
  // 차트 데이터 생성 (단순화된 시각화)
  const chartData = useMemo(() => {
    // 현재 시점 기준 60일간의 추정 데이터 포인트
    const data = [];
    const today = new Date();

    // MA60이 가장 오래된 가격, MA5가 가장 최근 가격 근처
    const priceRange = high - low;
    const basePrice = low + priceRange * 0.3;

    for (let i = 59; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);

      // 날짜 포맷 (MM/DD)
      const dateStr = `${date.getMonth() + 1}/${date.getDate()}`;

      // 주가 추정치 (선형 보간)
      const progress = (59 - i) / 59; // 0 ~ 1
      const estimatedPrice = basePrice + (currentPrice - basePrice) * progress;

      // 변동성 추가 (±2%)
      const randomFactor = 1 + (Math.random() - 0.5) * 0.04;
      const price = estimatedPrice * randomFactor;

      data.push({
        date: i === 0 ? '오늘' : i <= 5 ? dateStr : i % 5 === 0 ? dateStr : '',
        price: Math.round(price),
        ma5: ma5 || null,  // 모든 데이터 포인트에 표시
        ma20: ma20 || null,  // 모든 데이터 포인트에 표시
        ma60: ma60 || null,
      });
    }

    return data;
  }, [currentPrice, ma5, ma20, ma60, high, low]);

  // 커스텀 툴팁
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-300 rounded shadow-lg">
          <p className="text-sm font-semibold text-gray-800">{payload[0].payload.date}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-xs" style={{ color: entry.color }}>
              {entry.name}: {entry.value?.toLocaleString()}원
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200">
      <h4 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
        <span>📈</span> 주가 추이 ({symbolName})
      </h4>

      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart
          data={chartData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11 }}
            stroke="#6b7280"
          />
          <YAxis
            tick={{ fontSize: 11 }}
            stroke="#6b7280"
            tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: '12px' }}
            iconType="line"
          />

          {/* 주가 라인 - 초록색 */}
          <Line
            type="monotone"
            dataKey="price"
            stroke="#10b981"
            strokeWidth={2}
            dot={false}
            name="주가"
          />

          {/* 이동평균선 */}
          {ma5 && (
            <Line
              type="monotone"
              dataKey="ma5"
              stroke="#3b82f6"
              strokeWidth={1.5}
              dot={false}
              strokeDasharray="5 5"
              name="MA5"
            />
          )}
          {ma20 && (
            <Line
              type="monotone"
              dataKey="ma20"
              stroke="#f59e0b"
              strokeWidth={1.5}
              dot={false}
              strokeDasharray="5 5"
              name="MA20"
            />
          )}
          {ma60 && (
            <Line
              type="monotone"
              dataKey="ma60"
              stroke="#ef4444"
              strokeWidth={1.5}
              dot={false}
              strokeDasharray="3 3"
              name="MA60"
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>

      {/* 차트 범례 설명 */}
      <div className="mt-3 text-xs text-gray-600 flex flex-wrap gap-3">
        <div className="flex items-center gap-1">
          <div className="w-4 h-0.5 bg-green-500"></div>
          <span>주가</span>
        </div>
        {ma5 && (
          <div className="flex items-center gap-1">
            <div className="w-4 h-0.5 bg-blue-500 border-dashed"></div>
            <span>5일 이평선</span>
          </div>
        )}
        {ma20 && (
          <div className="flex items-center gap-1">
            <div className="w-4 h-0.5 bg-amber-500 border-dashed"></div>
            <span>20일 이평선</span>
          </div>
        )}
        {ma60 && (
          <div className="flex items-center gap-1">
            <div className="w-4 h-0.5 bg-red-500 border-dashed"></div>
            <span>60일 이평선</span>
          </div>
        )}
      </div>

      <p className="mt-2 text-xs text-gray-500 italic">
        * 차트는 시각화를 위한 추정 데이터이며, 실제 거래 데이터와 다를 수 있습니다.
      </p>
    </div>
  );
}
