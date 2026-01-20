"""
영수증 생성 도구

개인정보 보호를 위해 응답에는 이름과 금액을 최소화합니다.
"""

import os
import re
import glob
from datetime import datetime
import pandas as pd
from docxtpl import DocxTemplate


# 필수 컬럼
REQUIRED_COLUMNS = ["이름", "1월", "2월", "3월", "4월", "5월", "6월",
                    "7월", "8월", "9월", "10월", "11월", "12월", "연간 총합"]

# 기본 설정
DEFAULT_TEMPLATE = "donation_receipt_template.docx"
DEFAULT_OUTPUT_DIR = "receipts"
RECEIPT_PREFIX = ""


def find_latest_data_file(data_dir: str):
    """가장 최신 연도의 데이터 파일 찾기"""
    pattern = os.path.join(data_dir, "*_income_summary.xlsx")
    files = glob.glob(pattern)
    if not files:
        return None, None

    year_files = []
    for f in files:
        basename = os.path.basename(f)
        match = re.match(r"(\d{4})_income_summary\.xlsx", basename)
        if match:
            year_files.append((int(match.group(1)), f))

    if not year_files:
        return None, None

    year_files.sort(reverse=True)
    return year_files[0][1], year_files[0][0]


def extract_year_from_filename(filename: str):
    """파일명에서 연도 추출"""
    basename = os.path.basename(filename)
    match = re.match(r"(\d{4})_income", basename)
    if match:
        return int(match.group(1))
    return None


def get_issue_year(data_year: int):
    """데이터 연도에서 발급 연도 계산 (다음해 2자리)"""
    return (data_year + 1) % 100


def format_amount(amount):
    """금액을 천 단위 콤마 포맷으로 변환"""
    if pd.isna(amount) or amount == 0:
        return ""
    return f"{int(amount):,}"


def load_data(file_path: str):
    """Excel 파일에서 데이터 로드 및 이름 분리"""
    df = pd.read_excel(file_path)

    # 마지막 행(합계)은 제외
    df = df[df["이름"] != "합계"].copy()

    # NaN을 0으로 처리
    month_cols = [f"{i}월" for i in range(1, 13)]
    for col in month_cols + ["연간 총합"]:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)

    # 쉼표로 구분된 이름 분리하여 확장
    expanded_rows = []
    for _, row in df.iterrows():
        name = row["이름"]
        if "," in str(name):
            names = [n.strip() for n in str(name).split(",")]
            for individual_name in names:
                new_row = row.copy()
                new_row["이름"] = individual_name
                expanded_rows.append(new_row)
        else:
            expanded_rows.append(row)

    result_df = pd.DataFrame(expanded_rows)
    result_df = result_df.sort_values("이름").reset_index(drop=True)

    return result_df


def get_ledger_path(data_dir: str, issue_year: int):
    """발행대장 파일 경로 반환"""
    return os.path.join(data_dir, f"발행대장_{2000 + issue_year}.xlsx")


def load_or_create_ledger(ledger_path: str):
    """발행대장 로드 또는 생성"""
    if os.path.exists(ledger_path):
        return pd.read_excel(ledger_path)
    else:
        return pd.DataFrame(columns=["발급번호", "이름", "연간총합", "발행일시", "파일경로", "비고"])


def save_ledger(df, ledger_path: str):
    """발행대장 저장"""
    df.to_excel(ledger_path, index=False)


