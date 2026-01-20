# Docker로 MCP 서버 실행하기

Docker를 사용하면 Python 환경 설정 없이 MCP 서버를 실행할 수 있습니다.

## 사전 요구사항

- Docker Desktop 설치
  - macOS: https://docs.docker.com/desktop/install/mac-install/
  - Windows: https://docs.docker.com/desktop/install/windows-install/

## 빠른 시작

### 1. Docker 이미지 빌드

```bash
# 프로젝트 폴더에서 실행
cd examples/tax_return
docker build -t oikos-receipt .
```

### 2. 데이터 폴더 준비

```bash
# 데이터 폴더 생성
mkdir -p ~/기부금영수증/receipts

# 필요한 파일 복사
cp donation_receipt_template.docx ~/기부금영수증/
cp 2025_income_summary.xlsx ~/기부금영수증/
```

### 3. Claude Desktop 설정

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) 또는
`%APPDATA%\Claude\claude_desktop_config.json` (Windows) 파일을 편집:

```json
{
  "mcpServers": {
    "oikos-receipt": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "/Users/사용자이름/기부금영수증:/data",
        "oikos-receipt:latest"
      ]
    }
  }
}
```

> ⚠️ `/Users/사용자이름/기부금영수증` 부분을 실제 데이터 폴더 경로로 변경하세요.

### 4. Claude Desktop 재시작

Claude Desktop을 완전히 종료한 후 다시 실행합니다.

## 사용 예시

Claude Desktop에서 다음과 같이 대화할 수 있습니다:

```
사용자: 영수증 발행 대상자가 몇 명이야?
Claude: 총 94명의 대상자가 있습니다.

사용자: 홍길동 영수증 발행해줘
Claude: 홍길동님 영수증이 생성되었습니다.
        파일: /data/receipts/기부금영수증_홍길동.docx

사용자: 전체 영수증 발행해줘
Claude: 94명의 영수증을 생성합니다. 계속할까요?
```

## 명령어 레퍼런스

### 이미지 빌드

```bash
# 기본 빌드
docker build -t oikos-receipt .

# 버전 태그 추가
docker build -t oikos-receipt:1.0.0 .
```

### 수동 실행 (테스트용)

```bash
# 대화형 실행
docker run -it --rm \
  -v ~/기부금영수증:/data \
  oikos-receipt

# 목록 조회 테스트
echo '{"method": "tools/call", "params": {"name": "tool_list_recipients"}}' | \
  docker run -i --rm -v ~/기부금영수증:/data oikos-receipt
```

### 이미지 관리

```bash
# 이미지 목록
docker images | grep oikos

# 이미지 삭제
docker rmi oikos-receipt

# 캐시 정리
docker builder prune
```

## 폴더 구조

```
~/기부금영수증/           # 데이터 폴더 (볼륨 마운트)
├── donation_receipt_template.docx  # 영수증 템플릿
├── 2025_income_summary.xlsx        # 헌금 데이터
├── config.yaml                     # 설정 (선택)
├── receipts/                       # 생성된 영수증
│   ├── 기부금영수증_홍길동.docx
│   └── ...
└── 발행대장_2026.xlsx             # 발행 기록
```

## 문제 해결

### Docker 데몬이 실행되지 않음

```
Cannot connect to the Docker daemon
```

→ Docker Desktop을 실행하세요.

### 볼륨 마운트 권한 오류

```
Permission denied
```

→ Docker Desktop 설정에서 해당 폴더를 File Sharing에 추가하세요.
   (Settings → Resources → File Sharing)

### MCP 연결 실패

```
MCP server failed to start
```

1. Docker Desktop이 실행 중인지 확인
2. `claude_desktop_config.json` 경로 확인
3. 볼륨 마운트 경로가 올바른지 확인

### 이미지 빌드 실패

```bash
# 캐시 없이 새로 빌드
docker build --no-cache -t oikos-receipt .
```

## 업데이트

새 버전이 나오면:

```bash
# 최신 코드 받기
git pull

# 이미지 재빌드
docker build -t oikos-receipt .

# Claude Desktop 재시작
```

## Docker Hub에서 받기 (향후)

```bash
# Docker Hub에서 이미지 받기
docker pull elonj/oikos-receipt:latest

# Claude Desktop 설정에서 이미지 이름 변경
"oikos-receipt:latest" → "elonj/oikos-receipt:latest"
```
