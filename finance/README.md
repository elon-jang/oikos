# 헌금 전표 자동화

> 헌금 전표 이미지를 읽어 Excel 업로드 파일을 자동 생성하는 Claude Code 플러그인

## 사용법

Claude Code CLI에서 실행:

```
/process-offering 20260125
```

1. `20260125/` 폴더에 전표 이미지(.jpg) 저장
2. `/process-offering 20260125` 실행
3. 추출된 데이터 확인/수정
4. Excel 자동 생성 (`20260125.xlsx`)

## 주요 기능

- 전표 이미지 OCR 자동 인식 (Claude Vision)
- 교인 명부 기반 이름 자동 교정 (fuzzy matching)
- 19개 카테고리별 Excel 자동 입력
- 카테고리별 합계 검증

## 구조

```
.claude-plugin/
└── plugin.json               # 플러그인 매니페스트
commands/
└── process-offering.md       # /process-offering 슬래시 커맨드
scripts/
├── offering_config.py        # 카테고리 → Excel 행 매핑
├── correct_names.py          # 이름 교정 (difflib fuzzy matching)
├── process_offering.py       # 템플릿 생성 / 데이터 입력 / 검증
└── members.txt               # 교인 명부
```

## 설정

- 교인 명부 업데이트: `scripts/members.txt` (1줄 1명)
- 카테고리 변경: `scripts/offering_config.py`
- 개발 가이드: `CLAUDE.md`

## 향후 계획

- 헌금 데이터 분석 (월별/분기별/연간 리포트)
- 시각화 차트
- 예산 대비 실적 비교
