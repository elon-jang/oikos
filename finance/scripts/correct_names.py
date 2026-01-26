"""교인 명부 기반 이름 교정 모듈 (자모 분해 fuzzy matching)."""

import difflib
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MEMBERS_FILE = os.path.join(SCRIPT_DIR, "members.txt")

# 한글 자모 테이블
_CHOSUNG = list("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ")
_JUNGSUNG = list("ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ")
_JONGSUNG = [""] + list("ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ")


def decompose_hangul(text: str) -> list[str]:
    """한글 문자열을 초성/중성/종성 자모 리스트로 분해.

    예: '권언성' → ['ㄱ','ㅝ','ㄴ','ㅇ','ㅓ','ㄴ','ㅅ','ㅓ','ㅇ']
    """
    result = []
    for ch in text:
        code = ord(ch)
        if 0xAC00 <= code <= 0xD7A3:
            offset = code - 0xAC00
            cho = offset // (21 * 28)
            jung = (offset % (21 * 28)) // 28
            jong = offset % 28
            result.append(_CHOSUNG[cho])
            result.append(_JUNGSUNG[jung])
            if jong > 0:
                result.append(_JONGSUNG[jong])
        else:
            result.append(ch)
    return result


def jamo_similarity(a: str, b: str) -> float:
    """자모 분해 기반 유사도 (0.0 ~ 1.0).

    한글 글자를 초성/중성/종성으로 분해하여 비교하므로,
    획이 유사한 글자 간의 유사도가 문자 단위 비교보다 정확함.
    예: 정형모 vs 정형호 → 문자:0.67, 자모:0.875
    """
    jamo_a = decompose_hangul(a)
    jamo_b = decompose_hangul(b)
    return difflib.SequenceMatcher(None, jamo_a, jamo_b).ratio()


def load_members(filepath: str = MEMBERS_FILE) -> list[str]:
    """교인 명부 파일에서 이름 목록 로드."""
    with open(filepath, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def correct_name(name: str, members: list[str], cutoff: float = 0.5) -> dict:
    """
    단일 이름을 교인 명부와 대조하여 교정 (자모 분해 기반).

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

    # 자모 분해 기반 fuzzy matching — 전체 멤버에 대해 유사도 계산
    scores = [(m, jamo_similarity(name, m)) for m in members]
    scores.sort(key=lambda x: x[1], reverse=True)
    best_match, best_score = scores[0]

    if best_score >= cutoff:
        return {
            "original": name,
            "corrected": best_match,
            "status": "corrected",
            "confidence": round(best_score, 2),
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
