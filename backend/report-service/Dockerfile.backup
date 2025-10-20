FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 설치 (최소화)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# pip 업그레이드
RUN pip install --no-cache-dir --upgrade pip

# 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# Railway가 제공하는 PORT 환경 변수 사용 (기본값 8080)
# Railway는 자동으로 PORT를 설정하므로 ENV로 하드코딩하지 않음

# 실행 명령 (Python으로 직접 실행)
CMD ["python", "main.py"]
