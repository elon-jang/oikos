"""process_offering.py 테스트."""

import json
import os
import shutil
import sys
import tempfile
import unittest

# scripts/ 모듈 import를 위한 경로 설정
SCRIPT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
sys.path.insert(0, SCRIPT_DIR)

import offering_config
import process_offering


class TestCategoryValidation(unittest.TestCase):
    def test_slots_match_row_range(self):
        """모든 카테고리의 slots가 행 범위(end - start + 1)와 일치해야 함."""
        for cat_name, config in offering_config.CATEGORIES.items():
            expected = config["end"] - config["start"] + 1
            self.assertEqual(
                config["slots"], expected,
                f"{cat_name}: slots={config['slots']} != range {config['start']}-{config['end']} ({expected})"
            )

    def test_no_overlapping_rows(self):
        """카테고리 간 행이 겹치지 않아야 함."""
        seen = {}
        for cat_name, config in offering_config.CATEGORIES.items():
            for row in range(config["start"], config["end"] + 1):
                self.assertNotIn(
                    row, seen,
                    f"행 {row}: {cat_name}과 {seen.get(row)} 중복"
                )
                seen[row] = cat_name


class TestParseDate(unittest.TestCase):
    def test_valid_yyyymmdd(self):
        dt = process_offering._parse_date("20260125")
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 1)
        self.assertEqual(dt.day, 25)

    def test_invalid_format(self):
        with self.assertRaises(ValueError):
            process_offering._parse_date("2026-01-25")


class TestOutputPath(unittest.TestCase):
    def test_path_structure(self):
        path = process_offering._output_path("20260125")
        self.assertTrue(path.endswith("data/2026/0125/20260125.xlsx"))

    def test_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_base = process_offering.BASE_DIR
            process_offering.BASE_DIR = tmpdir
            try:
                path = process_offering._output_path("20260201")
                self.assertTrue(os.path.isdir(os.path.dirname(path)))
            finally:
                process_offering.BASE_DIR = orig_base


