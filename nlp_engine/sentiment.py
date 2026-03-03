import re
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification


# -----------------------------------------------------
# Model Configuration
# -----------------------------------------------------

MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"
THRESHOLD = 0.6   # τ for Equation (2)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()


# -----------------------------------------------------
# Expanded Pain / Unmet Need Lexicon
# -----------------------------------------------------

NEGATIVE_KEYWORDS = {
    # Performance issues
    "slow", "lag", "crash", "freeze", "glitch", "timeout", "delay",

    # Bugs & technical problems
    "bug", "issue", "problem", "error", "broken", "not working",
    "failure", "fault", "defect",

    # Frustration & dissatisfaction
    "hate", "annoying", "frustrating", "useless",
    "terrible", "worst", "awful", "disappointed",

    # Explicit unmet need signals
    "need", "wish", "should have", "missing",
    "lack", "could be better", "improve", "improvement",

    # Pricing pain
    "expensive", "overpriced", "costly", "price increase",

    # Support/service issues
    "no response", "no support", "unhelpful", "no solution"
}


# -----------------------------------------------------
# Text Cleaning
# -----------------------------------------------------

def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# -----------------------------------------------------
# Sentiment & Opportunity Detection
# -----------------------------------------------------

def analyze_sentiment(text: str) -> dict:
    text = clean_text(text)

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = F.softmax(logits, dim=1)

    # SST-2 output:
    # index 0 = negative
    # index 1 = positive
    negative_prob = probs[0][0].item()
    positive_prob = probs[0][1].item()

    # -------------------------------------------------
    # Equation (1)
    # P_opportunity(pi) = σ(W · vi + b)
    # Here classifier head already learned W and b
    # We treat negative probability as opportunity signal
    # -------------------------------------------------

    popportunity = negative_prob

    # -------------------------------------------------
    # Equation (2)
    # S = {pi | P_opportunity >= τ}
    # -------------------------------------------------

    is_relevant = popportunity >= THRESHOLD

    # Create VADER-like compound score for compatibility
    compound = positive_prob - negative_prob
    neutral_prob = 1 - abs(compound)

    # -------------------------------------------------
    # Keyword Amplification for Explicit Pain
    # -------------------------------------------------

    keyword_hits = sum(text.count(k) for k in NEGATIVE_KEYWORDS)
    keyword_boost = min(0.3, 0.05 * keyword_hits)

    complaint_intensity = min(
        1.0,
        abs(compound) + keyword_boost
    )

    # Sentiment label
    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return {
        "label": label,
        "compound": round(compound, 3),
        "negative": round(negative_prob, 3),
        "neutral": round(neutral_prob, 3),
        "positive": round(positive_prob, 3),
        "complaint_intensity": round(complaint_intensity, 3),
        "popportunity": round(popportunity, 3),
        "is_opportunity": is_relevant
    }