#!/usr/bin/env python3
"""
기부금 영수증 자동 발행 스크립트 (템플릿 기반)
- donation_receipt_template.docx 템플릿 사용
- YYYY_income_summary.xlsx 파일에서 데이터 읽기
- 쉼표로 구분된 부부 이름은 각각 별도 영수증 발행
- 발행 이력을 발행대장에 자동 기록

사용법:
    python generate_receipts.py                     # 전체 발행 (자동 연도 감지)
    python generate_receipts.py -n 홍길동            # 한 사람만
    python generate_receipts.py -n 홍길동,김철수     # 여러 명 (쉼표 구분)
    python generate_receipts.py --list              # 대상자 목록 확인
    python generate_receipts.py --year 2025         # 연도 수동 지정
    python generate_receipts.py --data 2024_income_summary.xlsx  # 데이터 파일 지정
    python generate_receipts.py --history           # 발행 이력 조회
    python generate_receipts.py --history -n 강신애  # 특정인 이력 조회
    python generate_receipts.py --pdf               # PDF로 변환
"""

import argparse
import os
import re
import glob
import sys
import subprocess
from datetime import datetime
import pandas as pd
from docxtpl import DocxTemplate

# 설정 기본값
DEFAULT_CONFIG = {
    "files": {
        "template": "donation_receipt_template.docx",
        "output_dir": "receipts"
    },
    "receipt": {
        "prefix": ""
    }
}

REQUIRED_COLUMNS = ["이름", "1월", "2월", "3월", "4월", "5월", "6월",
                    "7월", "8월", "9월", "10월", "11월", "12월", "연간 총합"]


def load_config():
    """설정 파일 로드"""
    config = DEFAULT_CONFIG.copy()

    # config.yaml 파일이 있으면 로드
    if os.path.exists("config.yaml"):
        try:
            import yaml
            with open("config.yaml", "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    # 중첩 딕셔너리 병합
                    for key, value in user_config.items():
                        if isinstance(value, dict) and key in config:
                            config[key].update(value)
                        else:
                            config[key] = value
        except ImportError:
            pass  # yaml 모듈 없으면 기본값 사용
        except Exception as e:
            print(f"⚠️  config.yaml 로드 실패: {e}")

    return config


# 전역 설정 로드
CONFIG = load_config()
TEMPLATE_FILE = CONFIG["files"]["template"]
OUTPUT_DIR = CONFIG["files"]["output_dir"]
RECEIPT_PREFIX = CONFIG["receipt"].get("prefix", "")


def validate_template(template_file):
    """템플릿 파일 존재 확인"""
    if not os.path.exists(template_file):
        print(f"❌ 오류: 템플릿 파일이 없습니다: {template_file}")
        print("   donation_receipt_template.docx 파일을 프로젝트 폴더에 추가하세요.")
        print("   또는 --template 옵션으로 템플릿 파일을 지정하세요.")
        return False
    return True


def validate_data_file(file_path):
    """데이터 파일 유효성 검사"""
    if not os.path.exists(file_path):
        print(f"❌ 오류: 데이터 파일이 없습니다: {file_path}")
        return False

    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"❌ 오류: 데이터 파일을 읽을 수 없습니다: {file_path}")
        print(f"   원인: {e}")
        return False

    # 필수 컬럼 확인
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        print(f"❌ 오류: 필수 컬럼이 없습니다: {', '.join(missing_cols)}")
        print(f"   필수 컬럼: {', '.join(REQUIRED_COLUMNS)}")
        return False

    # 금액 데이터 검증
    month_cols = [f"{i}월" for i in range(1, 13)] + ["연간 총합"]
    for col in month_cols:
        if col in df.columns:
            # 숫자가 아닌 값 확인 (NaN 제외)
            non_numeric = df[col].dropna().apply(lambda x: not isinstance(x, (int, float)))
            if non_numeric.any():
                print(f"⚠️  경고: '{col}' 컬럼에 숫자가 아닌 값이 있습니다.")

            # 음수 값 확인
            negative = df[col].dropna().apply(lambda x: isinstance(x, (int, float)) and x < 0)
            if negative.any():
                print(f"⚠️  경고: '{col}' 컬럼에 음수 값이 있습니다.")

    return True


