#!/usr/bin/env python3
"""
MCP 서버 단위 테스트

테스트 실행:
    pytest test_mcp_server.py -v
    pytest test_mcp_server.py -v --tb=short
"""

import os
import tempfile
import shutil
import pytest
import pandas as pd
from pathlib import Path

# MCP 서버 도구들 import
from mcp_server.tools.receipt import (
    list_recipients,
    generate_receipt,
    generate_all_receipts,
    preview_receipt,
    find_latest_data_file,
    extract_year_from_filename,
    get_issue_year,
    format_amount,
    load_data,
)
from mcp_server.tools.validate import (
    validate_data,
    validate_template,
)
from mcp_server.tools.history import (
    get_history,
    get_person_history,
)


# 테스트 데이터 경로
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DATA = os.path.join(TEST_DIR, "sample_income_summary.xlsx")
SAMPLE_TEMPLATE = os.path.join(TEST_DIR, "donation_receipt_template.docx")


class TestHelperFunctions:
    """유틸리티 함수 테스트"""

    def test_extract_year_from_filename(self):
        """파일명에서 연도 추출"""
        assert extract_year_from_filename("2025_income_summary.xlsx") == 2025
        assert extract_year_from_filename("2024_income_summary.xlsx") == 2024
        assert extract_year_from_filename("/path/to/2023_income_summary.xlsx") == 2023
        assert extract_year_from_filename("invalid_file.xlsx") is None

    def test_get_issue_year(self):
        """발급 연도 계산 (데이터 연도 + 1의 2자리)"""
        assert get_issue_year(2025) == 26
        assert get_issue_year(2024) == 25
        assert get_issue_year(2099) == 0  # 2100 % 100 = 0

    def test_format_amount(self):
        """금액 포맷팅"""
        assert format_amount(1000000) == "1,000,000"
        assert format_amount(50000) == "50,000"
        assert format_amount(0) == ""
        assert format_amount(None) == ""
        assert format_amount(float('nan')) == ""

    def test_find_latest_data_file(self):
        """최신 데이터 파일 찾기"""
        file_path, year = find_latest_data_file(TEST_DIR)
        # sample_income_summary.xlsx는 패턴과 맞지 않으므로 None일 수 있음
        # 테스트 디렉토리에 YYYY_income_summary.xlsx 파일이 있다면 찾아야 함
        if file_path:
            assert os.path.exists(file_path)
            assert year is not None


class TestLoadData:
    """데이터 로드 테스트"""

    def test_load_sample_data(self):
        """샘플 데이터 로드"""
        if not os.path.exists(SAMPLE_DATA):
            pytest.skip("샘플 데이터 파일이 없습니다")

        df = load_data(SAMPLE_DATA)
        assert len(df) > 0
        assert "이름" in df.columns
        assert "연간 총합" in df.columns

    def test_load_data_splits_comma_names(self):
        """쉼표로 구분된 이름 분리"""
        if not os.path.exists(SAMPLE_DATA):
            pytest.skip("샘플 데이터 파일이 없습니다")

        df = load_data(SAMPLE_DATA)
        # 부부 이름이 있으면 분리되어야 함
        # 각 이름에 쉼표가 없어야 함
        for name in df["이름"]:
            assert "," not in str(name), f"이름에 쉼표가 있음: {name}"


class TestListRecipients:
    """list_recipients 함수 테스트"""

    def test_list_recipients_with_sample_data(self):
        """샘플 데이터로 대상자 목록 조회"""
        result = list_recipients(TEST_DIR, "sample_income_summary.xlsx")

        assert result["status"] == "success"
        assert "count" in result
        assert result["count"] > 0
        assert "total_amount" in result
        assert "원" in result["total_amount"]

    def test_list_recipients_missing_file(self):
        """존재하지 않는 파일"""
        result = list_recipients(TEST_DIR, "nonexistent.xlsx")
        assert result["status"] == "error"

    def test_list_recipients_privacy(self):
        """개인정보 보호 확인 - 이름 목록 미포함"""
        result = list_recipients(TEST_DIR, "sample_income_summary.xlsx")

        if result["status"] == "success":
            # names 키가 없어야 함 (개인정보 보호)
            assert "names" not in result


class TestPreviewReceipt:
    """preview_receipt 함수 테스트"""

    def test_preview_receipt_success(self):
        """영수증 미리보기"""
        result = preview_receipt(TEST_DIR, "홍길동", "sample_income_summary.xlsx")

        if result["status"] == "error" and "찾을 수 없습니다" in result["message"]:
            pytest.skip("테스트 이름이 샘플 데이터에 없습니다")

        assert result["status"] == "success"
        assert "preview" in result
        assert "receipt_no" in result

    def test_preview_receipt_not_found(self):
        """존재하지 않는 사람"""
        result = preview_receipt(TEST_DIR, "존재하지않는이름", "sample_income_summary.xlsx")
        assert result["status"] == "error"
        assert "찾을 수 없습니다" in result["message"]


