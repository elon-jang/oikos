# 기부금 영수증 시스템 - Claude 컨텍스트

## 프로젝트 개요
교회/비영리단체용 기부금 영수증 자동 발행 시스템. MCP 서버, CLI, Python 스크립트 지원.

## 주요 경로
- `mcp_server/` - MCP 서버 코드
- `generate_receipts.py` - CLI 스크립트
- `deploy/` - Docker, 설치 스크립트
- `docs/` - 문서

## MCP 서버 베스트 프랙티스

### 도구 이름 규칙
- `tool_` 접두사 사용 금지 (Claude Desktop 호출 문제 발생)
- 설명적 이름 사용: `list_donation_recipients`, `generate_donation_receipt`

### Claude Desktop 설정
Docker보다 Python 직접 실행이 안정적:

```json
{
  "mcpServers": {
    "oikos-receipt": {
      "command": "/bin/bash",
      "args": [
        "-c",
        "cd /path/to/tax_return && DATA_DIR=/path/to/data python3 -m mcp_server.server"
      ]
    }
  }
}
```

### 주의사항
- `cwd` 옵션 미작동 → `bash -c "cd ... && ..."` 패턴 사용
- pyenv 사용 시 절대 경로 필요: `/Users/xxx/.pyenv/versions/myenv/bin/python3`
- stdout 출력 금지: `show_banner=False`, `log_level="ERROR"` 필수

### 디버깅
```bash
# MCP 서버 로그 확인
tail -f ~/Library/Logs/Claude/mcp-server-oikos-receipt.log

# Claude Desktop 로그
tail -f ~/Library/Logs/Claude/main.log
```

## 테스트
```bash
# 단위 테스트
pytest tests/

# MCP 서버 수동 테스트
python -m mcp_server.server
```
