# Docker로 MCP 서버 실행하기

Docker를 사용하면 Python 환경 설정 없이 MCP 서버를 실행할 수 있습니다.

## 사전 요구사항

- Docker Desktop 설치
  - macOS: https://docs.docker.com/desktop/install/mac-install/
  - Windows: https://docs.docker.com/desktop/install/windows-install/

## 빠른 시작

### 1. Docker 이미지 받기

```bash
# Docker Hub에서 이미지 받기 (권장)
docker pull joomanba/oikos-receipt:latest
```

또는 직접 빌드:

```bash
# 프로젝트 폴더에서 실행
cd tax_return
docker build -f deploy/Dockerfile -t oikos-receipt .
```

### 2. 데이터 폴더 준비

```bash
# 데이터 폴더 생성
mkdir -p ~/donation_receipts/receipts

# 필요한 파일 복사
cp donation_receipt_template.docx ~/donation_receipts/
cp 2025_income_summary.xlsx ~/donation_receipts/
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
        "-v", "/Users/사용자이름/donation_receipts:/data",
        "joomanba/oikos-receipt:latest"
      ]
    }
  }
}
```

> `/Users/사용자이름/donation_receipts` 부분을 실제 데이터 폴더 경로로 변경하세요.

### 4. Claude Desktop 재시작

Claude Desktop을 완전히 종료한 후 다시 실행합니다.

---

## 설치 테스트

Claude Desktop 실행 전에 터미널에서 먼저 테스트할 수 있습니다.

### 연결 테스트

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | \
  docker run -i --rm -v ~/donation_receipts:/data joomanba/oikos-receipt:latest
```

성공 시 `"serverInfo":{"name":"oikos-receipt"...}` 응답이 표시됩니다.

### 도구 호출 테스트

```bash
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","method":"notifications/initialized"}\n{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_donation_recipients","arguments":{}}}\n' | \
  docker run -i --rm -v ~/donation_receipts:/data joomanba/oikos-receipt:latest
```

성공 시 `"count":94,"total_amount":"50,820,000원"` 등 실제 데이터가 표시됩니다.

---

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

---

## MCP 도구 목록

| 도구 | 설명 |
|------|------|
| `list_donation_recipients` | 대상자 목록 조회 |
| `generate_donation_receipt` | 특정인 영수증 생성 |
| `generate_all_donation_receipts` | 전체 영수증 생성 |
| `preview_donation_receipt` | 영수증 미리보기 |
| `validate_donation_data` | 데이터 파일 검증 |
| `validate_receipt_template` | 템플릿 파일 검증 |
| `get_receipt_history` | 발행 이력 조회 |
| `get_person_receipt_history` | 특정인 이력 조회 |

---

## 명령어 레퍼런스

### 이미지 관리

```bash
# Docker Hub에서 최신 버전 받기
docker pull joomanba/oikos-receipt:latest

# 특정 버전 받기
docker pull joomanba/oikos-receipt:v1.1.0

# 이미지 목록
docker images | grep oikos

# 이미지 삭제
docker rmi joomanba/oikos-receipt:latest
```

### 직접 빌드

```bash
# 기본 빌드
cd tax_return
docker build -f deploy/Dockerfile -t oikos-receipt .

# 캐시 없이 새로 빌드
docker build --no-cache -f deploy/Dockerfile -t oikos-receipt .
```

---

## 폴더 구조

```
~/donation_receipts/           # 데이터 폴더 (볼륨 마운트)
├── donation_receipt_template.docx  # 영수증 템플릿
├── 2025_income_summary.xlsx        # 헌금 데이터
├── config.yaml                     # 설정 (선택)
├── receipts/                       # 생성된 영수증
│   ├── 기부금영수증_홍길동.docx
│   └── ...
└── 발행대장_2026.xlsx             # 발행 기록
```

---

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

### Claude Desktop에서 도구 호출 안됨

도구 이름이 올바른지 확인하세요. v1.1.0부터 도구 이름이 변경되었습니다:
- ~~`tool_list_recipients`~~ → `list_donation_recipients`
- ~~`tool_generate_receipt`~~ → `generate_donation_receipt`

최신 이미지를 사용하세요:
```bash
docker pull joomanba/oikos-receipt:latest
```

---

## 업데이트

새 버전이 나오면:

```bash
# 최신 이미지 받기
docker pull joomanba/oikos-receipt:latest

# Claude Desktop 재시작
```
