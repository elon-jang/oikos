# 교회 기부금 영수증 자동화 삽질기 🙏

> "수작업으로 94장의 영수증을 만들던 시절은 이제 안녕"

## 들어가며

매년 1월이 되면 교회 재정 담당자들의 한숨 소리가 들린다. 기부금 영수증 발행 시즌이 돌아왔기 때문이다. 엑셀에서 이름 하나하나 복사하고, 금액 옮기고, 오타 수정하고... 94명분을 만들다 보면 어느새 해가 지고 있다.

"이거 자동화하면 안 되나?"

그렇게 시작된 Python 스크립트 개발기. 오늘은 그 과정에서 배운 것들을 공유한다.

---

## 1. Word 템플릿의 마법: docxtpl 📝

처음엔 reportlab으로 PDF를 직접 그렸다. 폰트 깨지고, 레이아웃 틀어지고, A4 한 장에 안 들어가고... 삽질의 연속이었다.

그러다 발견한 **docxtpl**. Word 문서에 `{{name}}` 같은 placeholder를 넣어두면, Python에서 값만 넣어주면 끝이다.

```python
from docxtpl import DocxTemplate

template = DocxTemplate("영수증_템플릿.docx")
template.render({"name": "홍길동", "total": "1,000,000"})
template.save("영수증_홍길동.docx")
```

**교훈**: 바퀴를 재발명하지 말자. 이미 잘 만들어진 도구가 있다.

---

## 2. 파일명이 곧 데이터다 🗂️

매년 데이터 파일이 `2024_income_summary.xlsx`, `2025_income_summary.xlsx`로 쌓인다. 처음엔 연도를 수동으로 입력받았다.

```bash
python generate.py --year 2025  # 매번 이걸 쳐야 해?
```

그러다 깨달았다. **파일명에 이미 연도가 있잖아!**

```python
import glob, re

files = glob.glob("*_income_summary.xlsx")
for f in files:
    match = re.match(r"(\d{4})_income", f)
    if match:
        year = int(match.group(1))  # 2025 추출!
```

가장 최신 파일을 자동으로 찾아서 처리한다. 사용자는 그냥 `python generate.py`만 치면 된다.

**교훈**: 좋은 파일명 규칙은 자동화의 시작이다.

---

## 3. append()는 죽었다, concat() 만세 🐼

pandas로 발행대장에 새 기록을 추가하려고 했다.

```python
df = df.append(new_row)  # DeprecationWarning 폭탄!
```

pandas 2.0부터 `append()`가 사라졌다. 이제는 `concat()`을 써야 한다.

```python
new_row = pd.DataFrame([{"이름": "홍길동", "금액": 100000}])
df = pd.concat([df, new_row], ignore_index=True)
```

**주의**: dict를 `[{}]` 리스트로 감싸야 한다. 안 그러면 이상한 결과가 나온다.

**교훈**: 라이브러리 업데이트 로그를 가끔은 읽어보자.

---

## 4. 부부는 하나지만 영수증은 둘 💑

데이터에 "강신애,최정호"처럼 부부 이름이 쉼표로 들어온다. 같은 금액으로 각각 영수증을 발행해야 한다.

```python
if "," in name:
    names = [n.strip() for n in name.split(",")]
    for individual_name in names:
        # 각자 영수증 생성
```

단순한 로직이지만, 이걸 안 하면 "강신애,최정호" 앞으로 된 영수증 한 장만 나온다. 국세청에서 좋아하지 않을 것이다.

**교훈**: 도메인 지식이 코드보다 중요할 때가 있다.

---

## 5. 재발행도 기록이다 📋

같은 사람 영수증을 다시 발행하면? 그냥 덮어쓰면 될까?

아니다. **언제, 몇 번 발행했는지** 기록해야 한다. 감사 추적(audit trail)의 기본이다.

```python
existing = ledger_df[ledger_df["발급번호"] == receipt_no]
if not existing.empty:
    note = "재발행"  # 기존 기록 있으면 재발행 표시
```

발행대장에 모든 이력이 쌓인다. 나중에 "작년에 영수증 받았는데요?" 하면 바로 확인 가능.

**교훈**: 로그는 미래의 나를 구한다.

---

## 결과: 94장을 3초에 ⚡

```bash
$ python generate_receipts.py
데이터 파일: 2025_income_summary.xlsx (발급연도: 26)
전체 대상: 94명
  생성: 강신애 (26-001)
  생성: 강유주 (26-002)
  ...
완료! receipts/ 폴더에 94개 DOCX 생성됨
발행대장: 발행대장_2026.xlsx
```

수작업으로 하루 종일 걸리던 일이 3초로 줄었다. 이제 재정 담당자는 커피 한 잔 마시며 결과만 확인하면 된다.

---

## 마치며

자동화의 핵심은 **"반복되는 일을 찾아 없애는 것"**이다.

- 매년 반복되는 영수증 발행 → 스크립트로 자동화
- 매번 입력하는 연도 → 파일명에서 자동 추출
- 매번 확인하는 발행 이력 → 대장에 자동 기록

작은 불편함을 참지 말자. 그 불편함이 쌓이면 큰 시간 낭비가 된다.

다음 목표? PDF 자동 변환과 이메일 발송. 영수증이 알아서 교인들 메일함에 들어가는 그날까지! 🚀

---

*"좋은 코드는 게으른 사람이 만든다" - 어느 개발자*
