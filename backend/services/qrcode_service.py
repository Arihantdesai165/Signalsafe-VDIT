# -*- coding: utf-8 -*-
"""
Enhanced QR Code analysis service for SignalSafe Campus.
Decodes QR codes with multiple passes, validates UPI payment data,
executes baseline security checks (malicious links, suspicious handles),
and matches against active, approved JCER College QR registry records.
Supports dark-theme QRs, PhonePe stylized QRs with center logos,
and low-contrast or corrupted images with graceful diagnostic reporting.
"""

import re
import time
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from urllib.parse import urlparse, parse_qs, unquote
import numpy as np
import cv2
from ..utils.scoring import build_response, insufficient_evidence_response, clamp_score, score_to_status
from ..utils.ml_classifier import refine_with_ml

logger = logging.getLogger("signalsafe.qrcode")

# Try importing QR decoding libraries
try:
    import zxingcpp
    _HAS_ZXING = True
except ImportError:
    _HAS_ZXING = False

try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    _HAS_PYZBAR = True
except (ImportError, OSError, Exception):
    _HAS_PYZBAR = False

# ---------------------------------------------------------------------------
# Trusted UPI Processors (legitimate bank handles)
# These are NEVER flagged — even alone they indicate a safe transaction.
# ---------------------------------------------------------------------------
TRUSTED_UPI_PROCESSORS = [
    "@okicici", "@oksbi", "@okaxis", "@okhdfcbank",
    "@paytm", "@ybl", "@ibl", "@apl", "@upi", "@axl",
    "@sbi", "@icici", "@hdfcbank", "@pnb", "@boi", "@kotak",
    "@indus", "@federal", "@fbl", "@rbl", "@idbi", "@citi", "@hsbc",
    "@phonepe", "@gpay", "@jupiteraxis", "@barodampay", "@cnrb", "@uboi",
]

# ---------------------------------------------------------------------------
# Explicitly suspicious handles — confirmed scam patterns
# ---------------------------------------------------------------------------
SUSPICIOUS_HANDLES = [
    "@okbizaxis", "@okbiz", "@bizaxis", "@fastpay", "@quickupi",
    "@securepay", "@instantpay", "@safepay",
]

# Generic/Placeholder merchant names often used in fake QRs
GENERIC_MERCHANT_NAMES = [
    "unknown store", "merchant", "shop", "generic merchant",
    "test store", "payment recipient", "user", "customer",
    "retailer", "vendor", "store", "business",
]

# Suspicious keywords in merchant names
SUSPICIOUS_MERCHANT_KEYWORDS = [
    "lottery", "prize", "winner", "lucky", "claim", "reward",
    "free", "offer", "hack", "crack", "mod", "illegal",
    "casino", "betting", "gamble", "kyc", "refund", "bonus",
]


def _is_dark_background(img) -> Tuple[bool, float]:
    """
    Detect whether an image has a dark background / light modules (inverted polarity).
    Samples the outer perimeter corners (outer 5% perimeter).
    """
    try:
        h, w = img.shape[:2]
        if h < 20 or w < 20:
            return False, 255.0

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        bh = max(2, int(h * 0.05))
        bw = max(2, int(w * 0.05))

        tl = gray[0:bh, 0:bw]
        tr = gray[0:bh, w - bw:w]
        bl = gray[h - bh:h, 0:bw]
        br = gray[h - bh:h, w - bw:w]

        corners_mean = float((np.mean(tl) + np.mean(tr) + np.mean(bl) + np.mean(br)) / 4.0)
        return corners_mean < 115.0, corners_mean
    except Exception:
        return False, 255.0