class TestGenerateReceipt:
    """generate_receipt 함수 테스트"""

    @pytest.fixture
    def temp_data_dir(self):
        """임시 데이터 디렉토리 생성"""
        temp_dir = tempfile.mkdtemp()
        # 샘플 파일 복사
        if os.path.exists(SAMPLE_DATA):
            shutil.copy(SAMPLE_DATA, os.path.join(temp_dir, "sample_income_summary.xlsx"))
        if os.path.exists(SAMPLE_TEMPLATE):
            shutil.copy(SAMPLE_TEMPLATE, os.path.join(temp_dir, "donation_receipt_template.docx"))
        yield temp_dir
        # 정리
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_generate_receipt_no_template(self, temp_data_dir):
        """템플릿 없이 영수증 생성 시도"""
        # 템플릿 제거
        template_path = os.path.join(temp_data_dir, "donation_receipt_template.docx")
        if os.path.exists(template_path):
            os.remove(template_path)

        result = generate_receipt(temp_data_dir, "홍길동", "sample_income_summary.xlsx")
        assert result["status"] == "error"
        assert "템플릿" in result["message"]

    def test_generate_receipt_not_found(self, temp_data_dir):
        """존재하지 않는 사람"""
        result = generate_receipt(temp_data_dir, "존재하지않는이름", "sample_income_summary.xlsx")
        assert result["status"] == "error"

    @pytest.mark.skipif(
        not os.path.exists(SAMPLE_TEMPLATE),
        reason="템플릿 파일이 없습니다"
    )
    def test_generate_receipt_creates_file(self, temp_data_dir):
        """영수증 파일 생성 확인"""
        # 샘플 데이터에서 첫 번째 이름 찾기
        if not os.path.exists(os.path.join(temp_data_dir, "sample_income_summary.xlsx")):
            pytest.skip("샘플 데이터가 없습니다")

        df = load_data(os.path.join(temp_data_dir, "sample_income_summary.xlsx"))
        if len(df) == 0:
            pytest.skip("샘플 데이터가 비어있습니다")

        first_name = df.iloc[0]["이름"]
        result = generate_receipt(temp_data_dir, first_name, "sample_income_summary.xlsx")

        if result["status"] == "success":
            assert "file_path" in result
            assert os.path.exists(result["file_path"])


class TestGenerateAllReceipts:
    """generate_all_receipts 함수 테스트"""

    def test_preview_mode(self):
        """미리보기 모드 (confirm=False)"""
        result = generate_all_receipts(TEST_DIR, "sample_income_summary.xlsx", confirm=False)

        if result["status"] == "error":
            pytest.skip("샘플 데이터 접근 오류")

        assert result["status"] == "preview"
        assert "count" in result

    @pytest.fixture
    def temp_data_dir(self):
        """임시 데이터 디렉토리 생성"""
        temp_dir = tempfile.mkdtemp()
        if os.path.exists(SAMPLE_DATA):
            shutil.copy(SAMPLE_DATA, os.path.join(temp_dir, "sample_income_summary.xlsx"))
        if os.path.exists(SAMPLE_TEMPLATE):
            shutil.copy(SAMPLE_TEMPLATE, os.path.join(temp_dir, "donation_receipt_template.docx"))
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.skipif(
        not os.path.exists(SAMPLE_TEMPLATE),
        reason="템플릿 파일이 없습니다"
    )
    def test_generate_all_with_confirm(self, temp_data_dir):
        """전체 생성 (confirm=True)"""
        result = generate_all_receipts(temp_data_dir, "sample_income_summary.xlsx", confirm=True)

        if result["status"] == "error":
            pytest.skip(f"생성 오류: {result['message']}")

        assert result["status"] == "success"
        assert "generated" in result
        assert result["generated"] > 0


class TestValidateData:
    """validate_data 함수 테스트"""

    def test_validate_sample_data(self):
        """샘플 데이터 검증"""
        result = validate_data(TEST_DIR, "sample_income_summary.xlsx")

        # 샘플 데이터는 유효해야 함
        assert result["status"] in ["success", "warning"]
        assert "message" in result

    def test_validate_missing_file(self):
        """존재하지 않는 파일"""
        result = validate_data(TEST_DIR, "nonexistent.xlsx")
        assert result["status"] == "error"

    @pytest.fixture
    def invalid_data_file(self):
        """잘못된 데이터 파일 생성"""
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, "invalid_data.xlsx")

        # 필수 컬럼 누락된 데이터 생성
        df = pd.DataFrame({
            "이름": ["홍길동"],
            "1월": [10000],
            # 나머지 컬럼 누락
        })
        df.to_excel(file_path, index=False)

        yield temp_dir, file_path
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validate_missing_columns(self, invalid_data_file):
        """필수 컬럼 누락 검증"""
        temp_dir, file_path = invalid_data_file
        result = validate_data(temp_dir, os.path.basename(file_path))

        assert result["status"] == "error"
        assert "errors" in result
        assert any("컬럼 누락" in e for e in result["errors"])


