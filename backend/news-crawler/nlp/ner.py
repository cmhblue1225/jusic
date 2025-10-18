"""
종목명 Named Entity Recognition (NER)
뉴스 텍스트에서 종목명/종목코드를 추출
"""
import re
from typing import List, Dict
from supabase import Client


class StockNER:
    """종목명 추출기"""

    def __init__(self, supabase_client: Client):
        """
        Args:
            supabase_client: Supabase 클라이언트
        """
        self.supabase = supabase_client
        self.stocks: Dict[str, str] = {}  # {종목명: 종목코드}
        self.load_stock_master()

    def load_stock_master(self):
        """stock_master 테이블에서 전체 종목 로드"""
        try:
            response = self.supabase.table("stock_master").select("symbol, name").execute()

            if response.data:
                # 종목명 -> 종목코드 매핑
                for stock in response.data:
                    name = stock["name"]
                    symbol = stock["symbol"]
                    self.stocks[name] = symbol

                    # 약칭도 추가 (예: 삼성전자 -> 삼성)
                    if len(name) > 2:
                        short_name = name[:2]
                        if short_name not in self.stocks:
                            self.stocks[short_name] = symbol

                print(f"✅ {len(response.data)}개 종목 로드 완료")
            else:
                print("⚠️ stock_master 테이블이 비어있습니다.")

        except Exception as e:
            print(f"❌ stock_master 로드 실패: {str(e)}")

    def extract_symbols(self, text: str) -> List[str]:
        """
        텍스트에서 종목 코드 추출

        Args:
            text: 뉴스 제목 + 본문

        Returns:
            종목 코드 리스트 (중복 제거)
        """
        if not text:
            return []

        found_symbols = set()

        # 1. 종목 코드 패턴 매칭 (6자리 숫자)
        code_pattern = r'\b(\d{6})\b'
        code_matches = re.findall(code_pattern, text)
        for code in code_matches:
            # 유효한 종목 코드인지 확인 (stock_master에 존재)
            if code in [v for v in self.stocks.values()]:
                found_symbols.add(code)

        # 2. 종목명 매칭
        for stock_name, stock_code in self.stocks.items():
            # 정확한 종목명 매칭
            if stock_name in text:
                found_symbols.add(stock_code)

        return list(found_symbols)

    def extract_with_confidence(self, text: str) -> List[Dict[str, any]]:
        """
        신뢰도와 함께 종목 추출

        Args:
            text: 뉴스 텍스트

        Returns:
            [{symbol: str, name: str, confidence: float}]
        """
        if not text:
            return []

        results = []
        found = set()

        # 종목명으로 매칭
        for stock_name, stock_code in self.stocks.items():
            if stock_code in found:
                continue

            # 종목명이 텍스트에 포함되어 있는지
            if stock_name in text:
                # 신뢰도 계산 (단어 길이가 길수록 신뢰도 높음)
                confidence = min(1.0, len(stock_name) / 5.0)

                results.append({
                    "symbol": stock_code,
                    "name": stock_name,
                    "confidence": confidence
                })
                found.add(stock_code)

        # 신뢰도 순으로 정렬
        results.sort(key=lambda x: x["confidence"], reverse=True)

        return results


def test_ner():
    """테스트 함수"""
    from supabase import create_client
    import os
    from dotenv import load_dotenv

    load_dotenv()

    supabase = create_client(
        os.getenv("SUPABASE_URL", ""),
        os.getenv("SUPABASE_SERVICE_KEY", "")
    )

    ner = StockNER(supabase)

    # 테스트 케이스
    test_texts = [
        "삼성전자(005930)가 3분기 실적을 발표했다.",
        "SK하이닉스와 삼성전자가 메모리 시장을 주도하고 있다.",
        "NAVER(035420) 주가가 급등했다.",
        "카카오 클라우드 사업이 성장하고 있다.",
    ]

    for text in test_texts:
        print(f"\n📝 텍스트: {text}")
        symbols = ner.extract_symbols(text)
        print(f"✅ 추출된 종목: {symbols}")

        with_conf = ner.extract_with_confidence(text)
        for item in with_conf:
            print(f"  - {item['name']}({item['symbol']}): 신뢰도 {item['confidence']:.2f}")


if __name__ == "__main__":
    test_ner()
