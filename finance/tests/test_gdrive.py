"""gdrive.py 테스트 (Google API는 mock 사용)."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

SCRIPT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
sys.path.insert(0, SCRIPT_DIR)

import gdrive


class TestParseDate(unittest.TestCase):
    def test_mmdd(self):
        yyyy, mmdd, yyyymmdd = gdrive._parse_date("0125")
        self.assertEqual(mmdd, "0125")
        self.assertEqual(len(yyyy), 4)
        self.assertEqual(yyyymmdd, f"{yyyy}0125")

    def test_yyyymmdd(self):
        yyyy, mmdd, yyyymmdd = gdrive._parse_date("20260125")
        self.assertEqual(yyyy, "2026")
        self.assertEqual(mmdd, "0125")
        self.assertEqual(yyyymmdd, "20260125")

    def test_invalid_exits(self):
        with self.assertRaises(SystemExit):
            gdrive._parse_date("012")


class TestFormatSize(unittest.TestCase):
    def test_bytes(self):
        self.assertEqual(gdrive._format_size(500), "500B")

    def test_kb(self):
        self.assertEqual(gdrive._format_size(2048), "2.0KB")

    def test_mb(self):
        self.assertEqual(gdrive._format_size(2 * 1024 * 1024), "2.0MB")


class TestFindSubfolder(unittest.TestCase):
    def test_found(self):
        service = MagicMock()
        service.files().list().execute.return_value = {
            "files": [{"id": "folder123", "name": "0125"}]
        }
        result = gdrive._find_subfolder(service, "parent_id", "0125")
        self.assertEqual(result, "folder123")

    def test_not_found(self):
        service = MagicMock()
        service.files().list().execute.return_value = {"files": []}
        result = gdrive._find_subfolder(service, "parent_id", "9999")
        self.assertIsNone(result)


class TestCreateSubfolder(unittest.TestCase):
    def test_creates_folder(self):
        service = MagicMock()
        service.files().create().execute.return_value = {"id": "new_folder_id"}
        result = gdrive._create_subfolder(service, "parent_id", "0126")
        self.assertEqual(result, "new_folder_id")


class TestListFiles(unittest.TestCase):
    def test_returns_files(self):
        service = MagicMock()
        mock_files = [
            {"id": "1", "name": "test.pdf", "size": "1024",
             "mimeType": "application/pdf", "modifiedTime": "2026-01-27T00:00:00Z"},
        ]
        service.files().list().execute.return_value = {"files": mock_files}
        result = gdrive._list_files(service, "folder_id")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "test.pdf")

    def test_empty(self):
        service = MagicMock()
        service.files().list().execute.return_value = {"files": []}
        result = gdrive._list_files(service, "folder_id")
        self.assertEqual(result, [])


class TestHandleHttpError(unittest.TestCase):
    def test_403(self):
        from googleapiclient.errors import HttpError
        resp = MagicMock()
        resp.status = 403
        error = HttpError(resp, b"Forbidden")
        with self.assertRaises(SystemExit):
            gdrive._handle_http_error(error, "테스트")

    def test_429(self):
        from googleapiclient.errors import HttpError
        resp = MagicMock()
        resp.status = 429
        error = HttpError(resp, b"Rate limit")
        with self.assertRaises(SystemExit):
            gdrive._handle_http_error(error, "테스트")


if __name__ == "__main__":
    unittest.main()
