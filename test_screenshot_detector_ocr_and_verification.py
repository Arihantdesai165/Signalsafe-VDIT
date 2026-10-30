# -*- coding: utf-8 -*-
"""
SignalSafe Campus - Screenshot Detector OCR & Dataset-Based Verification Test Suite.
Validates end-to-end:
1. Demonstration screenshot 1:
   - OCR extracts UTR, recipient, and amount accurately.
   - Matches active dataset record.
   - Result is MATCH FOUND (REFERENCE_DATASET_MATCH / MATCHING_DEMO_RECORD).
   - Risk score is <= 15.
   - Status is safe.
   - No false mismatch warning.
2. Demonstration screenshot 2:
   - Matches its active dataset record.
   - Result is MATCH FOUND.
   - Risk score is <= 15.
   - Status is safe.
3. Screenshot with matched UTR and payee, but differing amount:
   - Primary matching succeeds (Result A).
   - Informational fields show the amount difference without causing the receipt to be marked suspicious.
   - Risk score remains <= 15.
4. Screenshot with matching UTR but different payee:
   - Correctly yields Result B: RECIPIENT_NAME_MISMATCH.
   - Status is suspicious.
   - Table highlights recipient mismatch.
5. Screenshot with valid-format UTR not present in the active dataset:
   - Correctly yields Result C: NO_MATCHING_RECORD.
   - Status is suspicious.
   - Clear message explaining UTR not in active dataset.
6. Corrupted or unreadable image:
   - Yields Result D: UNABLE_TO_VERIFY_OCR_UNCERTAIN.
   - Status is suspicious or unknown.
   - Prompts user to re-upload.
7. Ambiguous dataset test:
   - When dataset contains duplicate UTRs, detector yields Result E: AMBIGUOUS_DATASET_RECORD.
8. No active dataset test:
   - When no dataset is active, detector reports NO_ACTIVE_DATASET.
9. Verification of old rule absence:
   - Assert that no code path classifies a transaction as genuine based solely on transaction ID starting with T26.
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
    deactivate_active_dataset,
    MANDATORY_DEMO_NOTICE,
)
from backend.services.screenshot_service import analyze_screenshot
from backend.utils.ocr import analyze_image_ocr
from backend.database.connection import SessionLocal
from backend.database.models import ScreenshotDataset, ScreenshotTransactionRecord

client = TestClient(app)


class TestScreenshotDetectorOCRAndVerification(unittest.TestCase):

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

        # Ensure active 50-record dataset is loaded
        csv_path = "SignalSafe_Screenshot_Detector_50_Synthetic_Datasets.csv"
        assert os.path.exists(csv_path), f"Dataset CSV {csv_path} must exist."
        with open(csv_path, "r", encoding="utf-8") as f:
            csv_content = f.read()

        act = activate_new_dataset(
            csv_content=csv_content,
            filename="SignalSafe_Screenshot_Detector_50_Synthetic_Datasets.csv",
            admin_user=cls.cyberadmin_user,
            dataset_name="JCER Official Reference Dataset",
        )
        assert act["success"] is True, "Dataset activation must succeed."

    def test_01_demonstration_screenshot_1_accurate_ocr_and_match(self):
        """
        Demonstration screenshot 1:
        - OCR extracts UTR, recipient, and amount accurately.
        - Matches active dataset record.
        - Result is MATCH FOUND (REFERENCE_DATASET_MATCH / MATCHING_DEMO_RECORD).
        - Risk score is <= 15.
        - Status is safe.
        - No false mismatch warning.
        """
        img_path = "test_screenshots/screenshot_1_match.png"
        self.assertTrue(os.path.exists(img_path))
        with open(img_path, "rb") as f:
            img_bytes = f.read()

        # Verify OCR extraction directly
        ocr_fields = analyze_image_ocr(img_bytes)
        self.assertEqual(ocr_fields.get("utr_rrn"), "750877359769")
        self.assertIn("JAIN COLLEGE", ocr_fields.get("payee_name", "").upper())
        self.assertEqual(ocr_fields.get("amount"), "1680")
        self.assertEqual(ocr_fields.get("transaction_id"), "T2605111605573710174884")

        # Verify full screenshot analysis
        res = analyze_screenshot(img_bytes)
        self.assertIn(res["classification"], ["REFERENCE_DATASET_MATCH", "MATCHING_DEMO_RECORD"])
        self.assertEqual(res["status"], "safe")
        self.assertLessEqual(res["risk_score"], 15)
        self.assertEqual(len(res.get("mismatches", [])), 0)
        self.assertIn("DEMO DATA", res.get("demo_notice", ""))

        # Verify primary comparison table
        primary = res.get("primary_comparison", [])
        self.assertGreaterEqual(len(primary), 2)
        utr_row = next(r for r in primary if "UTR" in r["field"])
        payee_row = next(r for r in primary if "Recipient" in r["field"])
        self.assertTrue(utr_row["matched"])
        self.assertTrue(payee_row["matched"])

        # No claims of bank core verification
        for r in res.get("reasons", []):
            self.assertNotIn("payment verified", r.lower())
            self.assertNotIn("genuine payment", r.lower())

    def test_02_demonstration_screenshot_2_match(self):
        """
        Demonstration screenshot 2:
        - Matches its active dataset record (REC-2026-002, UTR 604170057839).
        - Result is MATCH FOUND.
        - Risk score is <= 15.
        - Status is safe.
        """
        img_path = "test_screenshots/screenshot_2_match.png"
        self.assertTrue(os.path.exists(img_path))
        with open(img_path, "rb") as f:
            img_bytes = f.read()

        res = analyze_screenshot(img_bytes)
        self.assertIn(res["classification"], ["REFERENCE_DATASET_MATCH", "MATCHING_DEMO_RECORD"])
        self.assertEqual(res["status"], "safe")
        self.assertLessEqual(res["risk_score"], 15)
        self.assertEqual(len(res.get("mismatches", [])), 0)
        self.assertIsNotNone(res.get("matched_record"))
        self.assertEqual(res["matched_record"]["record_id"], "REC-2026-002")
        self.assertEqual(res["matched_record"]["utr_rrn"], "604170057839")

    def test_03_matched_utr_payee_differing_amount_informational(self):
        """
        Screenshot with matched UTR and payee, but differing amount:
        - Primary matching succeeds (Result A: REFERENCE_DATASET_MATCH).
        - Informational fields show the amount difference without causing the receipt to be marked suspicious.
        - Risk score remains <= 15.
        """
        img_path = "test_screenshots/screenshot_amount_mismatch.png"
        self.assertTrue(os.path.exists(img_path))
        with open(img_path, "rb") as f:
            img_bytes = f.read()

        res = analyze_screenshot(img_bytes)
        self.assertIn(res["classification"], ["REFERENCE_DATASET_MATCH", "MATCHING_DEMO_RECORD"])
        self.assertEqual(res["status"], "safe")
        self.assertLessEqual(res["risk_score"], 15)
        self.assertEqual(len(res.get("mismatches", [])), 0)

        # Informational fields exist and display amount
        info_fields = res.get("informational_fields", [])
        self.assertTrue(any(f["field"] == "Amount" for f in info_fields))

    def test_04_matching_utr_different_payee_mismatch(self):
        """
        Screenshot with matching UTR but different payee:
        - Correctly yields Result B: RECIPIENT_NAME_MISMATCH.
        - Status is suspicious.
        - Table highlights recipient mismatch.
        - Risk score is approximately 65.
        """
        img_path = "test_screenshots/screenshot_payee_mismatch.png"
        self.assertTrue(os.path.exists(img_path))
        with open(img_path, "rb") as f:
            img_bytes = f.read()

        res = analyze_screenshot(img_bytes)
        self.assertIn(res["classification"], ["RECIPIENT_NAME_MISMATCH", "DETAILS_MISMATCH"])
        self.assertEqual(res["status"], "suspicious")
        self.assertEqual(res["risk_score"], 65)
        self.assertGreaterEqual(len(res.get("mismatches", [])), 1)

        primary = res.get("primary_comparison", [])
        payee_row = next(r for r in primary if "Recipient" in r["field"])
        self.assertFalse(payee_row["matched"])
        self.assertEqual(payee_row["result"], "Mismatch")

    def test_05_valid_format_utr_not_in_active_dataset(self):
        """
        Screenshot with valid-format UTR not present in the active dataset:
        - Correctly yields Result C: NO_MATCHING_RECORD.
        - Status is suspicious.
        - Clear message explaining UTR not in active dataset.
        - Risk score is approximately 45.
        """
        img_path = "test_screenshots/screenshot_unknown_ref.png"
        self.assertTrue(os.path.exists(img_path))
        with open(img_path, "rb") as f:
            img_bytes = f.read()

        res = analyze_screenshot(img_bytes)
        self.assertEqual(res["classification"], "NO_MATCHING_RECORD")
        self.assertEqual(res["status"], "suspicious")
        self.assertGreaterEqual(res["risk_score"], 45)
        self.assertLessEqual(res["risk_score"], 65)
        self.assertIsNone(res.get("matched_record"))

        # Clear explanation present in reasons or message
        has_clear_msg = any("not found" in r.lower() or "not match" in r.lower() for r in res.get("reasons", [])) or "not found" in res.get("message", "").lower()
        self.assertTrue(has_clear_msg)

    def test_06_unreadable_or_missing_utr_yields_ocr_uncertain(self):
        """
        Corrupted or unreadable image / missing UTR:
        - Yields Result D: UNABLE_TO_VERIFY_OCR_UNCERTAIN.
        - Status is suspicious or unknown.
        - Prompts user to re-upload.
        - Risk score is approximately 40.
        """
        img_path = "test_screenshots/screenshot_no_utr.png"
        self.assertTrue(os.path.exists(img_path))
        with open(img_path, "rb") as f:
            img_bytes = f.read()

        res = analyze_screenshot(img_bytes)
        self.assertIn(res["classification"], ["UNABLE_TO_VERIFY_OCR_UNCERTAIN", "INSUFFICIENT_INFORMATION"])
        self.assertIn(res["status"], ["suspicious", "unknown"])
        self.assertLessEqual(abs(res["risk_score"] - 40), 5)

        primary = res.get("primary_comparison", [])
        utr_row = next(r for r in primary if "UTR" in r["field"])
        self.assertFalse(utr_row["matched"])
        self.assertEqual(utr_row["result"], "OCR Uncertain")

        # Actionable guidance to re-upload
        has_prompt = any("upload" in r.lower() or "clearer" in r.lower() for r in res.get("reasons", [])) or "upload" in res.get("message", "").lower()
        self.assertTrue(has_prompt)

    def test_07_ambiguous_dataset_duplicate_utr(self):
        """
        Ambiguous dataset test:
        - When dataset contains duplicate UTRs, detector yields Result E: AMBIGUOUS_DATASET_RECORD.
        - Status is suspicious.
        - Risk score is approximately 50.
        """
        session = SessionLocal()
        try:
            active_ds = session.query(ScreenshotDataset).filter_by(is_active=True).first()
            self.assertIsNotNone(active_ds)

            # Insert duplicate record sharing UTR 750877359769
            dup_rec = ScreenshotTransactionRecord(
                dataset_id=active_ds.id,
                record_id="REC-DUP-999",
                transaction_id="T2605111605573710174884-DUP",
                utr_rrn="750877359769",
                transaction_date="2026-05-11",
                transaction_time="16:06:00",
                amount_inr=1680.00,
                payee_name="JAIN COLLEGE OF ENGINEERING AND RESEARCH",
                payee_vpa="jaincollege9120@fbl",
                verification_status="verified",
            )
            session.add(dup_rec)
            session.commit()

            with open("test_screenshots/screenshot_1_match.png", "rb") as f:
                img_bytes = f.read()

            res = analyze_screenshot(img_bytes)
            self.assertEqual(res["classification"], "AMBIGUOUS_DATASET_RECORD")
            self.assertEqual(res["status"], "suspicious")
            self.assertLessEqual(abs(res["risk_score"] - 50), 15)
            self.assertIn("ambiguous", res.get("message", "").lower())

            # Clean up duplicate record
            session.delete(dup_rec)
            session.commit()
        finally:
            session.close()

    def test_08_no_active_dataset(self):
        """
        No active dataset test:
        - When no dataset is active, detector reports NO_ACTIVE_DATASET.
        - Status is suspicious.
        """
        deact = deactivate_active_dataset(self.cyberadmin_user)
        self.assertTrue(deact["success"])

        try:
            with open("test_screenshots/screenshot_1_match.png", "rb") as f:
                img_bytes = f.read()

            res = analyze_screenshot(img_bytes)
            self.assertEqual(res["classification"], "NO_ACTIVE_DATASET")
            self.assertEqual(res["status"], "suspicious")
        finally:
            # Reactivate dataset for continued normal operation
            csv_path = "SignalSafe_Screenshot_Detector_50_Synthetic_Datasets.csv"
            with open(csv_path, "r", encoding="utf-8") as f:
                csv_content = f.read()
            activate_new_dataset(
                csv_content=csv_content,
                filename="SignalSafe_Screenshot_Detector_50_Synthetic_Datasets.csv",
                admin_user=self.cyberadmin_user,
                dataset_name="JCER Official Reference Dataset",
            )

    def test_09_verification_of_old_rule_absence(self):
        """
        Verification of old rule absence:
        - Assert that no code path classifies a transaction as genuine based solely on transaction ID starting with T26.
        - Confirm source files have no startswith('T26') heuristics.
        """
        with open("backend/services/screenshot_service.py", "r", encoding="utf-8") as f:
            code_service = f.read()
        with open("backend/services/screenshot_dataset_service.py", "r", encoding="utf-8") as f:
            code_ds = f.read()

        self.assertNotIn('.startswith("T26")', code_service)
        self.assertNotIn("T26 pattern", code_service)
        self.assertNotIn('.startswith("T26")', code_ds)
        self.assertNotIn("Only 'T26' is valid", code_service)


if __name__ == "__main__":
    unittest.main()
