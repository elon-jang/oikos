# Claude Code Development Guide: Offering (헌금 전표 자동화)

이 문서는 Claude Code가 헌금 전표 자동화 플러그인을 개발하고 유지보수할 때 참고하는 가이드입니다.

## 프로젝트 개요

**목적**: 매주 반복되는 "헌금 전표 이미지/PDF → Excel 입력" 업무를 자동화

**핵심 원칙**:
1. **정확성**: OCR 추출 후 교인 명부 기반 fuzzy matching으로 이름 교정
2. **검증**: 카테고리별 합계 교차 검증으로 입력 오류 방지
3. **사용자 확인**: 자동 추출 결과를 반드시 사용자에게 보여주고 승인 후 Excel 생성

## 아키텍처

### 폴더 구조

```
finance/
├── templates/
│   └── upload_sample.xlsx        # Excel 업로드 템플릿
├── data/                         # .gitignore 대상
│   └── 2026/
│       └── 0125/
│           ├── input/
│           │   ├── scan.pdf      # 스캔 PDF
│           │   └── *.jpg         # 전표 이미지
│           └── 20260125.xlsx     # 출력 Excel
├── commands/
│   └── process-offering.md       # 슬래시 커맨드 (이미지/PDF→추출→확인→Excel)
├── scripts/
│   ├── offering_config.py        # 카테고리 → Excel 행 매핑 설정
│   ├── correct_names.py          # 교인 명부 기반 이름 교정 (자모 분해 fuzzy matching)
│   ├── process_offering.py       # 템플릿 생성 / 데이터 입력 / 검증
│   └── members.txt               # 교인 명부 (1줄 1명)
├── CLAUDE.md
├── README.md
└── .gitignore
```

### 데이터 흐름

```
입력 (data/YYYY/MMDD/input/ — PDF 또는 JPG)
    ↓ Claude Vision (Read 도구)
추출 데이터 (이름, 금액, 카테고리)
    ↓ correct_names.py
교정된 데이터 (fuzzy matching)
    ↓ 사용자 확인 (AskUserQuestion)
확인된 데이터
    ↓ process_offering.py write
data/YYYY/MMDD/YYYYMMDD.xlsx (Excel 출력)
    ↓ process_offering.py verify
검증 결과
```

## 핵심 설계 결정

### 1. 이름 교정 (자모 분해 fuzzy matching)

**구현**: `correct_names.py` — 한글 자모(초성/중성/종성) 분해 후 `difflib.SequenceMatcher`

**원리**: 한글 글자를 자모로 분해하여 비교 → 획이 유사한 글자 간 유사도 향상
- 문자 단위: `정형호↔정형모` = 0.67, `정형호↔최정호` = 0.67 (구분 불가)
- 자모 단위: `정형호↔정형모` = 0.88, `정형호↔최정호` = 0.67 (정확히 구분)

**교정 성공**: `천인성→권언성`, `정형호→정형모`, `이주리→이루리`, `최건웅→최진웅` 등

**한계**: 3음절 이상 오인식 시 교정 불가 (`윤선섭↔윤순심` — 순→선, 심→섭 동시 오인식)

**대응**: `corrected`/`unknown` 표시 → 사용자 수동 확인 → 신규 교인이면 명부에 추가

### 2. Excel 템플릿 구조 (고정)

**파일**: `templates/upload_sample.xlsx` (92행, A-H열)
- Row 1-3: 헤더
- Row 4-95: 카테고리별 고정 슬롯 (offering_config.py에 매핑)
- Column A: 일자 (datetime, mm-dd-yy)
- Column B: 예배코드 (항상 1)
- Column C: 계좌코드 (항상 0)
- Column D: 계정코드 (카테고리별 고정)
- Column E: 이름
- Column F: 생년월일 (placeholder 2026-01-01)
- Column G: 금액 (accounting format)
- Column H: 적요 (카테고리명)

**주의**: 템플릿의 행 구조(카테고리 순서, 슬롯 수)는 교회 회계 시스템에 맞춰 고정.
변경 시 `offering_config.py`의 `CATEGORIES` 딕셔너리도 함께 수정 필요.

### 3. 입력 유형별 처리

**PDF 모드**: `data/YYYY/MMDD/input/scan.pdf`
- Read 도구로 전체 페이지 일괄 읽기
- 내용 기반 페이지 자동 분류

**이미지 모드**: `data/YYYY/MMDD/input/*.jpg`
- 각 이미지를 개별 Read
- 내용 기반 유형 자동 분류

**페이지 유형 자동 분류 (내용 기반)**:
- 통계표: 표 형태 → 여러 건의 (이름, 금액) 추출, 합계 교차 검증
- 전표: 단일 전표 → 총액 + 내역 추출, 부서명만 있으면 이름=부서명
- 중복: 이전 페이지와 동일 내용 → 건너뛰기
- 특별헌금: "송구영신", "헌신예배" 등 → 사용자에게 포함 여부 질문

## CLI 사용법

```bash
# 템플릿 생성 (MMDD 단축 지원)
python3 scripts/process_offering.py create 0125

# 데이터 입력 (JSON via stdin)
echo '{"십일조": [{"name": "최정호", "amount": 578000}]}' | \
  python3 scripts/process_offering.py write 0125

# 검증
python3 scripts/process_offering.py verify 0125

# YYYYMMDD 형식도 사용 가능
python3 scripts/process_offering.py create 20260125

# 이름 교정 (JSON via stdin)
echo '{"names": ["천인성", "정완구"]}' | python3 scripts/correct_names.py

# 교인 명부에 추가
python3 scripts/correct_names.py --add "새교인이름"
```

## 카테고리 변경 시

1. `scripts/offering_config.py`의 `CATEGORIES` 수정
2. 필요 시 `CATEGORY_ALIASES` 업데이트
3. 템플릿 xlsx의 행 구조가 변경된 경우 새 템플릿 파일 교체

## 개선 계획

- **Phase 1** ✅: 폴더 구조 정리, PDF 지원, MMDD 단축
- **Phase 2** ✅: 중복 감지, 특별헌금 플래그, 카테고리 매핑 개선
- **Phase 3**: Google Drive API (`scripts/gdrive.py` — pull/push)