def _try_decoders(target_img) -> Tuple[Optional[str], Optional[str]]:
    """
    Attempts decoding using available QR decoders in order of robustness:
    1. zxing-cpp (fastest, natively handles inverted polarity and center logos)
    2. pyzbar (standard zbar wrapper)
    3. OpenCV QRCodeDetector (fallback)
    Returns (decoded_text, decoder_name) or (None, None).
    """
    if target_img is None or target_img.size == 0:
        return None, None

    # 1. zxing-cpp
    if _HAS_ZXING:
        try:
            res = zxingcpp.read_barcode(target_img)
            if res and res.valid and res.text:
                txt = res.text.strip()
                if txt:
                    return txt, "zxing-cpp"
        except Exception as exc:
            logger.debug("zxing-cpp decode error: %s", exc)

    # 2. pyzbar
    if _HAS_PYZBAR:
        try:
            decoded = pyzbar_decode(target_img)
            if decoded:
                for item in decoded:
                    raw_txt = item.data.decode("utf-8", errors="ignore").strip()
                    if raw_txt:
                        return raw_txt, "pyzbar"
        except Exception as exc:
            logger.debug("pyzbar decode error: %s", exc)

    # 3. OpenCV QRCodeDetector
    try:
        detector = cv2.QRCodeDetector()
        txt, _, _ = detector.detectAndDecode(target_img)
        if txt and txt.strip():
            return txt.strip(), "opencv"
    except Exception as exc:
        logger.debug("opencv decode error: %s", exc)

    return None, None