def add_to_ledger(ledger_df, receipt_no, name, total, file_path, note=""):
    """발행대장에 기록 추가"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 기존 기록 확인 (동일 발급번호)
    existing = ledger_df[ledger_df["발급번호"] == receipt_no]
    if not existing.empty:
        note = "재발행"

    new_row = pd.DataFrame([{
        "발급번호": receipt_no,
        "이름": name,
        "연간총합": total,
        "발행일시": now,
        "파일경로": file_path,
        "비고": note
    }])

    return pd.concat([ledger_df, new_row], ignore_index=True)


def create_receipt_file(template_path, name, monthly_amounts, total_amount, receipt_no, output_path):
    """템플릿 기반 DOCX 영수증 생성"""
    template = DocxTemplate(template_path)

    context = {
        "receipt_no": receipt_no,
        "name": name,
        "month_1": format_amount(monthly_amounts.get("1월", 0)),
        "month_2": format_amount(monthly_amounts.get("2월", 0)),
        "month_3": format_amount(monthly_amounts.get("3월", 0)),
        "month_4": format_amount(monthly_amounts.get("4월", 0)),
        "month_5": format_amount(monthly_amounts.get("5월", 0)),
        "month_6": format_amount(monthly_amounts.get("6월", 0)),
        "month_7": format_amount(monthly_amounts.get("7월", 0)),
        "month_8": format_amount(monthly_amounts.get("8월", 0)),
        "month_9": format_amount(monthly_amounts.get("9월", 0)),
        "month_10": format_amount(monthly_amounts.get("10월", 0)),
        "month_11": format_amount(monthly_amounts.get("11월", 0)),
        "month_12": format_amount(monthly_amounts.get("12월", 0)),
        "total": format_amount(total_amount),
    }

    template.render(context)
    template.save(output_path)


# =============================================================================
# MCP 도구 함수들
# =============================================================================

def list_recipients(data_dir: str, data_file: str = None) -> dict:
    """
    대상자 목록 조회 (개인정보 보호)

    Returns:
        총 인원수와 총 금액만 반환 (이름 목록 미포함)
    """
    try:
        # 데이터 파일 결정
        if data_file:
            file_path = os.path.join(data_dir, data_file) if not os.path.isabs(data_file) else data_file
            data_year = extract_year_from_filename(file_path)
        else:
            file_path, data_year = find_latest_data_file(data_dir)

        if not file_path or not os.path.exists(file_path):
            return {
                "status": "error",
                "message": "데이터 파일을 찾을 수 없습니다. YYYY_income_summary.xlsx 파일이 필요합니다."
            }

        # 데이터 로드
        df = load_data(file_path)
        total_count = len(df)
        total_amount = df["연간 총합"].sum()
        issue_year = get_issue_year(data_year) if data_year else 26

        return {
            "status": "success",
            "count": total_count,
            "total_amount": f"{int(total_amount):,}원",
            "data_file": os.path.basename(file_path),
            "issue_year": f"20{issue_year}",
            "message": f"총 {total_count}명의 대상자가 있습니다. "
                       f"상세 목록은 {os.path.basename(file_path)} 파일을 확인하세요."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"목록 조회 실패: {str(e)}"
        }


def generate_receipt(
    data_dir: str,
    name: str,
    data_file: str = None,
    template_file: str = None
) -> dict:
    """
    특정 사람의 영수증 생성

    Returns:
        생성 결과 (금액 정보 미포함)
    """
    try:
        # 데이터 파일 결정
        if data_file:
            file_path = os.path.join(data_dir, data_file) if not os.path.isabs(data_file) else data_file
            data_year = extract_year_from_filename(file_path)
        else:
            file_path, data_year = find_latest_data_file(data_dir)

        if not file_path or not os.path.exists(file_path):
            return {
                "status": "error",
                "message": "데이터 파일을 찾을 수 없습니다."
            }

        # 템플릿 파일 결정
        if template_file:
            tpl_path = os.path.join(data_dir, template_file) if not os.path.isabs(template_file) else template_file
        else:
            tpl_path = os.path.join(data_dir, DEFAULT_TEMPLATE)

        if not os.path.exists(tpl_path):
            return {
                "status": "error",
                "message": f"템플릿 파일이 없습니다: {os.path.basename(tpl_path)}"
            }

        # 데이터 로드
        df = load_data(file_path)
        issue_year = get_issue_year(data_year) if data_year else 26

        # 대상자 찾기
        target = df[df["이름"] == name]
        if target.empty:
            return {
                "status": "error",
                "message": f"'{name}'을(를) 찾을 수 없습니다. 이름을 정확히 입력했는지 확인하세요."
            }

        row = target.iloc[0]

        # 발급번호 생성 (전체 목록 기준)
        receipt_no_map = {
            r["이름"]: f"{RECEIPT_PREFIX}{issue_year}-{idx+1:03d}"
            for idx, r in df.iterrows()
        }
        receipt_no = receipt_no_map.get(name, f"{RECEIPT_PREFIX}{issue_year}-000")

        # 월별 금액
        month_cols = [f"{i}월" for i in range(1, 13)]
        monthly_amounts = {col: row[col] for col in month_cols}
        total_amount = row["연간 총합"]

        # 출력 경로
        output_dir = os.path.join(data_dir, DEFAULT_OUTPUT_DIR)
        os.makedirs(output_dir, exist_ok=True)
        safe_name = name.replace("/", "_").replace("\\", "_")
        output_path = os.path.join(output_dir, f"기부금영수증_{safe_name}.docx")

        # 영수증 생성
        create_receipt_file(tpl_path, name, monthly_amounts, total_amount, receipt_no, output_path)

        # 발행대장 기록
        ledger_path = get_ledger_path(data_dir, issue_year)
        ledger_df = load_or_create_ledger(ledger_path)
        ledger_df = add_to_ledger(ledger_df, receipt_no, name, total_amount, output_path)
        save_ledger(ledger_df, ledger_path)

        return {
            "status": "success",
            "receipt_no": receipt_no,
            "file_path": output_path,
            "ledger_path": ledger_path,
            "message": f"영수증이 생성되었습니다. 파일: {output_path}"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"영수증 생성 실패: {str(e)}"
        }


def generate_all_receipts(
    data_dir: str,
    data_file: str = None,
    template_file: str = None,
    confirm: bool = False
) -> dict:
    """
    전체 영수증 생성

    confirm=False: 미리보기 (생성 안 함)
    confirm=True: 실제 생성
    """
    try:
        # 데이터 파일 결정
        if data_file:
            file_path = os.path.join(data_dir, data_file) if not os.path.isabs(data_file) else data_file
            data_year = extract_year_from_filename(file_path)
        else:
            file_path, data_year = find_latest_data_file(data_dir)

        if not file_path or not os.path.exists(file_path):
            return {
                "status": "error",
                "message": "데이터 파일을 찾을 수 없습니다."
            }

        # 데이터 로드
        df = load_data(file_path)
        total_count = len(df)
        total_amount = df["연간 총합"].sum()
        issue_year = get_issue_year(data_year) if data_year else 26

        # 미리보기 모드
        if not confirm:
            return {
                "status": "preview",
                "count": total_count,
                "total_amount": f"{int(total_amount):,}원",
                "data_file": os.path.basename(file_path),
                "issue_year": f"20{issue_year}",
                "message": f"{total_count}명의 영수증을 생성합니다. "
                           f"계속하려면 confirm=True로 다시 호출하세요."
            }

        # 템플릿 파일 확인
        if template_file:
            tpl_path = os.path.join(data_dir, template_file) if not os.path.isabs(template_file) else template_file
        else:
            tpl_path = os.path.join(data_dir, DEFAULT_TEMPLATE)

        if not os.path.exists(tpl_path):
            return {
                "status": "error",
                "message": f"템플릿 파일이 없습니다: {os.path.basename(tpl_path)}"
            }

        # 출력 폴더 생성
        output_dir = os.path.join(data_dir, DEFAULT_OUTPUT_DIR)
        os.makedirs(output_dir, exist_ok=True)

        # 발급번호 매핑
        receipt_no_map = {
            row["이름"]: f"{RECEIPT_PREFIX}{issue_year}-{idx+1:03d}"
            for idx, row in df.iterrows()
        }

        # 발행대장 로드
        ledger_path = get_ledger_path(data_dir, issue_year)
        ledger_df = load_or_create_ledger(ledger_path)

        month_cols = [f"{i}월" for i in range(1, 13)]
        success_count = 0
        failed_count = 0

        for _, row in df.iterrows():
            name = row["이름"]
            receipt_no = receipt_no_map.get(name, f"{RECEIPT_PREFIX}{issue_year}-000")
            monthly_amounts = {col: row[col] for col in month_cols}
            total_amount_row = row["연간 총합"]
            safe_name = name.replace("/", "_").replace("\\", "_")
            output_path = os.path.join(output_dir, f"기부금영수증_{safe_name}.docx")

            try:
                create_receipt_file(tpl_path, name, monthly_amounts, total_amount_row, receipt_no, output_path)
                ledger_df = add_to_ledger(ledger_df, receipt_no, name, total_amount_row, output_path)
                success_count += 1
            except Exception:
                failed_count += 1

        # 발행대장 저장
        save_ledger(ledger_df, ledger_path)

        return {
            "status": "success",
            "generated": success_count,
            "failed": failed_count,
            "output_dir": output_dir,
            "ledger_path": ledger_path,
            "message": f"{success_count}명의 영수증이 생성되었습니다. "
                       f"폴더: {output_dir}"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"전체 생성 실패: {str(e)}"
        }


def preview_receipt(data_dir: str, name: str, data_file: str = None) -> dict:
    """
    영수증 미리보기 (파일 생성 없이)

    Returns:
        영수증 내용 텍스트 형식
    """
    try:
        # 데이터 파일 결정
        if data_file:
            file_path = os.path.join(data_dir, data_file) if not os.path.isabs(data_file) else data_file
            data_year = extract_year_from_filename(file_path)
        else:
            file_path, data_year = find_latest_data_file(data_dir)

        if not file_path or not os.path.exists(file_path):
            return {
                "status": "error",
                "message": "데이터 파일을 찾을 수 없습니다."
            }

        # 데이터 로드
        df = load_data(file_path)
        issue_year = get_issue_year(data_year) if data_year else 26

        # 대상자 찾기
        target = df[df["이름"] == name]
        if target.empty:
            return {
                "status": "error",
                "message": f"'{name}'을(를) 찾을 수 없습니다."
            }

        row = target.iloc[0]

        # 발급번호 생성
        receipt_no_map = {
            r["이름"]: f"{RECEIPT_PREFIX}{issue_year}-{idx+1:03d}"
            for idx, r in df.iterrows()
        }
        receipt_no = receipt_no_map.get(name, f"{RECEIPT_PREFIX}{issue_year}-000")

        # 월별 금액 텍스트 생성
        month_cols = [f"{i}월" for i in range(1, 13)]
        monthly_text = []
        for col in month_cols:
            amount = row[col]
            if amount > 0:
                monthly_text.append(f"  {col}: {format_amount(amount)}원")

        total_amount = row["연간 총합"]

        preview_text = f"""
┌─────────────────────────────────────┐
│        기 부 금 영 수 증             │
├─────────────────────────────────────┤
│ 발급번호: {receipt_no}
│ 성명: {name}
├─────────────────────────────────────┤
│ 기부 내역:
{chr(10).join(monthly_text)}
│ ───────────────────────────────────
│ 합계: {format_amount(total_amount)}원
└─────────────────────────────────────┘
"""

        return {
            "status": "success",
            "receipt_no": receipt_no,
            "preview": preview_text,
            "message": f"미리보기입니다. 실제 생성하려면 generate_receipt('{name}')을 호출하세요."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"미리보기 실패: {str(e)}"
        }
