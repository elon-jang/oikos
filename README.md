# Oikos - 교회 업무 자동화 도구

> "오이코스(Oikos)"는 그리스어로 "가정, 공동체"를 의미합니다.
> 교회 공동체의 행정 업무를 자동화하여 더 중요한 사역에 집중할 수 있도록 돕습니다.

---

## 기부금 영수증 자동 발행 시스템

**매년 1월, 100명이 넘는 성도님들의 기부금 영수증을 일일이 만드느라 고생하셨나요?**

이제 Claude에게 말만 하세요:

```
나: 올해 영수증 발행 대상자가 몇 명이야?
Claude: 총 94명입니다. 전체 헌금 총액은 45,000,000원이에요.

나: 전체 영수증 발행해줘
Claude: 94명의 영수증을 생성할게요. 진행할까요?

나: 응!
Claude: 완료! 📁 receipts 폴더에 94개의 영수증이 생성되었어요.
```

**5분 만에 100명분 영수증 발행 완료!**

---

## 설치 방법

### 방법 1: Claude Desktop 사용자 (가장 쉬움)

**컴퓨터 잘 모르셔도 괜찮아요!** 아래 명령어 한 줄이면 끝납니다.

#### Mac 사용자

1. `터미널` 앱을 엽니다 (Spotlight에서 "터미널" 검색)
2. 아래 명령어를 복사해서 붙여넣고 Enter:

```bash
curl -sL https://raw.githubusercontent.com/elon-jang/oikos/master/tax_return/deploy/install.sh | bash
```

#### Windows 사용자

1. `PowerShell`을 관리자 권한으로 실행
2. 아래 명령어를 복사해서 붙여넣고 Enter:

```powershell
irm https://raw.githubusercontent.com/elon-jang/oikos/master/tax_return/deploy/install.ps1 | iex
```

**설치 완료 후:**
- `~/기부금영수증/` 폴더(Mac) 또는 `내 문서\기부금영수증\` 폴더(Windows)가 생성됩니다
- 이 폴더에 헌금 데이터 파일과 영수증 템플릿을 넣어주세요
- Claude Desktop을 재시작하면 사용 준비 완료!

> **Docker Desktop 필요**: 아직 설치 안 하셨다면 [Docker Desktop 다운로드](https://www.docker.com/products/docker-desktop/)에서 먼저 설치해주세요.

---

### 방법 2: Claude Code 사용자

개발자라면 `/receipt` 명령어로 더 빠르게!

```bash
# 플러그인 설치 (한 번만)
/plugin marketplace add elon-jang/claude-plugins
/plugin install oikos@elon-jang

# 사용
/receipt generate        # 전체 발행
/receipt generate 홍길동  # 특정인만
/receipt list            # 대상자 확인
```

---

### 방법 3: Python 직접 실행 (개발자용)

```bash
# 1. 저장소 다운로드
git clone https://github.com/elon-jang/oikos.git
cd oikos/tax_return

# 2. 필요한 패키지 설치
pip install pandas openpyxl docxtpl

# 3. 실행
python generate_receipts.py --list  # 대상자 확인
python generate_receipts.py         # 전체 발행
```

---

## 사용 방법

### Step 1: 데이터 준비

엑셀 파일을 `2025_income_summary.xlsx` 형식으로 만들어주세요:

| 이름 | 1월 | 2월 | 3월 | ... | 12월 | 연간 총합 |
|------|-----|-----|-----|-----|------|----------|
| 강신애 | 50,000 | 50,000 | 30,000 | ... | 50,000 | 450,000 |
| 김철수,박영희 | 100,000 | 100,000 | 100,000 | ... | 100,000 | 1,200,000 |

> **부부 헌금**: 이름을 쉼표로 구분하면 각각 별도 영수증이 발행됩니다!

### Step 2: 영수증 템플릿 준비

`donation_receipt_template.docx` 파일이 필요합니다.
- 기존 영수증 양식이 있다면 `{{name}}`, `{{total}}` 같은 placeholder만 추가
- 자세한 방법: [템플릿_만들기_가이드.md](tax_return/docs/템플릿_만들기_가이드.md)

### Step 3: 영수증 발행

**Claude Desktop에서:**
```
"전체 영수증 발행해줘"
"홍길동 영수증만 발행해줘"
"강신애 영수증 발행했었어?"
```

**터미널에서:**
```bash
python generate_receipts.py              # 전체 발행
python generate_receipts.py -n 홍길동     # 특정인 발행
python generate_receipts.py --history    # 발행 이력 확인
```

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| 자동 발행 | 엑셀 데이터 → Word 영수증 자동 생성 |
| 부부 분리 | "홍길동,김영희" → 각각 영수증 발행 |
| 발행대장 | 발행 이력 자동 기록 및 조회 |
| 연도 자동 감지 | 파일명에서 연도 자동 인식 |
| 재발행 추적 | 같은 사람 재발행 시 자동 기록 |
| 개인정보 보호 | Claude에 이름/금액 정보 노출 안 함 |

---

## 폴더 구조

```
oikos/
├── tax_return/                    # 기부금 영수증 시스템
│   ├── generate_receipts.py       # 메인 스크립트
│   ├── mcp_server/                # MCP 서버 (Claude Desktop용)
│   ├── tests/                     # 테스트 코드
│   ├── deploy/                    # 배포 관련 (Docker, 설치 스크립트)
│   ├── docs/                      # 문서
│   └── README.md                  # 상세 문서
└── examples/                      # 기타 예제
```

---

## 문서

| 문서 | 설명 |
|------|------|
| [시작하기 가이드](tax_return/docs/시작하기_가이드.md) | 처음 사용자를 위한 단계별 안내 |
| [MCP 사용 가이드](tax_return/docs/MCP_사용가이드.md) | Claude Desktop에서 사용하는 방법 |
| [템플릿 만들기 가이드](tax_return/docs/템플릿_만들기_가이드.md) | 영수증 템플릿 작성 방법 |
| [상세 README](tax_return/README.md) | 모든 옵션과 기능 설명 |

---

## 자주 묻는 질문

### Q: 개인정보가 외부로 전송되나요?
**A: 아니요!** 모든 데이터는 로컬 컴퓨터에서만 처리됩니다. Claude에게는 "94명 대상, 총액 4500만원" 같은 요약 정보만 전달되고, 개인 이름이나 금액은 절대 전송되지 않습니다.

### Q: 부부가 함께 헌금하면 어떻게 하나요?
**A:** 엑셀에서 이름을 쉼표로 구분하세요: `홍길동,김영희`
→ 자동으로 각각 별도 영수증이 발행됩니다 (금액은 동일)

### Q: 작년에 발행한 영수증을 다시 발행하고 싶어요
**A:** `python generate_receipts.py -n 홍길동` 으로 재발행하면 발행대장에 "재발행"으로 자동 기록됩니다.

### Q: Mac도 Windows도 아닌데요?
**A:** Linux도 지원합니다! Python만 설치되어 있으면 됩니다.

---

## 기여하기

버그 리포트, 기능 제안, PR 모두 환영합니다!

- Issues: [GitHub Issues](https://github.com/elon-jang/oikos/issues)
- 문의: GitHub Issues에 남겨주세요

---

## 라이선스

MIT License - 자유롭게 사용하세요!

---

**Made with love for church communities**
