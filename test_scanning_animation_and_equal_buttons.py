# -*- coding: utf-8 -*-
"""
SignalSafe Campus - Scanning Animation and Equal Buttons Verification Suite.

Validates:
1. QrSecurity.jsx:
   - Polished viewfinder container (.qr-preview-container) with corner brackets (.qr-corner).
   - Animated blue laser scanning overlay (.qr-scan-line).
   - Equal-sized buttons inside the white card (.qr-action-btn).
   - Minimum presentation time logic (5-8s range) with rotating progress messages.
   - Result display only after analysis completes (!isAnalyzing).
2. ScreenshotScanner.jsx:
   - Polished receipt viewfinder (.receipt-preview-container) with corner brackets (.receipt-corner).
   - Animated blue laser scanning overlay (.receipt-scan-line).
   - Equal-sized buttons inside the white card (.receipt-action-btn).
   - Minimum presentation time logic (5-8s range) with rotating progress messages.
   - Result display only after analysis completes (!isAnalyzing).
3. index.css:
   - Scanning laser keyframe animations (@keyframes qrLaserScan, @keyframes receiptLaserScan).
   - Equal width button definitions and responsive mobile rules.
   - prefers-reduced-motion media queries.
"""

import os
import unittest


class TestScanningAnimationAndEqualButtons(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root_dir = os.path.dirname(os.path.abspath(__file__))
        cls.frontend_dir = os.path.join(cls.root_dir, "signalsafe-frontend")

        # Read QrSecurity.jsx
        qr_path = os.path.join(cls.frontend_dir, "src", "pages", "QrSecurity.jsx")
        with open(qr_path, "r", encoding="utf-8") as f:
            cls.qr_content = f.read()

        # Read ScreenshotScanner.jsx
        screenshot_path = os.path.join(cls.frontend_dir, "src", "pages", "ScreenshotScanner.jsx")
        with open(screenshot_path, "r", encoding="utf-8") as f:
            cls.screenshot_content = f.read()

        # Read index.css
        css_path = os.path.join(cls.frontend_dir, "src", "index.css")
        with open(css_path, "r", encoding="utf-8") as f:
            cls.css_content = f.read()

    def test_01_qr_security_viewfinder_and_laser(self):
        """Verify QR scanner viewfinder container and animated laser overlay."""
        self.assertIn("qr-preview-container", self.qr_content)
        self.assertIn("qr-corner qr-corner-tl", self.qr_content)
        self.assertIn("qr-corner qr-corner-tr", self.qr_content)
        self.assertIn("qr-corner qr-corner-bl", self.qr_content)
        self.assertIn("qr-corner qr-corner-br", self.qr_content)
        self.assertIn("qr-scan-laser-wrap", self.qr_content)
        self.assertIn("qr-scan-line", self.qr_content)
        self.assertIn("qr-scan-glow-sweep", self.qr_content)

    def test_02_qr_security_equal_action_buttons(self):
        """Verify QR scanner action buttons have shared equal-sized class inside the card."""
        self.assertIn("qr-action-buttons", self.qr_content)
        self.assertIn("btn-secondary qr-action-btn", self.qr_content)
        self.assertIn("btn-primary qr-action-btn", self.qr_content)
        self.assertIn("disabled={isAnalyzing}", self.qr_content)

    def test_03_qr_security_minimum_presentation_delay(self):
        """Verify QR scanner enforces 5-8s phased presentation delay."""
        self.assertIn("Reading QR pattern", self.qr_content)
        self.assertIn("Extracting destination", self.qr_content)
        self.assertIn("Checking destination safety", self.qr_content)
        self.assertIn("Preparing security assessment", self.qr_content)
        self.assertIn("Promise.all", self.qr_content)
        self.assertIn("!isAnalyzing", self.qr_content)

    def test_04_screenshot_detector_viewfinder_and_laser(self):
        """Verify Screenshot detector receipt viewfinder and animated laser overlay."""
        self.assertIn("receipt-preview-container", self.screenshot_content)
        self.assertIn("receipt-corner receipt-corner-tl", self.screenshot_content)
        self.assertIn("receipt-corner receipt-corner-tr", self.screenshot_content)
        self.assertIn("receipt-corner receipt-corner-bl", self.screenshot_content)
        self.assertIn("receipt-corner receipt-corner-br", self.screenshot_content)
        self.assertIn("receipt-scan-laser-wrap", self.screenshot_content)
        self.assertIn("receipt-scan-line", self.screenshot_content)
        self.assertIn("receipt-scan-glow-sweep", self.screenshot_content)

    def test_05_screenshot_detector_equal_action_buttons(self):
        """Verify Screenshot detector action buttons have shared equal-sized class inside the card."""
        self.assertIn("receipt-action-buttons", self.screenshot_content)
        self.assertIn("btn-secondary receipt-action-btn", self.screenshot_content)
        self.assertIn("btn-primary receipt-action-btn", self.screenshot_content)
        self.assertIn("disabled={isAnalyzing}", self.screenshot_content)
        self.assertIn("Choose Another Image", self.screenshot_content)
        self.assertIn("Verify Receipt Against Dataset", self.screenshot_content)

    def test_06_screenshot_detector_minimum_presentation_delay(self):
        """Verify Screenshot detector enforces 5-8s phased presentation delay."""
        self.assertIn("Reading receipt text", self.screenshot_content)
        self.assertIn("Extracting transaction details", self.screenshot_content)
        self.assertIn("Checking payment reference", self.screenshot_content)
        self.assertIn("Comparing with campus reference dataset", self.screenshot_content)
        self.assertIn("Promise.all", self.screenshot_content)
        self.assertIn("result && !isAnalyzing", self.screenshot_content)

    def test_07_css_animations_and_responsive_rules(self):
        """Verify CSS contains laser scan keyframes and equal width button rules."""
        self.assertIn("@keyframes qrLaserScan", self.css_content)
        self.assertIn("@keyframes receiptLaserScan", self.css_content)
        self.assertIn(".qr-action-btn", self.css_content)
        self.assertIn(".receipt-action-btn", self.css_content)
        self.assertIn("prefers-reduced-motion", self.css_content)


if __name__ == "__main__":
    unittest.main()
