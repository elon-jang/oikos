# 기부금 영수증 MCP 서버 설치 스크립트 (Windows PowerShell)
#
# 사용법:
#   PowerShell에서 실행:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#   irm https://raw.githubusercontent.com/elon-jang/oikos/master/examples/tax_return/install.ps1 | iex
#

$ErrorActionPreference = "Stop"

Write-Host "🎁 기부금 영수증 MCP 서버 설치" -ForegroundColor Cyan
Write-Host "================================"
Write-Host ""

# 1. Docker 확인
Write-Host "1️⃣  Docker 확인 중..."
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker 확인됨: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker가 설치되어 있지 않습니다." -ForegroundColor Red
    Write-Host ""
    Write-Host "Docker Desktop을 먼저 설치하세요:"
    Write-Host "👉 https://docs.docker.com/desktop/install/windows-install/"
    exit 1
}

# Docker 데몬 확인
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker 데몬이 실행 중이 아닙니다." -ForegroundColor Red
    Write-Host "Docker Desktop을 실행하세요."
    exit 1
}

# 2. 데이터 폴더 생성
$dataDir = "$env:USERPROFILE\기부금영수증"
Write-Host ""
Write-Host "2️⃣  데이터 폴더 생성 중..."
New-Item -ItemType Directory -Force -Path "$dataDir\receipts" | Out-Null
Write-Host "✅ 폴더 생성됨: $dataDir" -ForegroundColor Green

# 3. Docker 이미지 빌드
Write-Host ""
Write-Host "3️⃣  Docker 이미지 준비 중..."

$tempDir = New-TemporaryFile | ForEach-Object { Remove-Item $_; New-Item -ItemType Directory -Path $_ }
Set-Location $tempDir

Write-Host "   소스 코드 다운로드 중..."
git clone --depth 1 https://github.com/elon-jang/oikos.git
Set-Location oikos/examples/tax_return

Write-Host "   Docker 이미지 빌드 중... (몇 분 소요될 수 있습니다)"
docker build -t oikos-receipt:latest . | Out-Null

# 샘플 파일 복사
Write-Host "   샘플 파일 복사 중..."
Copy-Item -Path "sample_income_summary.xlsx" -Destination $dataDir -ErrorAction SilentlyContinue

# 임시 폴더 정리
Set-Location $env:USERPROFILE
Remove-Item -Recurse -Force $tempDir

Write-Host "✅ Docker 이미지 준비됨" -ForegroundColor Green

# 4. Claude Desktop 설정
Write-Host ""
Write-Host "4️⃣  Claude Desktop 설정 중..."

$configDir = "$env:APPDATA\Claude"
$configFile = "$configDir\claude_desktop_config.json"

# 설정 디렉토리 생성
New-Item -ItemType Directory -Force -Path $configDir | Out-Null

# 기존 설정 백업
if (Test-Path $configFile) {
    Copy-Item $configFile "$configFile.backup"
    Write-Host "   기존 설정 백업됨: $configFile.backup"
}

# JSON 설정 생성/업데이트
$config = @{}
if (Test-Path $configFile) {
    try {
        $config = Get-Content $configFile | ConvertFrom-Json -AsHashtable
    } catch {
        $config = @{}
    }
}

if (-not $config.ContainsKey("mcpServers")) {
    $config["mcpServers"] = @{}
}

$config["mcpServers"]["oikos-receipt"] = @{
    "command" = "docker"
    "args" = @(
        "run", "-i", "--rm",
        "-v", "${dataDir}:/data",
        "oikos-receipt:latest"
    )
}

$config | ConvertTo-Json -Depth 10 | Set-Content $configFile -Encoding UTF8
Write-Host "✅ 설정 완료" -ForegroundColor Green

# 5. 완료 메시지
Write-Host ""
Write-Host "================================"
Write-Host "✅ 설치가 완료되었습니다!" -ForegroundColor Green
Write-Host ""
Write-Host "📂 데이터 폴더: $dataDir"
Write-Host "   다음 파일을 이 폴더에 넣으세요:"
Write-Host "   - donation_receipt_template.docx (영수증 템플릿)"
Write-Host "   - YYYY_income_summary.xlsx (헌금 데이터)"
Write-Host ""
Write-Host "🔄 Claude Desktop을 재시작하세요."
Write-Host ""
Write-Host "💬 사용 예시:"
Write-Host "   '영수증 대상자 목록 보여줘'"
Write-Host "   '홍길동 영수증 발행해줘'"
Write-Host "   '전체 영수증 발행해줘'"
Write-Host ""
