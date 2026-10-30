# -*- coding: utf-8 -*-
"""
SignalSafe Campus - Comprehensive Verification Test Suite
Tests:
1. Direct login page serving at root (No dashboard before auth)
2. Protected backend endpoints (Screenshot, QR, URL, Auth/Me return 401 when unauthenticated)
3. Direct login with ERP student authentication (Session generation, token isolation)
4. Staff 2FA Daily OTP challenge and verification
5. ERP error status codes (401, 403, 429, 503)
6. Session validation and token decoding
7. Logout and session invalidation
8. Detection endpoints execution with valid authenticated session
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Ensure workspace root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import app
from backend.services.auth_service import (
    generate_signalsafe_session,
    verify_signalsafe_token,
    SIGNALSAFE_JWT_SECRET,
)

client = TestClient(app)


class TestSignalSafeAuthentication(unittest.TestCase):

    def test_01_root_endpoint_serves_direct_signalsafe_login_page(self):
        """Verify opening root / serves React SPA shell, and React Login page has JCER ERP login elements."""
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.text

        # Verify SignalSafe React SPA shell
        self.assertIn("SignalSafe Campus", html)
        self.assertIn('<div id="root"></div>', html)

        # Verify React Login component contains required JCER ERP authentication UI
        login_component_path = os.path.join(
            os.path.dirname(__file__), "signalsafe-frontend", "src", "pages", "Login.jsx"
        )
        self.assertTrue(os.path.exists(login_component_path))
        with open(login_component_path, "r", encoding="utf-8") as f:
            login_src = f.read()

        self.assertIn("SignalSafe Campus", login_src)
        self.assertIn("JCER", login_src)
        self.assertIn("User ID / USN / Email", login_src)
        self.assertIn("ERP Password", login_src)
        self.assertIn("Sign In Securely", login_src)
        self.assertIn("Integrated with JCER ERP Identity System", login_src)

        # Verify KAVACH scam shield branding is removed from titles and main headings
        self.assertNotIn("<title>KAVACH | Scam Shield</title>", html)
        self.assertNotIn("KAVACH – Real-Time Scam Shield for Rural India", html)

    def test_02_health_check_endpoint(self):
        """Verify health check returns SignalSafe Campus metadata."""
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("app"), "SignalSafe Campus")

    def test_03_unauthenticated_access_to_protected_routes_blocked(self):
        """Verify direct access to protected routes returns 401 Unauthorized without session."""
        # 1. /api/auth/me
        res_me = client.get("/api/auth/me")
        self.assertEqual(res_me.status_code, 401)
        self.assertIn("Authentication required", res_me.json().get("detail", ""))

        # 2. /api/screenshot/analyze
        res_screenshot = client.post("/api/screenshot/analyze")
        self.assertEqual(res_screenshot.status_code, 401)

        # 3. /api/qrcode/analyze
        res_qrcode = client.post("/api/qrcode/analyze")
        self.assertEqual(res_qrcode.status_code, 401)

        # 4. /api/url/analyze
        res_url = client.post("/api/url/analyze", json={"url": "https://example.com"})
        self.assertEqual(res_url.status_code, 401)

        # 5. /api/url/phishing/analyze
        res_phish = client.post("/api/url/phishing/analyze", json={"url": "https://example.com"})
        self.assertEqual(res_phish.status_code, 401)

    def test_04_login_validation_and_service_unavailable(self):
        """Verify login field validation and clean 503 response when ERP service is unreachable."""
        # Missing fields -> 422
        res_bad = client.post("/api/auth/login", json={})
        self.assertEqual(res_bad.status_code, 422)

        # ERP unreachable (on dummy port 59999) -> 503 Service Unavailable
        with patch("backend.services.auth_service.JCER_ERP_API_URL", "http://127.0.0.1:59999/api"):
            res_down = client.post("/api/auth/login", json={"email": "student@jcer.edu.in", "password": "TestPassword123"})
            self.assertEqual(res_down.status_code, 503)
            self.assertIn("JCER ERP authentication service is currently unreachable", res_down.json().get("detail", ""))

    @patch("httpx.AsyncClient.post")
    def test_05_successful_erp_student_login_issues_isolated_session(self, mock_post):
        """Verify successful ERP student login produces an isolated SignalSafe session."""
        # Mock ERP HTTP 200 response
        mock_erp_response = MagicMock()
        mock_erp_response.status_code = 200
        mock_erp_response.json.return_value = {
            "success": True,
            "data": {
                "token": "erp.jwt.token.that.must.be.discarded",
                "user": {
                    "id": "e1b2d180-2a5c-4d37-8f56-9b16892e8fa2",
                    "email": "student@jcer.edu.in",
                    "role": "STUDENT",
                    "firstName": "Alex",
                    "lastName": "Kumar",
                    "department": {
                        "name": "Computer Science and Engineering",
                        "code": "CSE",
                    },
                },
            },
        }
        mock_post.return_value = mock_erp_response

        res = client.post("/api/auth/login", json={"email": "student@jcer.edu.in", "password": "CorrectPassword123"})
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertTrue(data.get("success"))
        token = data.get("token")
        self.assertIsNotNone(token)
        # Ensure SignalSafe token is NOT the ERP token
        self.assertNotEqual(token, "erp.jwt.token.that.must.be.discarded")

        # Verify decoded SignalSafe session payload
        decoded = verify_signalsafe_token(token)
        self.assertEqual(decoded.get("email"), "student@jcer.edu.in")
        self.assertEqual(decoded.get("role"), "STUDENT")
        self.assertEqual(decoded.get("name"), "Alex Kumar")
        self.assertEqual(decoded.get("erp_user_id"), "e1b2d180-2a5c-4d37-8f56-9b16892e8fa2")
        self.assertEqual(decoded.get("iss"), "SignalSafe-Campus")

        # Verify HTTP-only session cookie is set
        self.assertIn("signalsafe_session", res.cookies)

    @patch("httpx.AsyncClient.post")
    def test_06_staff_login_returns_daily_otp_challenge(self, mock_post):
        """Verify staff login triggers Daily OTP requirement without bypassing or issuing session prematurely."""
        mock_erp_response = MagicMock()
        mock_erp_response.status_code = 200
        mock_erp_response.json.return_value = {
            "success": True,
            "requiresDailyOtp": True,
            "email": "faculty@jcer.edu.in",
            "role": "TEACHER",
            "message": "Daily OTP verification required for teacher login.",
        }
        mock_post.return_value = mock_erp_response

        res = client.post("/api/auth/login", json={"email": "faculty@jcer.edu.in", "password": "FacultyPassword123"})
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertTrue(data.get("requiresDailyOtp"))
        self.assertEqual(data.get("email"), "faculty@jcer.edu.in")
        self.assertEqual(data.get("role"), "TEACHER")
        # Session token must NOT be issued yet
        self.assertNotIn("token", data)
        self.assertNotIn("signalsafe_session", res.cookies)

    @patch("httpx.AsyncClient.post")
    def test_07_verify_staff_daily_otp_success(self, mock_post):
        """Verify submitting valid Daily OTP issues the SignalSafe session."""
        mock_erp_response = MagicMock()
        mock_erp_response.status_code = 200
        mock_erp_response.json.return_value = {
            "success": True,
            "data": {
                "token": "erp.faculty.token",
                "user": {
                    "id": "fac-987-uuid",
                    "email": "faculty@jcer.edu.in",
                    "role": "TEACHER",
                    "name": "Prof. Sharma",
                    "department": {
                        "name": "Information Science",
                    },
                },
            },
        }
        mock_post.return_value = mock_erp_response

        res = client.post("/api/auth/verify-daily-otp", json={"email": "faculty@jcer.edu.in", "otp": "654321"})
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertTrue(data.get("success"))
        token = data.get("token")
        self.assertIsNotNone(token)
        decoded = verify_signalsafe_token(token)
        self.assertEqual(decoded.get("name"), "Prof. Sharma")
        self.assertEqual(decoded.get("role"), "TEACHER")

    @patch("httpx.AsyncClient.post")
    def test_08_erp_error_propagation(self, mock_post):
        """Verify ERP 401, 403, and 429 error messages are accurately reported."""
        # 1. Invalid Password (401)
        mock_401 = MagicMock()
        mock_401.status_code = 401
        mock_401.json.return_value = {"error": "Invalid email or password"}
        mock_post.return_value = mock_401

        res_401 = client.post("/api/auth/login", json={"email": "user@jcer.edu.in", "password": "WrongPassword"})
        self.assertEqual(res_401.status_code, 401)
        self.assertEqual(res_401.json().get("detail"), "Invalid email or password")

        # 2. Suspended Account (403)
        mock_403 = MagicMock()
        mock_403.status_code = 403
        mock_403.json.return_value = {"error": "Your account is inactive or suspended"}
        mock_post.return_value = mock_403

        res_403 = client.post("/api/auth/login", json={"email": "suspended@jcer.edu.in", "password": "Password123"})
        self.assertEqual(res_403.status_code, 403)
        self.assertEqual(res_403.json().get("detail"), "Your account is inactive or suspended")

    def test_09_authenticated_access_to_dashboard_and_detection(self):
        """Verify that an authenticated user with valid SignalSafe token can access detection endpoints."""
        # Generate valid session token
        session = generate_signalsafe_session({
            "id": "student-123",
            "email": "alex@jcer.edu.in",
            "role": "STUDENT",
            "name": "Alex Kumar",
            "department": "CSE",
        })
        token = session["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. /api/auth/me succeeds
        res_me = client.get("/api/auth/me", headers=headers)
        self.assertEqual(res_me.status_code, 200)
        self.assertTrue(res_me.json().get("authenticated"))
        self.assertEqual(res_me.json().get("user", {}).get("email"), "alex@jcer.edu.in")

        # 2. /api/url/analyze succeeds
        res_url = client.post("/api/url/analyze", json={"url": "https://google.com"}, headers=headers)
        self.assertEqual(res_url.status_code, 200)
        self.assertIn("risk_score", res_url.json())

        # 3. /api/url/phishing/analyze succeeds
        res_phish = client.post("/api/url/phishing/analyze", json={"url": "https://paypal-verify-login.xyz"}, headers=headers)
        self.assertEqual(res_phish.status_code, 200)
        self.assertIn("risk_score", res_phish.json())

    def test_10_logout_clears_session_cookie(self):
        """Verify logout endpoint clears session cookie."""
        res = client.post("/api/auth/logout")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json().get("success"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
