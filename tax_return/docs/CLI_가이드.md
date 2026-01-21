# CLI 가이드 (Python 직접 실행)

터미널에서 Python 스크립트로 영수증을 생성하는 방법입니다.
개발자나 자동화가 필요한 분께 추천합니다.

---

## 설치

### 필수 패키지

```bash
pip install pandas openpyxl docxtpl
```

### 선택 패키지

```bash
# 설정 파일 사용 시
pip install pyyaml

# PDF 변환 기능 사용 시
pip install docx2pdf  # Microsoft Word 필요
# 또는
brew install libreoffice  # macOS
```

### 프로젝트 다운로드

```bash
git clone https://github.com/elon-jang/oikos.git
cd oikos/tax_return
```

---

## 빠른 시작

```bash
# 샘플 데이터로 대상자 목록 확인
python generate_receipts.py --list --data sample_income_summary.xlsx

# 한 명 발행 테스트
python generate_receipts.py -n 홍길동 --data sample_income_summary.xlsx
```

---

## 실제 사용 준비

### 1. 템플릿 준비

[템플릿 만들기 가이드](템플릿_만들기_가이드.md)를 참고하여 `donation_receipt_template.docx` 파일을 준비하세요.

### 2. 데이터 준비

Excel 파일에 헌금 데이터를 입력합니다. 파일명은 `YYYY_income_summary.xlsx` 형식으로 저장하세요.

| 이름 | 1월 | 2월 | ... | 12월 | 연간 총합 |
|------|-----|-----|-----|------|----------|
| 강신애 | 50,000 | 30,000 | ... | 20,000 | 350,000 |
| 홍길동,김영희 | 100,000 | 100,000 | ... | 100,000 | 1,200,000 |

**포인트:**
- **부부 이름**: 쉼표로 구분하면 각각 별도 영수증 발행 (금액은 동일)
- **합계 행**: 자동으로 제외됩니다

### 3. 설정 파일 (선택)

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

## 명령어 옵션

### 기본 사용법

```bash
# 전체 발행 (자동 연도 감지)
python generate_receipts.py

# 대상자 목록 확인
python generate_receipts.py --list

# 한 사람만 발행
python generate_receipts.py -n 홍길동

# 여러 명 발행 (쉼표 구분)
python generate_receipts.py -n 홍길동,김철수,이영희
```

### 연도 및 파일 지정

```bash
# 연도 수동 지정
python generate_receipts.py --year 2025

# 다른 데이터 파일 사용
python generate_receipts.py --data 2024_income_summary.xlsx

# 다른 템플릿 사용
python generate_receipts.py --template my_template.docx
```

### 발행 이력

```bash
# 발행 이력 조회
python generate_receipts.py --history

# 특정인 발행 이력 조회
python generate_receipts.py --history -n 강신애
```

### PDF 변환

```bash
# PDF로 변환 (DOCX도 유지)
python generate_receipts.py --pdf
```

---

## 옵션 정리

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

## 출력 파일

### 영수증 파일

```
receipts/
├── 기부금영수증_강신애.docx
├── 기부금영수증_홍길동.docx
└── ...
```

### 발행대장

영수증 발행 시 자동으로 `발행대장_YYYY.xlsx` 파일에 기록됩니다.

| 컬럼 | 설명 | 예시 |
|------|------|------|
| 발급번호 | 영수증 번호 | 26-001 |
| 이름 | 기부자명 | 강신애 |
| 연간총합 | 헌금 총액 | 450,000 |
| 발행일시 | 발행 시간 | 2026-01-20 18:30:00 |
| 파일경로 | 생성된 파일 | receipts/기부금영수증_강신애.docx |
| 비고 | 재발행 등 | 재발행 |

---

## 발급번호 규칙

### 형식

`YY-NNN` (예: `26-001`)

- 2025년 데이터 → `26-XXX` (발급 연도 = 데이터 연도 + 1)

### 번호 부여 방식

**이름 가나다순 정렬 후 순차 부여** (발행 순서 아님)

```
26-001  강신애    ← 가나다순 1번째
26-002  강OO
...
26-076  장의진    ← 가나다순 76번째
...
26-094  홍OO      ← 가나다순 94번째
```

### 이 방식의 장점

| 장점 | 설명 |
|------|------|
| 번호 일관성 | 같은 사람은 항상 같은 번호 |
| 재발행 용이 | 동일 번호로 재발행, 대장에 "재발행" 기록 |
| 분할 발행 가능 | 오늘 일부, 내일 나머지 발행해도 번호 유지 |
| 추적 용이 | 이름만 알면 번호 예측 가능 |

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

## 더 알아보기

| 문서 | 설명 |
|------|------|
| [README.md](../README.md) | 프로젝트 개요 |
| [템플릿 만들기](템플릿_만들기_가이드.md) | 영수증 템플릿 작성법 |
| [MCP 사용 가이드](MCP_사용가이드.md) | Claude Desktop 사용법 |
