import pandas as pd
import numpy as np
import re
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from typing import Dict, Any, List, Tuple

# Download the VADER lexicon if not already present
try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon", quiet=True)

# Initialize VADER Sentiment Intensity Analyzer
try:
    sia = SentimentIntensityAnalyzer()
except Exception:
    # Fallback in case of network issues/incomplete nltk downloads
    sia = None

# A mapping of common emojis to text to ensure VADER captures them
EMOJI_SENTIMENT_MAP = {
    "😊": " happy positive ", "😀": " smile positive ", "😁": " grin positive ",
    "😍": " love positive ", "🥰": " adore positive ", "👍": " good support positive ",
    "🙌": " celebrate positive ", "🎉": " party positive ", "👏": " clap positive ",
    "❤️": " love positive ", "🔥": " awesome positive ", "✨": " great positive ",
    "😡": " angry negative mad ", "😠": " annoyed negative ", "🤬": " furious negative ",
    "😢": " sad negative crying ", "😭": " heartbroken negative crying ", "👎": " bad dislike negative ",
    "💩": " terrible garbage negative ", "🤮": " disgust sick negative ", "🤢": " gross negative ",
    "💀": " terrible dead negative ", "🤡": " joke nonsense negative ", "🥱": " boring negative ",
    "🤦": " facepalm frustrated negative ", "🤷": " clueless neutral ", "🙄": " roll eyes annoyed negative "
}

# Sarcasm phrase mappings
SARCASTIC_PHRASES = [
    r"\boh\s+great\b", r"\bwonderful\b.*\bcharged\b", r"\bthanks\s+for\s+nothing\b",
    r"\bbrilliant\b.*\bcrash\b", r"\blove\s+how\b", r"\bfantastic\b.*\bdelay\b",
    r"\bperfect\b.*\bbroken\b", r"\bamazing\s+service\b.*\bnot\b", r"\bgreat\s+job\b.*\bfailed\b"
]

def preprocess_text_for_sentiment(text: str) -> str:
    """
    Translates common emojis into descriptive text to enhance sentiment analyzer accuracy
    and standardizes casing.
    """
    clean_text = text.lower()
    for emoji, text_rep in EMOJI_SENTIMENT_MAP.items():
        clean_text = clean_text.replace(emoji, text_rep)
    return clean_text

def detect_sentiment(text: str) -> str:
    """
    Detects sentiment (Positive, Negative, Neutral) using VADER.
    """
    if not text or str(text).strip() == "":
        return "Neutral"
    
    # Preprocess text (including emoji expansion)
    processed = preprocess_text_for_sentiment(text)
    
    if sia:
        scores = sia.polarity_scores(processed)
        compound = scores["compound"]
        # VADER standard thresholds
        if compound >= 0.05:
            return "Positive"
        elif compound <= -0.05:
            return "Negative"
        else:
            return "Neutral"
    else:
        # Basic heuristic fallback if VADER fails to load
        positive_words = {"good", "great", "excellent", "fast", "happy", "love", "best", "perfect", "delicious", "nice", "friendly"}
        negative_words = {"bad", "worst", "slow", "terrible", "rude", "cold", "late", "crash", "bug", "error", "charge", "fail", "broken"}
        
        words = set(processed.split())
        pos_count = len(words.intersection(positive_words))
        neg_count = len(words.intersection(negative_words))
        
        if pos_count > neg_count:
            return "Positive"
        elif neg_count > pos_count:
            return "Negative"
        return "Neutral"

def detect_sarcasm(text: str, rating: float, sentiment: str) -> bool:
    """
    Identifies if a feedback text is sarcastic.
    Triggers:
    1. Text contains explicitly sarcastic phrases (e.g. 'Oh great, crashed again').
    2. Rating is very negative (1 or 2) but VADER sentiment is strongly positive (due to words like 'wonderful', 'perfect', 'amazing').
    3. Rating is very positive (5) but VADER sentiment is negative.
    """
    if not text:
        return False
    
    processed = text.lower()
    
    # 1. Regex pattern check for sarcastic tone
    for pattern in SARCASTIC_PHRASES:
        if re.search(pattern, processed):
            return True
            
    # 2. Contextual rating mismatch (Highly positive words but a rating of 1 or 2)
    # E.g. "Wonderful service, delivery rider left food in the rain." (Rating: 1)
    if not pd.isna(rating) and rating <= 2:
        positive_boosters = ["wonderful", "great", "fantastic", "perfect", "brilliant", "amazing", "excellent", "love", "thanks a lot"]
        for word in positive_boosters:
            # Word check and ensuring it isn't negated (e.g. "not wonderful")
            if word in processed and f"not {word}" not in processed:
                return True
                
    # 3. Text sarcasm cues combined with negative occurrences
    # E.g. "Thanks for double billing me, brilliant!" (Rating: 1 or 2)
    if "thanks" in processed and ("charge" in processed or "bill" in processed or "delay" in processed or "cold" in processed):
        if not pd.isna(rating) and rating <= 2:
            return True

    return False

def detect_contradiction(sentiment: str, rating: float) -> bool:
    """
    Detects contradictory reviews:
    - Rating is 5 but sentiment is Negative.
    - Rating is 1 but sentiment is Positive.
    """
    if pd.isna(rating):
        return False
    
    if rating == 5.0 and sentiment == "Negative":
        return True
    if rating == 1.0 and sentiment == "Positive":
        return True
        
    return False

