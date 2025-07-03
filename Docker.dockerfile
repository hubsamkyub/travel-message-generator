# 여행 잔금 문자 생성기 - Docker 배포
FROM python:3.9-slim

LABEL maintainer="Travel Message Generator"
LABEL description="여행 잔금 문자 생성 웹 애플리케이션"

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치를 위한 requirements.txt 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip3 install -r requirements.txt

# 애플리케이션 파일들 복사
COPY main_app.py .
COPY enhanced_processor.py .
COPY ui_helpers.py .
COPY error_handler.py .
COPY config_manager.py .
COPY template_manager.py .
COPY sample_data.py .

# 설정 파일들 복사
COPY .streamlit/ .streamlit/

# 디렉토리 생성
RUN mkdir -p logs templates configs sample_files

# 포트 노출
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Streamlit 실행
ENTRYPOINT ["streamlit", "run", "main_app.py", "--server.port=8501", "--server.address=0.0.0.0"]