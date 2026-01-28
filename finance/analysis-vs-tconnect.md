# Finance 프로젝트 분석 (T-Connect Skill 프레임워크 기준)

> 헌금 전표 자동화 프로젝트를 AIP Skill(T-Connect) 관점에서 분석한 결과

---

## 1. 구조 비교

```
T-Connect (AIP Skill)              Finance (Claude Code Plugin)
─────────────────────              ────────────────────────────
SKILL.md  ← LLM 업무 매뉴얼        CLAUDE.md  ← 개발 가이드
preset-prompt.md ← 플랫폼 지시문    (없음)
config/keywords.yaml ← 외부 설정    (없음 — offering_config.py에 내장)
references/schemas.md ← 스키마      (없음 — CLAUDE.md에 인라인)
scripts/convert.py                  scripts/process_offering.py
scripts/extract.py                  scripts/correct_names.py
scripts/generate.py                 scripts/gdrive.py + gdrive_config.py
templates/template.xlsx             templates/upload_sample.xlsx
(없음)                              commands/process-offering.md ← 슬래시 커맨드
(없음)                              tests/ ← 테스트 (73개)
(없음)                              .claude-plugin/plugin.json
```

---

## 2. 파이프라인 비교

### T-Connect

```
Excel → Markdown → raw_data.json → [LLM 판단] → final_data.json → Excel
[convert.py]  [extract.py]                        [generate.py]
```

### Finance

```
Drive pull → OCR 추출 → 이름 교정 → 사용자 확인 → Excel 생성 → 검증 → Drive push
[gdrive.py]   [LLM]   [correct_names.py] [LLM]  [process_offering.py]  [gdrive.py]
```

공통 패턴: **스크립트-LLM-스크립트 샌드위치**. 기계적 처리는 스크립트, 맥락 판단은 LLM.

---

## 3. 잘 된 부분 (T-Connect 패턴과 일치)

### 3.1 스크립트 vs LLM 역할 분리

| 역할 | Finance | T-Connect |
|------|---------|-----------|
| 기계적 처리 (스크립트) | Excel 생성, 데이터 입력, 검증, 백업 | Excel 변환, 데이터 추출, Excel 생성 |
| LLM 판단 | OCR 추출, 페이지 분류, 카테고리 판별 | 카테고리 판단, 모델 타입, 유효성 검증 |
| 사용자 소통 | AskUserQuestion으로 확인 | 디스플레이 크기 질의 |

핵심 설계 원칙이 일치합니다:
- **규칙이 100% 명확한 작업** → 스크립트
- **맥락 이해, 예외 처리, 사용자 소통** → LLM

### 3.2 CLI 인터페이스 표준화

```python
# Finance — positional args (매주 반복 사용에 최적화)
python3 scripts/process_offering.py create 0125
python3 scripts/process_offering.py write 0125
python3 scripts/process_offering.py verify 0125
python3 scripts/process_offering.py rollback 0125
python3 scripts/correct_names.py --add "새교인이름"
python3 scripts/gdrive.py pull 0125
python3 scripts/gdrive.py push 0125

# T-Connect — named args (일회성 작업, 명시적)
python scripts/convert.py --equipment-file {path} --output-dir {dir}
python scripts/extract.py --equipment-md {path} --output {path}
python scripts/generate.py --input {path} --template {path} --output {path}
```

Finance의 positional args가 매주 반복 사용에 더 적합합니다.
T-Connect의 named args는 일회성 작업에서 실수를 줄여줍니다.
각 사용 패턴에 맞는 올바른 선택입니다.

### 3.3 설정 자동 검증

```python
# Finance: offering_config.py — 모듈 로드 시 자동 검증
def _validate_categories():
    for cat_name, config in CATEGORIES.items():
        expected_slots = config["end"] - config["start"] + 1
        if config["slots"] != expected_slots:
            raise ValueError(f"slots={config['slots']}이지만 행 범위는 {expected_slots}개")
        # 행 중복도 감지
_validate_categories()  # 임포트 시 즉시 실행

# T-Connect: extract.py — config 없으면 기본값으로 폴백
def load_config():
    if not config_path.exists():
        return get_default_config()
```

Finance는 **로드 시점 검증**으로 잘못된 설정이 프로그램에 도달하기 전에 차단합니다.
T-Connect은 **fallback 기본값**으로 config 파일 없이도 동작합니다.
각각 다른 전략이지만 둘 다 합리적입니다.

### 3.4 테스트 (Finance 우위)

