#!/bin/bash
#
# 기부금 영수증 MCP 서버 설치 스크립트 (macOS)
#
# 사용법:
#   curl -sL https://raw.githubusercontent.com/elon-jang/oikos/master/tax_return/install.sh | bash
#

set -e

echo "🎁 기부금 영수증 MCP 서버 설치"
echo "================================"
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Docker 확인
echo "1️⃣  Docker 확인 중..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker가 설치되어 있지 않습니다.${NC}"
    echo ""
    echo "Docker Desktop을 먼저 설치하세요:"
    echo "👉 https://docs.docker.com/desktop/install/mac-install/"
    echo ""
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker 데몬이 실행 중이 아닙니다.${NC}"
    echo ""
    echo "Docker Desktop을 실행하세요."
    exit 1
fi
echo -e "${GREEN}✅ Docker 확인됨${NC}"

# 2. 데이터 폴더 생성
DATA_DIR="$HOME/기부금영수증"
echo ""
echo "2️⃣  데이터 폴더 생성 중..."
mkdir -p "$DATA_DIR/receipts"
echo -e "${GREEN}✅ 폴더 생성됨: $DATA_DIR${NC}"

# 3. Docker 이미지 빌드 또는 다운로드
echo ""
echo "3️⃣  Docker 이미지 준비 중..."

# 임시 디렉토리에 소스 다운로드
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

echo "   소스 코드 다운로드 중..."
git clone --depth 1 https://github.com/elon-jang/oikos.git
cd oikos/tax_return

echo "   Docker 이미지 빌드 중... (몇 분 소요될 수 있습니다)"
docker build -t oikos-receipt:latest . > /dev/null 2>&1

# 샘플 파일 복사
echo "   샘플 파일 복사 중..."
cp sample_income_summary.xlsx "$DATA_DIR/" 2>/dev/null || true

# 임시 폴더 정리
cd "$HOME"
rm -rf "$TEMP_DIR"

echo -e "${GREEN}✅ Docker 이미지 준비됨${NC}"

# 4. Claude Desktop 설정
echo ""
echo "4️⃣  Claude Desktop 설정 중..."

CONFIG_DIR="$HOME/Library/Application Support/Claude"
CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"

# 설정 디렉토리 생성
mkdir -p "$CONFIG_DIR"

# 기존 설정 백업
if [ -f "$CONFIG_FILE" ]; then
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
    echo "   기존 설정 백업됨: $CONFIG_FILE.backup"
fi

# Python으로 JSON 병합
python3 << EOF
import json
import os

config_path = "$CONFIG_FILE"
data_dir = "$DATA_DIR"

# 기존 설정 로드
config = {}
if os.path.exists(config_path):
    try:
        with open(config_path) as f:
            config = json.load(f)
    except:
        pass

# MCP 서버 추가
config.setdefault("mcpServers", {})
config["mcpServers"]["oikos-receipt"] = {
    "command": "docker",
    "args": [
        "run", "-i", "--rm",
        "-v", f"{data_dir}:/data",
        "oikos-receipt:latest"
    ]
}

# 저장
with open(config_path, "w") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("   Claude Desktop 설정 완료")
EOF

echo -e "${GREEN}✅ 설정 완료${NC}"

# 5. 완료 메시지
echo ""
echo "================================"
echo -e "${GREEN}✅ 설치가 완료되었습니다!${NC}"
echo ""
echo "📂 데이터 폴더: $DATA_DIR"
echo "   다음 파일을 이 폴더에 넣으세요:"
echo "   - donation_receipt_template.docx (영수증 템플릿)"
echo "   - YYYY_income_summary.xlsx (헌금 데이터)"
echo ""
echo "🔄 Claude Desktop을 재시작하세요."
echo ""
echo "💬 사용 예시:"
echo "   '영수증 대상자 목록 보여줘'"
echo "   '홍길동 영수증 발행해줘'"
echo "   '전체 영수증 발행해줘'"
echo ""
