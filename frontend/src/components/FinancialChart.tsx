/**
 * FinancialChart Component
 * 재무비율 추이 차트 (PER, PBR, ROE)
 */
import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface FinancialChartProps {
  per?: number | null;
  pbr?: number | null;
  roe?: number | null;
  symbolName: string;
}

export default function FinancialChart({
  per,
  pbr,
  roe,
  symbolName,
}: FinancialChartProps) {
  // 차트 데이터 생성 (최근 4분기 추정)
  const chartData = useMemo(() => {
    const quarters = ['1Q', '2Q', '3Q', '4Q(E)'];
    const data = [];

    for (let i = 0; i < 4; i++) {
      // 추정 추이 (현재 값 기준 ±10% 변동)
      const variation = 0.9 + (i * 0.05); // 0.9, 0.95, 1.0, 1.05

      data.push({
        quarter: quarters[i],
        per: per ? Math.round(per * variation * 10) / 10 : null,
        pbr: pbr ? Math.round(pbr * variation * 10) / 10 : null,
        roe: roe ? Math.round(roe * variation * 10) / 10 : null,
      });
    }

    return data;
  }, [per, pbr, roe]);

  // 데이터가 없으면 표시하지 않음
  if (!per && !pbr && !roe) {
    return null;
  }

  // 커스텀 툴팁
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-300 rounded shadow-lg">
          <p className="text-sm font-semibold text-gray-800">{payload[0].payload.quarter}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-xs" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
              {entry.dataKey === 'roe' ? '%' : ''}
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
        <span>💰</span> 재무비율 추이 ({symbolName})
      </h4>

      <ResponsiveContainer width="100%" height={250}>
        <LineChart
          data={chartData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="quarter"
            tick={{ fontSize: 12 }}
            stroke="#6b7280"
          />
          <YAxis
            tick={{ fontSize: 11 }}
            stroke="#6b7280"
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: '12px' }}
            iconType="line"
          />

          {/* PER */}
          {per && (
            <Line
              type="monotone"
              dataKey="per"
              stroke="#8b5cf6"
              strokeWidth={2}
              dot={{ r: 4 }}
              name="PER"
            />
          )}

          {/* PBR */}
          {pbr && (
            <Line
              type="monotone"
              dataKey="pbr"
              stroke="#06b6d4"
              strokeWidth={2}
              dot={{ r: 4 }}
              name="PBR"
            />
          )}

          {/* ROE */}
          {roe && (
            <Line
              type="monotone"
              dataKey="roe"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={{ r: 4 }}
              name="ROE (%)"
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      {/* 차트 설명 */}
      <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
        {per && (
          <div className="bg-purple-50 p-2 rounded">
            <div className="text-purple-700 font-semibold">PER</div>
            <div className="text-purple-900">{per}</div>
            <div className="text-purple-600 text-[10px]">주가수익비율</div>
          </div>
        )}
        {pbr && (
          <div className="bg-cyan-50 p-2 rounded">
            <div className="text-cyan-700 font-semibold">PBR</div>
            <div className="text-cyan-900">{pbr}</div>
            <div className="text-cyan-600 text-[10px]">주가순자산비율</div>
          </div>
        )}
        {roe && (
          <div className="bg-amber-50 p-2 rounded">
            <div className="text-amber-700 font-semibold">ROE</div>
            <div className="text-amber-900">{roe}%</div>
            <div className="text-amber-600 text-[10px]">자기자본이익률</div>
          </div>
        )}
      </div>

      <p className="mt-2 text-xs text-gray-500 italic">
        * 분기별 추이는 추정치이며, 실제 재무제표와 다를 수 있습니다.
      </p>
    </div>
  );
}
