"""
발행 이력 조회 도구

개인정보 보호를 위해 상세 내역은 로컬 파일 참조를 안내합니다.
"""

import os
import glob
from datetime import datetime
import pandas as pd


def get_ledger_path(data_dir: str, year: int):
    """발행대장 파일 경로 반환"""
    return os.path.join(data_dir, f"발행대장_{year}.xlsx")


def find_latest_ledger(data_dir: str):
    """가장 최신 발행대장 찾기"""
    pattern = os.path.join(data_dir, "발행대장_*.xlsx")
    files = glob.glob(pattern)
    if not files:
        return None, None

    year_files = []
    for f in files:
        basename = os.path.basename(f)
        try:
            year = int(basename.replace("발행대장_", "").replace(".xlsx", ""))
            year_files.append((year, f))
        except ValueError:
            continue

    if not year_files:
        return None, None

    year_files.sort(reverse=True)
    return year_files[0][1], year_files[0][0]


def get_history(data_dir: str, year: int = None) -> dict:
    """
    발행 이력 조회

    Returns:
        총 발행 건수와 요약 정보 (상세 내역 미포함)
    """
    try:
        # 연도 결정
        if year:
            ledger_path = get_ledger_path(data_dir, year)
            if not os.path.exists(ledger_path):
                return {
                    "status": "error",
                    "message": f"{year}년 발행 이력이 없습니다."
                }
        else:
            ledger_path, year = find_latest_ledger(data_dir)
            if not ledger_path:
                return {
                    "status": "info",
                    "message": "발행 이력이 없습니다. 아직 영수증을 발행하지 않았습니다."
                }

        # 발행대장 로드
        df = pd.read_excel(ledger_path)

        if df.empty:
            return {
                "status": "info",
                "year": year,
                "message": f"{year}년 발행 이력이 없습니다."
            }

        # 통계 계산
        total_count = len(df)
        unique_names = df["이름"].nunique()
        reissue_count = len(df[df["비고"] == "재발행"])

        # 최근 발행 일시
        latest_date = df["발행일시"].max() if "발행일시" in df.columns else None

        # 총 금액
        total_amount = df["연간총합"].sum() if "연간총합" in df.columns else 0

        return {
            "status": "success",
            "year": year,
            "total_records": total_count,
            "unique_recipients": unique_names,
            "reissue_count": reissue_count,
            "total_amount": f"{int(total_amount):,}원",
            "latest_date": str(latest_date) if latest_date else None,
            "ledger_path": ledger_path,
            "message": f"{year}년 발행 이력: 총 {total_count}건 ({unique_names}명). "
                       f"상세 내역은 {os.path.basename(ledger_path)} 파일을 확인하세요."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"이력 조회 실패: {str(e)}"
        }


def get_person_history(data_dir: str, name: str, year: int = None) -> dict:
    """
    특정 사람의 발행 이력 조회

    Returns:
        발행 여부와 횟수 (금액 정보 미포함)
    """
    try:
        # 연도 결정
        if year:
            ledger_path = get_ledger_path(data_dir, year)
            if not os.path.exists(ledger_path):
                return {
                    "status": "info",
                    "message": f"{year}년 발행 이력이 없습니다."
                }
        else:
            ledger_path, year = find_latest_ledger(data_dir)
            if not ledger_path:
                return {
                    "status": "info",
                    "message": "발행 이력이 없습니다."
                }

        # 발행대장 로드
        df = pd.read_excel(ledger_path)

        # 해당 이름 필터링
        person_records = df[df["이름"] == name]

        if person_records.empty:
            return {
                "status": "info",
                "year": year,
                "name": name,
                "issued": False,
                "message": f"'{name}'의 {year}년 발행 이력이 없습니다."
            }

        # 발행 횟수 계산
        issue_count = len(person_records)
        reissue_count = len(person_records[person_records["비고"] == "재발행"])
        latest_date = person_records["발행일시"].max()
        receipt_no = person_records.iloc[-1]["발급번호"]

        return {
            "status": "success",
            "year": year,
            "name": name,
            "issued": True,
            "issue_count": issue_count,
            "reissue_count": reissue_count,
            "latest_receipt_no": receipt_no,
            "latest_date": str(latest_date),
            "message": f"'{name}'의 {year}년 영수증이 발행되었습니다. "
                       f"(발급번호: {receipt_no}, 발행일: {latest_date})"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"이력 조회 실패: {str(e)}"
        }
