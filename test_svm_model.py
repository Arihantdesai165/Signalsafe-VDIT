import joblib
from pathlib import Path

MODEL_DIR = Path("ml_models")

model = joblib.load(MODEL_DIR / "url_linear_svm.pkl")
vectorizer = joblib.load(MODEL_DIR / "url_tfidf_vectorizer.pkl")

test_urls = [
    "https://www.google.com",
    "https://www.wikipedia.org",
    "https://www.youtube.com",
    "https://secure-login-verify-account.xyz/login",
    "http://192.168.1.10/login"
]

print("LINEAR SVM MODEL TEST")

for url in test_urls:
    features = vectorizer.transform([url])
    prediction = model.predict(features)[0]
    score = model.decision_function(features)[0]

    result = "MALICIOUS" if prediction == 1 else "BENIGN"

    print("\nURL:", url)
    print("Prediction:", result)
    print("Decision score:", round(float(score), 4))