```
Finance: 73개 테스트
├── test_process_offering.py  — 카테고리 검증, 템플릿, 입력, 에러, 백업, dry-run, summary, rollback
├── test_correct_names.py     — 자모 분해, 유사도, 교정, 명부 추가, 에러, 엣지 케이스
└── test_gdrive.py            — 날짜 파싱, 폴더 검색, 파일 목록, 에러 핸들링 (mock)

T-Connect: 0개 테스트
```

테스트 커버리지는 Finance가 명확히 우위입니다.

### 3.5 백업/롤백 (Finance 고유)

```python
# Finance: 자동 백업 + 롤백 지원
_backup_file(output_path)                              # 쓰기 전 자동 백업
python3 scripts/process_offering.py rollback 0125      # 백업에서 복원
```

매주 반복하는 업무에서 실수 복구는 필수입니다. T-Connect에는 없는 기능입니다.

### 3.6 외부 서비스 연동 (Finance 고유)

```python
# Finance: Google Drive API 연동
gdrive.py pull 0125   # 스캔 파일 다운로드
gdrive.py push 0125   # 완성 Excel 업로드
gdrive.py list         # 폴더 조회

# 에러 처리
_handle_http_error()   # 403, 404, 429 에러별 안내
RefreshError 캐치      # 토큰 만료 시 재인증 유도
```

T-Connect은 로컬 파일만 처리합니다.
Finance는 Google Drive를 통해 입출력 파이프라인을 완성합니다.

---

## 4. 차이점 및 개선 가능 영역

### 4.1 SKILL.md 부재 — 가장 큰 구조적 차이

Finance는 **Claude Code Plugin** 형태라서 T-Connect의 SKILL.md에 해당하는 단일 문서가 없습니다.

```
T-Connect의 지식 구조:
  SKILL.md (600줄) ← LLM이 읽는 유일한 매뉴얼
    + preset-prompt.md (53줄) ← 행동 규칙

Finance의 지식 분산:
  CLAUDE.md (243줄) ← 아키텍처, 설계 결정, CLI 사용법
  commands/process-offering.md (249줄) ← 실행 단계, 판단 기준
  (합계 492줄, 2개 파일에 분산)
```

Finance에서는 `process-offering.md`가 SKILL.md 역할을 겸합니다.
`CLAUDE.md`는 개발 가이드 역할이므로 T-Connect의 preset-prompt.md에 더 가깝습니다.

### 4.2 LLM 판단 기준 문서화 수준

T-Connect은 **5가지 패턴**을 사용하여 판단 기준을 상세히 문서화합니다:

| 패턴 | T-Connect 사용 여부 | Finance 사용 여부 |
|------|:------------------:|:-----------------:|
| 매핑 테이블 | O (Tier Table, MM종류 Table, Prefix Table) | O (카테고리 매핑 참고 테이블) |
| 의사결정 트리 | O (Drive Recorder Q1→Q2→Q3 플로우) | X |
| Before/After 예시 | O (raw_data→final_data 변환 예시) | △ (실제 작업 예시는 있으나 데이터 변환 예시 없음) |
| Warning (⚠️) | O (스피커 수≠디스플레이 크기) | △ (금액 오인식 주의만 기술) |
| 사용자 질의 프로토콜 | O (Batch Query Mode, 응답 파싱 규칙) | O (AskUserQuestion 선택지 정의) |

**Finance에서 보강 가능한 부분:**
- 페이지 유형 분류를 **의사결정 트리**로 표현
- OCR 오인식 패턴을 **Warning**으로 명시
- 추출 데이터 → JSON 변환의 **Before/After 예시** 추가

### 4.3 config 외부화 안 됨

Finance의 설정이 Python 코드에 내장되어 있습니다:

```python
# offering_config.py — 설정과 코드가 같은 파일
CATEGORIES = {
    "십일조": {"start": 4, "end": 26, "slots": 23, "account_code": 10501000000},
    ...
}
CATEGORY_ALIASES = {
    "산돌회": "샬롬전도회",
    ...
}
SPECIAL_OFFERING_KEYWORDS = ["송구영신", "헌신예배", ...]
```

T-Connect 방식이라면:

```yaml
# config/categories.yaml
categories:
  십일조: {start: 4, end: 26, slots: 23, account_code: 10501000000}
aliases:
  산돌회: 샬롬전도회
special_keywords: [송구영신, 헌신예배]
```

