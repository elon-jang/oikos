# 기부금 영수증 자동 발행 시스템

교회, 비영리단체 등에서 사용할 수 있는 기부금 영수증 자동 발행 시스템입니다.

## Claude Code 명령어

`/receipt` 명령어로 간편하게 사용할 수 있습니다.

### 플러그인 설치

```bash
# 1. 마켓플레이스 추가
/plugin marketplace add elon-jang/claude-plugins

# 2. 플러그인 설치
/plugin install oikos@elon-jang
```

> 플러그인 설치 방법: [claude-plugins README](https://github.com/elon-jang/claude-plugins/blob/master/README.md)

### 명령어 사용법

```bash
/receipt generate        # 전체 발행
/receipt generate 홍길동  # 특정인 발행
/receipt list            # 대상자 목록
/receipt history         # 발행 이력
/receipt history 강신애   # 특정인 이력
```

## 빠른 시작

### 1. 샘플로 테스트하기

```bash
# 샘플 데이터로 테스트
python generate_receipts.py --list --data sample_income_summary.xlsx
python generate_receipts.py -n 홍길동 --data sample_income_summary.xlsx
```

### 2. 실제 사용 준비

1. **템플릿 준비**: `템플릿_만들기_가이드.md` 참고하여 Word 템플릿 작성
2. **데이터 준비**: Excel 파일에 헌금 데이터 입력 (`YYYY_income_summary.xlsx`)
3. **설정 (선택)**: `config.sample.yaml` → `config.yaml` 복사 후 수정

```bash
# 설정 파일 복사
cp config.sample.yaml config.yaml

# 영수증 생성
python generate_receipts.py
```

## 파일 구조

```
tax_return/
├── generate_receipts.py          # 영수증 생성 스크립트
├── donation_receipt_template.docx # 영수증 템플릿 (직접 작성)
├── sample_income_summary.xlsx    # 샘플 헌금 데이터
├── config.sample.yaml            # 설정 파일 샘플
├── 템플릿_만들기_가이드.md         # 템플릿 작성 가이드
├── receipts/                     # 생성된 영수증 폴더
└── README.md                     # 이 문서
```

## 설치

```bash
pip install pandas openpyxl docxtpl

# 설정 파일 사용 시 (선택)
pip install pyyaml

# PDF 변환 기능 사용 시 (선택)
pip install docx2pdf  # Word 설치 필요
# 또는
brew install libreoffice  # macOS
```

## 사용법

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

# 발행 이력 조회
python generate_receipts.py --history

# 특정인 발행 이력 조회
python generate_receipts.py --history -n 강신애

# PDF로 변환 (DOCX도 유지)
python generate_receipts.py --pdf
python generate_receipts.py -n 홍길동 --pdf
```

### 옵션

| 옵션               | 설명             | 예시                            |
| ------------------ | ---------------- | ------------------------------- |
| (없음)             | 전체 발행 (자동 연도) | `python generate_receipts.py` |
| `-n 이름`        | 지정 인원만 발행 | `-n 홍길동`                   |
| `-n 이름1,이름2` | 여러 명 발행     | `-n 홍길동,김철수`            |
| `--list`         | 대상자 목록 출력 | `--list`                      |
| `--year 연도`    | 데이터 연도 수동 지정 | `--year 2025`               |
| `--data 파일`    | 데이터 파일 직접 지정 | `--data 2024_income_summary.xlsx` |
| `--history`      | 발행 이력 조회   | `--history`                   |
| `--history -n 이름` | 특정인 이력 조회 | `--history -n 강신애`         |
| `--pdf`          | PDF로 변환 (DOCX 유지) | `--pdf`                  |

## 입력 데이터

### 헌금 데이터 (`YYYY_income_summary.xlsx`)

| 이름          | 1월    | 2월    | ... | 12월   | 연간 총합 |
| ------------- | ------ | ------ | --- | ------ | --------- |
| 강신애,최정호 | 50,000 | 30,000 | ... | 20,000 | 350,000   |

- **부부 이름**: 쉼표로 구분 → 각각 별도 영수증 발행 (동일 금액)
- **합계 행**: 자동 제외

## 템플릿

### 템플릿 파일

`donation_receipt_template.docx` - Word 문서 템플릿

### Placeholder 목록

| Placeholder        | 위치           | 설명              | 예시    |
| ------------------ | -------------- | ----------------- | ------- |
| `{{receipt_no}}` | Table 1        | 발급번호          | 26-001  |
| `{{name}}`       | Table 2, 문단  | 기부자 성명 (2곳) | 홍길동  |
| `{{month_1}}`    | Table 4 Row 1  | 1월 금액          | 50,000  |
| `{{month_2}}`    | Table 4 Row 2  | 2월 금액          | 50,000  |
| ...                | ...            | ...               | ...     |
| `{{month_12}}`   | Table 4 Row 12 | 12월 금액         | 50,000  |
| `{{total}}`      | Table 4 Row 13 | 연간 총합         | 450,000 |

### 주의사항

- **A4 한 장 유지**: 여백, 폰트 크기 조절 시 주의
- **셀 병합**: 변경 시 레이아웃 깨질 수 있음
- **{{name}} 2곳**: Table 2와 하단 서명란에 각각 있음
- **연도 변경**: Table 4의 "2026년 1월" 및 하단 날짜 수정 필요

## 출력

- **형식**: DOCX (Word 문서), PDF (--pdf 옵션 사용 시)
- **파일명**: `기부금영수증_이름.docx` (또는 `.pdf`)
- **위치**: `receipts/` 폴더

## 주민등록번호/주소 처리

**빈칸으로 유지** - 수령인이 연말정산 시 직접 기입

## 연간 작업 순서

1. **원본 데이터 정리** (`헌금정리_프롬프트.md` 참고)

   - 이름 통합 (오타, 구분자)
   - 비개인 항목 제외 (셀, 무명 등)
   - 총액 검증
2. **영수증 생성**

   ```bash
   python generate_receipts.py
   ```
3. **검증**

   - 샘플 파일 열어서 확인
   - 총 인원수 확인 (부부 분리 반영)
4. **배포**

   - DOCX 파일 인쇄 또는 이메일 발송

## 설정 파일 (config.yaml)

설정 파일로 단체 정보와 파일 경로를 커스터마이징할 수 있습니다.

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

> 설정 파일이 없으면 기본값을 사용합니다.
> YAML 파싱을 위해 `pip install pyyaml` 필요

## 발급번호 규칙

- 형식: `[접두사]YY-NNN`
- 예: `26-001` (2026년 첫 번째 영수증)
- 접두사 설정 시: `A26-001`
- 이름 가나다순 정렬 후 순차 부여
- 연도는 데이터 파일 연도 + 1 (예: 2025 데이터 → 26-XXX)

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

### 이력 조회

```bash
python generate_receipts.py --history           # 전체 이력
python generate_receipts.py --history -n 강신애  # 특정인 이력
```

## 템플릿 수정 시 주의사항

1. Placeholder는 `{{변수명}}` 형식 유지
2. A4 한 장에 맞게 여백/폰트 조절
3. 수정 후 테스트 실행 필수

## 문제 해결

### 오류: 템플릿 파일이 없습니다

- `donation_receipt_template.docx` 파일이 프로젝트 폴더에 있는지 확인

### 오류: 데이터 파일을 찾을 수 없습니다

- `YYYY_income_summary.xlsx` 형식의 파일이 필요
- 또는 `--data 파일경로` 옵션으로 직접 지정

### 오류: 필수 컬럼이 없습니다

- Excel 파일에 필수 컬럼 확인: `이름`, `1월`~`12월`, `연간 총합`

### 오류: `TemplateSyntaxError`

- 템플릿의 placeholder 문법 확인 (`}}` 누락 등)

### 금액이 표시되지 않음

- Excel 데이터의 컬럼명 확인 (`1월`, `2월` 등)

### 부부가 분리되지 않음

- 이름에 쉼표(`,`) 사용 확인 (마침표 아님)

### PDF 변환 실패

- `docx2pdf` 설치: `pip install docx2pdf` (Microsoft Word 필요)
- 또는 LibreOffice 설치: `brew install libreoffice` (macOS)
