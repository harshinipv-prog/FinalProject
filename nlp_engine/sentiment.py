import re
from nltk.sentiment import SentimentIntensityAnalyzer

sia = SentimentIntensityAnalyzer()

NEGATIVE_KEYWORDS = {
    "crash", "slow", "bug", "issue", "problem",
    "hate", "broken", "annoying", "delay", "error"
}

def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def analyze_sentiment(text: str) -> dict:
    text = clean_text(text)
    scores = sia.polarity_scores(text)

    keyword_hits = sum(1 for k in NEGATIVE_KEYWORDS if k in text)

    complaint_intensity = min(
        1.0,
        abs(scores["compound"]) + (0.08 * keyword_hits)
    )

    return {
        "compound": round(scores["compound"], 3),
        "negative": round(scores["neg"], 3),
        "neutral": round(scores["neu"], 3),
        "positive": round(scores["pos"], 3),
        "complaint_intensity": round(complaint_intensity, 3)
    }
