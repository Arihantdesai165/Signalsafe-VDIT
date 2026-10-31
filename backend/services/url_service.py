# -*- coding: utf-8 -*-
"""
Enhanced URL analysis service for KAVACH.
Detects phishing/scam websites through advanced heuristic analysis.
"""

import re
import ssl
import socket
from urllib.parse import urlparse
import pickle
import numpy as np
import os
from datetime import datetime
from ..utils.scoring import build_response, clamp_score, score_to_status
from ..utils.url_feature_extractor import extract_url_features

# Paths for ML components
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "url_phishing_model.pkl")

# Try importing whois for domain age
try:
    import whois
    _HAS_WHOIS = True
except ImportError:
    _HAS_WHOIS = False

# Suspicious TLDs commonly used in phishing
SUSPICIOUS_TLDS = [
    ".xyz", ".top", ".club", ".online", ".site", ".icu",
    ".buzz", ".tk", ".ml", ".ga", ".cf", ".gq",
    ".work", ".click", ".link", ".info", ".stream",
]

# Phishing keywords commonly found in scam URLs
PHISHING_KEYWORDS = [
    "login", "verify", "secure", "update", "account",
    "confirm", "banking", "signin", "password", "credential",
    "suspend", "alert", "wallet", "paytm", "phonepe", "gpay",
    "reward", "prize", "winner", "claim", "free", "cashback",
    "kyc", "aadhar", "aadhaar", "pancard", "gift", "offer"
]

# Legitimate domains that should not be flagged
WHITELIST_DOMAINS = [
    "google.com", "paytm.com", "phonepe.com", "npci.org.in", 
    "sbi.co.in", "hdfcbank.com", "icicibank.com", "axisbank.com", 
    "kotak.com", "rbi.org.in", "gov.in", "nic.in", "amazon.in",
    "flipkart.com", "microsoft.com", "apple.com"
]

def _is_homograph(domain: str) -> bool:
    """Check if the domain contains mixed scripts or lookalike characters."""
    # Check for Punycode
    if domain.startswith("xn--"):
        return True
    
    # Check for lookalike characters that aren't common in legitimate domains
    lookalikes = ["0", "1", "l", "o", "v", "u"]
    # If a domain uses '0' where 'o' is expected, or '1' where 'l' is expected
    brand_lookalikes = {
        "P0YTM": "PAYTM", "PH0NEPE": "PHONEPE", "G00GLE": "GOOGLE",
        "P4YTM": "PAYTM", "S8I": "SBI", "HDFC8ANK": "HDFC"
    }
    domain_upper = domain.upper()
    for bad, good in brand_lookalikes.items():
        if bad in domain_upper:
            return True
    return False

