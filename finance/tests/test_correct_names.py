"""correct_names.py 테스트."""

import os
import sys
import tempfile
import unittest

SCRIPT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
sys.path.insert(0, SCRIPT_DIR)

import correct_names


class TestDecomposeHangul(unittest.TestCase):
    def test_basic(self):
        result = correct_names.decompose_hangul("가")
        self.assertEqual(result, ["ㄱ", "ㅏ"])

    def test_with_jongsung(self):
        result = correct_names.decompose_hangul("한")
        self.assertEqual(result, ["ㅎ", "ㅏ", "ㄴ"])

    def test_non_hangul_passthrough(self):
        result = correct_names.decompose_hangul("A1")
        self.assertEqual(result, ["A", "1"])

    def test_mixed(self):
        result = correct_names.decompose_hangul("권A")
        # 권 = ㄱ + ㅝ + ㄴ, A = A
        self.assertEqual(len(result), 4)
        self.assertEqual(result[-1], "A")


class TestJamoSimilarity(unittest.TestCase):
    def test_identical(self):
        score = correct_names.jamo_similarity("정형모", "정형모")
        self.assertEqual(score, 1.0)

    def test_similar_higher_than_different(self):
        # 정형모↔정형호 should be higher than 정형모↔최정호
        score1 = correct_names.jamo_similarity("정형모", "정형호")
        score2 = correct_names.jamo_similarity("정형모", "최정호")
        self.assertGreater(score1, score2)

    def test_completely_different(self):
        score = correct_names.jamo_similarity("가", "힣")
        self.assertLess(score, 0.5)


class TestCorrectName(unittest.TestCase):
    def setUp(self):
        self.members = ["권언성", "정형모", "이루리", "최진웅", "홍길동"]

    def test_exact_match(self):
        result = correct_names.correct_name("홍길동", self.members)
        self.assertEqual(result["status"], "exact")
        self.assertEqual(result["corrected"], "홍길동")

    def test_fuzzy_correction(self):
        result = correct_names.correct_name("천인성", self.members)
        self.assertEqual(result["status"], "corrected")
        self.assertEqual(result["corrected"], "권언성")

    def test_unknown_below_cutoff(self):
        result = correct_names.correct_name("가나다라마", self.members, cutoff=0.99)
        self.assertEqual(result["status"], "unknown")

    def test_empty_name(self):
        result = correct_names.correct_name("", self.members)
        self.assertEqual(result["status"], "exact")


class TestCorrectNamesBatch(unittest.TestCase):
    def test_batch(self):
        members = ["홍길동", "김철수"]
        results = correct_names.correct_names_batch(["홍길동", "김철수"], members)
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r["status"] == "exact" for r in results))


class TestAddMember(unittest.TestCase):
    def test_add_new(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("김철수\n홍길동\n")
            f.flush()
            filepath = f.name
        try:
            added = correct_names.add_member("박영희", filepath)
            self.assertTrue(added)
            members = correct_names.load_members(filepath)
            self.assertIn("박영희", members)
            # 정렬 확인
            self.assertEqual(members, sorted(members))
        finally:
            os.unlink(filepath)

    def test_add_duplicate(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("홍길동\n")
            f.flush()
            filepath = f.name
        try:
            added = correct_names.add_member("홍길동", filepath)
            self.assertFalse(added)
        finally:
            os.unlink(filepath)


class TestLoadMembersErrors(unittest.TestCase):
    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            correct_names.load_members("/nonexistent/path/members.txt")

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("")
            filepath = f.name
        try:
            members = correct_names.load_members(filepath)
            self.assertEqual(members, [])
        finally:
            os.unlink(filepath)

    def test_whitespace_only_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("  \n\n  \n")
            filepath = f.name
        try:
            members = correct_names.load_members(filepath)
            self.assertEqual(members, [])
        finally:
            os.unlink(filepath)


class TestAddMemberErrors(unittest.TestCase):
    def test_add_to_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            correct_names.add_member("홍길동", "/nonexistent/path/members.txt")


class TestCorrectNameEdgeCases(unittest.TestCase):
    def test_empty_members_list(self):
        result = correct_names.correct_name("홍길동", [])
        self.assertEqual(result["status"], "unknown")

    def test_single_char_name(self):
        members = ["김", "이", "박"]
        result = correct_names.correct_name("김", members)
        self.assertEqual(result["status"], "exact")


if __name__ == "__main__":
    unittest.main()
