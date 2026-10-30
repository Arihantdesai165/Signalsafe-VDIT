# -*- coding: utf-8 -*-
"""
SignalSafe Campus Screenshot Analysis Service.
Dataset-driven screenshot analysis that matches OCR-extracted transaction
details against the active CyberAdmin reference dataset.
Eliminates legacy prefix-based heuristics.
"""

import io
import os
import re
import numpy as np
from PIL import Image
from typing import Dict, Any

from ..utils.ocr import analyze_image_ocr
from ..utils.layout_validator import analyze_layout
from ..utils.scoring import build_response, insufficient_evidence_response, clamp_score
from ..utils.ml_feature_extractor import extract_features
from .screenshot_dataset_service import (
    match_screenshot_against_active_dataset,
    MANDATORY_DEMO_NOTICE,
)

MODEL_PATH = "screenshot_model.pkl"
_MODEL = None


def _get_model():
    """Lazy-load the Scikit-Learn model once."""
    global _MODEL
    if _MODEL is None:
        if os.path.exists(MODEL_PATH):
            try:
                import joblib
                _MODEL = joblib.load(MODEL_PATH)
            except Exception as e:
                print(f"SignalSafe: Failed to load ML model: {e}")
    return _MODEL


def _get_ml_prediction(image_bytes: bytes):
    """
    Get prediction and confidence using the feature-based ML model.
    Returns (prediction_label, confidence_score)
    """
    model = _get_model()
    if not model:
        return "UNKNOWN", 0.0

    try:
        features = extract_features(image_bytes)
        X = features.reshape(1, -1)
        probs = model.predict_proba(X)[0]
        real_prob = probs[1]
        prediction = "REAL" if real_prob > 0.5 else "FAKE"
        confidence = float(real_prob if real_prob > 0.5 else (1.0 - real_prob))
        return prediction, confidence
    except Exception as e:
        print(f"SignalSafe: ML Prediction error: {e}")
        return "UNKNOWN", 0.0


# Known legitimate UPI suffixes for advisory checks
KNOWN_UPI_SUFFIXES = [
    "@okicici", "@oksbi", "@okaxis", "@okhdfcbank", "@okbizaxis",
    "@paytm", "@ybl", "@ibl", "@apl", "@upi", "@axl",
    "@sbi", "@icici", "@hdfcbank", "@pnb", "@boi", "@kotak",
    "@indus", "@federal", "@rbl", "@idbi", "@citi", "@hsbc",
    "@phonepe", "@gpay", "@jupiteraxis",
]

# Suspicious keywords in merchant names
SUSPICIOUS_MERCHANT_KEYWORDS = [
    "lottery", "prize", "winner", "lucky", "claim", "reward",
    "free", "offer", "hack", "crack", "mod", "illegal",
    "casino", "betting", "gamble", "loan", "cash"
]


