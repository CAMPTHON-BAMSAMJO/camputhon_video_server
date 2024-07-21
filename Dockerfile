# 베이스 이미지로 Python 3.9 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    libsndfile1 \
    ffmpeg \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# 특정 정책만 주석 처리
RUN sed -i 's|<policy domain="path" rights="none" pattern="@\\*"/>|<!-- <policy domain="path" rights="none" pattern="@*"/> -->|g' /etc/ImageMagick-6/policy.xml

# requirements.txt 파일을 작업 디렉토리로 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 현재 디렉토리의 모든 파일을 작업 디렉토리로 복사
COPY . .

# Google Cloud 서비스 계정 키 파일을 이미지에 복사
COPY camputhon-stt-6b87122202e7.json /app/camputhon-stt-6b87122202e7.json

# 환경 변수 설정
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/camputhon-stt-6b87122202e7.json
ENV IMAGEMAGICK_BINARY=/usr/bin/convert

# FastAPI 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
