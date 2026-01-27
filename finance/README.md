# 헌금 전표 자동화

> 헌금 전표 이미지/PDF를 읽어 Excel 업로드 파일을 자동 생성하는 Claude Code 플러그인

## 사용법

Claude Code CLI에서 실행:

```
/process-offering 0125
```

1. `data/2026/0125/input/` 폴더에 전표 PDF 또는 이미지(.jpg) 저장
2. `/process-offering 0125` 실행 (MMDD 또는 YYYYMMDD)
3. 추출된 데이터 확인/수정
4. Excel 자동 생성 (`data/2026/0125/20260125.xlsx`)

## 주요 기능

- 전표 이미지/PDF OCR 자동 인식 (Claude Vision)
- 교인 명부 기반 이름 자동 교정 (fuzzy matching)
- 내용 기반 페이지 자동 분류 (통계표/전표/특별헌금)
- 19개 카테고리별 Excel 자동 입력
- 카테고리별 합계 검증
- 동일 카테고리 내 중복 항목 감지 (이름+금액)
- 특별헌금 키워드 자동 감지 (송구영신, 헌신예배 등)
- 카테고리 별칭 매핑 (공백/변형 자동 해석)

## 구조

```
templates/
└── upload_sample.xlsx           # Excel 업로드 템플릿
data/                            # .gitignore (입력/출력 데이터)
└── 2026/
    └── 0125/
        ├── input/               # 전표 PDF/이미지
        │   ├── scan.pdf
        │   └── *.jpg
        └── 20260125.xlsx        # 출력 Excel
commands/
└── process-offering.md          # /process-offering 슬래시 커맨드
scripts/
├── offering_config.py           # 카테고리 → Excel 행 매핑
├── correct_names.py             # 이름 교정 (difflib fuzzy matching)
├── process_offering.py          # 템플릿 생성 / 데이터 입력 / 검증
└── members.txt                  # 교인 명부
```

## 설정

- 교인 명부 업데이트: `scripts/members.txt` (1줄 1명)
- 카테고리 변경: `scripts/offering_config.py`
- 개발 가이드: `CLAUDE.md`

## 향후 계획

- Phase 2 ✅: 중복 감지, 특별헌금 플래그, 카테고리 매핑 개선
- Phase 3: Google Drive API 연동 (pull/push)