def _decode_qr_multi_pass(img, return_diagnostics: bool = False) -> Union[str, Tuple[str, Dict[str, Any]]]:
    """
    Robust multi-pass computer vision pipeline to decode QR codes:
    - Automatically senses dark-background vs light-background polarity.
    - Applies ordered preprocessing variants:
      1. Original image
      2. Grayscale
      3. Inverted grayscale (crucial for dark theme & PhonePe dark QR)
      4. Contrast-enhanced (CLAHE) & Inverted CLAHE
      5. Otsu thresholding & Inverted Otsu
      6. Adaptive Gaussian thresholding & Inverted Adaptive
      7. Upscaling (2x Lanczos/Cubic for small QR codes)
      8. Region crops (center 75% crop & contour bounding box around QR)
    - Short-circuits on first successful decode to guarantee low latency.
    """
    t0 = time.perf_counter()
    attempts: List[str] = []

    if img is None or img.size == 0:
        diagnostics = {
            "attempts": attempts,
            "successful_pass": None,
            "successful_decoder": None,
            "is_dark_theme": False,
            "duration_ms": 0.0,
        }
        return ("", diagnostics) if return_diagnostics else ""

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
    is_dark, corner_brightness = _is_dark_background(img)

    # Prepare common filters
    inv_gray = cv2.bitwise_not(gray)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)
    inv_clahe = cv2.bitwise_not(clahe)
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    inv_otsu = cv2.bitwise_not(otsu)
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 5)
    inv_adaptive = cv2.bitwise_not(adaptive)

    # Order candidates dynamically based on polarity detection
    candidates: List[Tuple[str, np.ndarray]] = []
    if is_dark:
        candidates.extend([
            ("original", img),
            ("inverted_gray", inv_gray),
            ("inverted_clahe", inv_clahe),
            ("inverted_otsu", inv_otsu),
            ("inverted_adaptive", inv_adaptive),
            ("grayscale", gray),
            ("clahe", clahe),
            ("otsu", otsu),
        ])
    else:
        candidates.extend([
            ("original", img),
            ("grayscale", gray),
            ("clahe", clahe),
            ("otsu", otsu),
            ("adaptive", adaptive),
            ("inverted_gray", inv_gray),
            ("inverted_clahe", inv_clahe),
            ("inverted_otsu", inv_otsu),
        ])

    # Check primary candidates
    for pass_name, candidate_img in candidates:
        attempts.append(pass_name)
        decoded_text, decoder_name = _try_decoders(candidate_img)
        if decoded_text:
            duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            theme_detected = is_dark or ("inverted" in pass_name)
            diagnostics = {
                "attempts": attempts,
                "successful_pass": pass_name,
                "successful_decoder": decoder_name,
                "is_dark_theme": theme_detected,
                "corner_brightness": corner_brightness,
                "duration_ms": duration_ms,
            }
            logger.info("QR decoded in pass '%s' using decoder '%s' in %.2fms (dark_theme=%s)",
                        pass_name, decoder_name, duration_ms, theme_detected)
            return (decoded_text, diagnostics) if return_diagnostics else decoded_text

    # Upscaling pass for small QR codes (if smaller dimension < 600px)
    if min(h, w) < 600:
        scale_factor = 2
        upscaled_gray = cv2.resize(gray, (w * scale_factor, h * scale_factor), interpolation=cv2.INTER_CUBIC)
        upscaled_inv = cv2.bitwise_not(upscaled_gray)

        upscale_candidates = (
            [("upscaled_inv", upscaled_inv), ("upscaled_gray", upscaled_gray)]
            if is_dark else
            [("upscaled_gray", upscaled_gray), ("upscaled_inv", upscaled_inv)]
        )

        for pass_name, c_img in upscale_candidates:
            attempts.append(pass_name)
            decoded_text, decoder_name = _try_decoders(c_img)
            if decoded_text:
                duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                theme_detected = is_dark or ("inv" in pass_name)
                diagnostics = {
                    "attempts": attempts,
                    "successful_pass": pass_name,
                    "successful_decoder": decoder_name,
                    "is_dark_theme": theme_detected,
                    "corner_brightness": corner_brightness,
                    "duration_ms": duration_ms,
                }
                return (decoded_text, diagnostics) if return_diagnostics else decoded_text

    # Bounded Region Crop Passes (Center Crop & Contour Box Crop)
    crop_candidates = []
    # Center 75% crop
    if h > 80 and w > 80:
        y1, y2 = int(h * 0.125), int(h * 0.875)
        x1, x2 = int(w * 0.125), int(w * 0.875)
        center_crop = gray[y1:y2, x1:x2]
        center_crop_inv = inv_gray[y1:y2, x1:x2]
        if is_dark:
            crop_candidates.extend([("center_crop_inv", center_crop_inv), ("center_crop", center_crop)])
        else:
            crop_candidates.extend([("center_crop", center_crop), ("center_crop_inv", center_crop_inv)])

    # Contour-based square bounding box crop
    try:
        contours, _ = cv2.findContours(otsu, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        img_area = h * w
        for cnt in contours:
            cx, cy, cw, ch = cv2.boundingRect(cnt)
            cnt_area = cw * ch
            aspect = cw / float(ch) if ch > 0 else 0
            if cnt_area > 0.05 * img_area and 0.7 <= aspect <= 1.3:
                margin = int(min(cw, ch) * 0.10)
                bx1 = max(0, cx - margin)
                by1 = max(0, cy - margin)
                bx2 = min(w, cx + cw + margin)
                by2 = min(h, cy + ch + margin)
                box_crop = gray[by1:by2, bx1:bx2]
                box_crop_inv = inv_gray[by1:by2, bx1:bx2]
                if is_dark:
                    crop_candidates.extend([("contour_crop_inv", box_crop_inv), ("contour_crop", box_crop)])
                else:
                    crop_candidates.extend([("contour_crop", box_crop), ("contour_crop_inv", box_crop_inv)])
                break
    except Exception as exc:
        logger.debug("Contour detection error: %s", exc)

    for pass_name, c_img in crop_candidates:
        attempts.append(pass_name)
        decoded_text, decoder_name = _try_decoders(c_img)
        if decoded_text:
            duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            theme_detected = is_dark or ("inv" in pass_name)
            diagnostics = {
                "attempts": attempts,
                "successful_pass": pass_name,
                "successful_decoder": decoder_name,
                "is_dark_theme": theme_detected,
                "corner_brightness": corner_brightness,
                "duration_ms": duration_ms,
            }
            return (decoded_text, diagnostics) if return_diagnostics else decoded_text

    # No QR detected across all passes
    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    diagnostics = {
        "attempts": attempts,
        "successful_pass": None,
        "successful_decoder": None,
        "is_dark_theme": is_dark,
        "corner_brightness": corner_brightness,
        "duration_ms": duration_ms,
    }
    return ("", diagnostics) if return_diagnostics else ""


def _parse_upi_uri(text: str) -> dict:
    """
    Parse a UPI payment URI and extract parameters accurately with URL unquoting
    and whitespace normalization. Handles optional parameters (aid, mode, purpose).
    """
    text = (text or "").strip()
    if not (text.lower().startswith("upi://pay") or text.lower().startswith("upi://")):
        return {"is_upi": False}

    try:
        parsed = urlparse(text)
        params: Dict[str, str] = {}
        for k, v in parse_qs(parsed.query).items():
            if v and v[0]:
                params[k.strip().lower()] = unquote(v[0]).strip()

        pa = params.get("pa", "").lower()
        pn = " ".join(params.get("pn", "").split())
        am = params.get("am", "").replace(",", "")
        cu = params.get("cu", "INR").upper() or "INR"
        tn = " ".join(params.get("tn", "").split())
        mc = params.get("mc", "").upper()
        tr = params.get("tr", "")
        aid = params.get("aid", "")
        mode = params.get("mode", "")
        purpose = params.get("purpose", "")
        orgid = params.get("orgid", "")
        sign = params.get("sign", "")

        return {
            "is_upi": True,
            "pa": pa,
            "pn": pn,
            "am": am,
            "cu": cu,
            "tn": tn,
            "mc": mc,
            "tr": tr,
            "aid": aid,
            "mode": mode,
            "purpose": purpose,
            "orgid": orgid,
            "sign": sign,
        }
    except Exception:
        return {"is_upi": False}


def _extract_processor(upi_id: str) -> str:
    """Extract the @handle processor from a UPI ID."""
    if "@" in upi_id:
        return "@" + upi_id.split("@", 1)[1]
    return ""


def analyze_qrcode(image_bytes: bytes) -> dict:
    """
    Analyze a QR code image for fraudulent UPI payment data and verify against
    the official JCER College payment QR registry. Supports dark-theme QRs,
    PhonePe stylized QRs with center logos, and multi-pass computer vision fallback.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        fail_reasons = [
            "Could not decode image file format.",
            "Actionable Guidance: Please provide a valid PNG, JPEG, or WEBP image file.",
        ]
        res = insufficient_evidence_response("Could not decode image file.")
        res["classification"] = "UNABLE_TO_VERIFY"
        res["sub_classification"] = "DECODING_FAILED"
        res["heading"] = "Unable to Verify QR Code"
        res["is_college_verified"] = False
        res["reasons"] = fail_reasons
        res["college_verification"] = {
            "classification": "UNABLE_TO_VERIFY",
            "sub_classification": "DECODING_FAILED",
            "heading": "Unable to Verify QR Code",
            "explanation": "Could not decode image file format.",
            "is_college_verified": False,
            "registry_match": None,
            "matched_fields": [],
            "differing_fields": [],
            "security_findings": fail_reasons,
        }
        res["diagnostics"] = {
            "attempts": [],
            "successful_pass": None,
            "successful_decoder": None,
            "is_dark_theme": False,
            "duration_ms": 0.0,
        }
        return res

    decoded_text, diagnostics = _decode_qr_multi_pass(img, return_diagnostics=True)
    if not decoded_text:
        fail_reasons = [
            "No readable QR code could be detected in the uploaded image.",
            "Actionable Guidance: Ensure the QR code is well-lit, holds flat without creases, has minimal glare or shadows, and is centered squarely in the frame.",
        ]
        res = insufficient_evidence_response("No decodable QR code detected in the image.")
        res["classification"] = "UNABLE_TO_VERIFY"
        res["sub_classification"] = "DECODING_FAILED"
        res["heading"] = "Decoding Failed — Unreadable QR"
        res["is_college_verified"] = False
        res["reasons"] = fail_reasons
        res["evidence_summary"] = "No decodable QR pattern identified after multi-pass enhancement."
        res["college_verification"] = {
            "classification": "UNABLE_TO_VERIFY",
            "sub_classification": "DECODING_FAILED",
            "heading": "Decoding Failed — Unreadable QR",
            "explanation": "No decodable QR pattern could be identified after multiple enhancement passes. Please retake or crop the image.",
            "is_college_verified": False,
            "registry_match": None,
            "matched_fields": [],
            "differing_fields": [],
            "security_findings": fail_reasons,
        }
        res["diagnostics"] = diagnostics
        return res

    upi_data = _parse_upi_uri(decoded_text)

    risk_score = 0
    reasons = []
    evidence_points = 0

    # ------------------------------------------------------------------
    # Non-UPI content (URLs, random text, malformed URIs)
    # ------------------------------------------------------------------
    if not upi_data.get("is_upi"):
        if decoded_text.startswith("http"):
            risk_score += 95
            reasons.append("CRITICAL BLOCK: QR code contains a hidden phishing link instead of a secure payment address. This is a common method used to steal banking details.")
            evidence_points += 1
        else:
            risk_score += 90
            reasons.append("CRITICAL ALERT: Malformed payment data detected. This QR code does NOT contain a valid UPI payment address.")
            evidence_points += 1

        final_score = clamp_score(risk_score)
        base_res = {
            "risk_score": final_score,
            "status": score_to_status(final_score),
            "payment_to": "",
            "payee_name": "",
            "amount": "",
            "processor": "",
            "upi_uri": "",
            "confidence": "high",
            "reasons": reasons,
            "extracted_fields": {
                "Raw Data": decoded_text[:200],
                "Detected Theme": "Dark Theme" if diagnostics.get("is_dark_theme") else "Light Theme",
                "Decoder Pass": diagnostics.get("successful_pass") or "standard",
            },
            "evidence_summary": "Dangerous non-UPI content detected.",
            "decoded_data": decoded_text,
            "diagnostics": diagnostics,
        }

        # Query college registry for non-UPI response formatting
        try:
            from .college_qr_service import match_qr_against_college_registry
            college_match = match_qr_against_college_registry(decoded_text, upi_data, base_res)
            base_res["college_verification"] = college_match
            base_res["classification"] = college_match.get("classification")
            base_res["heading"] = college_match.get("heading")
            base_res["is_college_verified"] = college_match.get("is_college_verified", False)
            base_res["registry_notice"] = college_match.get("registry_notice")
        except Exception as exc:
            logger.warning("College registry lookup error on non-UPI: %s", exc)

        return base_res

    # ------------------------------------------------------------------
    # UPI Fraud Detection Rules (Baseline Security Engine)
    # ------------------------------------------------------------------
    pa = upi_data.get("pa", "")
    pn = upi_data.get("pn", "")
    am = upi_data.get("am", "")
    mc = upi_data.get("mc", "")
    processor = _extract_processor(pa)

    # Flags for baseline safety
    is_suspicious_handle = False
    is_domain_like = False
    has_high_risk_keyword = False
    has_suspicious_prefix = False

    # Rule 1: Missing or invalid UPI ID (critical)
    if not pa:
        risk_score += 85
        reasons.append("HIGH RISK: Missing recipient information in QR code.")
        evidence_points += 1
    elif "@" not in pa:
        risk_score += 85
        reasons.append(f"HIGH RISK: Invalid payment address format ('{pa}'). Legitimate payments require a '@' handle.")
        evidence_points += 1
    else:
        # Check handle against known lists
        is_trusted = any(pa.lower().endswith(s) for s in TRUSTED_UPI_PROCESSORS)
        is_suspicious_handle = any(pa.lower().endswith(s) for s in SUSPICIOUS_HANDLES)

        if is_suspicious_handle:
            risk_score += 90
            reasons.append(f"BLOCK RECOMMENDED: Confirmed scam handle '{processor}' detected. This handle has been flagged for financial fraud.")
            evidence_points += 1
        elif not is_trusted:
            # Unknown processor — moderate alert unless verified in college registry
            risk_score += 40
            reasons.append(f"Security Alert: This payment uses an unrecognized bank handle '{processor}'. Verify merchant identity before proceeding.")
            evidence_points += 1

        # Suspicious prefix (test/fake/fraud/000)
        if any(pa.lower().startswith(p) for p in ["test", "fake", "fraud", "000", "xxx"]):
            has_suspicious_prefix = True
            risk_score += 90
            reasons.append(f"BLOCK RECOMMENDED: Payment address uses a fraudulent prefix ('{pa[:4]}') common in scam operations.")
            evidence_points += 1

        # Domain-like handle (e.g. @paypal.com)
        if "." in processor:
            is_domain_like = True
            risk_score += 85
            reasons.append(f"SCAM RISK: The handle '{processor}' mimics a website to deceive users. Official UPI handles do not use domain extensions.")
            evidence_points += 1

    # Rule 2: Payee name analysis
    if not pn:
        risk_score += 35
        reasons.append("Security Warning: Merchant name is missing from the QR code.")
        evidence_points += 1
    else:
        pn_lower = pn.lower().strip()
        is_generic = any(pn_lower == g for g in GENERIC_MERCHANT_NAMES) or \
                     any(pn_lower == f"{g} {i}" for g in GENERIC_MERCHANT_NAMES for i in range(100))

        if is_generic:
            risk_score += 45
            reasons.append(f"Security Alert: Generic merchant name '{pn}' detected. Legitimate businesses usually provide their official registered name.")
            evidence_points += 1

        hits = [k for k in SUSPICIOUS_MERCHANT_KEYWORDS if k in pn_lower]
        if hits:
            has_high_risk_keyword = True
            risk_score += 90
            reasons.append(f"BLOCK RECOMMENDED: The name '{pn}' uses scam keywords ({', '.join(hits)}) to lure users.")
            evidence_points += 1

    # Rule 3: Amount anomalies
    if am:
        try:
            val = float(am)
            if val > 100000:
                risk_score += 30
                reasons.append(f"Caution: QR is requesting a very high amount (₹{val:,.2f}).")
                evidence_points += 1
            elif val <= 0:
                risk_score += 20
                reasons.append("Alert: Requested payment amount is invalid.")
                evidence_points += 1
        except ValueError:
            risk_score += 15
            reasons.append("Alert: Payment amount format is incorrect.")
            evidence_points += 1

    # Safe-baseline calculation
    has_valid_pa = pa and "@" in pa
    has_pn = bool(pn)
    is_trusted_processor = any(pa.lower().endswith(s) for s in TRUSTED_UPI_PROCESSORS) if has_valid_pa else False
    major_red_flags = is_suspicious_handle or is_domain_like or has_high_risk_keyword or has_suspicious_prefix or not has_valid_pa

    if has_valid_pa and has_pn and is_trusted_processor and not major_red_flags:
        risk_score = min(risk_score, 15)

    # ------------------------------------------------------------------
    # Layered JCER College QR Registry Matching
    # ------------------------------------------------------------------
    candidate_summary = f"{evidence_points} risk factor(s) identified."
    base_response = {
        "risk_score": clamp_score(risk_score),
        "status": score_to_status(clamp_score(risk_score)),
        "reasons": reasons,
    }

    try:
        from .college_qr_service import match_qr_against_college_registry
        college_match = match_qr_against_college_registry(decoded_text, upi_data, base_response)
    except Exception as exc:
        logger.warning("College QR matching lookup failed: %s", exc)
        college_match = {
            "classification": "UNABLE_TO_VERIFY",
            "heading": "Unable to Verify College Registry",
            "explanation": "College registry check encountered an internal error.",
            "is_college_verified": False,
            "registry_match": None,
            "matched_fields": [],
            "differing_fields": [],
            "security_findings": reasons,
        }

    classification = college_match.get("classification")

    # Combine registry verification findings with baseline security
    if classification == "VERIFIED_JCER_COLLEGE_QR":
        if not major_red_flags:
            risk_score = min(risk_score, 10)
            reasons = [
                f"Official JCER College QR Verified: Registered destination for '{college_match.get('registered_display_name')}' "
                f"({college_match.get('payment_purpose')}).",
                college_match.get("registry_notice", ""),
            ]
            candidate_summary = f"Official JCER College QR verified for {college_match.get('registered_display_name')}."
    elif classification == "KNOWN_COLLEGE_RECIPIENT_DETAILS_DIFFER":
        risk_score = max(risk_score, 65)
        diff_count = len(college_match.get("differing_fields", []))
        diff_reasons = [
            f"Known College Recipient with Discrepancies: Destination '{college_match.get('expected_upi_id')}' matches "
            f"'{college_match.get('registered_display_name')}', but {diff_count} parameter(s) differ from the approved record."
        ]
        for diff in college_match.get("differing_fields", []):
            diff_reasons.append(f"Discrepancy: {diff.get('description') or diff.get('field')}")
        reasons = diff_reasons + reasons
        candidate_summary = "Known JCER recipient detected, but payment parameters differ from official registry."
    elif classification == "OTHER_UPI_QR_NOT_REGISTERED":
        # Crucial: Legitimate external merchant / individual destination — NEVER claim fake or scam!
        if not major_red_flags:
            risk_score = min(risk_score, 15)
            reasons = [
                f"Valid External UPI QR: Payment destination '{pa}' uses recognized banking handle ({processor}).",
                "Unregistered Destination: This UPI QR does not match an approved JCER college payment destination.",
            ]
            candidate_summary = f"Valid external payment destination ({pa}), not registered in JCER catalog."
        else:
            reasons.append("Unregistered Destination: This UPI QR does not match an approved JCER college payment destination.")
    elif classification == "SUSPICIOUS_OR_UNSAFE_QR":
        risk_score = max(risk_score, 85)

    final_score = clamp_score(risk_score)
    final_status = score_to_status(final_score)

    response = {
        "risk_score": final_score,
        "status": final_status,
        "payment_to": pa,
        "payee_name": pn,
        "amount": am,
        "processor": processor,
        "upi_uri": decoded_text.strip() if final_status == "safe" else "",
        "confidence": "high",
        "reasons": reasons,
        "extracted_fields": {
            k: v for k, v in {
                "UPI ID": pa,
                "Payee Name": pn,
                "Amount": f"₹{am}" if am else "",
                "Processor": processor,
                "Currency": upi_data.get("cu", "INR"),
                "Transaction Note": upi_data.get("tn", ""),
                "Merchant Code": mc,
                "Application ID": upi_data.get("aid", ""),
                "Transaction Ref": upi_data.get("tr", ""),
                "Mode": upi_data.get("mode", ""),
                "Purpose Code": upi_data.get("purpose", ""),
                "Detected Theme": "Dark Theme" if diagnostics.get("is_dark_theme") else "Light Theme",
                "Decoder Pass": diagnostics.get("successful_pass", "standard"),
                "Decoder Engine": diagnostics.get("successful_decoder", "standard"),
            }.items() if v
        },
        "evidence_summary": candidate_summary,
        "decoded_data": decoded_text,
        "diagnostics": diagnostics,
        # College QR Verification Payload
        "classification": classification,
        "heading": college_match.get("heading"),
        "is_college_verified": college_match.get("is_college_verified", False),
        "registered_display_name": college_match.get("registered_display_name"),
        "payment_purpose": college_match.get("payment_purpose"),
        "department": college_match.get("department"),
        "official_recipient_name": college_match.get("official_recipient_name"),
        "expected_upi_id": college_match.get("expected_upi_id"),
        "expected_amount": college_match.get("expected_amount"),
        "matched_fields": college_match.get("matched_fields", []),
        "differing_fields": college_match.get("differing_fields", []),
        "registry_match": college_match.get("registry_match"),
        "registry_notice": college_match.get("registry_notice"),
        "college_verification": college_match,
    }

    return response