def analyze_screenshot(image_bytes: bytes) -> dict:
    """
    Main entry point for payment screenshot analysis.
    Executes dataset-driven verification:
    1. Extracts structured fields via OCR.
    2. Performs computer vision layout and template analysis.
    3. Compares extracted fields against active reference dataset.
    4. Evaluates secondary indicators (layout anomalies, ML tampering detection).
    5. Returns unified, explainable result with mandatory DEMO DATA notice.
    """
    # 1. Layout & Template Analysis
    layout_res = analyze_layout(image_bytes)
    identified_app = layout_res.get('template', 'unknown')

    # 2. OCR Analysis
    fields = analyze_image_ocr(image_bytes)
    if "error" in fields:
        return insufficient_evidence_response("Could not process image file. Please upload a valid PNG or JPEG receipt.")

    ocr_conf = fields.get('ocr_confidence', 0.0)
    raw_text = fields.get('raw_text_preview', '').strip()

    if not raw_text and ocr_conf < 20:
        return insufficient_evidence_response(
            "No text could be extracted from the image. Please upload a clearer, uncropped screenshot."
        )

    # 3. Reference Dataset Matching
    # (Matches against the active CyberAdmin dataset stored in PostgreSQL)
    dataset_match = match_screenshot_against_active_dataset(fields)
    classification = dataset_match.get("classification", "INSUFFICIENT_INFORMATION")

    reasons = []
    evidence_points = 0
    final_score = dataset_match.get("risk_score", 45)
    status = dataset_match.get("status", "suspicious")

    # 4. Integrate Dataset Classification & Build Reasons
    if classification in ("REFERENCE_DATASET_MATCH", "MATCHING_DEMO_RECORD"):
        final_score = dataset_match.get("risk_score", 15)
        status = "safe"
        reasons.append("The extracted UTR/RRN and recipient name match a record in the active demonstration dataset.")
        reasons.append(f"Match Method: {dataset_match.get('match_method', 'Exact UTR/RRN & Recipient Name Match')}.")
        reasons.append(f"{MANDATORY_DEMO_NOTICE}: Matches synthetic reference dataset; does not constitute real bank verification.")

    elif classification in ("RECIPIENT_NAME_MISMATCH", "DETAILS_MISMATCH"):
        final_score = dataset_match.get("risk_score", 65)
        status = "suspicious"
        reasons.append(
            dataset_match.get(
                "message",
                "The extracted UTR/RRN matches a dataset record, but the recipient name differs from the expected recipient. Manual verification is recommended."
            )
        )
        for m in dataset_match.get("mismatches", []):
            reasons.append(f"Discrepancy: {m}")
        reasons.append(f"{MANDATORY_DEMO_NOTICE}: Reference verification completed against demonstration dataset.")
        evidence_points += len(dataset_match.get("mismatches", [])) or 1

    elif classification == "NO_MATCHING_RECORD":
        final_score = dataset_match.get("risk_score", 45)
        status = "suspicious"
        reasons.append(
            dataset_match.get(
                "message",
                "The UTR/RRN was not found in the currently active demonstration dataset. This does not, by itself, prove that the payment is fake."
            )
        )
        reasons.append(f"{MANDATORY_DEMO_NOTICE}: Reference verification completed against demonstration dataset.")
        evidence_points += 1

    elif classification in ("UNABLE_TO_VERIFY_OCR_UNCERTAIN", "INSUFFICIENT_INFORMATION"):
        final_score = dataset_match.get("risk_score", 40)
        status = "suspicious"
        reasons.append(
            dataset_match.get(
                "message",
                "Unable to Verify — OCR Uncertain: The UTR/RRN could not be read reliably from the screenshot. Please upload a clearer, uncropped screenshot of the receipt."
            )
        )
        reasons.append(f"{MANDATORY_DEMO_NOTICE}: Reference verification completed against demonstration dataset.")
        evidence_points += 1

    elif classification == "AMBIGUOUS_DATASET_RECORD":
        final_score = dataset_match.get("risk_score", 50)
        status = "suspicious"
        reasons.append(
            dataset_match.get(
                "message",
                "Multiple records in the active reference dataset share this UTR/RRN. Ambiguous dataset records require CyberAdmin review."
            )
        )
        reasons.append(f"{MANDATORY_DEMO_NOTICE}: Reference verification completed against demonstration dataset.")
        evidence_points += 1

    elif classification == "NO_ACTIVE_DATASET":
        final_score = dataset_match.get("risk_score", 40)
        status = "suspicious"
        reasons.append("No reference dataset is currently active. Verification against campus records is unavailable.")
        reasons.append(f"{MANDATORY_DEMO_NOTICE}: Reference dataset is inactive.")
        evidence_points += 1

    # 5. Secondary Checks: Suspicious Merchant Keywords & Handle Anomalies
    # Only applied if NOT a verified demonstration dataset match
    if classification not in ("REFERENCE_DATASET_MATCH", "MATCHING_DEMO_RECORD"):
        mname = fields.get('merchant_name') or fields.get('payee_name')
        if mname:
            hits = [k for k in SUSPICIOUS_MERCHANT_KEYWORDS if k in mname.lower()]
            if hits:
                final_score = min(100, final_score + 20)
                reasons.append(f"Recipient name contains suspicious keyword(s): {', '.join(hits)}.")
                evidence_points += 1

        upi = fields.get('upi_id') or fields.get('payee_vpa')
        if upi:
            has_known_suffix = any(upi.endswith(s) for s in KNOWN_UPI_SUFFIXES)
            if not has_known_suffix:
                reasons.append(f"UPI ID handle '{upi}' uses an uncommon domain suffix.")

        # 6. Secondary Layout & ML Tampering Indicators
        ml_prediction, ml_confidence = _get_ml_prediction(image_bytes)
        if ml_prediction == "FAKE" and ml_confidence > 0.75:
            final_score = min(100, final_score + 15)
            reasons.append(f"AI tampering detector flagged potential visual manipulation ({ml_confidence:.1%} confidence).")
            evidence_points += 1
    else:
        ml_prediction, ml_confidence = _get_ml_prediction(image_bytes)

    # Format extracted fields for response
    clean_extracted_fields = {
        "transaction_id": fields.get("transaction_id") or fields.get("txn_id"),
        "utr_rrn": fields.get("utr_rrn") or fields.get("bank_ref"),
        "amount": fields.get("amount"),
        "currency": fields.get("currency", "INR"),
        "payee_name": fields.get("payee_name") or fields.get("merchant_name"),
        "payee_vpa": fields.get("payee_vpa") or fields.get("upi_id"),
        "transaction_date": fields.get("transaction_date") or fields.get("date"),
        "transaction_time": fields.get("transaction_time") or fields.get("time"),
        "payment_status": fields.get("payment_status") or fields.get("status"),
        "payer_account_masked": fields.get("payer_account_masked"),
        "bank_or_app_label": fields.get("bank_or_app_label") or fields.get("app_name") or fields.get("bank_name"),
    }
    # Filter out None values
    clean_extracted_fields = {k: v for k, v in clean_extracted_fields.items() if v is not None}

    # Confidence calculation
    conf_level = "high" if ocr_conf > 70 else ("medium" if ocr_conf > 40 else "low")

    # Evidence summary
    if classification in ("REFERENCE_DATASET_MATCH", "MATCHING_DEMO_RECORD"):
        evidence_summary = f"Matched demonstration dataset (v{dataset_match.get('dataset_version', 1)}). {MANDATORY_DEMO_NOTICE}."
    elif classification in ("RECIPIENT_NAME_MISMATCH", "DETAILS_MISMATCH"):
        evidence_summary = f"Recipient name mismatch detected against reference dataset record (v{dataset_match.get('dataset_version', 1)})."
    elif classification == "NO_MATCHING_RECORD":
        evidence_summary = "No matching reference record found in active demonstration dataset."
    elif classification in ("UNABLE_TO_VERIFY_OCR_UNCERTAIN", "INSUFFICIENT_INFORMATION"):
        evidence_summary = "OCR could not reliably extract UTR/RRN identifier from screenshot."
    elif classification == "AMBIGUOUS_DATASET_RECORD":
        evidence_summary = "Ambiguous record: multiple reference dataset entries share this UTR/RRN."
    elif classification == "NO_ACTIVE_DATASET":
        evidence_summary = "No active reference dataset configured."
    else:
        evidence_summary = f"{evidence_points} verification indicator(s) noted."

    response = {
        "risk_score": clamp_score(final_score),
        "status": status,
        "confidence": conf_level,
        "ocr_confidence": round(ocr_conf, 2),
        "reasons": reasons,
        "extracted_fields": clean_extracted_fields,
        "evidence_summary": evidence_summary,
        "classification": classification,
        "heading": dataset_match.get("heading", "Screenshot Analysis"),
        "message": dataset_match.get("message", ""),
        "demo_notice": MANDATORY_DEMO_NOTICE,
        "matched_record": dataset_match.get("matched_record"),
        "primary_comparison": dataset_match.get("primary_comparison", []),
        "informational_fields": dataset_match.get("informational_fields", []),
        "comparison_fields": dataset_match.get("comparison_fields", []),
        "mismatches": dataset_match.get("mismatches", []),
        "dataset_match": dataset_match,
        "layout_valid": layout_res.get('layout_score', 0) > 0.6,
        "app_identified": identified_app,
        "ml_prediction": ml_prediction,
        "ml_confidence": round(ml_confidence, 4),
    }

    return response
