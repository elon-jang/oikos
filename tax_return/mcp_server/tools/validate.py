"""
데이터 및 템플릿 검증 도구

개인정보 보호를 위해 오류 메시지에 이름을 포함하지 않습니다.
"""

import os
import re
import glob
import pandas as pd
from docxtpl import DocxTemplate


# 필수 컬럼
REQUIRED_COLUMNS = ["이름", "1월", "2월", "3월", "4월", "5월", "6월",
                    "7월", "8월", "9월", "10월", "11월", "12월", "연간 총합"]

# 필수 placeholder
REQUIRED_PLACEHOLDERS = [
    "receipt_no", "name",
    "month_1", "month_2", "month_3", "month_4", "month_5", "month_6",
    "month_7", "month_8", "month_9", "month_10", "month_11", "month_12",
    "total"
]

DEFAULT_TEMPLATE = "donation_receipt_template.docx"


def find_latest_data_file(data_dir: str):
    """가장 최신 연도의 데이터 파일 찾기"""
    pattern = os.path.join(data_dir, "*_income_summary.xlsx")
    files = glob.glob(pattern)
    if not files:
        return None

    year_files = []
    for f in files:
        basename = os.path.basename(f)
        match = re.match(r"(\d{4})_income_summary\.xlsx", basename)
        if match:
            year_files.append((int(match.group(1)), f))

    if not year_files:
        return None

    year_files.sort(reverse=True)
    return year_files[0][1]


def validate_data(data_dir: str, data_file: str = None) -> dict:
    """
    데이터 파일 유효성 검사

    Returns:
        검증 결과 (오류는 행 번호만, 이름 미포함)
    """
    try:
        # 데이터 파일 결정
        if data_file:
            file_path = os.path.join(data_dir, data_file) if not os.path.isabs(data_file) else data_file
        else:
            file_path = find_latest_data_file(data_dir)

        if not file_path or not os.path.exists(file_path):
            return {
                "status": "error",
                "message": "데이터 파일을 찾을 수 없습니다. YYYY_income_summary.xlsx 파일이 필요합니다."
            }

        # 파일 읽기 시도
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            return {
                "status": "error",
                "message": f"파일을 읽을 수 없습니다: {str(e)}"
            }

        errors = []
        warnings = []

        # 1. 필수 컬럼 확인
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            errors.append(f"필수 컬럼 누락: {', '.join(missing_cols)}")

        # 2. 데이터가 있는지 확인
        if len(df) == 0:
            errors.append("데이터가 없습니다 (빈 파일)")

        # 3. 금액 컬럼 검증
        month_cols = [f"{i}월" for i in range(1, 13)] + ["연간 총합"]
        for col in month_cols:
            if col not in df.columns:
                continue

            # 숫자가 아닌 값 확인 (행 번호만 표시)
            for idx, value in df[col].items():
                if pd.notna(value) and not isinstance(value, (int, float)):
                    warnings.append(f"행 {idx+2}: '{col}' 컬럼에 숫자가 아닌 값")

                # 음수 값 확인
                if isinstance(value, (int, float)) and value < 0:
                    warnings.append(f"행 {idx+2}: '{col}' 컬럼에 음수 값")

        # 4. 월별 합계 검증 (연간 총합과 비교)
        if all(col in df.columns for col in month_cols):
            month_only_cols = [f"{i}월" for i in range(1, 13)]
            for idx, row in df.iterrows():
                monthly_sum = sum(row[col] if pd.notna(row[col]) and isinstance(row[col], (int, float)) else 0
                                  for col in month_only_cols)
                annual_total = row["연간 총합"] if pd.notna(row["연간 총합"]) else 0

                if abs(monthly_sum - annual_total) > 1:  # 1원 오차 허용
                    warnings.append(f"행 {idx+2}: 월별 합계({int(monthly_sum)})와 연간 총합({int(annual_total)})이 다름")

        # 5. 중복 이름 확인 (개수만)
        if "이름" in df.columns:
            # 쉼표로 분리된 이름 확장
            all_names = []
            for name in df["이름"].dropna():
                if "," in str(name):
                    all_names.extend([n.strip() for n in str(name).split(",")])
                else:
                    all_names.append(str(name))

            duplicates = [name for name in set(all_names) if all_names.count(name) > 1]
            if duplicates:
                warnings.append(f"중복된 이름 {len(duplicates)}건 (상세 내용은 파일에서 확인)")

        # 결과 반환
        if errors:
            return {
                "status": "error",
                "file": os.path.basename(file_path),
                "errors": errors,
                "warnings": warnings,
                "message": f"데이터 파일에 {len(errors)}개 오류가 있습니다."
            }
        elif warnings:
            return {
                "status": "warning",
                "file": os.path.basename(file_path),
                "row_count": len(df),
                "warnings": warnings,
                "message": f"데이터 파일에 {len(warnings)}개 경고가 있습니다. 확인이 필요합니다."
            }
        else:
            return {
                "status": "success",
                "file": os.path.basename(file_path),
                "row_count": len(df),
                "message": "데이터 파일이 유효합니다."
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"검증 실패: {str(e)}"
        }


def validate_template(data_dir: str, template_file: str = None) -> dict:
    """
    템플릿 파일 유효성 검사

    Returns:
        검증 결과 (누락된 placeholder 목록)
    """
    try:
        # 템플릿 파일 결정
        if template_file:
            file_path = os.path.join(data_dir, template_file) if not os.path.isabs(template_file) else template_file
        else:
            file_path = os.path.join(data_dir, DEFAULT_TEMPLATE)

        if not os.path.exists(file_path):
            return {
                "status": "error",
                "message": f"템플릿 파일이 없습니다: {os.path.basename(file_path)}"
            }

        # 템플릿 로드 및 placeholder 추출
        try:
            template = DocxTemplate(file_path)
            # docxtpl의 undeclared_template_variables를 사용하여 placeholder 확인
            # 실제로는 렌더링 시도를 해봐야 알 수 있음
        except Exception as e:
            return {
                "status": "error",
                "message": f"템플릿 파일을 읽을 수 없습니다: {str(e)}"
            }

        # 테스트 렌더링으로 placeholder 확인
        test_context = {p: "TEST" for p in REQUIRED_PLACEHOLDERS}

        try:
            template.render(test_context)
        except Exception as e:
            error_msg = str(e)
            # Jinja2 에러에서 누락된 변수 추출 시도
            if "undefined" in error_msg.lower():
                return {
                    "status": "warning",
                    "file": os.path.basename(file_path),
                    "message": f"템플릿에 정의되지 않은 변수가 있을 수 있습니다: {error_msg}"
                }

        return {
            "status": "success",
            "file": os.path.basename(file_path),
            "required_placeholders": REQUIRED_PLACEHOLDERS,
            "message": "템플릿 파일이 유효합니다. 필수 placeholder가 모두 포함되어 있는지 직접 확인하세요."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"템플릿 검증 실패: {str(e)}"
        }
