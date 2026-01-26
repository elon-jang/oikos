"""교인 명부 기반 이름 교정 모듈 (fuzzy matching)."""

import difflib
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MEMBERS_FILE = os.path.join(SCRIPT_DIR, "members.txt")


def load_members(filepath: str = MEMBERS_FILE) -> list[str]:
    """교인 명부 파일에서 이름 목록 로드."""
    with open(filepath, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def correct_name(name: str, members: list[str], cutoff: float = 0.5) -> dict:
    """
    단일 이름을 교인 명부와 대조하여 교정.

    Returns:
        {
            "original": "천인성",
            "corrected": "권언성",
            "status": "corrected" | "exact" | "unknown",
            "confidence": 0.67
        }
    """
    name = name.strip()
    if not name:
        return {"original": name, "corrected": name, "status": "exact", "confidence": 1.0}

    # 정확히 일치
    if name in members:
        return {"original": name, "corrected": name, "status": "exact", "confidence": 1.0}

    # fuzzy matching
    matches = difflib.get_close_matches(name, members, n=1, cutoff=cutoff)
    if matches:
        match = matches[0]
        ratio = difflib.SequenceMatcher(None, name, match).ratio()
        return {
            "original": name,
            "corrected": match,
            "status": "corrected",
            "confidence": round(ratio, 2),
        }

    # 매칭 없음
    return {"original": name, "corrected": name, "status": "unknown", "confidence": 0.0}


def correct_names_batch(names: list[str], members: list[str] | None = None, cutoff: float = 0.5) -> list[dict]:
    """여러 이름을 일괄 교정."""
    if members is None:
        members = load_members()
    return [correct_name(name, members, cutoff) for name in names]


def add_member(name: str, filepath: str = MEMBERS_FILE) -> bool:
    """신규 교인을 명부에 추가."""
    members = load_members(filepath)
    if name in members:
        return False
    members.append(name)
    members.sort()
    with open(filepath, "w", encoding="utf-8") as f:
        for m in members:
            f.write(m + "\n")
    return True


def main():
    """CLI: JSON 입력을 받아 교정 결과를 JSON으로 출력.

    Usage:
        echo '{"names": ["천인성", "정완구"]}' | python correct_names.py
        python correct_names.py --add "새교인이름"
    """
    if len(sys.argv) > 1 and sys.argv[1] == "--add":
        name = sys.argv[2]
        added = add_member(name)
        print(json.dumps({"added": added, "name": name}, ensure_ascii=False))
        return

    input_data = json.loads(sys.stdin.read())
    names = input_data.get("names", [])
    cutoff = input_data.get("cutoff", 0.5)
    members = load_members()
    results = correct_names_batch(names, members, cutoff)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
