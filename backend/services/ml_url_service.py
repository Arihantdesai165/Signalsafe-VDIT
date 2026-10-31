# -*- coding: utf-8 -*-
"""
SignalSafe Campus - ML-based Malicious URL Detection Service.
Loads the trained Linear Support Vector Classifier (LinearSVC) and TF-IDF
character n-gram vectorizer from ml_models/ to perform high-accuracy
inference for Website Safety Checker and Malicious Link Scanner.
Includes a verified trusted domain allowlist to prevent false positives on known authentic services.
"""

import os
import re
import logging
from typing import Dict, Any, Optional, Set
from urllib.parse import urlparse
import numpy as np
import joblib

logger = logging.getLogger("signalsafe.ml_url")

# Resolve model paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ML_MODELS_DIR = os.path.join(BASE_DIR, "ml_models")
MODEL_PATH = os.path.join(ML_MODELS_DIR, "url_linear_svm.pkl")
VECTORIZER_PATH = os.path.join(ML_MODELS_DIR, "url_tfidf_vectorizer.pkl")
TRUSTED_DOMAINS_FILE = os.path.join(ML_MODELS_DIR, "trusted_domains.txt")

# Core built-in verified trusted domains (manual allowlist)
BUILTIN_TRUSTED_DOMAINS: Set[str] = {
    "google.com",
    "google.co.in",
    "wikipedia.org",
    "github.com",
    "microsoft.com",
    "apple.com",
    "jcer.edu",
    "jcer.edu.in",
    "gov.in",
    "nic.in",
    "amazon.com",
    "amazon.in",
    "flipkart.com",
    "paytm.com",
    "phonepe.com",
    "sbi.co.in",
    "hdfcbank.com",
    "icicibank.com",
    "axisbank.com",
    "kotak.com",
    "rbi.org.in",
    "npci.org.in",
    "youtube.com",
    "linkedin.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "yahoo.com",
    "bing.com",
}

# Module-level singletons for lazy loading
_model = None
_vectorizer = None
_model_load_attempted = False
_model_error: Optional[str] = None


