# Python 3.9-slim 이미지를 베이스로 사용
FROM python:3.9-slim

# Playwright 실행에 필요한 OS 라이브러리 설치
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgbm1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 환경 변수 설정 (필요시 포트 설정)
ENV PORT=3000

WORKDIR /app

# requirements.txt 복사 후 의존성 설치 (PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD 환경 변수 설정은 빌드 시점에 설정된 상태여야 함)
COPY requirements.txt .
RUN pip install -r requirements.txt

# 런타임 시 필요한 브라우저 설치 (chromium만 설치)
RUN playwright install chromium

# 전체 프로젝트 파일 복사
COPY . .

# 서버 실행: 여기서는 Python API 엔트리 포인트 파일을 실행 (실제 파일명으로 수정)
CMD ["python", "api/index.py"]
