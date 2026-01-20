# 기부금 영수증 명령어

기부금 영수증 발행 시스템을 간편하게 사용하는 명령어입니다.

## 사용법

```
/receipt [작업] [옵션]
```

## 작업

| 작업 | 설명 | 예시 |
|------|------|------|
| `generate` | 영수증 생성 (기본값) | `/receipt generate` |
| `list` | 대상자 목록 조회 | `/receipt list` |
| `history` | 발행 이력 조회 | `/receipt history` |

## 예시

```bash
# 전체 영수증 발행
/receipt generate

# 특정인 영수증 발행
/receipt generate 홍길동

# 여러 명 발행
/receipt generate 홍길동,김철수

# 대상자 목록 확인
/receipt list

# 발행 이력 조회
/receipt history

# 특정인 이력 조회
/receipt history 강신애

# 템플릿 지정
/receipt generate --template my_template.docx

# 데이터 파일 지정
/receipt list --data sample_income_summary.xlsx

# 템플릿과 데이터 모두 지정
/receipt generate 홍길동 --template my_template.docx --data 2024_income_summary.xlsx
```

---

## 실행 지침

$ARGUMENTS를 파싱하여 아래 규칙에 따라 명령어를 실행하세요.

### 1. 작업 파싱

```
$ARGUMENTS 형식: [작업] [이름]
- 작업: generate, list, history (없으면 generate)
- 이름: 선택적 (쉼표로 여러 명 가능)
```

### 2. 명령어 매핑

| 입력 | 실행 명령어 |
|------|-------------|
| `/receipt` | `python generate_receipts.py` |
| `/receipt generate` | `python generate_receipts.py` |
| `/receipt generate 홍길동` | `python generate_receipts.py -n 홍길동` |
| `/receipt generate 홍길동,김철수` | `python generate_receipts.py -n 홍길동,김철수` |
| `/receipt list` | `python generate_receipts.py --list` |
| `/receipt history` | `python generate_receipts.py --history` |
| `/receipt history 홍길동` | `python generate_receipts.py --history -n 홍길동` |

### 3. 실행 위치

반드시 `examples/tax_return` 폴더에서 실행해야 합니다.

```bash
cd /Users/elon/elon/ai/projects/church/oikos/examples/tax_return
python generate_receipts.py [옵션]
```

### 4. 결과 보고

실행 후 다음 정보를 사용자에게 보고하세요:
- 생성된 영수증 개수
- 발행대장 파일 위치
- 오류가 있으면 원인과 해결 방법

### 5. 추가 옵션

사용자가 옵션을 지정하면 해당 옵션을 명령어에 추가하세요:

| 옵션 | 설명 | 예시 |
|------|------|------|
| `--template 파일` | 템플릿 파일 지정 | `--template my_template.docx` |
| `--data 파일` | 데이터 파일 지정 | `--data sample_income_summary.xlsx` |
| `--year 연도` | 연도 지정 | `--year 2024` |
| `--pdf` | PDF 변환 | `--pdf` |

**명령어 조합 예시:**

| 입력 | 실행 명령어 |
|------|-------------|
| `/receipt list --data sample.xlsx` | `python generate_receipts.py --list --data sample.xlsx` |
| `/receipt generate --template t.docx` | `python generate_receipts.py --template t.docx` |
| `/receipt generate 홍길동 --template t.docx --data d.xlsx` | `python generate_receipts.py -n 홍길동 --template t.docx --data d.xlsx` |
| `/receipt generate --pdf` | `python generate_receipts.py --pdf` |
