# 헌금 전표 자동화

> 헌금 전표 이미지/PDF를 읽어 Excel 업로드 파일을 자동 생성하는 Claude Code 플러그인

## 시작하기

### 1. 사전 요구사항

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) 설치 및 로그인
- Python 3.10+
- Google Drive OAuth 인증 파일 (Drive 연동 사용 시)

### 2. 의존성 설치

```bash
pip3 install openpyxl                    # Excel 처리
pip3 install google-auth-oauthlib google-api-python-client   # Drive 연동
```

### 3. Google Drive 설정 (최초 1회)

Drive 연동을 사용하려면 OAuth Desktop 타입의 인증 파일이 필요합니다.

```bash
# 인증 파일 위치 확인 (기본 경로)
ls ~/elon/credentials/gdrive-credentials.json
```

인증 파일이 준비되면, 최초 실행 시 브라우저가 열리며 Google 계정 인증을 요청합니다.
인증 후 토큰이 자동 저장되어 이후에는 자동 로그인됩니다.

```bash
# 연결 테스트 — 브라우저 인증 후 Drive 폴더 목록 출력
python3 scripts/gdrive.py list
```

**경로 변경이 필요하면** 환경 변수로 오버라이드:

```bash
export GDRIVE_CREDENTIALS_PATH="/my/path/credentials.json"
export GDRIVE_TOKEN_PATH="/my/path/token.json"
export GDRIVE_FOLDER_ID="구글드라이브폴더ID"
```

## 매주 사용법

### 방법 A: 슬래시 커맨드 (권장)

Claude Code에서 한 줄로 전체 과정을 자동 수행합니다.

```
/process-offering 0125
```

자동으로 아래 과정이 진행됩니다:

```
Drive에서 스캔 파일 다운로드 (input 폴더가 비어있을 때)
  ↓
전표/통계표 OCR 추출 (PDF 또는 JPG)
  ↓
교인 명부 기반 이름 자동 교정
  ↓
카테고리별 데이터 정리 → 사용자 확인
  ↓
Excel 생성 및 합계 검증
  ↓
완성된 Excel을 Drive에 업로드
```

**사용자가 직접 하는 것**: 추출 결과 확인 + 이름/금액 수정 승인뿐입니다.

### 방법 B: 수동 단계별 실행

원하는 단계만 개별 실행할 수 있습니다.

```bash
# 1. Drive에서 스캔 파일 가져오기
python3 scripts/gdrive.py pull 0125
#    → data/2026/0125/input/scan.pdf 다운로드됨

# 2. Claude Code에서 /process-offering 0125 실행
#    (또는 아래처럼 스크립트를 직접 호출)

# 3. Excel 템플릿 생성
python3 scripts/process_offering.py create 0125
#    → data/2026/0125/20260125.xlsx 생성됨

# 4. 데이터 입력 (JSON)
echo '{
  "십일조": [
    {"name": "최정호", "amount": 578000},
    {"name": "박경애", "amount": 580000}
  ],
  "감사": [
    {"name": "정평화", "amount": 50000}
  ]
}' | python3 scripts/process_offering.py write 0125

# 5. 검증 — 카테고리별 합계 출력
python3 scripts/process_offering.py verify 0125

# 6. Drive에 업로드
python3 scripts/gdrive.py push 0125
#    → 20260125.xlsx가 Drive에 업로드됨
```

### 실제 작업 예시 (2026.1.25)

```
$ claude
> /process-offering 0125

[0단계] input 폴더 비어있음 → Drive에서 다운로드? → "예"
        scan.pdf 다운로드 완료 (5.7MB)

[1단계] PDF 16페이지 읽기

[2단계] 페이지 분류
        - p2: 십일조 통계표 (18건)
        - p3: 감사 통계표 (9건)
        - p4: 장년부주일 전표 (₩242,000)
        - p16: 헌신예배 전표 → 특별헌금 감지!
        - p11, p13: 중복 → 건너뜀

[3단계] 이름 교정 — 천인성→권언성 ✓, 최건웅→최진웅 ✓

[4단계] 결과 표시
        ### 십일조 (18건, 합계: 5,338,000원)
        | # | 이름          | 금액    | 비고              |
        |---|---------------|---------|-------------------|
        | 1 | 최정호        | 578,000 |                   |
        | 2 | 박경애        | 580,000 |                   |
        | 3 | 권언성,하공남  | 450,000 | 천인성→권언성 ✓    |
        ...

        → "확인 완료" 또는 "수정 필요" 선택

[5단계] Excel 생성 — 59건 입력 완료

[6단계] 검증 통과 — 전체 합계 7,494,000원 ✓

[7단계] Drive에 업로드? → "예"
        20260125.xlsx → Drive 0125/ 폴더 업로드 완료
```

