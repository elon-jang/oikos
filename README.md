# Oikos

Claude Code 활용 예제 모음입니다.

## 예제 목록

### 1. 엑셀/문서 자동화 (`examples/excel_doc_automation`)

| 폴더 | 설명 |
|------|------|
| 1. 데이터 피봇-필터링 | 엑셀 데이터 피봇 및 필터링 |
| 2. 데이터 취합 | 여러 엑셀 파일 데이터 취합 |
| 3. 문서 자동화 | 엑셀 데이터로 Word 문서 자동 생성 |
| 4. 웹 크롤링 | 웹사이트 데이터 수집 |

### 2. 기부금 영수증 시스템 (`examples/tax_return`)

교회 기부금 영수증 자동 발행 시스템

**주요 기능**:
- 엑셀 데이터 → Word 영수증 자동 생성
- 연도 자동 감지 및 발급번호 부여
- 발행 이력 관리 (발행대장)
- 부부 이름 자동 분리 발행

**사용법**:
```bash
cd examples/tax_return
pip install pandas openpyxl docxtpl

# 전체 발행
python generate_receipts.py

# 특정인 발행
python generate_receipts.py -n 홍길동

# 발행 이력 조회
python generate_receipts.py --history
```

자세한 내용은 [examples/tax_return/README.md](examples/tax_return/README.md) 참고

## 환경

- Python 3.8+
- Claude Code

## 라이선스

MIT License
