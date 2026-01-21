# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-01-21

### Fixed
- MCP 도구 이름 개선으로 Claude Desktop 호출 문제 해결
  - `tool_*` 접두사 제거 → 설명적 이름 사용
  - 예: `tool_list_recipients` → `list_donation_recipients`

### Added
- MCP 서버 Python 직접 실행 방식 지원
  - Docker 연결 문제 시 대안으로 권장
  - pyenv 환경 지원
- CLAUDE.md 추가 (MCP 베스트 프랙티스 문서)

### Changed
- Docker 이미지 업데이트 (`joomanba/oikos-receipt:v1.1.0`)

---

## [1.0.0] - 2026-01-21

### Added
- 기부금 영수증 자동 발행 시스템
- MCP 서버 (Claude Desktop 연동)
- Docker 지원 (원클릭 설치)
- Python CLI 인터페이스
- 발행대장 자동 기록
- 부부 이름 자동 분리 기능
- 연도 자동 감지 기능
- 재발행 추적 기능

### Documentation
- 비개발자 친화적 문서 작성
- 시작하기 가이드
- MCP 사용 가이드
- 템플릿 만들기 가이드
- Docker 설정 가이드

### Infrastructure
- 폴더 구조 재정리 (tests/, deploy/, docs/)
- macOS/Windows 설치 스크립트
- Docker 이미지 빌드 지원

---

## [Unreleased]

### Planned
- CI/CD 파이프라인 (GitHub Actions)
- 테스트 커버리지 확대
- PDF 내보내기 기능 완성
- 진행률 표시 기능