def convert_to_pdf(docx_path):
    """DOCX를 PDF로 변환"""
    pdf_path = docx_path.replace(".docx", ".pdf")

    # 방법 1: docx2pdf 라이브러리 시도
    try:
        from docx2pdf import convert
        convert(docx_path, pdf_path)
        return pdf_path
    except ImportError:
        pass
    except Exception:
        pass

    # 방법 2: LibreOffice 사용 (macOS/Linux)
    try:
        result = subprocess.run([
            "soffice", "--headless", "--convert-to", "pdf",
            "--outdir", os.path.dirname(docx_path) or ".",
            docx_path
        ], capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and os.path.exists(pdf_path):
            return pdf_path
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 방법 3: macOS에서 textutil + cupsfilter (제한적)
    # 실패 시 None 반환
    return None


def find_latest_data_file():
    """가장 최신 연도의 데이터 파일 찾기"""
    pattern = "*_income_summary.xlsx"
    files = glob.glob(pattern)
    if not files:
        return None, None

    # 파일명에서 연도 추출하여 정렬
    year_files = []
    for f in files:
        match = re.match(r"(\d{4})_income_summary\.xlsx", f)
        if match:
            year_files.append((int(match.group(1)), f))

    if not year_files:
        return None, None

    year_files.sort(reverse=True)
    return year_files[0][1], year_files[0][0]


def extract_year_from_filename(filename):
    """파일명에서 연도 추출"""
    match = re.match(r"(\d{4})_income", filename)
    if match:
        return int(match.group(1))
    return None


def get_issue_year(data_year):
    """데이터 연도에서 발급 연도 계산 (다음해 2자리)"""
    return (data_year + 1) % 100


def format_amount(amount):
    """금액을 천 단위 콤마 포맷으로 변환"""
    if pd.isna(amount) or amount == 0:
        return ""
    return f"{int(amount):,}"


def get_ledger_path(issue_year):
    """발행대장 파일 경로 반환"""
    return f"발행대장_{2000 + issue_year}.xlsx"


def load_or_create_ledger(ledger_path):
    """발행대장 로드 또는 생성"""
    if os.path.exists(ledger_path):
        return pd.read_excel(ledger_path)
    else:
        return pd.DataFrame(columns=["발급번호", "이름", "연간총합", "발행일시", "파일경로", "비고"])


def save_ledger(df, ledger_path):
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


def show_history(ledger_path, filter_name=None):
    """발행 이력 조회"""
    if not os.path.exists(ledger_path):
        print("발행 이력이 없습니다.")
        return

    df = pd.read_excel(ledger_path)

    if filter_name:
        df = df[df["이름"] == filter_name]
        if df.empty:
            print(f"'{filter_name}'의 발행 이력이 없습니다.")
            return
        print(f"'{filter_name}' 발행 이력:")
    else:
        print(f"전체 발행 이력 ({len(df)}건):")

    for _, row in df.iterrows():
        note = f" ({row['비고']})" if pd.notna(row['비고']) and row['비고'] else ""
        print(f"  {row['발급번호']} | {row['이름']} | {format_amount(row['연간총합'])}원 | {row['발행일시']}{note}")


def load_data(file_path):
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
        if "," in name:
            names = [n.strip() for n in name.split(",")]
            for individual_name in names:
                new_row = row.copy()
                new_row["이름"] = individual_name
                expanded_rows.append(new_row)
        else:
            expanded_rows.append(row)

    result_df = pd.DataFrame(expanded_rows)
    result_df = result_df.sort_values("이름").reset_index(drop=True)

    return result_df


def create_receipt(template_path, name, monthly_amounts, total_amount, receipt_no, output_path):
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


def main():
    parser = argparse.ArgumentParser(description="기부금 영수증 자동 발행")
    parser.add_argument("-n", "--name", dest="names",
                        help="발행 대상 이름 (여러 명: 쉼표로 구분)")
    parser.add_argument("--list", action="store_true",
                        help="대상자 목록만 출력")
    parser.add_argument("--year", type=int,
                        help="데이터 연도 수동 지정 (예: 2025)")
    parser.add_argument("--data",
                        help="데이터 파일 경로 (예: 2024_income_summary.xlsx)")
    parser.add_argument("--template",
                        help="템플릿 파일 경로 (예: my_template.docx)")
    parser.add_argument("--history", action="store_true",
                        help="발행 이력 조회")
    parser.add_argument("--pdf", action="store_true",
                        help="PDF로 변환 (DOCX도 유지)")
    args = parser.parse_args()

    # 템플릿 파일 결정
    template_file = args.template if args.template else TEMPLATE_FILE

    # 템플릿 파일 확인 (history 모드가 아닐 때만)
    if not args.history and not args.list:
        if not validate_template(template_file):
            sys.exit(1)

    # 데이터 파일 결정
    if args.data:
        data_file = args.data
        data_year = extract_year_from_filename(data_file)
    elif args.year:
        data_file = f"{args.year}_income_summary.xlsx"
        data_year = args.year
    else:
        data_file, data_year = find_latest_data_file()
        if not data_file:
            print("❌ 오류: 데이터 파일을 찾을 수 없습니다.")
            print("   YYYY_income_summary.xlsx 형식의 파일이 필요합니다.")
            print("   또는 --data 옵션으로 파일을 지정하세요.")
            sys.exit(1)

    # 데이터 파일 유효성 검사
    if not validate_data_file(data_file):
        sys.exit(1)

    # 발급 연도 계산
    if data_year:
        issue_year = get_issue_year(data_year)
    else:
        issue_year = 26  # 기본값

    ledger_path = get_ledger_path(issue_year)

    # 발행 이력 조회
    if args.history:
        filter_name = args.names.split(",")[0].strip() if args.names else None
        show_history(ledger_path, filter_name)
        return

    # 데이터 로드
    df = load_data(data_file)
    print(f"데이터 파일: {data_file} (발급연도: {issue_year})")

    # 목록만 출력
    if args.list:
        print(f"총 {len(df)}명:")
        for idx, row in df.iterrows():
            print(f"  {idx+1:3d}. {row['이름']} ({format_amount(row['연간 총합'])}원)")
        return

    # 대상 필터링
    if args.names:
        # 쉼표로 구분된 이름 파싱
        target_names = [n.strip() for n in args.names.split(",")]
        df_filtered = df[df["이름"].isin(target_names)]

        # 찾지 못한 이름 확인
        found_names = set(df_filtered["이름"].tolist())
        not_found = set(target_names) - found_names
        if not_found:
            print(f"⚠️  찾을 수 없는 이름: {', '.join(not_found)}")

        if df_filtered.empty:
            print("발행 대상이 없습니다.")
            return

        df = df_filtered
        print(f"선택된 대상: {len(df)}명")
    else:
        print(f"전체 대상: {len(df)}명")

    # 출력 폴더 생성
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 전체 데이터에서 발급번호 매핑 (일관성 유지)
    df_all = load_data(data_file)
    receipt_no_map = {row["이름"]: f"{RECEIPT_PREFIX}{issue_year}-{idx+1:03d}" for idx, row in df_all.iterrows()}

    # 발행대장 로드
    ledger_df = load_or_create_ledger(ledger_path)

    month_cols = [f"{i}월" for i in range(1, 13)]
    count = 0
    pdf_count = 0
    pdf_failed = False

    for _, row in df.iterrows():
        name = row["이름"]
        receipt_no = receipt_no_map.get(name, f"{RECEIPT_PREFIX}{issue_year}-000")
        monthly_amounts = {col: row[col] for col in month_cols}
        total_amount = row["연간 총합"]
        safe_name = name.replace("/", "_").replace("\\", "_")

        output_path = os.path.join(OUTPUT_DIR, f"기부금영수증_{safe_name}.docx")

        try:
            create_receipt(template_file, name, monthly_amounts, total_amount, receipt_no, output_path)
        except Exception as e:
            print(f"  ❌ 실패: {name} - {e}")
            continue

        # PDF 변환
        if args.pdf:
            pdf_path = convert_to_pdf(output_path)
            if pdf_path:
                pdf_count += 1
            elif not pdf_failed:
                pdf_failed = True
                print("  ⚠️  PDF 변환 실패: docx2pdf 또는 LibreOffice가 필요합니다.")
                print("     설치: pip install docx2pdf (Word 필요) 또는 brew install libreoffice")

        # 발행대장에 기록
        ledger_df = add_to_ledger(ledger_df, receipt_no, name, total_amount, output_path)

        print(f"  생성: {name} ({receipt_no})")
        count += 1

    # 발행대장 저장
    save_ledger(ledger_df, ledger_path)

    print(f"\n완료! {OUTPUT_DIR}/ 폴더에 {count}개 DOCX 생성됨")
    if args.pdf and pdf_count > 0:
        print(f"       {pdf_count}개 PDF 변환됨")
    print(f"발행대장: {ledger_path}")


if __name__ == "__main__":
    main()