class TestValidateTemplate:
    """validate_template 함수 테스트"""

    def test_validate_sample_template(self):
        """샘플 템플릿 검증"""
        if not os.path.exists(SAMPLE_TEMPLATE):
            pytest.skip("템플릿 파일이 없습니다")

        result = validate_template(TEST_DIR, "donation_receipt_template.docx")
        assert result["status"] in ["success", "warning"]

    def test_validate_missing_template(self):
        """존재하지 않는 템플릿"""
        result = validate_template(TEST_DIR, "nonexistent.docx")
        assert result["status"] == "error"


class TestGetHistory:
    """get_history 함수 테스트"""

    def test_get_history_no_ledger(self):
        """발행대장이 없을 때"""
        temp_dir = tempfile.mkdtemp()
        try:
            result = get_history(temp_dir)
            assert result["status"] in ["info", "error"]
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def temp_dir_with_ledger(self):
        """발행대장이 있는 임시 디렉토리"""
        temp_dir = tempfile.mkdtemp()
        ledger_path = os.path.join(temp_dir, "발행대장_2026.xlsx")

        # 발행대장 생성
        df = pd.DataFrame([
            {"발급번호": "26-001", "이름": "홍길동", "연간총합": 1200000,
             "발행일시": "2026-01-20 10:00:00", "파일경로": "receipts/홍길동.docx", "비고": ""},
            {"발급번호": "26-002", "이름": "김철수", "연간총합": 600000,
             "발행일시": "2026-01-20 10:05:00", "파일경로": "receipts/김철수.docx", "비고": ""},
            {"발급번호": "26-001", "이름": "홍길동", "연간총합": 1200000,
             "발행일시": "2026-01-21 09:00:00", "파일경로": "receipts/홍길동.docx", "비고": "재발행"},
        ])
        df.to_excel(ledger_path, index=False)

        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_get_history_with_ledger(self, temp_dir_with_ledger):
        """발행대장 조회"""
        result = get_history(temp_dir_with_ledger)

        assert result["status"] == "success"
        assert result["total_records"] == 3
        assert result["unique_recipients"] == 2
        assert result["reissue_count"] == 1


class TestGetPersonHistory:
    """get_person_history 함수 테스트"""

    @pytest.fixture
    def temp_dir_with_ledger(self):
        """발행대장이 있는 임시 디렉토리"""
        temp_dir = tempfile.mkdtemp()
        ledger_path = os.path.join(temp_dir, "발행대장_2026.xlsx")

        df = pd.DataFrame([
            {"발급번호": "26-001", "이름": "홍길동", "연간총합": 1200000,
             "발행일시": "2026-01-20 10:00:00", "파일경로": "receipts/홍길동.docx", "비고": ""},
        ])
        df.to_excel(ledger_path, index=False)

        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_get_person_history_found(self, temp_dir_with_ledger):
        """발행된 사람 조회"""
        result = get_person_history(temp_dir_with_ledger, "홍길동")

        assert result["status"] == "success"
        assert result["issued"] is True
        assert result["latest_receipt_no"] == "26-001"

    def test_get_person_history_not_found(self, temp_dir_with_ledger):
        """발행되지 않은 사람 조회"""
        result = get_person_history(temp_dir_with_ledger, "존재하지않는이름")

        assert result["status"] == "info"
        assert result["issued"] is False


class TestPrivacyProtection:
    """개인정보 보호 테스트"""

    def test_list_recipients_no_names(self):
        """대상자 목록에 이름 미포함"""
        result = list_recipients(TEST_DIR, "sample_income_summary.xlsx")

        if result["status"] == "success":
            # 이름 목록이 노출되면 안 됨
            assert "names" not in result
            assert "name_list" not in result

    def test_validate_data_no_names_in_errors(self):
        """검증 오류에 이름 미포함"""
        result = validate_data(TEST_DIR, "sample_income_summary.xlsx")

        # 경고나 오류가 있을 때 이름이 노출되면 안 됨
        if result.get("warnings"):
            for warning in result["warnings"]:
                # "행 N:" 형식만 허용
                assert "행" in warning or "중복" in warning

    def test_get_history_summary_only(self):
        """이력 조회 시 요약만 제공"""
        result = get_history(TEST_DIR)

        if result["status"] == "success":
            # 상세 목록이 노출되면 안 됨
            assert "records" not in result
            assert "details" not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
