# -*- coding: utf-8 -*-
"""
SignalSafe Campus - React Integration Verification Suite
Tests end-to-end integration between Vite frontend, Python FastAPI backend,
ERP session authentication, and all cybersecurity detection engines.
"""

import os
import unittest
import requests
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.auth_service import generate_signalsafe_session

client = TestClient(app)
VITE_DEV_URL = "http://localhost:5175"

class TestReactFrontendIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Generate a test student session
        cls.test_student = {
            "id": "STU-2026-TEST",
            "email": "student.test@jcer.edu",
            "firstName": "Rohan",
            "lastName": "Deshmukh",
            "role": "STUDENT",
            "department": {"name": "Computer Science & Engineering", "code": "CSE"}
        }
        session = generate_signalsafe_session(cls.test_student)
        cls.token = session["token"]
        cls.auth_headers = {"Authorization": f"Bearer {cls.token}"}

    def test_01_backend_health(self):
        """Verify Python backend is healthy and returns app metadata."""
        res = client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("app"), "SignalSafe Campus")

    def test_02_vite_proxy_or_serving(self):
        """Verify Vite dev server or FastAPI serves React index.html."""
        # Verify FastAPI serves React index.html (SPA entry)
        res_backend = client.get("/")
        self.assertEqual(res_backend.status_code, 200)
        self.assertIn("SignalSafe Campus", res_backend.text)
        self.assertIn('<div id="root"></div>', res_backend.text)

    def test_03_auth_me_endpoint(self):
        """Verify /api/auth/me returns authenticated student user profile."""
        res = client.get("/api/auth/me", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("authenticated"))
        self.assertEqual(data["user"]["name"], "Rohan Deshmukh")
        self.assertEqual(data["user"]["role"], "STUDENT")

    def test_04_fraudulent_website_detection(self):
        """Verify Fraudulent Website Detection endpoint (/api/url/phishing/analyze)."""
        payload = {"url": "http://paytem-secure-login.xyz/verify"}
        res = client.post("/api/url/phishing/analyze", json=payload, headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("risk_score", data)
        self.assertIn("status", data)
        self.assertIn("reasons", data)
        self.assertIn("extracted_fields", data)
        self.assertGreater(data["risk_score"], 35)

    def test_05_malicious_link_checker(self):
        """Verify Malicious Link Checker endpoint (/api/url/analyze)."""
        payload = {"url": "https://google.com"}
        res = client.post("/api/url/analyze", json=payload, headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("risk_score", data)
        self.assertEqual(data["status"], "safe")

    def test_06_report_incident_endpoint(self):
        """Verify Report an Incident endpoint (/api/url/report) persists report."""
        test_scam_url = "http://phishing-scam-test-domain.xyz"
        payload = {"url": test_scam_url}
        res = client.post("/api/url/report", json=payload, headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        self.assertGreaterEqual(data.get("report_count", 0), 1)

    def test_07_qr_code_scam_detector(self):
        """Verify QR Code Security endpoint (/api/qrcode/analyze) with real QR image."""
        qr_file_path = os.path.join(os.path.dirname(__file__), "datasets", "qr", "safe", "unionrealqr.jpeg")
        if not os.path.exists(qr_file_path):
            self.skipTest(f"Test QR file not found at {qr_file_path}")

        with open(qr_file_path, "rb") as f:
            files = {"file": ("unionrealqr.jpeg", f, "image/jpeg")}
            res = client.post("/api/qrcode/analyze", files=files, headers=self.auth_headers)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertIn("risk_score", data)
            self.assertIn("status", data)
            self.assertIn("payment_to", data)

    def test_08_screenshot_scam_detector(self):
        """Verify Screenshot Scam Detector endpoint (/api/screenshot/analyze)."""
        screenshot_path = os.path.join(os.path.dirname(__file__), "data", "real", "real (1).jpeg")
        if not os.path.exists(screenshot_path):
            self.skipTest(f"Test screenshot not found at {screenshot_path}")

        with open(screenshot_path, "rb") as f:
            files = {"file": ("real (1).jpeg", f, "image/jpeg")}
            res = client.post("/api/screenshot/analyze", files=files, headers=self.auth_headers)
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertIn("risk_score", data)
            self.assertIn("status", data)
            self.assertIn("extracted_fields", data)

    def test_09_unauthorized_access_rejected(self):
        """Verify protected endpoints reject requests without valid Bearer token."""
        res = client.get("/api/auth/me")
        self.assertEqual(res.status_code, 401)

        res_qr = client.post("/api/qrcode/analyze")
        self.assertEqual(res_qr.status_code, 401)

    def test_10_react_frontend_assets_exist(self):
        """Verify React application files in signalsafe-frontend."""
        base_dir = os.path.join(os.path.dirname(__file__), "signalsafe-frontend")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "package.json")))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "vite.config.js")))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "src", "App.jsx")))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "src", "pages", "Dashboard.jsx")))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "src", "pages", "QrSecurity.jsx")))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "src", "pages", "WebsiteChecker.jsx")))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "src", "pages", "LinkScanner.jsx")))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "src", "pages", "EmailDetector.jsx")))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "src", "pages", "ReportIncident.jsx")))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "src", "pages", "ScreenshotScanner.jsx")))

if __name__ == "__main__":
    unittest.main()
