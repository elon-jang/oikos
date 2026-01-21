# 기부금 영수증 자동 발행 시스템

교회, 비영리단체 등에서 사용할 수 있는 기부금 영수증 자동 발행 시스템입니다.

---

## 어떤 방법을 선택할까요?

| 방법 | 이런 분께 추천 | 난이도 |
|------|---------------|--------|
| [MCP 서버 (Docker)](#mcp-서버-docker-설치) | Claude Desktop 사용자, 환경 설정 간편 | ⭐ |
| [MCP 서버 (Python)](#mcp-서버-python-설치) | Claude Desktop 사용자, **안정적!** | ⭐⭐ |
| [Claude Code 명령어](#claude-code-명령어) | 개발자, Claude Code 사용자 | ⭐ |
| [Python 직접 실행](#python-직접-실행) | 개발자, 커스터마이징 원하시는 분 | ⭐⭐ |

---

## MCP 서버 (Docker) 설치

> **"Claude야, 영수증 만들어줘!"** 한마디면 끝!

Claude Desktop에서 자연어로 영수증을 발행할 수 있습니다.

### 설치하기 전에

**Docker Desktop**이 필요합니다. 아직 설치 안 하셨다면:
1. [Docker Desktop 다운로드](https://www.docker.com/products/docker-desktop/) 페이지 방문
2. 운영체제에 맞는 버전 다운로드
3. 설치 후 실행 (처음 실행 시 1-2분 걸릴 수 있어요)

### 원클릭 설치

#### Mac 사용자

1. **터미널 앱 열기**
   - `Cmd + Space` 누르고 "터미널" 입력 후 Enter
   - 또는 `응용 프로그램 > 유틸리티 > 터미널`

2. **아래 명령어 복사해서 붙여넣기**
   ```bash
   curl -sL https://raw.githubusercontent.com/elon-jang/oikos/master/tax_return/deploy/install.sh | bash
   ```

3. **Enter 누르고 기다리기** (설치는 1-2분 정도 걸려요)

#### Windows 사용자

1. **PowerShell 열기**
   - `Win + X` 누르고 "Windows PowerShell (관리자)" 선택
   - 또는 시작 메뉴에서 "PowerShell" 검색 후 "관리자 권한으로 실행"

2. **아래 명령어 복사해서 붙여넣기**
   ```powershell
   irm https://raw.githubusercontent.com/elon-jang/oikos/master/tax_return/deploy/install.ps1 | iex
   ```

3. **Enter 누르고 기다리기**

### 설치 완료 후

설치가 완료되면:
- Mac: `~/donation_receipts/` 폴더가 생성됩니다
- Windows: `내 문서\donation_receipts\` 폴더가 생성됩니다

이 폴더에 다음 파일들을 넣어주세요:
- 헌금 데이터 파일 (`2025_income_summary.xlsx`)
- 영수증 템플릿 (`donation_receipt_template.docx`)

그런 다음 **Claude Desktop을 재시작**하면 사용 준비 완료!

### 사용 예시

Claude Desktop을 열고 이렇게 말해보세요:

```
나: 영수증 발행 대상자가 몇 명이야?
Claude: 총 94명의 대상자가 있습니다. 전체 헌금 총액은 45,000,000원입니다.

나: 홍길동 영수증 발행해줘
Claude: 홍길동님 영수증이 생성되었습니다!
        파일: ~/donation_receipts/receipts/기부금영수증_홍길동.docx

나: 전체 영수증 발행해줘
Claude: 94명의 영수증을 생성합니다. 계속할까요?

나: 응!
Claude: 완료! 94개의 영수증이 receipts 폴더에 생성되었어요.
```

### MCP 도구 목록

| 도구 | 설명 | 사용 예시 |
|------|------|----------|
| `list_donation_recipients` | 대상자 목록 조회 | "누가 영수증 받아야 해?" |
| `generate_donation_receipt` | 특정인 영수증 생성 | "홍길동 영수증 만들어줘" |
| `generate_all_donation_receipts` | 전체 영수증 생성 | "전체 영수증 발행해" |
| `preview_donation_receipt` | 영수증 미리보기 | "홍길동 영수증 미리 보여줘" |
| `validate_donation_data` | 데이터 파일 검증 | "데이터 파일 확인해줘" |
| `validate_receipt_template` | 템플릿 파일 검증 | "템플릿 괜찮은지 봐줘" |
| `get_receipt_history` | 발행 이력 조회 | "지금까지 뭐 발행했어?" |
| `get_person_receipt_history` | 특정인 이력 조회 | "홍길동 언제 발행했었지?" |

> 자세한 내용: [DOCKER.md](docs/DOCKER.md), [MCP_사용가이드.md](docs/MCP_사용가이드.md)

---

## MCP 서버 (Python) 설치

> Docker 없이 Python으로 직접 MCP 서버 실행! **더 안정적입니다.**

Docker 연결 문제가 발생하거나, 더 안정적인 방식을 원한다면 Python 직접 실행을 추천합니다.

### 설치하기 전에

**Python 3.9+**가 필요합니다.

```bash
# 필수 패키지 설치
pip install fastmcp pandas openpyxl docxtpl pyyaml

# 프로젝트 다운로드
git clone https://github.com/elon-jang/oikos.git
cd oikos/tax_return
```

### Claude Desktop 설정

`~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) 또는
`%APPDATA%\Claude\claude_desktop_config.json` (Windows) 파일에 추가:

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
- `python3`: pyenv 사용 시 절대 경로 (예: `/Users/사용자/.pyenv/versions/myenv/bin/python3`)

### 설정 완료 후

Claude Desktop을 재시작하면 사용 준비 완료!

> 자세한 내용: [PYTHON.md](docs/PYTHON.md)

---

## Claude Code 명령어

> `/receipt` 한 번이면 영수증 발행 끝!

### 플러그인 설치

```bash
# 1. 마켓플레이스 추가 (한 번만)
/plugin marketplace add elon-jang/claude-plugins

# 2. 플러그인 설치
/plugin install oikos@elon-jang
```

### 명령어 사용법

```bash
# 전체 영수증 발행
/receipt generate

# 특정인 발행 - 홍길동님 영수증만!
/receipt generate 홍길동

# 여러 명 한번에
/receipt generate 홍길동,김철수,이영희

# 대상자 목록 확인
/receipt list

# 발행 이력 확인
/receipt history

# 특정인 이력 확인
/receipt history 강신애

# 다른 템플릿 사용
/receipt generate --template my_template.docx

# 다른 데이터 파일 사용
/receipt list --data sample_income_summary.xlsx
```

> 플러그인 설치 방법: [claude-plugins README](https://github.com/elon-jang/claude-plugins/blob/master/README.md)

---

## Python 직접 실행

> 개발자라면 Python으로 직접 컨트롤!

### 설치

```bash
# 필수 패키지
pip install pandas openpyxl docxtpl

# 설정 파일 사용 시 (선택)
pip install pyyaml

# PDF 변환 기능 사용 시 (선택)
pip install docx2pdf  # Microsoft Word 필요
# 또는
brew install libreoffice  # macOS
```

### 빠른 시작

```bash
# 샘플 데이터로 테스트해보기
python generate_receipts.py --list --data sample_income_summary.xlsx

# 한 명만 발행해보기
python generate_receipts.py -n 홍길동 --data sample_income_summary.xlsx
```

### 실제 사용 준비

1. **템플릿 준비**: [템플릿_만들기_가이드.md](docs/템플릿_만들기_가이드.md) 참고
2. **데이터 준비**: Excel 파일에 헌금 데이터 입력 (`YYYY_income_summary.xlsx`)
3. **설정 (선택)**: `config.sample.yaml` → `config.yaml` 복사 후 수정

```bash
# 설정 파일 복사
cp config.sample.yaml config.yaml

# 영수증 생성!
python generate_receipts.py
```

### 명령어 옵션

```bash
# 전체 발행 (자동 연도 감지)
python generate_receipts.py

# 한 사람만 발행
python generate_receipts.py -n 홍길동

# 여러 명 발행 (쉼표 구분)
python generate_receipts.py -n 홍길동,김철수,이영희

# 대상자 목록 확인
python generate_receipts.py --list

# 연도 수동 지정
python generate_receipts.py --year 2025

# 다른 데이터 파일 사용
python generate_receipts.py --data 2024_income_summary.xlsx

# 다른 템플릿 사용
python generate_receipts.py --template my_template.docx

# 발행 이력 조회
python generate_receipts.py --history

# 특정인 발행 이력 조회
python generate_receipts.py --history -n 강신애

# PDF로 변환 (DOCX도 유지)
python generate_receipts.py --pdf
```

### 옵션 정리

| 옵션 | 설명 | 예시 |
|------|------|------|
| (없음) | 전체 발행 (자동 연도) | `python generate_receipts.py` |
| `-n 이름` | 지정 인원만 발행 | `-n 홍길동` |
| `-n 이름1,이름2` | 여러 명 발행 | `-n 홍길동,김철수` |
| `--list` | 대상자 목록 출력 | `--list` |
| `--year 연도` | 데이터 연도 수동 지정 | `--year 2025` |
| `--data 파일` | 데이터 파일 직접 지정 | `--data 2024_income_summary.xlsx` |
| `--template 파일` | 템플릿 파일 지정 | `--template my_template.docx` |
| `--history` | 발행 이력 조회 | `--history` |
| `--history -n 이름` | 특정인 이력 조회 | `--history -n 강신애` |
| `--pdf` | PDF로 변환 (DOCX 유지) | `--pdf` |

---

## 입력 데이터

### 헌금 데이터 파일 (`YYYY_income_summary.xlsx`)

| 이름 | 1월 | 2월 | ... | 12월 | 연간 총합 |
|------|-----|-----|-----|------|----------|
| 강신애 | 50,000 | 30,000 | ... | 20,000 | 350,000 |
| 홍길동,김영희 | 100,000 | 100,000 | ... | 100,000 | 1,200,000 |

**포인트:**
- **부부 이름**: 쉼표로 구분하면 각각 별도 영수증 발행! (금액은 동일)
- **합계 행**: 자동으로 제외됩니다

---

## 템플릿

### 템플릿 파일

`donation_receipt_template.docx` - Word 문서 템플릿

### Placeholder 목록

| Placeholder | 설명 | 예시 |
|-------------|------|------|
| `{{receipt_no}}` | 발급번호 | 26-001 |
| `{{name}}` | 기부자 성명 | 홍길동 |
| `{{month_1}}` ~ `{{month_12}}` | 월별 금액 | 50,000 |
| `{{total}}` | 연간 총합 | 450,000 |

### 주의사항

- **A4 한 장 유지**: 여백, 폰트 크기 조절 시 주의
- **`{{name}}`은 2곳**: Table과 하단 서명란에 각각 있어요
- **연도 변경**: 템플릿 내 연도 직접 수정 필요

---

## 발급번호 규칙

- 형식: `YY-NNN` (예: `26-001`)
- 2025년 데이터 → `26-XXX` (발급 연도는 데이터 연도 + 1)
- 이름 가나다순 정렬 후 순차 부여

---

## 발행대장

영수증 발행 시 자동으로 `발행대장_YYYY.xlsx` 파일에 기록됩니다.

### 대장 컬럼

| 컬럼 | 설명 | 예시 |
|------|------|------|
| 발급번호 | 영수증 번호 | 26-001 |
| 이름 | 기부자명 | 강신애 |
| 연간총합 | 헌금 총액 | 450,000 |
| 발행일시 | 발행 시간 | 2026-01-20 18:30:00 |
| 파일경로 | 생성된 파일 | receipts/기부금영수증_강신애.docx |
| 비고 | 재발행 등 | 재발행 |

---

## 설정 파일 (config.yaml)

```bash
cp config.sample.yaml config.yaml
```

```yaml
# config.yaml 예시
organization:
  name: "OO교회"
  representative: "홍길동"

files:
  template: "donation_receipt_template.docx"
  output_dir: "receipts"

receipt:
  prefix: ""  # 발급번호 접두사 (예: "A" → "A26-001")
```

---

## 연간 작업 순서

### 1단계: 원본 데이터 정리

- 이름 통합 (오타, 구분자)
- 비개인 항목 제외 (셀, 무명 등)
- 총액 검증

### 2단계: 영수증 생성

```bash
python generate_receipts.py
```

### 3단계: 검증

- 샘플 파일 열어서 확인
- 총 인원수 확인 (부부 분리 반영)

### 4단계: 배포

- DOCX 파일 인쇄 또는 이메일 발송

---

## 파일 구조

```
tax_return/
├── generate_receipts.py          # 영수증 생성 스크립트
├── donation_receipt_template.docx # 영수증 템플릿 (직접 작성)
├── sample_income_summary.xlsx    # 샘플 헌금 데이터
├── config.sample.yaml            # 설정 파일 샘플
├── mcp_server/                   # MCP 서버 (Claude Desktop용)
├── tests/                        # 테스트 코드
├── deploy/                       # 배포 파일 (Docker, 설치 스크립트)
├── docs/                         # 문서
├── receipts/                     # 생성된 영수증 폴더
└── README.md                     # 이 문서
```

---

## 문제 해결

### 템플릿 파일이 없습니다

`donation_receipt_template.docx` 파일이 프로젝트 폴더에 있는지 확인하세요.

### 데이터 파일을 찾을 수 없습니다

`YYYY_income_summary.xlsx` 형식의 파일이 필요합니다.
또는 `--data 파일경로` 옵션으로 직접 지정하세요.

### 필수 컬럼이 없습니다

Excel 파일에 필수 컬럼이 있는지 확인하세요:
- `이름`, `1월`~`12월`, `연간 총합`

### TemplateSyntaxError

템플릿의 placeholder 문법을 확인하세요. (`}}` 누락 등)

### 부부가 분리되지 않음

이름에 쉼표(`,`)를 사용했는지 확인하세요. (마침표 아님!)

### PDF 변환 실패

- `docx2pdf` 설치: `pip install docx2pdf` (Microsoft Word 필요)
- 또는 LibreOffice 설치: `brew install libreoffice` (macOS)

---

**Made with love for church communities**
