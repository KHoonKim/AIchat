# Dockerfile
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 종속성 파일 복사 및 설치
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 설정 (Heroku는 기본적으로 $PORT 환경 변수를 사용)
ENV PORT=8000

# 애플리케이션 시작 명령어
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT

