# 기부금 영수증 MCP 서버 구현 계획

## 개요

비개발자도 쉽게 사용할 수 있는 기부금 영수증 발행 시스템을 MCP 서버로 구현합니다.

**목표:**
- Claude Desktop/Code에서 자연어로 영수증 발행
- 원클릭 설치
- 개인정보 보호 (로컬 처리)

---

## 배포 방식 비교

| 방식 | 대상 | 난이도 | 추천 |
|------|------|--------|------|
| **Docker 이미지** | Docker 사용자 | ⭐ | ✅ 1순위 |
| **로컬 설치 스크립트** | 터미널 사용자 | ⭐⭐ | ✅ 2순위 |
| **GUI 설치 도우미** | 완전 비개발자 | ⭐ | 3순위 |
| Smithery 등록 | MCP 생태계 | ⭐ | 4순위 |

---

## Phase 1: MCP 서버 핵심 구현 ✅

### 1.1 프로젝트 구조 생성

- [x] `mcp_server/` 디렉토리 생성
- [x] `mcp_server/__init__.py` 생성
- [x] `mcp_server/server.py` - 메인 MCP 서버
- [x] `mcp_server/tools/` 디렉토리 생성
- [x] `mcp_server/tools/receipt.py` - 영수증 도구
- [x] `mcp_server/tools/validate.py` - 검증 도구
- [x] `mcp_server/tools/history.py` - 이력 도구
- [x] `requirements.txt` 업데이트

**목표 구조:**
```
examples/tax_return/
├── mcp_server/
│   ├── __init__.py
│   ├── server.py
│   └── tools/
│       ├── __init__.py
│       ├── receipt.py
│       ├── validate.py
│       └── history.py
├── generate_receipts.py  (기존 유지)
└── ...
```

### 1.2 MCP 도구 구현

#### 영수증 도구 (`receipt.py`)

- [x] `list_recipients()` - 대상자 목록 조회
  - [x] 데이터 파일 자동 감지
  - [x] 총 인원수 반환 (개인정보 미포함)
  - [x] 총 금액 합계 반환
- [x] `generate_receipt(name: str)` - 특정인 영수증 생성
  - [x] 이름으로 대상자 검색
  - [x] 영수증 파일 생성
  - [x] 발행대장 기록
  - [x] 결과 요약 반환 (금액 미포함)
- [x] `generate_all_receipts()` - 전체 영수증 생성
  - [x] 확인 메시지 반환 (생성 전)
  - [x] 배치 생성 실행
  - [x] 진행 상황 로깅
  - [x] 결과 요약 반환
- [x] `preview_receipt(name: str)` - 영수증 미리보기
  - [x] 텍스트 형식으로 미리보기 생성
  - [x] 금액 마스킹 옵션

#### 검증 도구 (`validate.py`)

- [x] `validate_data(file_path: str)` - 데이터 파일 검증
  - [x] 필수 컬럼 확인
  - [x] 숫자 형식 확인
  - [x] 합계 검증
  - [x] 오류 목록 반환 (행 번호만, 이름 미포함)
- [x] `validate_template(file_path: str)` - 템플릿 검증
  - [x] placeholder 확인
  - [x] 누락된 placeholder 목록

#### 이력 도구 (`history.py`)

- [x] `get_history(year: int)` - 발행 이력 조회
  - [x] 총 발행 건수 반환
  - [x] 최근 발행 일시
  - [x] 상세 내역은 파일 참조 안내
- [x] `get_person_history(name: str)` - 특정인 이력
  - [x] 발행 여부만 반환
  - [x] 상세 내역은 파일 참조 안내

### 1.3 개인정보 보호 설계

- [x] 응답에서 개인 이름 제외 (옵션)
- [x] 응답에서 금액 제외 (옵션)
- [x] 상세 정보는 "로컬 파일 확인" 안내
- [ ] 설정 파일로 보호 수준 조절 (추후 구현)

**응답 예시:**
```python
# 안전한 응답
{
    "status": "success",
    "count": 94,
    "output_dir": "receipts/",
    "message": "94명의 영수증이 생성되었습니다. receipts/ 폴더를 확인하세요."
}

# 개인정보 포함하지 않음
# ❌ {"name": "홍길동", "amount": 1200000}
```

---

## Phase 2: Docker 이미지 구현 ✅

### 2.1 Docker 파일 작성

- [x] `Dockerfile` 생성
  - [x] Python 3.11 slim 베이스
  - [x] 의존성 설치
  - [x] MCP 서버 복사
  - [x] 볼륨 마운트 포인트 설정
  - [x] 엔트리포인트 설정
- [x] `.dockerignore` 생성
- [x] `docker-compose.yml` 생성 (개발용)

**Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp_server/ ./mcp_server/
COPY generate_receipts.py .
VOLUME /data
ENV DATA_DIR=/data
CMD ["python", "-m", "mcp_server.server"]
```

### 2.2 이미지 빌드 및 테스트

- [ ] 로컬 빌드 테스트
  ```bash
  docker build -t oikos-receipt:dev .
  ```
- [ ] 볼륨 마운트 테스트
  ```bash
  docker run -v ~/test-data:/data oikos-receipt:dev
  ```
- [ ] MCP 연결 테스트 (stdio)
- [ ] Claude Desktop 연동 테스트

> ⚠️ Docker Desktop 실행 시 테스트 가능

### 2.3 Docker Hub 배포

- [ ] Docker Hub 계정 설정
- [ ] 이미지 태깅 규칙 정의
  - `latest` - 최신 안정 버전
  - `vX.Y.Z` - 버전별 태그
- [ ] 이미지 푸시
  ```bash
  docker push joomanba/oikos-receipt:latest
  ```
- [ ] README 작성 (Docker Hub용)

---

## Phase 3: 원클릭 설치 도구 ✅

### 3.1 설치 스크립트

#### macOS (`install.sh`)

- [x] Docker 설치 여부 확인
- [x] Docker 미설치 시 안내 메시지
- [x] 이미지 다운로드 (`docker pull`)
- [x] 데이터 폴더 생성 (`~/기부금영수증/`)
- [x] 샘플 파일 다운로드
- [x] Claude Desktop 설정 자동 추가
- [x] 완료 메시지 출력

#### Windows (`install.bat` / `install.ps1`)

- [x] Docker Desktop 확인
- [x] 이미지 다운로드
- [x] 데이터 폴더 생성
- [x] Claude 설정 추가 (PowerShell)
- [x] 완료 메시지

### 3.2 GUI 설치 도우미

- [x] `install_gui.py` 작성
  - [x] Docker 상태 확인 표시
  - [x] 데이터 폴더 선택 UI
  - [x] 설치 진행률 표시
  - [x] 오류 메시지 친화적 표시
- [x] PyInstaller 빌드 스크립트 작성
  - [x] `build_installer.sh` (macOS)
  - [x] `build_installer.bat` (Windows)
- [ ] PyInstaller로 실행 파일 생성
  - [ ] macOS: `기부금영수증 설치.app`
  - [ ] Windows: `기부금영수증_설치.exe`
- [ ] 테스트 (클린 환경)

### 3.3 설치 문서

- [x] `DOCKER.md` 작성
  - [x] Docker Desktop 설치 방법
  - [x] 원클릭 설치 방법
  - [x] 수동 설치 방법
  - [x] 문제 해결 가이드
- [ ] 영상 튜토리얼 (선택)

---

## Phase 4: 문서화 및 테스트 ✅

### 4.1 사용자 문서

- [x] `README.md` 업데이트
  - [x] MCP 설치 방법 추가
  - [x] Docker 사용법 추가
  - [x] Claude에서 사용 예시
- [x] `MCP_사용가이드.md` 작성
  - [x] 설치 후 첫 사용법
  - [x] 자주 쓰는 명령어 예시
  - [x] 문제 해결

### 4.2 테스트

- [x] 단위 테스트 작성
  - [x] `test_mcp_server.py` (28개 테스트)
  - [x] 각 도구 함수 테스트
- [x] 통합 테스트
  - [x] `test_mcp_integration.py` (9개 테스트)
  - [ ] Docker 컨테이너 테스트
  - [ ] Claude Desktop 연동 테스트
- [ ] 사용자 테스트
  - [ ] 비개발자 테스트 (실제 교회 담당자)
  - [ ] 피드백 수집

### 4.3 CI/CD 설정

- [ ] GitHub Actions 워크플로우
  - [ ] 테스트 자동 실행
  - [ ] Docker 이미지 자동 빌드
  - [ ] Docker Hub 자동 푸시 (태그 시)

---

## Phase 5: 배포 및 유지보수

### 5.1 초기 배포

- [ ] Docker Hub에 v1.0.0 배포
- [ ] GitHub Release 생성
- [ ] 설치 스크립트 URL 확정
- [ ] 문서 최종 검토

### 5.2 유지보수 계획

- [ ] 버전 관리 정책 수립
- [ ] 이슈 트래킹 설정
- [ ] 업데이트 알림 방법 결정

---

## 기술 명세

### MCP 서버 설정

```python
# mcp_server/server.py
from fastmcp import FastMCP

mcp = FastMCP(
    name="oikos-receipt",
    description="기부금 영수증 발행 시스템"
)

# 도구 등록
from .tools import receipt, validate, history

mcp.include_router(receipt.router)
mcp.include_router(validate.router)
mcp.include_router(history.router)
```

### Claude Desktop 설정

```json
{
  "mcpServers": {
    "oikos-receipt": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/Users/사용자/기부금영수증:/data",
        "joomanba/oikos-receipt:latest"
      ]
    }
  }
}
```

### 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `DATA_DIR` | `/data` | 데이터 디렉토리 |
| `PRIVACY_MODE` | `true` | 개인정보 마스킹 |
| `LOG_LEVEL` | `INFO` | 로그 레벨 |

---

## 예상 사용 흐름

```
사용자: 올해 영수증 발행 대상자 몇 명이야?
Claude: [list_recipients 도구 호출]
        총 94명입니다. 전체 헌금 총액은 45,000,000원입니다.
        상세 목록은 ~/기부금영수증/2025_income_summary.xlsx를 확인하세요.

사용자: 전체 영수증 발행해줘
Claude: [generate_all_receipts 도구 호출]
        94명의 영수증을 생성합니다. 계속할까요?

사용자: 응
Claude: [generate_all_receipts 확인 후 실행]
        ✅ 94명의 영수증이 생성되었습니다.
        📁 위치: ~/기부금영수증/receipts/
        📋 발행대장: ~/기부금영수증/발행대장_2026.xlsx

사용자: 강신애 영수증 재발행해줘
Claude: [generate_receipt 도구 호출]
        ✅ 강신애님 영수증이 재발행되었습니다.
        📁 파일: ~/기부금영수증/receipts/기부금영수증_강신애.docx
        (발행대장에 '재발행'으로 기록됨)
```

---

## 일정 (예상)

| Phase | 작업 | 예상 시간 | 상태 |
|-------|------|-----------|------|
| Phase 1 | MCP 서버 핵심 구현 | 4-6시간 | ✅ 완료 |
| Phase 2 | Docker 이미지 구현 | 2-3시간 | ✅ 파일 작성 완료 |
| Phase 3 | 원클릭 설치 도구 | 3-4시간 | ✅ 스크립트 작성 완료 |
| Phase 4 | 문서화 및 테스트 | 2-3시간 | ✅ 테스트 작성 완료 |
| Phase 5 | 배포 | 1-2시간 | ⏳ 대기 중 |
| **합계** | | **12-18시간** | |

---

## 미해결 사항

1. **Docker Hub 계정명** - `elonj` 또는 다른 이름?
2. ~~개인정보 보호 수준~~ - 기본값: 이름/금액 미포함 (완료)
3. **Smithery 등록** - 진행 여부?
4. ~~GUI 설치 도우미~~ - 스크립트 작성 완료, 빌드는 추후

---

*문서 생성일: 2026-01-21*
*최종 수정: 2026-01-21*
*상태: Phase 1-4 완료, Phase 5 대기*
