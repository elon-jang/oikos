#!/bin/bash
#
# GUI 설치 도우미 빌드 스크립트 (macOS)
#
# 사전 요구사항:
#   pip install pyinstaller
#
# 사용법:
#   ./build_installer.sh
#

set -e

echo "🔨 GUI 설치 도우미 빌드"
echo "========================"
echo ""

# PyInstaller 확인
if ! command -v pyinstaller &> /dev/null; then
    echo "❌ PyInstaller가 설치되어 있지 않습니다."
    echo "   pip install pyinstaller"
    exit 1
fi

# 빌드 디렉토리 정리
rm -rf build dist *.spec

# macOS 앱 빌드
echo "📦 macOS 앱 빌드 중..."
pyinstaller \
    --name "기부금영수증 설치" \
    --onefile \
    --windowed \
    --noconfirm \
    --clean \
    install_gui.py

echo ""
echo "✅ 빌드 완료!"
echo ""
echo "생성된 파일:"
if [ -d "dist/기부금영수증 설치.app" ]; then
    echo "  macOS: dist/기부금영수증 설치.app"
elif [ -f "dist/기부금영수증 설치" ]; then
    echo "  실행파일: dist/기부금영수증 설치"
fi
echo ""
echo "배포 방법:"
echo "  1. dist/ 폴더의 앱을 압축"
echo "  2. GitHub Release에 업로드"
echo "  3. 사용자는 다운로드 후 더블클릭으로 실행"
