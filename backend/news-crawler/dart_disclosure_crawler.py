"""
🔥 Phase 2.3: DART 전자공시 크롤링
금융감독원 전자공시시스템(DART) 공시 정보 수집
"""
import os
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import zipfile
import io
import xml.etree.ElementTree as ET

load_dotenv()


class DartDisclosureCrawler:
    """DART 전자공시 크롤러"""

    def __init__(self):
        # DART Open API 키 (환경 변수에서 로드)
        self.api_key = os.getenv("DART_API_KEY", "")
        self.base_url = "https://opendart.fss.or.kr/api"

        if not self.api_key:
            print("⚠️ DART_API_KEY 환경 변수가 설정되지 않았습니다.")
            print("   https://opendart.fss.or.kr/ 에서 API 키를 발급받으세요.")

    async def get_corp_code(self, stock_code: str) -> Optional[str]:
        """
        종목 코드로 DART 기업 코드 조회

        Args:
            stock_code: 종목 코드 (예: '005930')

        Returns:
            str: DART 기업 코드 (8자리)
        """
        # DART는 종목코드와 별도의 기업코드(corp_code) 사용
        # 매핑 테이블이 필요하거나 API로 조회

        # 간단한 매핑 (실제로는 DART corpCode.xml 파일 다운로드 필요)
        # https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={api_key}

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/corpCode.xml"
                params = {"crtfc_key": self.api_key}

                async with session.get(url, params=params, timeout=30) as response:
                    if response.status != 200:
                        print(f"⚠️ DART corpCode 조회 실패: HTTP {response.status}")
                        return None

                    # ZIP 파일 다운로드 및 압축 해제
                    zip_data = await response.read()
                    with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
                        xml_filename = z.namelist()[0]
                        xml_data = z.read(xml_filename)

                    # XML 파싱
                    root = ET.fromstring(xml_data)

                    # 종목 코드로 검색
                    for corp in root.findall('list'):
                        stock_code_elem = corp.find('stock_code')
                        if stock_code_elem is not None and stock_code_elem.text:
                            if stock_code_elem.text.strip() == stock_code:
                                corp_code_elem = corp.find('corp_code')
                                if corp_code_elem is not None:
                                    return corp_code_elem.text.strip()

                    print(f"⚠️ 종목 코드 {stock_code}에 해당하는 DART 기업 코드를 찾을 수 없습니다.")
                    return None

        except Exception as e:
            print(f"❌ DART 기업 코드 조회 실패: {str(e)}")
            return None

    async def crawl_disclosures(
        self,
        corp_code: str,
        days: int = 30,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        특정 기업의 전자공시 목록 조회

        Args:
            corp_code: DART 기업 코드 (8자리)
            days: 조회 기간 (일)
            limit: 최대 공시 수

        Returns:
            List[Dict]: 전자공시 목록
        """
        if not self.api_key:
            print("❌ DART API 키가 설정되지 않았습니다.")
            return []

        disclosures = []

        try:
            # 날짜 범위 설정
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            begin_de = start_date.strftime("%Y%m%d")
            end_de = end_date.strftime("%Y%m%d")

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/list.json"
                params = {
                    "crtfc_key": self.api_key,
                    "corp_code": corp_code,
                    "bgn_de": begin_de,
                    "end_de": end_de,
                    "page_count": limit
                }

                async with session.get(url, params=params, timeout=10) as response:
                    if response.status != 200:
                        print(f"⚠️ DART 공시 조회 실패: HTTP {response.status}")
                        return []

                    data = await response.json()

                    if data.get("status") != "000":
                        error_msg = data.get("message", "Unknown error")
                        print(f"⚠️ DART API 오류: {error_msg}")
                        return []

                    items = data.get("list", [])

                    for item in items[:limit]:
                        disclosure = {
                            "corp_code": item.get("corp_code"),
                            "corp_name": item.get("corp_name"),
                            "stock_code": item.get("stock_code"),
                            "report_nm": item.get("report_nm"),  # 공시 제목
                            "rcept_no": item.get("rcept_no"),  # 접수번호
                            "flr_nm": item.get("flr_nm"),  # 공시 제출인
                            "rcept_dt": item.get("rcept_dt"),  # 접수일자 (YYYYMMDD)
                            "rm": item.get("rm"),  # 비고
                            "published_at": self._parse_dart_date(item.get("rcept_dt")),
                            "source": "dart",
                            "importance": self._classify_importance(item.get("report_nm", ""))
                        }

                        disclosures.append(disclosure)

            print(f"✅ DART 공시 조회 완료: {len(disclosures)}개")
            return disclosures

        except Exception as e:
            print(f"❌ DART 공시 조회 실패: {str(e)}")
            return []

    async def get_disclosure_detail(
        self,
        rcept_no: str
    ) -> Optional[Dict[str, Any]]:
        """
        공시 상세 내용 조회

        Args:
            rcept_no: 접수번호

        Returns:
            Dict: 공시 상세 정보
        """
        if not self.api_key:
            return None

        try:
            async with aiohttp.ClientSession() as session:
                # DART는 공시 원문을 HTML/PDF로 제공
                # 여기서는 메타데이터만 반환
                url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"

                return {
                    "rcept_no": rcept_no,
                    "detail_url": url,
                    "message": "DART 공시 원문은 웹 페이지에서 확인하세요."
                }

        except Exception as e:
            print(f"❌ 공시 상세 조회 실패: {str(e)}")
            return None

    def _parse_dart_date(self, date_str: str) -> Optional[str]:
        """
        DART 날짜 문자열 파싱 (YYYYMMDD → ISO 8601)

        Args:
            date_str: DART 날짜 문자열 (예: '20250118')

        Returns:
            str: ISO 8601 형식 날짜
        """
        try:
            if not date_str or len(date_str) != 8:
                return None

            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])

            dt = datetime(year, month, day)
            return dt.isoformat()

        except Exception as e:
            print(f"  ⚠️ DART 날짜 파싱 오류 ({date_str}): {str(e)}")
            return None

    def _classify_importance(self, report_name: str) -> str:
        """
        공시 중요도 분류

        Args:
            report_name: 공시 제목

        Returns:
            str: 중요도 (critical/high/medium/low)
        """
        # 긴급 공시 (매우 중요)
        critical_keywords = [
            "합병", "분할", "영업양수도", "주요사항보고서", "증자",
            "감자", "유상증자", "무상증자", "전환사채", "신주인수권부사채"
        ]

        # 중요 공시
        high_keywords = [
            "재무제표", "사업보고서", "분기보고", "반기보고",
            "매출", "당기순이익", "영업이익", "지배구조"
        ]

        # 보통 공시
        medium_keywords = [
            "공시", "정정", "철회", "변경", "임원", "주주총회"
        ]

        report_lower = report_name.lower()

        if any(keyword in report_lower for keyword in critical_keywords):
            return "critical"
        elif any(keyword in report_lower for keyword in high_keywords):
            return "high"
        elif any(keyword in report_lower for keyword in medium_keywords):
            return "medium"
        else:
            return "low"

    async def analyze_disclosure_impact(
        self,
        disclosures: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        공시 내용으로부터 영향도 분석

        Args:
            disclosures: 공시 목록

        Returns:
            Dict: 영향도 분석 결과
        """
        if not disclosures:
            return {
                "total_count": 0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "recent_critical": [],
                "overall_impact": "none"
            }

        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0
        recent_critical = []

        for disclosure in disclosures:
            importance = disclosure.get("importance", "low")

            if importance == "critical":
                critical_count += 1
                recent_critical.append({
                    "title": disclosure.get("report_nm"),
                    "date": disclosure.get("rcept_dt"),
                    "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={disclosure.get('rcept_no')}"
                })
            elif importance == "high":
                high_count += 1
            elif importance == "medium":
                medium_count += 1
            else:
                low_count += 1

        # 전체 영향도 평가
        if critical_count > 0:
            overall_impact = "critical"
        elif high_count >= 2:
            overall_impact = "high"
        elif high_count >= 1 or medium_count >= 3:
            overall_impact = "medium"
        else:
            overall_impact = "low"

        return {
            "total_count": len(disclosures),
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
            "recent_critical": recent_critical[:3],  # 최근 3개만
            "overall_impact": overall_impact
        }


async def main():
    """테스트 함수"""
    crawler = DartDisclosureCrawler()

    # 삼성전자 DART 공시 조회
    stock_code = "005930"
    print(f"🔍 DART 기업 코드 조회 중: {stock_code}")

    corp_code = await crawler.get_corp_code(stock_code)

    if corp_code:
        print(f"✅ DART 기업 코드: {corp_code}")

        print(f"\n📋 전자공시 조회 중...")
        disclosures = await crawler.crawl_disclosures(corp_code, days=30, limit=10)

        if disclosures:
            print(f"\n✅ 조회 완료: {len(disclosures)}개 공시")
            print("\n최근 공시 목록:")

            for i, disc in enumerate(disclosures, 1):
                print(f"{i}. [{disc['importance'].upper()}] {disc['report_nm']}")
                print(f"   날짜: {disc['rcept_dt']} | 제출: {disc['flr_nm']}")
                print(f"   URL: https://dart.fss.or.kr/dsaf001/main.do?rcpNo={disc['rcept_no']}")
                print()

            # 영향도 분석
            impact = await crawler.analyze_disclosure_impact(disclosures)
            print("\n📊 공시 영향도 분석:")
            print(f"  - 전체 공시: {impact['total_count']}개")
            print(f"  - 긴급 공시: {impact['critical_count']}개")
            print(f"  - 중요 공시: {impact['high_count']}개")
            print(f"  - 보통 공시: {impact['medium_count']}개")
            print(f"  - 낮은 공시: {impact['low_count']}개")
            print(f"  - 전체 영향도: {impact['overall_impact'].upper()}")

            if impact['recent_critical']:
                print("\n  🔥 최근 긴급 공시:")
                for crit in impact['recent_critical']:
                    print(f"    - {crit['title']} ({crit['date']})")
    else:
        print("❌ DART 기업 코드를 찾을 수 없습니다.")


if __name__ == "__main__":
    asyncio.run(main())
