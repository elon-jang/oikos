"""헌금 카테고리 → Excel 행 매핑 설정."""

# 특별헌금 키워드 (파일명 또는 페이지 내용에 포함 시 특별헌금으로 분류)
SPECIAL_OFFERING_KEYWORDS = [
    "송구영신",
    "헌신예배",
    "제직헌신",
    "부활절",
    "추수감사",
    "성탄절",
    "맥추감사",
]

# 카테고리별 설정: (시작행, 끝행, 슬롯수, 계정코드, 예배코드)
# 행 번호는 Excel 기준 (1-indexed, 헤더 3행 이후 데이터 시작 = 4행)
CATEGORIES = {
    "십일조":     {"start": 4,  "end": 26, "slots": 23, "account_code": 10501000000, "service_code": 1},
    "장년부주일": {"start": 27, "end": 27, "slots": 1,  "account_code": 10502000000, "service_code": 1},
    "감사":       {"start": 28, "end": 44, "slots": 17, "account_code": 10503000000, "service_code": 1},
    "생일감사":   {"start": 45, "end": 48, "slots": 4,  "account_code": 10504000000, "service_code": 1},
    "일천번제":   {"start": 49, "end": 52, "slots": 4,  "account_code": 10505000000, "service_code": 1},
    "어린이부":   {"start": 53, "end": 53, "slots": 1,  "account_code": 10301000000, "service_code": 1},
    "중고등부":   {"start": 54, "end": 54, "slots": 1,  "account_code": 10302000000, "service_code": 1},
    "청년부":     {"start": 55, "end": 55, "slots": 1,  "account_code": 10303000000, "service_code": 1},
    "장학":       {"start": 56, "end": 61, "slots": 6,  "account_code": 10401000000, "service_code": 1},
    "구제":       {"start": 62, "end": 68, "slots": 7,  "account_code": 10402000000, "service_code": 1},
    "월정선교":   {"start": 69, "end": 87, "slots": 19, "account_code": 242003,      "service_code": 1},
    "갈렙전도회": {"start": 88, "end": 88, "slots": 1,  "account_code": 242004,      "service_code": 1},
    "남전도회":   {"start": 89, "end": 89, "slots": 1,  "account_code": 242005,      "service_code": 1},
    "안나전도회": {"start": 90, "end": 90, "slots": 1,  "account_code": 242006,      "service_code": 1},
    "여전도회":   {"start": 91, "end": 91, "slots": 1,  "account_code": 242007,      "service_code": 1},
    "셀헌금":     {"start": 92, "end": 92, "slots": 1,  "account_code": 242008,      "service_code": 1},
    "샬롬전도회": {"start": 93, "end": 93, "slots": 1,  "account_code": 242009,      "service_code": 1},
    "통장이자":   {"start": 94, "end": 94, "slots": 1,  "account_code": 242202,      "service_code": 1},
    "기타수입":   {"start": 95, "end": 95, "slots": 1,  "account_code": 10202000000, "service_code": 1},
}

# 카테고리 별칭 매핑 (이미지 OCR에서 다른 이름으로 인식될 수 있는 경우)
CATEGORY_ALIASES = {
    # 기존
    "산돌회": "샬롬전도회",
    "주일헌금": "장년부주일",
    "주일학교 헌금": "중고등부",  # 문맥에 따라 다를 수 있음
    "십일조헌금": "십일조",
    "감사헌금": "감사",
    "생일감사헌금": "생일감사",
    "장학헌금": "장학",
    "구제헌금": "구제",
    "월정헌금": "월정선교",
    "선교헌금": "월정선교",
    # 추가 — 공백/변형
    "십일조 헌금": "십일조",
    "감사 헌금": "감사",
    "생일 감사": "생일감사",
    "장학 헌금": "장학",
    "구제 헌금": "구제",
    "월정 선교": "월정선교",
    "정기선교": "월정선교",
    "주일 헌금": "장년부주일",
    "장년부 주일": "장년부주일",
    "장년주일": "장년부주일",
    "산돌전도회": "샬롬전도회",
    "셀 헌금": "셀헌금",
    "기타 수입": "기타수입",
    "통장 이자": "통장이자",
}

# 카테고리 순서 (Excel 행 순서와 동일)
CATEGORY_ORDER = list(CATEGORIES.keys())


def _validate_categories():
    """CATEGORIES 설정 일관성 검증 (모듈 로드 시 자동 실행)."""
    seen_rows = set()
    for cat_name, config in CATEGORIES.items():
        start, end = config["start"], config["end"]
        expected_slots = end - start + 1
        actual_slots = config.get("slots")
        if actual_slots != expected_slots:
            raise ValueError(
                f"CATEGORIES 설정 오류 — {cat_name}: slots={actual_slots}이지만 "
                f"행 범위 {start}-{end}은 {expected_slots}개입니다"
            )
        for row in range(start, end + 1):
            if row in seen_rows:
                raise ValueError(
                    f"CATEGORIES 설정 오류 — 행 {row}이 여러 카테고리에서 사용됩니다 ({cat_name})"
                )
            seen_rows.add(row)


_validate_categories()


def resolve_category(raw_name: str) -> str | None:
    """OCR에서 추출한 카테고리명을 정규화된 카테고리명으로 변환.

    Returns:
        정규화된 카테고리명 또는 None (매칭 실패 시).
    """
    name = raw_name.strip()
    # 1. 정확히 일치
    if name in CATEGORIES:
        return name
    # 2. 별칭 매핑
    if name in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[name]
    # 3. 공백/특수문자 제거 후 재시도
    normalized = name.replace(" ", "").replace("·", "")
    if normalized in CATEGORIES:
        return normalized
    for alias, cat in CATEGORY_ALIASES.items():
        if alias.replace(" ", "") == normalized:
            return cat
    # 4. 부분 일치 (카테고리명이 포함된 경우)
    for cat_name in CATEGORIES:
        if cat_name in name:
            return cat_name
    return None


def suggest_categories(raw_name: str) -> list[dict]:
    """카테고리 후보 목록 반환 (resolve 실패 시 사용).

    Returns:
        [{"category": str, "score": float}, ...] 최대 5건, 점수 내림차순.
    """
    name = raw_name.strip().replace(" ", "")
    suggestions = []
    for cat_name in CATEGORIES:
        overlap = sum(1 for c in name if c in cat_name)
        if overlap >= 1 and len(name) >= 2:
            score = overlap / max(len(name), len(cat_name))
            if score >= 0.3:
                suggestions.append({"category": cat_name, "score": round(score, 2)})
    return sorted(suggestions, key=lambda x: x["score"], reverse=True)[:5]