def classify_category(text: str) -> str:
    """
    Classifies the feedback text into one of the business domains:
    - Billing
    - App Bug
    - Delivery
    - Staff/Support
    - Other
    """
    if not text:
        return "Other"
        
    processed = text.lower()
    
    # Define keyword weights
    categories = {
        "Billing": ["charge", "billing", "bill", "refund", "price", "wallet", "cost", "pay", "fee", "money", "overcharged", "card", "transaction", "payment", "invoice", "double charged", "charged twice", "cashback"],
        "App Bug": ["app", "bug", "crash", "lag", "error", "freeze", "frozen", "login", "signin", "logout", "loading", "button", "screen", "stuck", "update", "working", "click", "page", "slow", "functional", "ios", "android"],
        "Delivery": ["delivery", "rider", "driver", "late", "delay", "cold", "food", "address", "location", "tracking", "map", "arrive", "arrived", "deliver", "missing item", "item missing", "spilled", "packaging", "time"],
        "Staff/Support": ["support", "agent", "chat", "call", "help", "rude", "polite", "wait", "service", "customer service", "care", "response", "ticket", "assistance", "helpline", "operator", "attitude"]
    }
    
    scores = {cat: 0 for cat in categories}
    
    for cat, keywords in categories.items():
        for kw in keywords:
            # Count occurrences of the keyword
            matches = len(re.findall(r'\b' + re.escape(kw) + r'\b', processed))
            scores[cat] += matches
            
    # Find the maximum score
    max_score = 0
    best_cat = "Other"
    
    for cat, score in scores.items():
        if score > max_score:
            max_score = score
            best_cat = cat
            
    return best_cat

def generate_issue_summary(text: str, category: str, sentiment: str) -> str:
    """
    Generates a concise, one-line, business-friendly summary of the customer's feedback.
    """
    if not text or str(text).strip() == "":
        return "No feedback text provided."
        
    processed = text.strip()
    
    # Standard sentence extraction
    sentences = re.split(r'[.!?]+', processed)
    first_sentence = sentences[0].strip() if sentences else processed
    
    # Shorten first sentence if too long
    if len(first_sentence) > 60:
        first_sentence = first_sentence[:57] + "..."
        
    # Pattern matching for specific actionable summaries
    processed_lower = processed.lower()
    
    if category == "Billing":
        if "double" in processed_lower or "twice" in processed_lower:
            return "Billing: Customer charged twice for order."
        if "refund" in processed_lower:
            return "Billing: Requesting refund for order issue."
        if sentiment == "Negative":
            return f"Billing: Dispute regarding charges or prices ('{first_sentence}')."
        return "Billing: Inquiry about billing details."
        
    elif category == "App Bug":
        if "crash" in processed_lower:
            return "App Bug: Application crashes during operation."
        if "login" in processed_lower or "sign" in processed_lower:
            return "App Bug: Login or sign-in errors."
        if sentiment == "Negative":
            return f"App Bug: Technical error report ('{first_sentence}')."
        return "App Bug: Feedback regarding mobile app usability."
        
    elif category == "Delivery":
        if "late" in processed_lower or "delay" in processed_lower:
            return "Delivery: Late or delayed delivery report."
        if "cold" in processed_lower:
            return "Delivery: Food delivered cold or stale."
        if "missing" in processed_lower:
            return "Delivery: Report of missing item(s) in delivery."
        if sentiment == "Negative":
            return f"Delivery: Delayed or poor delivery experience ('{first_sentence}')."
        return "Delivery: Feedback on driver/delivery route."
        
    elif category == "Staff/Support":
        if "rude" in processed_lower:
            return "Support: Driver or support agent reported as rude."
        if "wait" in processed_lower:
            return "Support: Long wait time for support agent response."
        if sentiment == "Negative":
            return f"Support: Customer service issue ('{first_sentence}')."
        return "Support: General customer service feedback."
        
    # Fallback / "Other" category
    if sentiment == "Negative":
        return f"General Complaint: '{first_sentence}'"
    elif sentiment == "Positive":
        return f"Positive Feedback: '{first_sentence}'"
    return f"Neutral Feedback: '{first_sentence}'"

def enrich_feedback_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enriches the cleaned feedback DataFrame with NLP and heuristic classifications.
    Columns added:
    - sentiment (Positive, Negative, Neutral)
    - category (Billing, App Bug, Delivery, Staff/Support, Other)
    - sarcasm_flag (True/False)
    - contradiction_flag (True/False)
    - issue_summary (Concise summary text)
    """
    enriched_df = df.copy()
    
    # 1. Generate sentiments
    enriched_df["sentiment"] = enriched_df["feedback_text"].apply(detect_sentiment)
    
    # 2. Classify categories
    enriched_df["category"] = enriched_df["feedback_text"].apply(classify_category)
    
    # 3. Detect sarcasm (vectorized or element-wise)
    enriched_df["sarcasm_flag"] = enriched_df.apply(
        lambda row: detect_sarcasm(row["feedback_text"], row["rating"], row["sentiment"]), axis=1
    )
    
    # Adjust sentiment if sarcasm is detected (sarcasm usually implies a complaint, so change positive to negative)
    def resolve_sarcasm_sentiment(row):
        if row["sarcasm_flag"] and row["sentiment"] == "Positive":
            return "Negative"
        return row["sentiment"]
        
    enriched_df["sentiment"] = enriched_df.apply(resolve_sarcasm_sentiment, axis=1)
    
    # 4. Detect rating/text contradictions
    enriched_df["contradiction_flag"] = enriched_df.apply(
        lambda row: detect_contradiction(row["sentiment"], row["rating"]), axis=1
    )
    
    # 5. Generate issue summary
    enriched_df["issue_summary"] = enriched_df.apply(
        lambda row: generate_issue_summary(row["feedback_text"], row["category"], row["sentiment"]), axis=1
    )
    
    return enriched_df
