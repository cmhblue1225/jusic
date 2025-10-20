"""
🔍 Trading Intelligence Platform - 환경 설정 검증 스크립트
모든 필수 환경 변수 및 API 키 유효성을 자동으로 검증합니다.
"""
import os
import sys
import asyncio
from dotenv import load_dotenv
from typing import Dict, List, Tuple

# 환경 변수 로드
load_dotenv()

# ANSI 색상 코드
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text: str):
    """헤더 출력"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")


def print_success(text: str):
    """성공 메시지"""
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text: str):
    """에러 메시지"""
    print(f"{RED}❌ {text}{RESET}")


def print_warning(text: str):
    """경고 메시지"""
    print(f"{YELLOW}⚠️  {text}{RESET}")


def check_env_var(var_name: str, required: bool = True) -> Tuple[bool, str]:
    """환경 변수 확인"""
    value = os.getenv(var_name)

    if value:
        # 민감한 정보는 일부만 표시
        if 'KEY' in var_name or 'SECRET' in var_name:
            masked_value = value[:10] + '...' + value[-5:] if len(value) > 15 else value[:5] + '...'
        else:
            masked_value = value[:50] + '...' if len(value) > 50 else value

        return True, masked_value
    else:
        if required:
            return False, "Not set"
        else:
            return True, "Not set (optional)"


async def verify_kis_api() -> bool:
    """KIS API 연결 테스트"""
    try:
        from kis_data import KISDataAPI

        api = KISDataAPI()
        token = await api.get_access_token()

        if token and len(token) > 20:
            print_success(f"KIS API 토큰 발급 성공: {token[:20]}...")
            return True
        else:
            print_error("KIS API 토큰 발급 실패")
            return False

    except Exception as e:
        print_error(f"KIS API 연결 실패: {str(e)}")
        return False


async def verify_openai_api() -> bool:
    """OpenAI API 연결 테스트"""
    try:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print_warning("OPENAI_API_KEY가 설정되지 않았습니다")
            return False

        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model='gpt-4',
            messages=[{'role': 'user', 'content': 'Test'}],
            max_tokens=5
        )

        if response and response.choices:
            print_success(f"OpenAI API 연결 성공: {response.choices[0].message.content}")
            return True
        else:
            print_error("OpenAI API 응답 없음")
            return False

    except Exception as e:
        print_error(f"OpenAI API 연결 실패: {str(e)}")
        return False


async def verify_claude_api() -> bool:
    """Claude API 연결 테스트"""
    try:
        import anthropic

        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key:
            print_warning("CLAUDE_API_KEY가 설정되지 않았습니다")
            return False

        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model='claude-3-5-sonnet-20241022',
            max_tokens=5,
            messages=[{'role': 'user', 'content': 'Test'}]
        )

        if response and response.content:
            print_success(f"Claude API 연결 성공: {response.content[0].text}")
            return True
        else:
            print_error("Claude API 응답 없음")
            return False

    except Exception as e:
        print_error(f"Claude API 연결 실패: {str(e)}")
        return False


async def verify_supabase() -> bool:
    """Supabase 연결 테스트"""
    try:
        from supabase import create_client

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")

        if not url or not key:
            print_error("SUPABASE_URL 또는 SUPABASE_SERVICE_KEY가 설정되지 않았습니다")
            return False

        client = create_client(url, key)

        # 간단한 쿼리 테스트
        response = client.table('profiles').select('id').limit(1).execute()

        if response:
            print_success("Supabase 연결 성공")
            return True
        else:
            print_error("Supabase 쿼리 실패")
            return False

    except Exception as e:
        print_error(f"Supabase 연결 실패: {str(e)}")
        return False


async def main():
    """메인 검증 함수"""
    print_header("Trading Intelligence Platform")
    print_header("환경 설정 검증 스크립트")

    results: Dict[str, bool] = {}

    # 1. 필수 환경 변수 확인
    print_header("1. 필수 환경 변수 확인")

    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY",
        "KIS_APP_KEY",
        "KIS_APP_SECRET",
        "OPENAI_API_KEY",
        "CLAUDE_API_KEY"
    ]

    for var in required_vars:
        success, value = check_env_var(var, required=True)
        if success:
            print_success(f"{var}: {value}")
        else:
            print_error(f"{var}: {value}")
        results[var] = success

    # 2. 선택적 환경 변수 확인
    print_header("2. 선택적 환경 변수 확인")

    optional_vars = [
        "NAVER_CLIENT_ID",
        "NAVER_CLIENT_SECRET",
        "DART_API_KEY",
        "AI_ANALYSIS_ENABLED",
        "USE_AI_ENSEMBLE"
    ]

    for var in optional_vars:
        success, value = check_env_var(var, required=False)
        if value != "Not set (optional)":
            print_success(f"{var}: {value}")
        else:
            print_warning(f"{var}: {value}")

    # 3. API 연결 테스트
    print_header("3. API 연결 테스트")

    print("🔍 KIS API 테스트 중...")
    results["KIS_API"] = await verify_kis_api()

    print("\n🔍 Supabase 테스트 중...")
    results["SUPABASE"] = await verify_supabase()

    print("\n🔍 OpenAI API 테스트 중...")
    results["OPENAI_API"] = await verify_openai_api()

    print("\n🔍 Claude API 테스트 중...")
    results["CLAUDE_API"] = await verify_claude_api()

    # 4. 검증 결과 요약
    print_header("4. 검증 결과 요약")

    total_checks = len(results)
    passed_checks = sum(1 for v in results.values() if v)
    failed_checks = total_checks - passed_checks

    if failed_checks == 0:
        print_success(f"모든 검증 통과! ({passed_checks}/{total_checks})")
        print_success("✅ 시스템이 정상적으로 구성되었습니다.")
        print("\n다음 명령으로 서비스를 시작하세요:")
        print(f"{BLUE}  python -m uvicorn main:app --reload --port 3000{RESET}\n")
        return 0
    else:
        print_error(f"검증 실패: {failed_checks}개 항목")
        print_warning(f"통과: {passed_checks}/{total_checks}")

        print("\n실패한 항목:")
        for key, value in results.items():
            if not value:
                print_error(f"  - {key}")

        print("\n📖 설정 가이드를 참조하세요:")
        print(f"{BLUE}  /Users/dev/jusik/SETUP_GUIDE.md{RESET}\n")
        return 1

    # 5. 다음 단계 안내
    print_header("5. 다음 단계")

    print("✅ 서비스 시작:")
    print(f"{BLUE}  cd backend/report-service{RESET}")
    print(f"{BLUE}  python -m uvicorn main:app --reload --port 3000{RESET}\n")

    print("✅ API 테스트:")
    print(f"{BLUE}  curl -X POST http://localhost:3000/api/reports \\{RESET}")
    print(f"{BLUE}    -H 'Content-Type: application/json' \\{RESET}")
    print(f"{BLUE}    -d '{{\"symbol\":\"005930\",\"symbol_name\":\"삼성전자\"}}'{{RESET}}\n")


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}검증이 중단되었습니다.{RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"검증 중 오류 발생: {str(e)}")
        sys.exit(1)
