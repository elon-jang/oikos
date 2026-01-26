# Claude Code Development Guide: Offering (헌금 전표 자동화)

이 문서는 Claude Code가 헌금 전표 자동화 플러그인을 개발하고 유지보수할 때 참고하는 가이드입니다.

## 프로젝트 개요

**목적**: 매주 반복되는 "헌금 전표 이미지 → Excel 입력" 업무를 자동화

**핵심 원칙**:
1. **정확성**: OCR 추출 후 교인 명부 기반 fuzzy matching으로 이름 교정
2. **검증**: 카테고리별 합계 교차 검증으로 입력 오류 방지
3. **사용자 확인**: 자동 추출 결과를 반드시 사용자에게 보여주고 승인 후 Excel 생성

## 아키텍처

### 모듈 구조

```
commands/
└── process-offering.md    # 슬래시 커맨드 (이미지→추출→확인→Excel)

scripts/
├── offering_config.py     # 카테고리 → Excel 행 매핑 설정
├── correct_names.py       # 교인 명부 기반 이름 교정 (difflib)
├── process_offering.py    # 템플릿 생성 / 데이터 입력 / 검증
└── members.txt            # 교인 명부 (1줄 1명)
```

### 데이터 흐름

```
이미지 (YYYYMMDD/*.jpg)
    ↓ Claude Vision (Read 도구)
추출 데이터 (이름, 금액, 카테고리)
    ↓ correct_names.py
교정된 데이터 (fuzzy matching)
    ↓ 사용자 확인 (AskUserQuestion)
확인된 데이터
    ↓ process_offering.py write
YYYYMMDD.xlsx (Excel 출력)
    ↓ process_offering.py verify
검증 결과
```

## 핵심 설계 결정

### 1. 이름 교정 (fuzzy matching)

**구현**: `correct_names.py` — `difflib.get_close_matches(cutoff=0.5)`

**한계**: 한글 필기체 OCR 특성상 자음/모음 단위 오인식 발생
- `천인성↔권언성` (ratio=0.33) — cutoff 이하로 자동 매칭 불가, `unknown` 처리
- `윤선섭↔윤순심` (ratio=0.33) — 마찬가지

**대응**: `unknown` 표시 → 사용자 수동 확인 → 신규 교인이면 명부에 추가

### 2. Excel 템플릿 구조 (고정)

**파일**: `2026헌금_업로드샘플.xlsx` (92행, A-H열)
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

### 3. 이미지 유형별 처리

**통계표** (1.jpg, 3.jpg, 10.jpg, 11.jpg):
- 표 형태 → 여러 건의 (이름, 금액) 추출
- 합계 행으로 교차 검증

**전표** (2.jpg, 4-9.jpg):
- 단일 전표 → 총액 + 내역 추출
- 부서명만 있으면 이름=부서명

**특별헌금** (번호 없는 파일명):
- 사용자에게 입력 여부 질문

## CLI 사용법

```bash
# 템플릿 생성
python3 scripts/process_offering.py create 20260125

# 데이터 입력 (JSON via stdin)
echo '{"십일조": [{"name": "최정호", "amount": 578000}]}' | \
  python3 scripts/process_offering.py write 20260125

# 검증
python3 scripts/process_offering.py verify 20260125

# 이름 교정 (JSON via stdin)
echo '{"names": ["천인성", "정완구"]}' | python3 scripts/correct_names.py

# 교인 명부에 추가
python3 scripts/correct_names.py --add "새교인이름"
```

## 카테고리 변경 시

1. `scripts/offering_config.py`의 `CATEGORIES` 수정
2. 필요 시 `CATEGORY_ALIASES` 업데이트
3. 템플릿 xlsx의 행 구조가 변경된 경우 새 템플릿 파일 교체