def analyze_url(url: str) -> dict:
    """
    Analyze a URL for phishing indicators.
    """
    reasons = []
    risk_score = 0
    evidence_points = 0

    # Normalize URL
    url = url.strip()
    if not url.startswith("http"):
        # If it contains :// but not http, it might be upi:// which is handled by QR
        if "://" in url and not url.startswith("http"):
              return build_response(0, ["Not a standard web URL."], {"raw": url}, "high", "Non-HTTP protocol.")
        url = "http://" + url

    try:
        parsed = urlparse(url)
    except Exception:
        return build_response(50, ["Could not parse the URL format."], {}, "low", "Invalid format.")

    domain = parsed.hostname or ""
    path = parsed.path or ""
    full_url_lower = url.lower()

    if not domain:
        return build_response(0, ["No valid domain found in URL."], {}, "low", "Empty domain.")

    # Check if whitelisted
    for safe_domain in WHITELIST_DOMAINS:
        if domain == safe_domain or domain.endswith("." + safe_domain):
            return build_response(0, ["Trusted domain."], {"domain": domain}, "high", "Whitelisted.")

    # Rule 1: IP-based URL
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", domain):
        risk_score += 35
        reasons.append("URL uses an IP address instead of a domain name (classic phishing).")
        evidence_points += 1

    # Rule 2: Suspicious TLD
    for tld in SUSPICIOUS_TLDS:
        if domain.endswith(tld):
            risk_score += 20
            reasons.append(f"Domain uses a high-risk TLD: '{tld}'.")
            evidence_points += 1
            break

    # Rule 3: Phishing keywords in Domain or Path
    hits = [k for k in PHISHING_KEYWORDS if k in full_url_lower]
    if hits:
        # Keywords in domain are more dangerous than in path
        in_domain = any(k in domain.lower() for k in hits)
        penalty = 25 if in_domain else 15
        risk_score += penalty
        reasons.append(f"URL contains suspicious keywords: {', '.join(hits[:4])}.")
        evidence_points += 1

    # Rule 4: Excessive subdomains / Depth
    subdomain_count = domain.count(".")
    if subdomain_count >= 3:
        risk_score += 15
        reasons.append(f"Excessive subdomain nesting ({subdomain_count} levels).")
        evidence_points += 1

    # Rule 5: Homograph / Lookalike
    if _is_homograph(domain):
        risk_score += 30
        reasons.append("Domain contains lookalike characters or Punycode (Homograph attack).")
        evidence_points += 1

    # Rule 6: Credential stealing (@ symbol)
    if "@" in domain: # Credentials in URL
        risk_score += 35
        reasons.append("URL contains '@' symbol in domain — used to hide the real destination.")
        evidence_points += 1

    # Rule 7: Brand Mimicry (Typosquatting)
    brand_mimics = {
        "paytem": "paytm", "paytim": "paytm", "payatm": "paytm",
        "phonpe": "phonepe", "fonepe": "phonepe", "gpay-": "google pay",
        "amozon": "amazon", "flipkrt": "flipkart"
    }
    for mimic, real in brand_mimics.items():
        if mimic in domain.lower():
            risk_score += 30
            reasons.append(f"Domain appears to mimic trusted brand '{real}' using a typo.")
            evidence_points += 1
            break

    # Rule 8: Long URL with many params (Hiding destination)
    if len(url) > 120 or url.count("?") > 1:
        risk_score += 10
        reasons.append("Unusually complex URL — often used to obfuscate the real target.")
        evidence_points += 1

    # Rule 9: SSL Certificate Check (Lightweight)
    # If HTTPS but failing handshake = suspicious. If HTTP = neutral/slight risk.
    ssl_valid = _check_ssl(domain)
    if parsed.scheme == "https" and not ssl_valid:
        risk_score += 15
        reasons.append("HTTPS claimed but SSL certificate is invalid or self-signed.")
        evidence_points += 1
    elif parsed.scheme == "http":
        # Many small Indian shops still use HTTP, so we're cautious but not blocking
        risk_score += 5
        reasons.append("Website uses unencrypted HTTP connection.")

    # Rule 10: Domain Age (Only if WHOIS is fast/available)
    domain_age = None
    if _HAS_WHOIS:
        domain_age = _check_domain_age(domain)
        if domain_age is not None and domain_age < 30:
            risk_score += 30
            reasons.append(f"Domain is very new (created {domain_age} days ago).")
            evidence_points += 1

    # ML-Based Refinement using Linear SVM Model
    ml_probability = 0
    ml_classification = "Legitimate"
    ml_confidence_pct = 50.0
    try:
        from .ml_url_service import predict_url_safety
        ml_eval = predict_url_safety(url)
        ml_classification = ml_eval["classification"]
        ml_confidence_pct = ml_eval["confidence_percentage"]
        ml_probability = ml_eval["confidence"] if ml_eval["prediction"] == 1 else (1.0 - ml_eval["confidence"])
        if ml_eval["prediction"] == 1:
            risk_score = max(risk_score, ml_eval["risk_score"])
            reasons.append(f"ML Analysis: URL classified as Malicious ({ml_confidence_pct}% confidence).")
            evidence_points += 1
        else:
            if evidence_points == 0:
                risk_score = min(risk_score, 10)
    except Exception:
        pass
    
    # Final Calibration
    final_score = clamp_score(risk_score)
    summary = f"{evidence_points} indicator(s) identified."
    if evidence_points == 0:
        summary = "No phishing indicators found. URL appears safe."
        reasons = ["Validated against known phishing patterns and trusted domains."]

    base_response = build_response(
        risk_score=final_score,
        reasons=reasons,
        extracted_fields={
            "domain": domain,
            "scheme": parsed.scheme,
            "ssl_valid": ssl_valid,
            "domain_age_days": domain_age,
            "ml_risk_probability": round(ml_probability * 100, 1)
        },
        confidence="high" if os.path.exists(MODEL_PATH) else "medium",
        evidence_summary=summary
    )
    
    base_response["status"] = score_to_status(final_score)
    return base_response

def _check_ssl(domain: str) -> bool:
    """Check if a domain has a valid SSL certificate."""
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(2)
            s.connect((domain, 443))
        return True
    except Exception:
        return False

def _check_domain_age(domain: str) -> int | None:
    """Check domain age in days using WHOIS. Returns None if unavailable."""
    try:
        w = whois.whois(domain)
        creation_date = w.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        if creation_date:
            age = (datetime.now() - creation_date).days
            return max(age, 0)
    except Exception:
        pass
    return None
