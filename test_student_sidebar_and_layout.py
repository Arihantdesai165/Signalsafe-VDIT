# -*- coding: utf-8 -*-
"""
SignalSafe Campus - Student Sidebar and UI Layout Verification Suite.

Validates:
1. Student role navigation menu does NOT contain 'Screenshot Detector'.
2. Student role navigation preserves the exact requested item list & ordering:
   - DASHBOARD: Student Dashboard
   - SECURITY TOOLS:
     - Website Safety Checker
     - Malicious Link Scanner
     - QR Code Security
     - Report Incident
     - Phishing Email (Preview)
   - ACCOUNT:
     - My Profile
     - Security Settings
3. CyberAdmin role navigation retains 'Screenshot Detector'.
4. Sidebar width is updated to desktop 280-300px range (--sidebar-width: 290px).
5. Menu labels have no-wrap protection to avoid awkward breaks.
6. Main content container (.page-content) has removed fixed centering max-width (uses full-width 100%).
7. TopNav matches page alignment without narrow centering margins.
8. Security tool pages (WebsiteChecker, LinkScanner, QrSecurity, ReportIncident, Profile, Settings)
   use full-width flexible layout rather than narrow 840/880px containers.
"""

import os
import re
import unittest


class TestStudentSidebarAndLayout(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root_dir = os.path.dirname(os.path.abspath(__file__))
        cls.frontend_dir = os.path.join(cls.root_dir, "signalsafe-frontend")

        # Read Sidebar.jsx
        sidebar_path = os.path.join(cls.frontend_dir, "src", "components", "common", "Sidebar.jsx")
        with open(sidebar_path, "r", encoding="utf-8") as f:
            cls.sidebar_content = f.read()

        # Read index.css
        css_path = os.path.join(cls.frontend_dir, "src", "index.css")
        with open(css_path, "r", encoding="utf-8") as f:
            cls.css_content = f.read()

        # Read TopNav.jsx
        topnav_path = os.path.join(cls.frontend_dir, "src", "components", "common", "TopNav.jsx")
        with open(topnav_path, "r", encoding="utf-8") as f:
            cls.topnav_content = f.read()

    def test_01_student_nav_excludes_screenshot_detector(self):
        """Verify Screenshot Detector is removed from studentNav."""
        match = re.search(r'const studentNav = \[(.*?)\];\s*const activeNav', self.sidebar_content, re.DOTALL)
        self.assertIsNotNone(match, "studentNav array must be defined in Sidebar.jsx")
        student_block = match.group(1)

        self.assertNotIn("Screenshot Detector", student_block)
        self.assertNotIn("path: '/screenshot'", student_block)

    def test_02_student_nav_contains_required_items_in_order(self):
        """Verify studentNav contains all required items in the correct order."""
        match = re.search(r'const studentNav = \[(.*?)\];\s*const activeNav', self.sidebar_content, re.DOTALL)
        self.assertIsNotNone(match)
        student_block = match.group(1)

        expected_order = [
            ("Student Dashboard", "/dashboard"),
            ("Website Safety Checker", "/website"),
            ("Malicious Link Scanner", "/link"),
            ("QR Code Security", "/qrcode"),
            ("Report Incident", "/report"),
            ("Phishing Email", "/email"),
            ("My Profile", "/profile"),
            ("Security Settings", "/settings"),
        ]

        last_pos = 0
        for label, path in expected_order:
            pos_label = student_block.find(label, last_pos)
            self.assertNotEqual(pos_label, -1, f"Menu item '{label}' missing or out of order in studentNav")
            pos_path = student_block.find(path, last_pos)
            self.assertNotEqual(pos_path, -1, f"Path '{path}' missing or out of order in studentNav")
            last_pos = pos_path

    def test_03_cyberadmin_nav_retains_screenshot_detector(self):
        """Verify cyberAdminNav still contains Screenshot Detector."""
        match = re.search(r'const cyberAdminNav = \[(.*?)\];\s*const studentNav', self.sidebar_content, re.DOTALL)
        self.assertIsNotNone(match, "cyberAdminNav array must be defined in Sidebar.jsx")
        cyber_admin_block = match.group(1)

        self.assertIn("Screenshot Detector", cyber_admin_block)
        self.assertIn("path: '/screenshot'", cyber_admin_block)

    def test_04_sidebar_width_and_layout_css(self):
        """Verify sidebar width is set to 280-300px range and no-wrap styling is present."""
        self.assertIn("--sidebar-width: 290px", self.css_content)
        self.assertIn("margin-left: var(--sidebar-width", self.css_content)
        self.assertIn("white-space: nowrap", self.css_content)

    def test_05_page_content_is_full_width(self):
        """Verify .page-content does not have fixed-width max-width centering."""
        # Find .page-content definition
        match = re.search(r'\.page-content\s*\{([^}]+)\}', self.css_content)
        self.assertIsNotNone(match, ".page-content must be defined in index.css")
        rules = match.group(1)
        self.assertNotIn("margin: 0 auto", rules)
        self.assertIn("width: 100%", rules)

    def test_06_topnav_matches_full_width(self):
        """Verify TopNav uses 100% width and does not have centering max-width."""
        self.assertIn("app-topnav", self.topnav_content)
        self.assertNotIn("maxWidth: '1360px',", self.topnav_content)

    def test_07_security_pages_use_full_width_layout(self):
        """Verify security tool pages do not use narrow 840/880px centering containers."""
        pages_to_check = [
            "WebsiteChecker.jsx",
            "LinkScanner.jsx",
            "QrSecurity.jsx",
            "ReportIncident.jsx",
            "Profile.jsx",
            "Settings.jsx",
            "EmailDetector.jsx",
            "ScreenshotScanner.jsx",
        ]

        for page in pages_to_check:
            page_path = os.path.join(self.frontend_dir, "src", "pages", page)
            with open(page_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertNotIn("maxWidth: '880px', margin: '0 auto'", content, f"{page} still has narrow 880px container")
            self.assertNotIn("maxWidth: '840px', margin: '0 auto'", content, f"{page} still has narrow 840px container")
            self.assertIn("width: '100%'", content, f"{page} should specify width: 100%")


if __name__ == "__main__":
    unittest.main()

