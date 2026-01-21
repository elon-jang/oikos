# 기부금 영수증 자동 발행 시스템

교회, 비영리단체를 위한 기부금 영수증 자동 발행 시스템입니다.
Claude Desktop에서 **"홍길동 영수증 발행해줘"** 한마디면 끝!

---

## 시작하기

### 어떤 방법을 선택할까요?

| 사용자 유형 | 추천 방법 | 가이드 |
|------------|----------|--------|
| 처음 사용하시는 분 | Docker 원클릭 설치 | [시작하기 가이드](docs/시작하기_가이드.md) |
| Claude Desktop 사용자 | MCP 서버 (Docker) | [Docker 가이드](docs/DOCKER.md) |
| Docker 연결 문제 시 | MCP 서버 (Python) | [Python 가이드](docs/PYTHON.md) |
| 개발자 / CLI 선호 | Python 스크립트 | [CLI 가이드](docs/CLI_가이드.md) |

> **권장**: Docker 방식이 가장 간편합니다. 연결 문제 발생 시 Python 방식으로 전환하세요.

---

## 주요 기능

- **자연어 영수증 발행**: "홍길동 영수증 만들어줘"
- **전체 일괄 발행**: 수백 명도 한번에
- **발행대장 자동 기록**: 재발행 추적 가능
- **부부 자동 분리**: 쉼표로 구분된 이름 각각 발행
- **데이터 검증**: 발행 전 오류 확인

---

## 문서 목록

### 설치 가이드

| 문서 | 설명 |
|------|------|
| [시작하기 가이드](docs/시작하기_가이드.md) | 처음부터 차근차근 설치 |
| [Docker 가이드](docs/DOCKER.md) | Docker로 MCP 서버 실행 |
| [Python 가이드](docs/PYTHON.md) | Python으로 MCP 서버 실행 |
| [CLI 가이드](docs/CLI_가이드.md) | 터미널에서 직접 실행 |

### 사용 가이드

| 문서 | 설명 |
|------|------|
| [MCP 사용 가이드](docs/MCP_사용가이드.md) | Claude Desktop 사용법 상세 |
| [템플릿 만들기](docs/템플릿_만들기_가이드.md) | 영수증 템플릿 작성법 |

---

## 빠른 설치 (Mac)

```bash
curl -sL https://raw.githubusercontent.com/elon-jang/oikos/master/tax_return/deploy/install.sh | bash
```

Windows는 [시작하기 가이드](docs/시작하기_가이드.md)를 참고하세요.

---

## 필요한 파일

| 파일 | 설명 |
|------|------|
| `donation_receipt_template.docx` | 영수증 템플릿 ([만들기 가이드](docs/템플릿_만들기_가이드.md)) |
| `YYYY_income_summary.xlsx` | 헌금 데이터 (연도_income_summary.xlsx) |

---

## 사용 예시

Claude Desktop에서:

```
나: 영수증 대상자가 몇 명이야?
Claude: 총 94명입니다. 전체 금액은 50,820,000원이에요.

나: 홍길동 영수증 발행해줘
Claude: 홍길동님 영수증이 생성되었습니다! (26-042)

나: 전체 영수증 발행해줘
Claude: 94명의 영수증을 생성합니다. 계속할까요?
```

---

## 프로젝트 구조

```
tax_return/
├── mcp_server/          # MCP 서버 (Claude Desktop용)
├── generate_receipts.py # CLI 스크립트
├── deploy/              # 설치 스크립트, Dockerfile
├── docs/                # 문서
└── tests/               # 테스트
```

---

## 문의 및 기여

- **Issues**: [GitHub Issues](https://github.com/elon-jang/oikos/issues)
- **기여**: Pull Request 환영합니다

---

**Made with love for church communities**