**현실적 판단**: Finance는 매주 같은 팀이 반복 사용하므로 Python 내장 방식이 오히려 실용적입니다.
YAML 분리는 여러 교회에서 동일 스크립트를 다른 설정으로 사용할 때 비로소 의미가 있습니다.
현재로서는 **불필요한 분리** — 현행 유지가 적절합니다.

### 4.4 references (스키마 문서) 부재

T-Connect은 `references/schemas.md`에서 raw_data.json, final_data.json의 정확한 스키마와 예시를 제공합니다.

Finance는 데이터 구조가 `process-offering.md`에 인라인으로 들어있습니다:

```json
{
    "십일조": [
        {"name": "최정호", "amount": 578000}
    ]
}
```

Finance의 JSON 구조는 단순(`{카테고리: [{name, amount}]}`)하여 별도 스키마 문서가 필요 없습니다.
T-Connect은 raw_data.json/final_data.json 간 **구조 변환**이 복잡하므로 스키마 문서가 필수였습니다.

### 4.5 다국어 지원 없음

```
T-Connect: 3개 언어 (영어, 일본어, 한국어)
  - 감지 우선순위, 언어별 응답 샘플, 용어 테이블 제공

Finance: 한국어 단일
  - 특정 교회의 내부 업무이므로 다국어 불필요
```

### 4.6 Frontmatter 비교

```yaml
# T-Connect SKILL.md
---
name: tconnect
description: "T-Connect Confirmation Request Form auto-generation.
  Use when user mentions T-Connect, confirmation request form..."
---

# Finance process-offering.md
---
name: process-offering
description: 헌금 전표 이미지/PDF를 읽어 Excel 파일로 자동 입력합니다
argument-hint: "MMDD 또는 YYYYMMDD (예: 0125)"
allowed-tools:
  - AskUserQuestion
  - Glob
  - Bash
  - Read
  - Write
  - Edit
---
```

Finance의 frontmatter가 더 풍부합니다:
- `argument-hint`: 인자 형식 안내 — T-Connect에 없는 Claude Code Plugin 고유 기능
- `allowed-tools`: 도구 사용 제한 — 보안 및 실행 범위 통제

---

## 5. 종합 평가

```
평가 항목                T-Connect  Finance   비고
─────────────────────  ────────  ────────  ──────────────────────────
스크립트/LLM 역할 분리    ★★★★★    ★★★★★    둘 다 명확
파이프라인 설계            ★★★★★    ★★★★★    둘 다 명확한 단계 구분
LLM 판단 기준 문서화      ★★★★★    ★★★☆☆    Finance는 인라인, 의사결정 트리/예시 부족
config 외부화             ★★★★★    ★★☆☆☆    Python 내장 (실용적이지만 분리 안 됨)
스키마/참조 문서           ★★★★☆    ★★★☆☆    Finance는 JSON이 단순하여 인라인 충분
CLI 인터페이스             ★★★★☆    ★★★★★    Finance가 반복 사용에 더 적합
테스트                    ☆☆☆☆☆    ★★★★★    Finance 73개 vs T-Connect 0개
사용자 소통 프로토콜       ★★★★★    ★★★★☆    T-Connect이 더 정형화 (Batch Query)
다국어 지원               ★★★★★    ☆☆☆☆☆    Finance는 한국어 단일 (적절한 선택)
백업/롤백                 ☆☆☆☆☆    ★★★★★    Finance만 있음
외부 서비스 연동           ☆☆☆☆☆    ★★★★★    Finance: Google Drive 완전 통합
에러 핸들링               ★★☆☆☆    ★★★★★    Finance: API 에러, 입력 검증, 방어 처리
```

---

## 6. 구체적 개선 제안

### 우선순위 높음

#### 6.1 process-offering.md에 의사결정 트리 추가

현재:
```markdown
| 내용 특징 | 유형 | 처리 |
|-----------|------|------|
| 표 형태 + "통계표" 제목 | 통계표 | 표에서 (이름, 금액) 쌍 추출 |
| 단일 전표 양식 + 금액 | 전표 | 총액 + 내역 추출 |
```

추가 제안:
```markdown
페이지 읽기 후 분류 흐름:
│
├─ Q1: 표 형태 + 여러 줄의 (이름, 금액) 쌍이 있는가?
│   └─ Yes → 통계표
│   └─ No → Continue
│
├─ Q2: 단일 전표 양식 (총액 + 내역)인가?
│   └─ Yes → 전표
│   └─ No → Continue
│
├─ Q3: 이전 페이지와 동일 내용인가?
│   └─ Yes → 중복 (건너뛰기)
│   └─ No → Continue
│
├─ Q4: 특별헌금 키워드 포함? (송구영신, 헌신예배 등)
│   └─ Yes → 사용자에게 포함 여부 질문
│   └─ No → 기타 (사용자에게 유형 질문)
```

