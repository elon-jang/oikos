# Python으로 MCP 서버 실행하기

Python을 직접 사용하여 MCP 서버를 실행하는 방법입니다.
Docker 연결 문제가 발생하거나 더 안정적인 방식을 원할 때 권장합니다.

## 사전 요구사항

- Python 3.9 이상
- pip (Python 패키지 관리자)

## 빠른 시작

### 1. 프로젝트 다운로드

```bash
git clone https://github.com/elon-jang/oikos.git
cd oikos/tax_return
```

### 2. 패키지 설치

```bash
pip install fastmcp pandas openpyxl docxtpl pyyaml
```

### 3. 데이터 폴더 준비

```bash
# 데이터 폴더 생성
mkdir -p ~/donation_receipts/receipts

# 필요한 파일 복사
cp donation_receipt_template.docx ~/donation_receipts/
cp sample_income_summary.xlsx ~/donation_receipts/
```

### 4. Claude Desktop 설정

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) 또는
`%APPDATA%\Claude\claude_desktop_config.json` (Windows) 파일을 편집:

```json
{
  "mcpServers": {
    "oikos-receipt": {
      "command": "/bin/bash",
      "args": [
        "-c",
        "cd /path/to/oikos/tax_return && DATA_DIR=/path/to/donation_receipts python3 -m mcp_server.server"
      ]
    }
  }
}
```

**수정 필요한 경로:**
- `/path/to/oikos/tax_return`: 프로젝트 경로
- `/path/to/donation_receipts`: 데이터 파일이 있는 폴더

### 5. Claude Desktop 재시작

Claude Desktop을 완전히 종료한 후 다시 실행합니다.

---

## 설치 테스트

Claude Desktop 실행 전에 터미널에서 먼저 테스트할 수 있습니다.

### 서버 실행 테스트

```bash
cd /path/to/oikos/tax_return
DATA_DIR=/path/to/donation_receipts python3 -m mcp_server.server
```

정상이면 아무 출력 없이 대기합니다. `Ctrl+C`로 종료.

### 연결 테스트

```bash
cd /path/to/oikos/tax_return
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | \
  DATA_DIR=~/donation_receipts python3 -m mcp_server.server
```

성공 시 `"serverInfo":{"name":"oikos-receipt"...}` 응답이 표시됩니다.

### 도구 호출 테스트

```bash
cd /path/to/oikos/tax_return
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n{"jsonrpc":"2.0","method":"notifications/initialized"}\n{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_donation_recipients","arguments":{}}}\n' | \
  DATA_DIR=~/donation_receipts python3 -m mcp_server.server
```

성공 시 `"count":94,"total_amount":"50,820,000원"` 등 실제 데이터가 표시됩니다.

---

## pyenv 사용 시

pyenv로 Python을 관리하는 경우, **절대 경로**를 사용해야 합니다.

### Python 경로 확인

```bash
# pyenv 환경의 Python 경로 확인
which python3
# 예: /Users/사용자/.pyenv/versions/myenv/bin/python3
```

### 설정 예시

```json
{
  "mcpServers": {
    "oikos-receipt": {
      "command": "/bin/bash",
      "args": [
        "-c",
        "cd /Users/사용자/oikos/tax_return && DATA_DIR=/Users/사용자/donation_receipts /Users/사용자/.pyenv/versions/myenv/bin/python3 -m mcp_server.server"
      ]
    }
  }
}
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

## 폴더 구조

```
~/donation_receipts/           # 데이터 폴더
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

### ModuleNotFoundError: No module named 'fastmcp'

필수 패키지가 설치되지 않았습니다.

```bash
pip install fastmcp pandas openpyxl docxtpl pyyaml
```

### ModuleNotFoundError: No module named 'mcp_server'

프로젝트 디렉토리에서 실행해야 합니다.

```bash
cd /path/to/oikos/tax_return
```

또는 설정에서 `cd` 명령을 확인하세요.

### Claude Desktop에서 서버가 시작되지 않음

1. 경로가 올바른지 확인
2. Python 경로가 절대 경로인지 확인 (pyenv 사용 시)
3. `bash -c "cd ... && ..."` 패턴 사용 확인

> **참고**: Claude Desktop의 `cwd` 옵션은 작동하지 않습니다.
> 반드시 `bash -c "cd /path && python ..."` 패턴을 사용하세요.

### 로그 확인

```bash
# MCP 서버 로그
tail -f ~/Library/Logs/Claude/mcp-server-oikos-receipt.log

# Claude Desktop 메인 로그
tail -f ~/Library/Logs/Claude/main.log
```

---

## Docker vs Python 비교

| 항목 | Docker | Python |
|------|--------|--------|
| 설치 난이도 | 쉬움 (원클릭) | 중간 (패키지 설치 필요) |
| 안정성 | 연결 문제 가능 | **안정적** |
| 환경 의존성 | 없음 | Python 3.9+ 필요 |
| 업데이트 | docker pull | git pull + pip install |
| 디버깅 | 어려움 | 쉬움 |

**권장**: Docker 연결 문제가 발생하면 Python 방식으로 전환하세요.

---

## 업데이트

새 버전이 나오면:

```bash
# 최신 코드 받기
cd /path/to/oikos
git pull

# 패키지 업데이트
pip install -r tax_return/requirements.txt

# Claude Desktop 재시작
```

---

## 더 알아보기

| 문서 | 설명 |
|------|------|
| [README.md](../README.md) | 프로젝트 개요 |
| [Docker 가이드](DOCKER.md) | Docker로 MCP 서버 실행 |
| [MCP 사용 가이드](MCP_사용가이드.md) | Claude Desktop 사용법 상세 |
| [CLI 가이드](CLI_가이드.md) | 터미널에서 직접 실행 |
| [템플릿 만들기](템플릿_만들기_가이드.md) | 영수증 템플릿 작성법 |
