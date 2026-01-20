# 기부금 영수증 MCP 서버 Docker 이미지
#
# 빌드: docker build -t oikos-receipt .
# 실행: docker run -i -v /path/to/data:/data oikos-receipt

FROM python:3.11-slim

# 메타데이터
LABEL maintainer="elon-jang"
LABEL description="기부금 영수증 MCP 서버"
LABEL version="1.0.0"

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (최소화)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY mcp_server/ ./mcp_server/
COPY generate_receipts.py .

# 데이터 디렉토리 (볼륨 마운트 포인트)
VOLUME /data

# 환경 변수
ENV DATA_DIR=/data
ENV PYTHONUNBUFFERED=1

# MCP 서버는 stdio 모드로 실행
# Claude Desktop이 stdin/stdout으로 통신
ENTRYPOINT ["python", "-m", "mcp_server.server"]