class _TemplateTestBase(unittest.TestCase):
    """tmpdir에 템플릿을 복사하고 BASE_DIR을 교체하는 공통 setUp/tearDown."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._orig_base = process_offering.BASE_DIR
        self._orig_template = process_offering.TEMPLATE_FILE
        process_offering.BASE_DIR = self.tmpdir
        templates_dir = os.path.join(self.tmpdir, "templates")
        os.makedirs(templates_dir, exist_ok=True)
        shutil.copy2(self._orig_template, os.path.join(templates_dir, "upload_sample.xlsx"))
        process_offering.TEMPLATE_FILE = os.path.join(templates_dir, "upload_sample.xlsx")

    def tearDown(self):
        process_offering.BASE_DIR = self._orig_base
        process_offering.TEMPLATE_FILE = self._orig_template
        shutil.rmtree(self.tmpdir)


class TestCreateTemplate(_TemplateTestBase):

    def test_creates_file(self):
        path = process_offering.create_template("20260125")
        self.assertTrue(os.path.exists(path))
        self.assertTrue(path.endswith("20260125.xlsx"))

    def test_backup_on_existing(self):
        path = process_offering.create_template("20260125")
        self.assertTrue(os.path.exists(path))
        # 두 번째 호출 시 백업 생성
        path2 = process_offering.create_template("20260125")
        backup = path2.replace(".xlsx", "_backup.xlsx")
        self.assertTrue(os.path.exists(backup))


class TestWriteData(_TemplateTestBase):

    def test_write_creates_template_if_missing(self):
        data = {"십일조": [{"name": "테스트", "amount": 100}]}
        result = process_offering.write_data("20260125", json.dumps(data))
        self.assertIn("1건", result)

    def test_write_multiple_entries(self):
        data = {
            "십일조": [
                {"name": "홍길동", "amount": 100000},
                {"name": "김철수", "amount": 200000},
            ]
        }
        result = process_offering.write_data("20260125", json.dumps(data))
        self.assertIn("2건", result)

    def test_write_unknown_category_warns(self):
        data = {"없는카테고리": [{"name": "테스트", "amount": 100}]}
        result = process_offering.write_data("20260125", json.dumps(data))
        self.assertIn("알 수 없는 카테고리", result)

    def test_write_overflow_warns(self):
        # 십일조 has 23 slots
        data = {"십일조": [{"name": f"테스트{i}", "amount": 100} for i in range(25)]}
        result = process_offering.write_data("20260125", json.dumps(data))
        self.assertIn("초과", result)

    def test_backup_before_overwrite(self):
        data = {"십일조": [{"name": "테스트", "amount": 100}]}
        process_offering.write_data("20260125", json.dumps(data))
        # 두 번째 write → 백업 생성
        process_offering.write_data("20260125", json.dumps(data))
        output_path = process_offering._output_path("20260125")
        backup_path = output_path.replace(".xlsx", "_backup.xlsx")
        self.assertTrue(os.path.exists(backup_path))


class TestVerify(_TemplateTestBase):

    def test_verify_missing_file(self):
        result = process_offering.verify("20260201")
        parsed = json.loads(result)
        self.assertIn("error", parsed)

    def test_verify_after_write(self):
        data = {
            "십일조": [
                {"name": "홍길동", "amount": 100000},
                {"name": "김철수", "amount": 200000},
            ]
        }
        process_offering.write_data("20260125", json.dumps(data))
        result = process_offering.verify("20260125")
        parsed = json.loads(result)
        self.assertEqual(parsed["십일조"]["count"], 2)
        self.assertEqual(parsed["십일조"]["total"], 300000)
        self.assertEqual(parsed["_summary"]["grand_total"], 300000)


class TestValidateData(unittest.TestCase):
    def test_valid_data(self):
        data = {"십일조": [{"name": "홍길동", "amount": 100000}]}
        errors = process_offering._validate_data(data)
        self.assertEqual(errors, [])

    def test_not_dict(self):
        errors = process_offering._validate_data([1, 2, 3])
        self.assertEqual(len(errors), 1)
        self.assertIn("dict", errors[0])

    def test_entries_not_list(self):
        errors = process_offering._validate_data({"십일조": "잘못된형식"})
        self.assertEqual(len(errors), 1)
        self.assertIn("list", errors[0])

    def test_entry_not_dict(self):
        errors = process_offering._validate_data({"십일조": ["문자열"]})
        self.assertEqual(len(errors), 1)
        self.assertIn("dict", errors[0])

    def test_missing_name(self):
        errors = process_offering._validate_data({"십일조": [{"amount": 100}]})
        self.assertEqual(len(errors), 1)
        self.assertIn("이름", errors[0])

    def test_empty_name(self):
        errors = process_offering._validate_data({"십일조": [{"name": "  ", "amount": 100}]})
        self.assertEqual(len(errors), 1)
        self.assertIn("이름", errors[0])

    def test_missing_amount(self):
        errors = process_offering._validate_data({"십일조": [{"name": "홍길동"}]})
        self.assertEqual(len(errors), 1)
        self.assertIn("amount", errors[0])

    def test_negative_amount(self):
        errors = process_offering._validate_data({"십일조": [{"name": "홍길동", "amount": -100}]})
        self.assertEqual(len(errors), 1)
        self.assertIn("0 이상", errors[0])

    def test_string_amount(self):
        errors = process_offering._validate_data({"십일조": [{"name": "홍길동", "amount": "백만원"}]})
        self.assertEqual(len(errors), 1)

    def test_multiple_errors(self):
        data = {
            "십일조": [
                {"name": "", "amount": -1},
                {"name": "홍길동"},
            ]
        }
        errors = process_offering._validate_data(data)
        self.assertGreaterEqual(len(errors), 3)


class TestWriteDataValidation(_TemplateTestBase):

    def test_invalid_json_raises(self):
        with self.assertRaises(json.JSONDecodeError):
            process_offering.write_data("20260125", "{잘못된 json")

    def test_validation_rejects_bad_data(self):
        data = {"십일조": [{"name": "홍길동"}]}  # amount 없음
        result = process_offering.write_data("20260125", json.dumps(data))
        self.assertIn("검증 실패", result)

    def test_validation_rejects_negative_amount(self):
        data = {"십일조": [{"name": "홍길동", "amount": -500}]}
        result = process_offering.write_data("20260125", json.dumps(data))
        self.assertIn("검증 실패", result)


class TestDryRun(_TemplateTestBase):

    def test_dry_run_no_file_created(self):
        data = {"십일조": [{"name": "홍길동", "amount": 100000}]}
        result = process_offering.write_data("20260125", json.dumps(data), dry_run=True)
        self.assertIn("[dry-run]", result)
        output_path = process_offering._output_path("20260125")
        self.assertFalse(os.path.exists(output_path))

    def test_dry_run_shows_summary(self):
        data = {
            "십일조": [
                {"name": "홍길동", "amount": 100000},
                {"name": "김철수", "amount": 200000},
            ],
            "감사": [{"name": "박영희", "amount": 50000}],
        }
        result = process_offering.write_data("20260125", json.dumps(data), dry_run=True)
        self.assertIn("3건", result)
        self.assertIn("350,000", result)
        self.assertIn("십일조", result)
        self.assertIn("감사", result)

    def test_dry_run_validation_still_rejects(self):
        data = {"십일조": [{"name": "홍길동"}]}
        result = process_offering.write_data("20260125", json.dumps(data), dry_run=True)
        self.assertIn("검증 실패", result)

    def test_dry_run_warnings_shown(self):
        data = {"없는카테고리": [{"name": "테스트", "amount": 100}]}
        result = process_offering.write_data("20260125", json.dumps(data), dry_run=True)
        self.assertIn("알 수 없는 카테고리", result)


class TestSummary(_TemplateTestBase):

    def test_summary_no_data(self):
        result = process_offering.summary("202601")
        parsed = json.loads(result)
        self.assertIn("error", parsed)

    def test_summary_single_week(self):
        data = {
            "십일조": [{"name": "홍길동", "amount": 100000}],
            "감사": [{"name": "김철수", "amount": 50000}],
        }
        process_offering.write_data("20260125", json.dumps(data))
        result = process_offering.summary("202601")
        parsed = json.loads(result)
        self.assertEqual(parsed["month"], "2026-01")
        self.assertEqual(parsed["weeks"], 1)
        self.assertEqual(parsed["grand_total"], 150000)
        self.assertEqual(parsed["categories"]["십일조"]["total"], 100000)
        self.assertEqual(parsed["categories"]["감사"]["total"], 50000)

    def test_summary_multiple_weeks(self):
        data1 = {"십일조": [{"name": "홍길동", "amount": 100000}]}
        data2 = {"십일조": [{"name": "김철수", "amount": 200000}]}
        process_offering.write_data("20260118", json.dumps(data1))
        process_offering.write_data("20260125", json.dumps(data2))
        result = process_offering.summary("202601")
        parsed = json.loads(result)
        self.assertEqual(parsed["weeks"], 2)
        self.assertEqual(parsed["categories"]["십일조"]["count"], 2)
        self.assertEqual(parsed["categories"]["십일조"]["total"], 300000)
        self.assertEqual(parsed["grand_total"], 300000)
        self.assertEqual(len(parsed["weekly_totals"]), 2)

    def test_summary_wrong_month(self):
        data = {"십일조": [{"name": "홍길동", "amount": 100000}]}
        process_offering.write_data("20260125", json.dumps(data))
        result = process_offering.summary("202602")
        parsed = json.loads(result)
        self.assertIn("error", parsed)


class TestRollback(_TemplateTestBase):

    def test_rollback_restores_backup(self):
        data1 = {"십일조": [{"name": "홍길동", "amount": 100000}]}
        process_offering.write_data("20260125", json.dumps(data1))
        # 두 번째 write → 첫 번째가 backup으로 이동
        data2 = {"십일조": [{"name": "김철수", "amount": 999999}]}
        process_offering.write_data("20260125", json.dumps(data2))

        output_path = process_offering._output_path("20260125")
        backup_path = output_path.replace(".xlsx", "_backup.xlsx")
        self.assertTrue(os.path.exists(backup_path))

        # rollback → backup이 현재 파일로 복원
        result = process_offering.rollback("20260125")
        self.assertIn("복원 완료", result)
        self.assertFalse(os.path.exists(backup_path))

        # verify로 복원된 데이터 확인 (data1의 홍길동 100000)
        verify_result = json.loads(process_offering.verify("20260125"))
        self.assertEqual(verify_result["십일조"]["entries"][0]["name"], "홍길동")
        self.assertEqual(verify_result["십일조"]["entries"][0]["amount"], 100000)

    def test_rollback_no_backup(self):
        process_offering.create_template("20260125")
        result = process_offering.rollback("20260125")
        self.assertIn("백업 파일 없음", result)

    def test_rollback_removes_backup_after_restore(self):
        data = {"십일조": [{"name": "테스트", "amount": 100}]}
        process_offering.write_data("20260125", json.dumps(data))
        process_offering.write_data("20260125", json.dumps(data))
        output_path = process_offering._output_path("20260125")
        backup_path = output_path.replace(".xlsx", "_backup.xlsx")
        self.assertTrue(os.path.exists(backup_path))

        process_offering.rollback("20260125")
        self.assertFalse(os.path.exists(backup_path))
        self.assertTrue(os.path.exists(output_path))


class TestBackupFile(unittest.TestCase):
    def test_backup_creates_copy(self):
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            f.write(b"test content")
            filepath = f.name
        try:
            backup_path = process_offering._backup_file(filepath)
            self.assertTrue(os.path.exists(backup_path))
            self.assertTrue(backup_path.endswith("_backup.xlsx"))
        finally:
            os.unlink(filepath)
            if os.path.exists(backup_path):
                os.unlink(backup_path)


if __name__ == "__main__":
    unittest.main()
