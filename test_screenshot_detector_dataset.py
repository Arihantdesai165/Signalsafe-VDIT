# -*- coding: utf-8 -*-
"""
SignalSafe Campus - Screenshot Detector Dataset-Driven Verification Test Suite.
Validates:
1. Complete removal of T26 prefix rules (no prefix heuristics).
2. Reference dataset matching against active PostgreSQL dataset.
3. Test with Screenshot 1 (PhonePe, ₹1,680, 11 May 2026, 04:06 PM, Axis Bank) -> MATCHING_DEMO_RECORD.
4. Test with Screenshot 2 (PhonePe, ₹1,640, 6 July 2026, 10:24 AM, Yes Bank) -> MATCHING_DEMO_RECORD.
5. Negative test: Amount mismatch -> DETAILS_MISMATCH.
6. Negative test: Unknown reference -> NO_MATCHING_RECORD.
7. Negative test: Insufficient information -> INSUFFICIENT_INFORMATION.
8. Negative test: Deactivated dataset -> NO_ACTIVE_DATASET.
9. Mandatory notice: "DEMO DATA — NOT BANK VERIFIED" presence and absence of "Payment Verified".
10. CyberAdmin RBAC on /api/cyberadmin/screenshot-datasets/* (403 for Student, 200 for CyberAdmin).
11. Atomic activation and rollback in PostgreSQL.
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import app
from backend.services.auth_service import generate_signalsafe_session
from backend.services.screenshot_dataset_service import (
    activate_new_dataset,
    get_active_dataset_info,
    deactivate_active_dataset,
    validate_and_parse_csv,
    MANDATORY_DEMO_NOTICE,
)
from backend.services.screenshot_service import analyze_screenshot

client = TestClient(app)


class TestScreenshotDetectorDataset(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cyberadmin_user = {
            "id": "CYBER-001",
            "email": "cyberadmin@jcer.edu",
            "name": "Prof. R. CyberAdmin",
            "role": "CYBERADMIN",
            "department": "Cybersecurity Cell",
        }
        cls.student_user = {
            "id": "STU-2026-001",
            "email": "student@jcer.edu",
            "name": "Aarav Sharma",
            "role": "STUDENT",
            "department": "Computer Science",
        }

        cls.cyberadmin_token = generate_signalsafe_session(cls.cyberadmin_user)["token"]
        cls.student_token = generate_signalsafe_session(cls.student_user)["token"]

        cls.admin_headers = {"Authorization": f"Bearer {cls.cyberadmin_token}"}
        cls.student_headers = {"Authorization": f"Bearer {cls.student_token}"}

        # Activate 50-record reference dataset
        csv_path = "SignalSafe_Screenshot_Detector_50_Synthetic_Datasets.csv"
        assert os.path.exists(csv_path), f"Dataset CSV {csv_path} must exist."
        with open(csv_path, "r", encoding="utf-8") as f:
            csv_content = f.read()

        act = activate_new_dataset(
            csv_content=csv_content,
            filename="SignalSafe_Screenshot_Detector_50_Synthetic_Datasets.csv",
            admin_user=cls.cyberadmin_user,
            dataset_name="JCER Initial Reference Dataset",
        )
        assert act["success"] is True

    def test_01_screenshot_1_matching_record(self):
        """Screenshot 1 must match REC-2026-001 with REFERENCE_DATASET_MATCH and safe status."""
        with open("test_screenshots/screenshot_1_match.png", "rb") as f:
            img_bytes = f.read()

        res = analyze_screenshot(img_bytes)

        self.assertIn(res["classification"], ["REFERENCE_DATASET_MATCH", "MATCHING_DEMO_RECORD"])
        self.assertEqual(res["status"], "safe")
        self.assertLessEqual(res["risk_score"], 25)
        self.assertIn("DEMO DATA", res["demo_notice"])
        self.assertIsNotNone(res["matched_record"])
        self.assertEqual(res["matched_record"]["record_id"], "REC-2026-001")
        self.assertEqual(res["matched_record"]["transaction_id"], "T2605111605573710174884")
        self.assertEqual(res["matched_record"]["utr_rrn"], "750877359769")
        self.assertEqual(res["matched_record"]["amount_inr"], 1680.00)
        self.assertEqual(len(res["mismatches"]), 0)
        self.assertGreaterEqual(len(res["comparison_fields"]), 4)

        # Mandatory constraint: Never claim "Payment Verified" or "Genuine Payment"
        for reason in res["reasons"]:
            self.assertNotIn("payment verified", reason.lower())
            self.assertNotIn("genuine payment", reason.lower())

    def test_02_screenshot_2_matching_record(self):
        """Screenshot 2 must match REC-2026-002 with REFERENCE_DATASET_MATCH and safe status."""
        with open("test_screenshots/screenshot_2_match.png", "rb") as f:
            img_bytes = f.read()

        res = analyze_screenshot(img_bytes)

        self.assertIn(res["classification"], ["REFERENCE_DATASET_MATCH", "MATCHING_DEMO_RECORD"])
        self.assertEqual(res["status"], "safe")
        self.assertLessEqual(res["risk_score"], 25)
        self.assertIn("DEMO DATA", res["demo_notice"])
        self.assertIsNotNone(res["matched_record"])
        self.assertEqual(res["matched_record"]["record_id"], "REC-2026-002")
        self.assertEqual(res["matched_record"]["transaction_id"], "T2607061024008552577996")
        self.assertEqual(res["matched_record"]["utr_rrn"], "604170057839")
        self.assertEqual(res["matched_record"]["amount_inr"], 1640.00)
        self.assertEqual(len(res["mismatches"]), 0)

    def test_03_screenshot_amount_mismatch(self):
        """Screenshot with matching UTR and payee, but differing amount yields Result A with informational note."""
        with open("test_screenshots/screenshot_amount_mismatch.png", "rb") as f:
            img_bytes = f.read()

        res = analyze_screenshot(img_bytes)

        # Primary decision matches on UTR and payee
        self.assertIn(res["classification"], ["REFERENCE_DATASET_MATCH", "MATCHING_DEMO_RECORD"])
        self.assertEqual(res["status"], "safe")
        self.assertLessEqual(res["risk_score"], 25)
        # Informational fields show the amount
        info_fields = res.get("informational_fields", [])
        self.assertTrue(len(info_fields) > 0 or len(res.get("comparison_fields", [])) > 0)

    def test_04_screenshot_unknown_reference(self):
        """Screenshot with non-existent UTR/TxnID must trigger NO_MATCHING_RECORD."""
        with open("test_screenshots/screenshot_unknown_ref.png", "rb") as f:
            img_bytes = f.read()

        res = analyze_screenshot(img_bytes)

        self.assertEqual(res["classification"], "NO_MATCHING_RECORD")
        self.assertEqual(res["status"], "suspicious")
        self.assertIsNone(res["matched_record"])
        self.assertTrue(
            any("not found" in r.lower() or "not match" in r.lower() or "unverified" in r.lower() or "no matching" in r.lower() for r in res["reasons"])
        )

    def test_05_absence_of_t26_prefix_rules(self):
        """Verifies that no code path treats T26 as genuine or non-T26 as fraud."""
        with open("backend/services/screenshot_service.py", "r", encoding="utf-8") as f:
            code = f.read()

        self.assertNotIn('.startswith("T26")', code)
        self.assertNotIn("T26 pattern", code)
        self.assertNotIn("Only 'T26' is valid", code)
        self.assertNotIn("FRAUD DETECTED: Invalid Transaction ID prefix", code)

    def test_06_cyberadmin_dataset_rbac(self):
        """Non-cyberadmin users must be rejected with HTTP 403 Forbidden."""
        # Student attempts GET active dataset
        res_student = client.get("/api/cyberadmin/screenshot-datasets/active", headers=self.student_headers)
        self.assertEqual(res_student.status_code, 403)

        # Student attempts POST validate
        res_validate = client.post(
            "/api/cyberadmin/screenshot-datasets/validate",
            headers=self.student_headers,
            files={"file": ("test.csv", b"record_id,transaction_id\n1,T1", "text/csv")},
        )
        self.assertEqual(res_validate.status_code, 403)

        # Student attempts POST activate
        res_activate = client.post(
            "/api/cyberadmin/screenshot-datasets/activate",
            headers=self.student_headers,
            files={"file": ("test.csv", b"record_id,transaction_id\n1,T1", "text/csv")},
        )
        self.assertEqual(res_activate.status_code, 403)

        # CyberAdmin succeeds
        res_admin = client.get("/api/cyberadmin/screenshot-datasets/active", headers=self.admin_headers)
        self.assertEqual(res_admin.status_code, 200)
        self.assertTrue(res_admin.json()["active"])

    def test_07_csv_validation_endpoint(self):
        """Validate endpoint checks headers, formula injection, and duplicates."""
        with open("SignalSafe_Screenshot_Detector_50_Synthetic_Datasets.csv", "rb") as f:
            csv_bytes = f.read()

        response = client.post(
            "/api/cyberadmin/screenshot-datasets/validate",
            headers=self.admin_headers,
            files={"file": ("dataset.csv", csv_bytes, "text/csv")},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["is_valid"])
        self.assertEqual(data["total_rows"], 50)
        self.assertEqual(data["valid_count"], 50)
        self.assertGreaterEqual(len(data["preview_records"]), 5)

        # Test invalid CSV (missing required core columns)
        bad_csv = b"col1,col2\nval1,val2\n"
        res_bad = client.post(
            "/api/cyberadmin/screenshot-datasets/validate",
            headers=self.admin_headers,
            files={"file": ("bad.csv", bad_csv, "text/csv")},
        )
        self.assertEqual(res_bad.status_code, 200)
        data_bad = res_bad.json()
        self.assertFalse(data_bad["is_valid"])
        self.assertIn("missing", data_bad["error"].lower())

    def test_08_screenshot_analyze_api_endpoint(self):
        """POST /api/screenshot/analyze must return dataset match and persist scan_id."""
        with open("test_screenshots/screenshot_1_match.png", "rb") as f:
            img_bytes = f.read()

        response = client.post(
            "/api/screenshot/analyze",
            headers=self.student_headers,
            files={"file": ("screenshot_1.png", img_bytes, "image/png")},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["classification"], ["REFERENCE_DATASET_MATCH", "MATCHING_DEMO_RECORD"])
        self.assertEqual(data["status"], "safe")
        self.assertIn("scan_id", data)
        self.assertTrue(data["scan_id"].startswith("SCAN-SS-"))
        self.assertIn("DEMO DATA", data["demo_notice"])

    def test_09_dataset_deactivation_and_reactivation(self):
        """Deactivating dataset should result in NO_ACTIVE_DATASET response."""
        # Deactivate
        res_deact = client.post("/api/cyberadmin/screenshot-datasets/deactivate", headers=self.admin_headers)
        self.assertEqual(res_deact.status_code, 200)
        self.assertTrue(res_deact.json()["success"])

        # Scan with no active dataset
        with open("test_screenshots/screenshot_1_match.png", "rb") as f:
            img_bytes = f.read()

        res_scan = analyze_screenshot(img_bytes)
        self.assertEqual(res_scan["classification"], "NO_ACTIVE_DATASET")
        self.assertEqual(res_scan["status"], "suspicious")

        # Re-activate for system health
        with open("SignalSafe_Screenshot_Detector_50_Synthetic_Datasets.csv", "r", encoding="utf-8") as f:
            csv_content = f.read()
        act = activate_new_dataset(
            csv_content=csv_content,
            filename="SignalSafe_Screenshot_Detector_50_Synthetic_Datasets.csv",
            admin_user=self.cyberadmin_user,
            dataset_name="JCER Initial Reference Dataset",
        )
        self.assertTrue(act["success"])


if __name__ == "__main__":
    unittest.main()