## Google Drive 명령어

```bash
# 폴더 목록 조회
python3 scripts/gdrive.py list
# 출력 예:
#   이름                              크기        수정일
#   -----------------------------------------------------------------
#   [DIR] 0125                        -           2026-01-27
#   20260118.xlsx                     17.5KB      2026-01-25
#   Scan Jan 25, 2026 at 12.21.pdf   5.7MB       2026-01-27

# 입력 파일 다운로드 (PDF/JPG만)
python3 scripts/gdrive.py pull 0125
# → Drive의 0125/ 폴더에서 → data/2026/0125/input/으로 다운로드
# → 0125 폴더가 없으면 파일명에 "0125" 포함된 파일 검색

# 출력 Excel 업로드
python3 scripts/gdrive.py push 0125
# → data/2026/0125/20260125.xlsx → Drive에 업로드
# → Drive에 동일 파일명이 있으면 덮어쓰기
```

**Drive 폴더 구조 권장:**

```
헌금전표폴더/              ← GDRIVE_FOLDER_ID
├── 0118/                  ← MMDD 폴더
│   └── scan.pdf
├── 0125/
│   ├── scan.pdf           ← pull 대상
│   └── 20260125.xlsx      ← push 결과
└── ...
```

## 교인 명부 관리

```bash
# 이름 교정 테스트
echo '{"names": ["천인성", "정형호"]}' | python3 scripts/correct_names.py
# 출력: 천인성→권언성 (corrected), 정형호→정형모 (corrected)

# 신규 교인 추가
python3 scripts/correct_names.py --add "새교인이름"

# 명부 직접 편집
# scripts/members.txt — 1줄에 이름 1개
```

## 주요 기능

- 전표 이미지/PDF OCR 자동 인식 (Claude Vision)
- 교인 명부 기반 이름 자동 교정 (한글 자모 분해 fuzzy matching)
- 내용 기반 페이지 자동 분류 (통계표/전표/특별헌금)
- 19개 카테고리별 Excel 자동 입력
- 카테고리별 합계 검증
- 동일 카테고리 내 중복 항목 감지 (이름+금액)
- 특별헌금 키워드 자동 감지 (송구영신, 헌신예배 등)
- 카테고리 별칭 매핑 (공백/변형 자동 해석)
- Google Drive 연동 (파일 다운로드/업로드/목록 조회)

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
├── correct_names.py             # 이름 교정 (한글 자모 분해 fuzzy matching)
├── process_offering.py          # 템플릿 생성 / 데이터 입력 / 검증
├── gdrive_config.py             # Google Drive API 설정
├── gdrive.py                    # Google Drive 연동 (pull/push/list)
└── members.txt                  # 교인 명부
```

## 설정 변경

- **교인 명부**: `scripts/members.txt` (1줄 1명)
- **카테고리 변경**: `scripts/offering_config.py` → `CATEGORIES` / `CATEGORY_ALIASES`
- **Drive 폴더 변경**: `scripts/gdrive_config.py` 또는 환경 변수
- **개발 가이드**: `CLAUDE.md`

## 완료된 개선

- Phase 1 ✅: 폴더 구조 정리, PDF 지원, MMDD 단축
- Phase 2 ✅: 중복 감지, 특별헌금 플래그, 카테고리 매핑 개선
- Phase 3 ✅: Google Drive API 연동 (pull/push/list)
- Phase 4 ✅: Drive 폴더 자동 생성, Excel write 백업, API 에러 핸들링, 테스트 스위트
- Phase 5 ✅: 입력 검증, 설정 일관성 검증, 파일 I/O 방어, 에러 경로 테스트
- Phase 6 ✅: 테스트 setUp 리팩터링, dry-run, 월간 요약, rollback (73개 테스트)
- Phase 7 ✅: LLM 판단 정확도 향상 — 의사결정 트리, OCR Warning 체계화, 변환 예시, 카테고리 우선순위, 역할 분담표
- Phase 8 ✅: 문서 역할 정리 — CLAUDE.md(설계)/process-offering.md(실행) 분리, 중복 제거, 운영 안정성(재실행/신뢰도 기준)
