@echo off
REM GUI 설치 도우미 빌드 스크립트 (Windows)
REM
REM 사전 요구사항:
REM   pip install pyinstaller
REM
REM 사용법:
REM   build_installer.bat

echo 🔨 GUI 설치 도우미 빌드
echo ========================
echo.

REM PyInstaller 확인
where pyinstaller >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ PyInstaller가 설치되어 있지 않습니다.
    echo    pip install pyinstaller
    exit /b 1
)

REM 빌드 디렉토리 정리
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
del /q *.spec 2>nul

REM Windows exe 빌드
echo 📦 Windows exe 빌드 중...
pyinstaller ^
    --name "기부금영수증_설치" ^
    --onefile ^
    --windowed ^
    --noconfirm ^
    --clean ^
    install_gui.py

echo.
echo ✅ 빌드 완료!
echo.
echo 생성된 파일:
echo   Windows: dist\기부금영수증_설치.exe
echo.
echo 배포 방법:
echo   1. dist\ 폴더의 exe를 압축
echo   2. GitHub Release에 업로드
echo   3. 사용자는 다운로드 후 더블클릭으로 실행

pause
