import os
import joblib

# Get project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Model paths
MODEL_PATH = os.path.join(
    BASE_DIR, "ml_models", "url_logistic_model.pkl"
)

VECTORIZER_PATH = os.path.join(
    BASE_DIR, "ml_models", "url_tfidf_vectorizer.pkl"
)

# Load trained model and vectorizer
model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)

print("MODEL AND VECTORIZER LOADED SUCCESSFULLY!")

# Test URLs
test_urls = [
    "https://example.com",
    "https://www.google.com",
    "https://www.wikipedia.org",
    "http://secure-login-verify-account.xyz/login"
]

# Convert URLs into TF-IDF features
features = vectorizer.transform(test_urls)

# Generate predictions and scores
predictions = model.predict(features)
probabilities = model.predict_proba(features)

# Display results
for url, prediction, probability in zip(
    test_urls, predictions, probabilities
):
    print("\nURL:", url)
    print("Prediction:", "MALICIOUS" if prediction == 1 else "BENIGN")
    print("Benign score:", round(probability[0] * 100, 2), "%")
    print("Malicious score:", round(probability[1] * 100, 2), "%")