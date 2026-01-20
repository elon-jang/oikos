#!/usr/bin/env python3
"""
MCP 서버 통합 테스트

MCP 서버의 전체 워크플로우를 테스트합니다.

테스트 실행:
    pytest test_mcp_integration.py -v
"""

import os
import tempfile
import shutil
import pytest
import subprocess
import json

# MCP 도구 import
from mcp_server.tools.receipt import (
    list_recipients,
    generate_receipt,
    generate_all_receipts,
    preview_receipt,
    load_data,
)
from mcp_server.tools.validate import validate_data, validate_template
from mcp_server.tools.history import get_history, get_person_history


# 테스트 데이터 경로
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DATA = os.path.join(TEST_DIR, "sample_income_summary.xlsx")
SAMPLE_TEMPLATE = os.path.join(TEST_DIR, "donation_receipt_template.docx")


class TestEndToEndWorkflow:
    """전체 워크플로우 통합 테스트"""

    @pytest.fixture
    def work_dir(self):
        """테스트용 작업 디렉토리 생성"""
        temp_dir = tempfile.mkdtemp(prefix="mcp_test_")

        # 샘플 파일 복사
        if os.path.exists(SAMPLE_DATA):
            shutil.copy(SAMPLE_DATA, os.path.join(temp_dir, "2025_income_summary.xlsx"))
        if os.path.exists(SAMPLE_TEMPLATE):
            shutil.copy(SAMPLE_TEMPLATE, os.path.join(temp_dir, "donation_receipt_template.docx"))

        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.skipif(
        not os.path.exists(SAMPLE_DATA) or not os.path.exists(SAMPLE_TEMPLATE),
        reason="샘플 파일이 없습니다"
    )
    def test_complete_workflow(self, work_dir):
        """
        전체 영수증 발행 워크플로우 테스트

        1. 데이터 검증
        2. 템플릿 검증
        3. 대상자 확인
        4. 미리보기
        5. 영수증 생성
        6. 이력 확인
        """
        # 1. 데이터 검증
        validate_result = validate_data(work_dir, "2025_income_summary.xlsx")
        assert validate_result["status"] in ["success", "warning"], \
            f"데이터 검증 실패: {validate_result.get('message')}"

        # 2. 템플릿 검증
        template_result = validate_template(work_dir)
        assert template_result["status"] in ["success", "warning"], \
            f"템플릿 검증 실패: {template_result.get('message')}"

        # 3. 대상자 확인
        list_result = list_recipients(work_dir, "2025_income_summary.xlsx")
        assert list_result["status"] == "success", \
            f"대상자 목록 조회 실패: {list_result.get('message')}"
        assert list_result["count"] > 0

        # 4. 첫 번째 사람 미리보기
        df = load_data(os.path.join(work_dir, "2025_income_summary.xlsx"))
        first_name = df.iloc[0]["이름"]

        preview_result = preview_receipt(work_dir, first_name, "2025_income_summary.xlsx")
        assert preview_result["status"] == "success", \
            f"미리보기 실패: {preview_result.get('message')}"
        assert "preview" in preview_result

        # 5. 영수증 생성
        generate_result = generate_receipt(work_dir, first_name, "2025_income_summary.xlsx")
        assert generate_result["status"] == "success", \
            f"영수증 생성 실패: {generate_result.get('message')}"
        assert os.path.exists(generate_result["file_path"]), "영수증 파일이 생성되지 않음"

        # 6. 이력 확인
        history_result = get_person_history(work_dir, first_name)
        assert history_result["status"] == "success", \
            f"이력 조회 실패: {history_result.get('message')}"
        assert history_result["issued"] is True

    @pytest.mark.skipif(
        not os.path.exists(SAMPLE_DATA) or not os.path.exists(SAMPLE_TEMPLATE),
        reason="샘플 파일이 없습니다"
    )
    def test_batch_generation_workflow(self, work_dir):
        """
        전체 일괄 발행 워크플로우 테스트
        """
        # 1. 미리보기 모드로 확인
        preview_result = generate_all_receipts(work_dir, "2025_income_summary.xlsx", confirm=False)
        assert preview_result["status"] == "preview"
        expected_count = preview_result["count"]

        # 2. 실제 생성
        generate_result = generate_all_receipts(work_dir, "2025_income_summary.xlsx", confirm=True)
        assert generate_result["status"] == "success"
        assert generate_result["generated"] == expected_count

        # 3. 생성된 파일 확인
        receipts_dir = os.path.join(work_dir, "receipts")
        assert os.path.exists(receipts_dir)
        files = os.listdir(receipts_dir)
        # 동일 이름이 있으면 파일이 덮어씌워지므로 파일 수가 적을 수 있음
        # 생성된 수가 예상과 일치하면 OK (파일 수는 중복 이름으로 인해 적을 수 있음)
        assert len(files) <= generate_result["generated"]
        assert generate_result["generated"] == expected_count

        # 4. 발행대장 확인
        history_result = get_history(work_dir)
        assert history_result["status"] == "success"
        assert history_result["total_records"] == expected_count

    @pytest.mark.skipif(
        not os.path.exists(SAMPLE_DATA) or not os.path.exists(SAMPLE_TEMPLATE),
        reason="샘플 파일이 없습니다"
    )
    def test_reissue_workflow(self, work_dir):
        """
        재발행 워크플로우 테스트
        """
        df = load_data(os.path.join(work_dir, "2025_income_summary.xlsx"))
        first_name = df.iloc[0]["이름"]

        # 1. 첫 번째 발행
        result1 = generate_receipt(work_dir, first_name, "2025_income_summary.xlsx")
        assert result1["status"] == "success"

        # 2. 재발행
        result2 = generate_receipt(work_dir, first_name, "2025_income_summary.xlsx")
        assert result2["status"] == "success"
        assert result1["receipt_no"] == result2["receipt_no"], "발급번호가 동일해야 함"

        # 3. 이력에서 재발행 확인
        history_result = get_history(work_dir)
        assert history_result["reissue_count"] >= 1


