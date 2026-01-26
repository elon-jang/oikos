"""헌금 전표 Excel 처리 스크립트.

Functions:
    create_template(date_str) — 샘플 xlsx 복사 → 날짜 세팅 → YYYYMMDD.xlsx 생성
    write_data(date_str, data_json) — JSON 데이터를 Excel에 입력
    verify(date_str) — 입력된 데이터 읽어서 카테고리별 합계 출력
"""

import json
import os
import shutil
import sys
from datetime import datetime

import openpyxl

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
TEMPLATE_FILE = os.path.join(BASE_DIR, "2026헌금_업로드샘플.xlsx")

# Import config
sys.path.insert(0, SCRIPT_DIR)
from offering_config import CATEGORIES, CATEGORY_ORDER


def _parse_date(date_str: str) -> datetime:
    """YYYYMMDD 문자열을 datetime으로 변환."""
    return datetime.strptime(date_str, "%Y%m%d")


def _output_path(date_str: str) -> str:
    """날짜에 해당하는 Excel 파일 경로."""
    return os.path.join(BASE_DIR, f"{date_str}.xlsx")


def create_template(date_str: str) -> str:
    """샘플 xlsx를 복사하고 날짜를 세팅하여 새 파일 생성.

    Returns:
        생성된 파일 경로
    """
    output_path = _output_path(date_str)
    target_date = _parse_date(date_str)

    # 이미 파일이 있으면 백업
    if os.path.exists(output_path):
        backup_path = output_path.replace(".xlsx", "_backup.xlsx")
        shutil.copy2(output_path, backup_path)
        print(f"기존 파일 백업: {backup_path}")

    # 템플릿 복사
    shutil.copy2(TEMPLATE_FILE, output_path)

    # 날짜 세팅
    wb = openpyxl.load_workbook(output_path)
    ws = wb.active

    for row_num in range(4, 96):  # rows 4-95
        cell_a = ws.cell(row=row_num, column=1)  # Column A: 일자
        cell_a.value = target_date

    wb.save(output_path)
    print(f"템플릿 생성 완료: {output_path}")
    return output_path


def write_data(date_str: str, data_json: str) -> str:
    """JSON 데이터를 Excel에 입력.

    Args:
        date_str: YYYYMMDD 형식 날짜
        data_json: 카테고리별 데이터 JSON 문자열
            {
                "십일조": [{"name": "최정호", "amount": 578000}, ...],
                "장년부주일": [{"name": "장년부", "amount": 242000}],
                ...
            }

    Returns:
        처리 결과 메시지
    """
    output_path = _output_path(date_str)
    data = json.loads(data_json) if isinstance(data_json, str) else data_json

    if not os.path.exists(output_path):
        create_template(date_str)

    wb = openpyxl.load_workbook(output_path)
    ws = wb.active

    warnings = []
    total_entries = 0

    for category, entries in data.items():
        if category not in CATEGORIES:
            warnings.append(f"⚠ 알 수 없는 카테고리: {category}")
            continue

        config = CATEGORIES[category]
        start_row = config["start"]
        slots = config["slots"]

        if len(entries) > slots:
            warnings.append(
                f"⚠ {category}: {len(entries)}건 > {slots}슬롯 (초과 {len(entries) - slots}건 누락됨)"
            )

        for i, entry in enumerate(entries[:slots]):
            row_num = start_row + i
            name = entry.get("name", "")
            amount = entry.get("amount", 0)

            ws.cell(row=row_num, column=5).value = name     # Column E: 이름
            ws.cell(row=row_num, column=7).value = amount    # Column G: 금액
            total_entries += 1

    wb.save(output_path)

    result = f"입력 완료: {total_entries}건 → {output_path}"
    if warnings:
        result += "\n" + "\n".join(warnings)
    print(result)
    return result


def verify(date_str: str) -> str:
    """입력된 데이터를 읽어서 카테고리별 합계 출력.

    Returns:
        검증 결과 JSON 문자열
    """
    output_path = _output_path(date_str)
    if not os.path.exists(output_path):
        return json.dumps({"error": f"파일 없음: {output_path}"}, ensure_ascii=False)

    wb = openpyxl.load_workbook(output_path)
    ws = wb.active

    result = {}
    grand_total = 0

    for category in CATEGORY_ORDER:
        config = CATEGORIES[category]
        start_row = config["start"]
        end_row = config["end"]

        entries = []
        cat_total = 0

        for row_num in range(start_row, end_row + 1):
            name = ws.cell(row=row_num, column=5).value    # Column E
            amount = ws.cell(row=row_num, column=7).value  # Column G

            if name and amount:
                entries.append({"name": name, "amount": amount})
                cat_total += amount

        if entries:
            result[category] = {
                "entries": entries,
                "count": len(entries),
                "total": cat_total,
            }
            grand_total += cat_total

    result["_summary"] = {
        "grand_total": grand_total,
        "categories_with_data": len([k for k in result if not k.startswith("_")]),
    }

    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(output)
    return output


def main():
    """CLI 인터페이스.

    Usage:
        python process_offering.py create 20260125
        python process_offering.py write 20260125 '{"십일조": [...]}'
        python process_offering.py verify 20260125
    """
    if len(sys.argv) < 3:
        print("Usage: python process_offering.py <command> <date> [data_json]")
        print("Commands: create, write, verify")
        sys.exit(1)

    command = sys.argv[1]
    date_str = sys.argv[2]

    if command == "create":
        create_template(date_str)
    elif command == "write":
        if len(sys.argv) < 4:
            # Read JSON from stdin
            data_json = sys.stdin.read()
        else:
            data_json = sys.argv[3]
        write_data(date_str, data_json)
    elif command == "verify":
        verify(date_str)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
