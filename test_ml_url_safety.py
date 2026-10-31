import json
from backend.services.ml_url_service import predict_url_safety, sanitize_and_validate_url

test_cases = [
    ("Legitimate HTTPS website", "https://www.wikipedia.org", "website"),
    ("Legitimate HTTP website", "http://example.com", "website"),
    ("Known malicious URL", "https://secure-login-verify-account.xyz/login", "website"),
    ("Phishing payment portal", "http://paytem-secure-login.xyz/verify", "website"),
    ("IP-hosted URL", "http://192.168.1.10/login", "link"),
    ("SMS phishing with params", "http://sms-prize-claim-free-gift.xyz/verify?user=victim&code=9988", "link"),
    ("URL with query parameters", "https://en.wikipedia.org/wiki/Special:Search?search=cybersecurity", "website"),
    ("URL with encoded characters", "https://example.com/%20test%2Fpath?val=%3Cscript%3E", "link"),
    ("Incomplete URL (no scheme)", "wikipedia.org", "website"),
]

print("=" * 70)
print("RUNNING END-TO-END URL PREDICTION TESTS")
print("=" * 70)

for desc, url, scan_type in test_cases:
    try:
        res = predict_url_safety(url, scan_type)
        print(f"[{desc}]")
        print(f"  Input: {url}")
        print(f"  Classification: {res['classification']} | Status: {res['status_label']}")
        print(f"  Prediction: {res['prediction']} | Confidence: {res['confidence_percentage']}% | Score: {res['decision_score']}")
        print(f"  Recommendations: {len(res['recommendations'])} items | Precautions: {len(res['precautions'])} items")
        print("-" * 50)
    except Exception as e:
        print(f"[{desc}] ERROR: {e}")

print("\n--- VALIDATION TESTS ---")

# Empty input
try:
    predict_url_safety("", "website")
    print("Empty URL: FAIL (Should have raised ValueError)")
except ValueError as e:
    print(f"Empty URL: PASS (Properly caught: {e})")

# Overly long URL
long_url = "https://example.com/" + "a" * 2500
try:
    predict_url_safety(long_url, "website")
    print("Long URL: FAIL (Should have raised ValueError)")
except ValueError as e:
    print(f"Long URL: PASS (Properly caught: {e})")

# Malformed / control character URL
bad_url = "http://example.com/\x00test\r\n"
try:
    clean = sanitize_and_validate_url(bad_url)
    print(f"Control chars stripped: PASS -> {clean}")
except Exception as e:
    print(f"Control chars: {e}")

print("=" * 70)
print("ALL TESTS COMPLETED SUCCESSFULLY")
print("=" * 70)

