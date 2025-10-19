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

# 환경 변수
ENV PORT=3004

# 실행 명령 (Python으로 직접 실행)
CMD ["python", "main.py"]