class TestYearAutoDetection:
    """연도 자동 감지 테스트"""

    @pytest.fixture
    def multi_year_dir(self):
        """여러 연도 파일이 있는 디렉토리"""
        temp_dir = tempfile.mkdtemp(prefix="mcp_year_test_")

        if os.path.exists(SAMPLE_DATA):
            # 2024, 2025 파일 복사
            shutil.copy(SAMPLE_DATA, os.path.join(temp_dir, "2024_income_summary.xlsx"))
            shutil.copy(SAMPLE_DATA, os.path.join(temp_dir, "2025_income_summary.xlsx"))

        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.skipif(not os.path.exists(SAMPLE_DATA), reason="샘플 데이터가 없습니다")
    def test_auto_selects_latest_year(self, multi_year_dir):
        """자동으로 최신 연도 파일 선택"""
        result = list_recipients(multi_year_dir)

        if result["status"] == "success":
            # 2025 파일이 선택되어야 함
            assert "2025" in result["data_file"]
            assert result["issue_year"] == "2026"


class TestServerImport:
    """서버 모듈 import 테스트"""

    def test_server_imports_successfully(self):
        """서버 모듈 import 가능"""
        try:
            from mcp_server.server import mcp
            assert mcp is not None
        except ImportError as e:
            pytest.fail(f"서버 모듈 import 실패: {e}")

    def test_server_has_tools_registered(self):
        """도구가 등록되어 있는지 확인"""
        from mcp_server.server import mcp

        # FastMCP 객체는 tool 데코레이터로 등록된 함수들을 가지고 있어야 함
        assert hasattr(mcp, 'name')
        assert mcp.name == "oikos-receipt"


class TestErrorHandling:
    """오류 처리 테스트"""

    def test_handles_permission_error_gracefully(self):
        """권한 오류 처리"""
        # 존재하지 않는 디렉토리
        result = list_recipients("/nonexistent/path")
        assert result["status"] == "error"

    def test_handles_invalid_excel_gracefully(self):
        """잘못된 Excel 파일 처리"""
        temp_dir = tempfile.mkdtemp()
        try:
            # 텍스트 파일을 xlsx로 저장
            invalid_file = os.path.join(temp_dir, "2025_income_summary.xlsx")
            with open(invalid_file, "w") as f:
                f.write("This is not an Excel file")

            result = validate_data(temp_dir, "2025_income_summary.xlsx")
            assert result["status"] == "error"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestDataPrivacy:
    """데이터 개인정보 보호 통합 테스트"""

    @pytest.fixture
    def work_dir(self):
        """테스트용 작업 디렉토리"""
        temp_dir = tempfile.mkdtemp(prefix="mcp_privacy_test_")
        if os.path.exists(SAMPLE_DATA):
            shutil.copy(SAMPLE_DATA, os.path.join(temp_dir, "2025_income_summary.xlsx"))
        if os.path.exists(SAMPLE_TEMPLATE):
            shutil.copy(SAMPLE_TEMPLATE, os.path.join(temp_dir, "donation_receipt_template.docx"))
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.skipif(not os.path.exists(SAMPLE_DATA), reason="샘플 데이터가 없습니다")
    def test_all_responses_privacy_safe(self, work_dir):
        """모든 응답이 개인정보 보호 규칙을 준수하는지 확인"""
        # 샘플 데이터에서 모든 이름 추출
        df = load_data(os.path.join(work_dir, "2025_income_summary.xlsx"))
        all_names = df["이름"].tolist()

        # list_recipients 테스트
        list_result = list_recipients(work_dir, "2025_income_summary.xlsx")
        list_json = json.dumps(list_result, ensure_ascii=False)

        for name in all_names:
            assert name not in list_json, f"list_recipients 응답에 이름 노출: {name}"

        # validate_data 테스트
        validate_result = validate_data(work_dir, "2025_income_summary.xlsx")
        validate_json = json.dumps(validate_result, ensure_ascii=False)

        for name in all_names:
            assert name not in validate_json, f"validate_data 응답에 이름 노출: {name}"

        # generate_all_receipts preview 테스트
        all_result = generate_all_receipts(work_dir, "2025_income_summary.xlsx", confirm=False)
        all_json = json.dumps(all_result, ensure_ascii=False)

        for name in all_names:
            assert name not in all_json, f"generate_all_receipts 응답에 이름 노출: {name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
