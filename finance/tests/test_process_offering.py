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

import process_offering


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


class TestCreateTemplate(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._orig_base = process_offering.BASE_DIR
        process_offering.BASE_DIR = self.tmpdir
        # 템플릿 파일 복사
        templates_dir = os.path.join(self.tmpdir, "templates")
        os.makedirs(templates_dir, exist_ok=True)
        shutil.copy2(process_offering.TEMPLATE_FILE, os.path.join(templates_dir, "upload_sample.xlsx"))
        process_offering.TEMPLATE_FILE = os.path.join(templates_dir, "upload_sample.xlsx")

    def tearDown(self):
        process_offering.BASE_DIR = self._orig_base
        process_offering.TEMPLATE_FILE = os.path.join(self._orig_base, "templates", "upload_sample.xlsx")
        shutil.rmtree(self.tmpdir)

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


class TestWriteData(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._orig_base = process_offering.BASE_DIR
        process_offering.BASE_DIR = self.tmpdir
        templates_dir = os.path.join(self.tmpdir, "templates")
        os.makedirs(templates_dir, exist_ok=True)
        shutil.copy2(process_offering.TEMPLATE_FILE, os.path.join(templates_dir, "upload_sample.xlsx"))
        process_offering.TEMPLATE_FILE = os.path.join(templates_dir, "upload_sample.xlsx")

    def tearDown(self):
        process_offering.BASE_DIR = self._orig_base
        process_offering.TEMPLATE_FILE = os.path.join(self._orig_base, "templates", "upload_sample.xlsx")
        shutil.rmtree(self.tmpdir)

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


class TestVerify(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._orig_base = process_offering.BASE_DIR
        process_offering.BASE_DIR = self.tmpdir
        templates_dir = os.path.join(self.tmpdir, "templates")
        os.makedirs(templates_dir, exist_ok=True)
        shutil.copy2(process_offering.TEMPLATE_FILE, os.path.join(templates_dir, "upload_sample.xlsx"))
        process_offering.TEMPLATE_FILE = os.path.join(templates_dir, "upload_sample.xlsx")

    def tearDown(self):
        process_offering.BASE_DIR = self._orig_base
        process_offering.TEMPLATE_FILE = os.path.join(self._orig_base, "templates", "upload_sample.xlsx")
        shutil.rmtree(self.tmpdir)

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


if __name__ == "__main__":
    unittest.main()
