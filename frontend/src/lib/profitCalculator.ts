/**
 * 수익률 계산 유틸리티
 * Phase 2.2.1: 실시간 시세 연동 수익률 계산
 */

export interface ProfitData {
  totalInvestment: number; // 총 투자금액
  totalEvaluation: number; // 총 평가금액
  totalProfit: number; // 총 평가손익
  profitRate: number; // 수익률 (%)
}

export interface StockProfit {
  symbol: string;
  name: string;
  quantity: number;
  avgPrice: number;
  currentPrice: number;
  investment: number; // 투자금액
  evaluation: number; // 평가금액
  profit: number; // 평가손익
  profitRate: number; // 수익률 (%)
}

/**
 * 포트폴리오 아이템 (DB 스키마)
 */
export interface PortfolioItem {
  id: string;
  user_id: string;
  symbol: string;
  symbol_name: string;
  qty: number;
  avg_price: number;
  created_at: string;
  updated_at: string;
}

/**
 * 실시간 시세가 포함된 포트폴리오 아이템
 */
export interface PortfolioWithProfit extends PortfolioItem {
  currentPrice: number | null; // 현재가 (실시간 또는 종가)
  investment: number; // 투자금액
  evaluation: number; // 평가금액
  profit: number; // 평가손익
  profitRate: number; // 수익률 (%)
}

/**
 * 개별 종목 수익률 계산
 */
export function calculateStockProfit(
  quantity: number,
  avgPrice: number,
  currentPrice: number
): {
  investment: number;
  evaluation: number;
  profit: number;
  profitRate: number;
} {
  const investment = quantity * avgPrice;
  const evaluation = quantity * currentPrice;
  const profit = evaluation - investment;
  const profitRate = investment > 0 ? (profit / investment) * 100 : 0;

  return {
    investment,
    evaluation,
    profit,
    profitRate,
  };
}

/**
 * 전체 포트폴리오 수익률 계산
 */
export function calculatePortfolioProfit(stocks: StockProfit[]): ProfitData {
  const totalInvestment = stocks.reduce((sum, stock) => sum + stock.investment, 0);
  const totalEvaluation = stocks.reduce((sum, stock) => sum + stock.evaluation, 0);
  const totalProfit = totalEvaluation - totalInvestment;
  const profitRate = totalInvestment > 0 ? (totalProfit / totalInvestment) * 100 : 0;

  return {
    totalInvestment,
    totalEvaluation,
    totalProfit,
    profitRate,
  };
}

/**
 * 실시간 시세를 사용한 포트폴리오 평가금액 계산
 * @param portfolioItems DB에서 가져온 포트폴리오 아이템들
 * @param currentPrices 실시간 시세 Map (symbol → price)
 * @returns 평가금액이 계산된 포트폴리오 아이템들
 */
export function calculatePortfolioWithPrices(
  portfolioItems: PortfolioItem[],
  currentPrices: Map<string, number>
): PortfolioWithProfit[] {
  return portfolioItems.map((item) => {
    const currentPrice = currentPrices.get(item.symbol) || null;

    // 현재가가 없으면 평균단가를 사용 (fallback)
    const priceToUse = currentPrice ?? item.avg_price;

    const { investment, evaluation, profit, profitRate } = calculateStockProfit(
      item.qty,
      item.avg_price,
      priceToUse
    );

    return {
      ...item,
      currentPrice,
      investment,
      evaluation,
      profit,
      profitRate,
    };
  });
}

/**
 * 포트폴리오 전체 통계 계산
 * @param portfolioWithProfit 평가금액이 계산된 포트폴리오 아이템들
 * @returns 전체 통계 데이터
 */
export function calculatePortfolioStats(portfolioWithProfit: PortfolioWithProfit[]): ProfitData {
  const totalInvestment = portfolioWithProfit.reduce((sum, item) => sum + item.investment, 0);
  const totalEvaluation = portfolioWithProfit.reduce((sum, item) => sum + item.evaluation, 0);
  const totalProfit = totalEvaluation - totalInvestment;
  const profitRate = totalInvestment > 0 ? (totalProfit / totalInvestment) * 100 : 0;

  return {
    totalInvestment,
    totalEvaluation,
    totalProfit,
    profitRate,
  };
}

/**
 * 수익률 색상 결정
 */
export function getProfitColor(profitRate: number): string {
  if (profitRate > 0) return 'text-red-600'; // 상승 (빨간색)
  if (profitRate < 0) return 'text-blue-600'; // 하락 (파란색)
  return 'text-gray-600'; // 보합
}

/**
 * 수익률 포맷팅 (+/-부호 포함)
 */
export function formatProfitRate(profitRate: number): string {
  const sign = profitRate > 0 ? '+' : '';
  return `${sign}${profitRate.toFixed(2)}%`;
}

/**
 * 금액 포맷팅 (천단위 콤마)
 */
export function formatCurrency(amount: number): string {
  return amount.toLocaleString('ko-KR');
}