def get_trusted_domains() -> Set[str]:
    """
    Returns the set of verified trusted domains, combining built-ins
    with any user-defined entries from ml_models/trusted_domains.txt.
    """
    domains = set(BUILTIN_TRUSTED_DOMAINS)
    if os.path.isfile(TRUSTED_DOMAINS_FILE):
        try:
            with open(TRUSTED_DOMAINS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    entry = line.strip().lower()
                    if entry and not entry.startswith("#"):
                        domains.add(entry)
        except Exception as exc:
            logger.warning("Could not read custom trusted domains file: %s", exc)
    return domains


def is_whitelisted_domain(hostname: str) -> bool:
    """
    Checks if a hostname belongs to a known verified, trusted domain
    (e.g., google.com, www.google.com, accounts.google.com) to prevent
    false-positive classification from ML n-gram artifacts.
    """
    if not hostname:
        return False
    host = hostname.lower().strip().rstrip(".")
    trusted = get_trusted_domains()

    for domain in trusted:
        if host == domain or host.endswith("." + domain):
            return True
    return False


def get_model_and_vectorizer():
    """
    Lazy loads the trained LinearSVC model and TF-IDF character vectorizer.
    Maintains singleton instances in memory for sub-millisecond inference.
    """
    global _model, _vectorizer, _model_load_attempted, _model_error

    if _model is not None and _vectorizer is not None:
        return _model, _vectorizer

    if _model_load_attempted and _model_error:
        raise RuntimeError(_model_error)

    _model_load_attempted = True

    if not os.path.exists(MODEL_PATH):
        _model_error = f"Trained Linear SVM model file not found at: {MODEL_PATH}"
        logger.error(_model_error)
        raise FileNotFoundError(_model_error)

    if not os.path.exists(VECTORIZER_PATH):
        _model_error = f"Trained TF-IDF vectorizer file not found at: {VECTORIZER_PATH}"
        logger.error(_model_error)
        raise FileNotFoundError(_model_error)

    try:
        logger.info("Loading TF-IDF vectorizer from %s...", VECTORIZER_PATH)
        _vectorizer = joblib.load(VECTORIZER_PATH)

        logger.info("Loading Linear SVM model from %s...", MODEL_PATH)
        _model = joblib.load(MODEL_PATH)

        logger.info(
            "ML URL Classification Engine initialized successfully. (Classes: %s, Features: %s)",
            getattr(_model, "classes_", [0, 1]),
            getattr(_model, "coef_", np.empty((0,))).shape,
        )
        return _model, _vectorizer
    except Exception as exc:
        _model_error = f"Failed to initialize ML URL detection engine: {str(exc)}"
        logger.exception(_model_error)
        raise RuntimeError(_model_error) from exc


def sanitize_and_validate_url(raw_url: str) -> str:
    """
    Sanitizes, validates, and normalizes input URL.
    Enforces safe length constraints and basic structure without making external network calls.
    """
    if not raw_url or not isinstance(raw_url, str):
        raise ValueError("URL must be a non-empty string.")

    cleaned = raw_url.strip()

    # Limit length to prevent memory/DoS attacks
    if len(cleaned) > 2048:
        raise ValueError("URL length exceeds maximum allowed limit of 2048 characters.")

    # Remove dangerous unprintable characters or control codes
    cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", cleaned)

    # Basic structural check
    if not cleaned:
        raise ValueError("URL cannot be empty or solely whitespace.")

    # Auto-prepend scheme if missing for standardized parsing
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", cleaned):
        cleaned = "https://" + cleaned

    try:
        parsed = urlparse(cleaned)
        if not parsed.netloc and not parsed.path:
            raise ValueError("URL lacks a valid hostname, IP address, or domain destination.")
    except Exception as exc:
        raise ValueError(f"Malformed URL structure: {str(exc)}") from exc

    return cleaned


def predict_url_safety(raw_url: str, scan_type: str = "website") -> Dict[str, Any]:
    """
    Core URL safety prediction function using trained LinearSVC + TF-IDF character vectorizer,
    with automatic verified domain allowlist bypass for authentic institutions/services.
    
    Args:
        raw_url: Input URL from user
        scan_type: 'website' (Website Safety Checker) or 'link' (Malicious Link Scanner)

    Returns:
        Structured prediction dictionary with classification, confidence, scores,
        and contextual security recommendations.
    """
    cleaned_url = sanitize_and_validate_url(raw_url)
    parsed = urlparse(cleaned_url)
    hostname = (parsed.hostname or "").lower().strip()

    # 1. Manual / Verified Trusted Domain Allowlist Check
    if is_whitelisted_domain(hostname):
        classification = "Legitimate"
        status = "safe"
        status_label = "NO MALICIOUS INDICATORS DETECTED"
        summary = (
            f"Verified Legitimate Domain: '{hostname}' is recognized as an authentic, trusted destination."
        )
        recommendations = [
            "Verify that your browser displays a secure HTTPS padlock icon before entering sensitive data.",
            "Ensure the destination URL in your browser address bar matches the intended service.",
            "Never share personal passwords, USN credentials, or UPI PINs on third-party prompts.",
        ]
        precautions = [
            "Always verify that you are communicating directly with the official service.",
            "Be vigilant against fraudulent ads, external redirect links, or phishing pages hosted by third parties.",
            "Report any suspicious unsolicited messages prompting for college credentials.",
        ]
        return {
            "success": True,
            "url": cleaned_url,
            "prediction": 0,
            "classification": classification,
            "status": status,
            "status_label": status_label,
            "confidence": 0.99,
            "confidence_percentage": 99.0,
            "decision_score": -5.0,
            "risk_score": 1,
            "scan_type": scan_type,
            "summary": summary,
            "recommendations": recommendations,
            "precautions": precautions,
            "verified_trusted_domain": True,
            "model_metadata": {
                "model_type": "Linear Support Vector Classifier (LinearSVC)",
                "vectorizer": "TF-IDF Character N-gram (3-5)",
                "classes": ["0: Legitimate", "1: Malicious"],
                "dataset_scope": "996k URL Cybersecurity Dataset + Verified Trust Engine",
                "verification_source": "Verified Known-Good Domain Allowlist",
            },
        }

    # 2. Machine Learning Model Inference for General URLs
    model, vectorizer = get_model_and_vectorizer()

    # Transform raw URL into TF-IDF character n-gram feature vector
    features = vectorizer.transform([cleaned_url])

    # Linear SVM inference
    prediction = int(model.predict(features)[0])
    decision_score = float(model.decision_function(features)[0])

    # Calibrated confidence calculation via logistic sigmoid
    raw_confidence = float(1.0 / (1.0 + np.exp(-abs(decision_score))))
    clamped_confidence = min(max(raw_confidence, 0.50), 0.999)
    confidence_percentage = round(clamped_confidence * 100.0, 1)

    is_malicious = (prediction == 1)

    # 3. Contextual status labels and precautions
    if is_malicious:
        classification = "Malicious"
        status = "danger"
        status_label = "MALICIOUS WEBSITE" if scan_type == "website" else "MALICIOUS LINK"
        summary = (
            "Model classification: High-risk indicators detected. "
            "Structural patterns match confirmed phishing, credential harvesting, or malicious infrastructure."
        )
        recommendations = [
            "Do NOT open, click, or browse to this URL.",
            "Do NOT enter any JCER credentials, USN, OTPs, or passwords.",
            "Do NOT download files or execute scripts from this destination.",
            "Report this suspicious link to the campus CyberAdmin review queue immediately.",
        ]
        precautions = [
            "Phishing sites often mimic genuine student fee portals or JCER login screens.",
            "Scammers use deceptive subdomains, character replacements, and lookalike paths.",
            "Always access college services directly via the official JCER ERP portal.",
        ]
        risk_score = int(round(confidence_percentage))
    else:
        classification = "Legitimate"
        status = "safe"
        status_label = "NO MALICIOUS INDICATORS DETECTED"
        summary = (
            "Model classification: No malicious indicators detected. "
            "Structural character patterns align with legitimate, benign web addresses."
        )
        recommendations = [
            "Verify that your browser displays a secure HTTPS padlock icon before entering data.",
            "Ensure the domain name exactly matches the official institution or organization domain.",
            "Never share your UPI PIN or personal passwords on any web form.",
        ]
        precautions = [
            "Machine learning predictions provide probabilistic risk assessment and cannot guarantee complete safety.",
            "Compromised legitimate domains or new zero-day campaigns may not yet be recorded.",
            "Always exercise caution before submitting sensitive financial or academic information.",
        ]
        risk_score = int(round((1.0 - clamped_confidence) * 100.0))

    return {
        "success": True,
        "url": cleaned_url,
        "prediction": prediction,
        "classification": classification,
        "status": status,
        "status_label": status_label,
        "confidence": round(clamped_confidence, 4),
        "confidence_percentage": confidence_percentage,
        "decision_score": round(decision_score, 4),
        "risk_score": risk_score,
        "scan_type": scan_type,
        "summary": summary,
        "recommendations": recommendations,
        "precautions": precautions,
        "verified_trusted_domain": False,
        "model_metadata": {
            "model_type": "Linear Support Vector Classifier (LinearSVC)",
            "vectorizer": "TF-IDF Character N-gram (3-5)",
            "classes": ["0: Legitimate", "1: Malicious"],
            "dataset_scope": "996k URL Cybersecurity Dataset",
        },
    }
