# Oikos - 교회 업무 자동화 도구

> "오이코스(Oikos)"는 그리스어로 "가정, 공동체"를 의미합니다.
> 교회 공동체의 행정 업무를 자동화하여 더 중요한 사역에 집중할 수 있도록 돕습니다.

---

## 기능

| 모듈 | 설명 | 상태 |
|------|------|------|
| [tax_return](tax_return/README.md) | 기부금 영수증 자동 발행 | ✅ 완료 |
| [bulletin](bulletin/) | 주보 자동 생성 | 🔜 예정 |
| [membership](membership/) | 교적 관리 | 🔜 예정 |
| [sermon](sermon/) | 설교 요약/정리 | 🔜 예정 |
| [events](events/) | 행사 안내문 생성 | 🔜 예정 |
| [finance](finance/) | 재정 보고서 | 🔜 예정 |

---

## 기부금 영수증 자동 발행

Claude Desktop에서 **"홍길동 영수증 발행해줘"** 한마디면 끝!

```
나: 전체 영수증 발행해줘
Claude: 94명의 영수증을 생성할게요. 진행할까요?

나: 응!
Claude: 완료! 94개의 영수증이 생성되었어요.
```

**5분 만에 100명분 영수증 발행 완료!**

### 빠른 시작

**Mac:**
```bash
curl -sL https://raw.githubusercontent.com/elon-jang/oikos/master/tax_return/deploy/install.sh | bash
```

**Windows:**
```powershell
irm https://raw.githubusercontent.com/elon-jang/oikos/master/tax_return/deploy/install.ps1 | iex
```

> [Docker Desktop](https://www.docker.com/products/docker-desktop/) 설치 필요

자세한 내용: [tax_return/README.md](tax_return/README.md)

---

## 문서

| 문서 | 설명 |
|------|------|
| [시작하기 가이드](tax_return/docs/시작하기_가이드.md) | 처음 사용자용 |
| [Docker 가이드](tax_return/docs/DOCKER.md) | Docker로 MCP 서버 실행 |
| [Python 가이드](tax_return/docs/PYTHON.md) | Python으로 MCP 서버 실행 |
| [CLI 가이드](tax_return/docs/CLI_가이드.md) | 터미널에서 직접 실행 |

---

## 프로젝트 구조

```
oikos/
├── tax_return/      # 기부금 영수증 ✅
├── bulletin/        # 주보 자동 생성 🔜
├── membership/      # 교적 관리 🔜
├── sermon/          # 설교 요약/정리 🔜
├── events/          # 행사 안내문 🔜
├── finance/         # 재정 보고서 🔜
└── README.md
```

---

## 기여

- **Issues**: [GitHub Issues](https://github.com/elon-jang/oikos/issues)
- **PR**: 환영합니다!

## 라이선스

MIT License

---

**Made with love for church communities**