#### 6.2 OCR 오인식 Warning 보강

현재 `process-offering.md`에 금액 오인식만 간략히 언급되어 있습니다.

추가 제안:
```markdown
⚠️ **OCR 오인식 주의사항:**
- 필기체 숫자: 5↔3, 8↔0, 1↔7 혼동 빈번
- 쉼표 위치: 580,000 → 58,0000 또는 5,80000
- 한글 이름: 획이 유사한 글자 혼동 (호↔모, 건↔진, 천→권)
  → correct_names.py의 자모 분해가 대부분 해결
  → 3음절 이상 동시 오인식 시 교정 불가 (unknown 처리)
- 부서명: "어린이부" → "어린이뷰" 등
  → 정확히 일치하지 않으면 사용자 확인 필요
```

### 우선순위 중간

#### 6.3 데이터 변환 Before/After 예시 추가

OCR 추출 결과 → JSON 입력 데이터로의 변환을 예시로 보여주면 LLM의 정확도가 높아집니다.

```markdown
**OCR 추출 (통계표 페이지):**
| 이름 | 금액 |
|------|------|
| 최정호 | 578,000 |
| 박경애 | 580,000 |
| 천인성,하공남 | 450,000 |
합계: 1,608,000

**이름 교정 후:**
천인성 → 권언성 (corrected, confidence: 0.67)

**최종 JSON:**
```json
{
  "십일조": [
    {"name": "최정호", "amount": 578000},
    {"name": "박경애", "amount": 580000},
    {"name": "권언성,하공남", "amount": 450000}
  ]
}
```

**주의:** 교정된 이름만 대체. 쉼표로 연결된 이름은 그대로 유지.
```

### 우선순위 낮음 (현행 유지 권장)

| 항목 | 이유 |
|------|------|
| config YAML 분리 | 단일 교회 사용, Python 내장이 실용적 |
| references 별도 문서 | JSON 구조가 단순하여 인라인 충분 |
| 다국어 지원 | 한국어 단일 사용 환경 |
| SKILL.md 통합 | Plugin 형태 유지가 사용 패턴에 적합 |

---

## 7. 아키텍처 판단: AIP Skill vs Claude Code Plugin

### Finance가 Plugin으로 남아야 하는 이유

| 판단 기준 | AIP Skill (T-Connect) | Claude Code Plugin (Finance) |
|-----------|:--------------------:|:--------------------------:|
| 배포 대상 | 불특정 다수 | 특정 팀 (1개 교회) |
| 사용 빈도 | 비정기 (차종 출시 시) | **매주 반복** |
| 실행 환경 | AIP 플랫폼 | **로컬 CLI** |
| 외부 연동 | 없음 | **Google Drive** |
| 인터랙션 | 파일 업로드 → 결과 | **슬래시 커맨드 → 단계별 확인** |
| 데이터 민감도 | 차량 스펙 (공개) | **교인 개인정보 (비공개)** |

Finance는:
- **매주 반복** → 슬래시 커맨드(`/process-offering 0125`)가 자연스러움
- **로컬 실행** → 교인 명부, 금액 데이터가 로컬에만 존재
- **Google Drive 연동** → AIP보다 CLI에서 인증 관리가 용이
- **단계별 확인** → AskUserQuestion 기반 인터랙션이 CLI에 최적화

**결론: 현재 Claude Code Plugin 형태가 Finance의 사용 패턴에 최적입니다.**

---

## 8. Finance가 T-Connect에 줄 수 있는 교훈

Finance에는 있지만 T-Connect에 없는 것들:

| Finance 기능 | T-Connect에 적용 가능성 |
|-------------|----------------------|
| 테스트 스위트 (73개) | **높음** — extract.py, generate.py에 단위 테스트 추가 가능 |
| 백업/롤백 | 중간 — 출력 Excel 덮어쓰기 방지 |
| dry-run 모드 | **높음** — final_data.json 미리보기 후 Excel 생성 |
| 입력 데이터 검증 | 중간 — raw_data.json 구조 검증 |
| 월간 요약 (summary) | 낮음 — 차종별 일회성 작업 |
| 외부 서비스 연동 | 낮음 — AIP 플랫폼이 파일 관리 |

---

*분석 기준: T-Connect Skill (tconnect.zip) vs Finance Plugin (finance/)*
*분석일: 2026-01-28*
