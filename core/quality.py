import pandas as pd
import numpy as np
import re
from typing import Dict, Any, List

def analyze_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Performs a thorough data quality analysis on the feedback dataset.
    
    Identifies:
    - Missing timestamps
    - Missing ratings
    - Missing feedback text
    - Exact duplicate rows vs duplicate feedback text
    - Invalid ratings (outside 1-5 range)
    - Junk/meaningless feedback text
    - Emoji-only feedback text
    - Inconsistent/unparseable timestamps
    
    Returns a dictionary summarizing the issues.
    """
    report = {}
    total_rows = len(df)
    report["total_rows"] = total_rows
    
    # 1. Missing feedback text
    missing_feedback_mask = df["feedback_text"].isna() | (df["feedback_text"].astype(str).str.strip() == "")
    report["missing_feedback_count"] = int(missing_feedback_mask.sum())
    report["missing_feedback_pct"] = float((report["missing_feedback_count"] / total_rows) * 100) if total_rows > 0 else 0.0
    
    # 2. Missing ratings
    # Check for NaN, None or null
    missing_rating_mask = df["rating"].isna() | (df["rating"].astype(str).str.strip().isin(["", "NaN", "nan", "None", "null"]))
    report["missing_rating_count"] = int(missing_rating_mask.sum())
    report["missing_rating_pct"] = float((report["missing_rating_count"] / total_rows) * 100) if total_rows > 0 else 0.0
    
    # 3. Missing timestamps
    missing_timestamp_mask = df["timestamp"].isna() | (df["timestamp"].astype(str).str.strip().isin(["", "NaN", "nan", "None", "null"]))
    report["missing_timestamp_count"] = int(missing_timestamp_mask.sum())
    report["missing_timestamp_pct"] = float((report["missing_timestamp_count"] / total_rows) * 100) if total_rows > 0 else 0.0

    # 4. Duplicate rows (exact duplicate rows)
    exact_duplicates_count = int(df.duplicated(keep="first").sum())
    report["exact_duplicates_count"] = exact_duplicates_count
    report["exact_duplicates_pct"] = float((exact_duplicates_count / total_rows) * 100) if total_rows > 0 else 0.0
    
    # Duplicate feedback text (where feedback text is duplicate but rows might differ in timestamp/rating/id)
    # Exclude null feedback from this count to avoid conflating missing feedback with duplicates
    valid_feedback = df[~missing_feedback_mask]
    duplicate_feedback_text_count = int(valid_feedback.duplicated(subset=["feedback_text"], keep="first").sum())
    report["duplicate_feedback_text_count"] = duplicate_feedback_text_count
    report["duplicate_feedback_text_pct"] = float((duplicate_feedback_text_count / total_rows) * 100) if total_rows > 0 else 0.0

    # 5. Invalid Ratings (Not in range 1-5 or non-numeric)
    def is_invalid_rating(val):
        if pd.isna(val):
            return False  # Missing is captured separately
        try:
            num = float(val)
            return num < 1.0 or num > 5.0 or not num.is_integer()
        except (ValueError, TypeError):
            return True
            
    invalid_rating_mask = df["rating"].apply(is_invalid_rating)
    report["invalid_rating_count"] = int(invalid_rating_mask.sum())
    report["invalid_rating_pct"] = float((report["invalid_rating_count"] / total_rows) * 100) if total_rows > 0 else 0.0

    # 6. Emojis-only feedback
    # Pattern to match strings consisting purely of emojis and whitespace
    # Note: Using standard unicode emoji character ranges
    emoji_pattern = re.compile(
        r'^[\s\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b50\u2b06\u2b07\u2190-\u21ff\u2900-\u297f\u3030\u303d\u3297\u3299\u3030]+$'
    )
    def check_emoji_only(text):
        if pd.isna(text) or str(text).strip() == "":
            return False
        clean_text = str(text).strip()
        # Check if the text matches the emoji-only pattern
        return bool(emoji_pattern.match(clean_text))

    emoji_only_mask = df["feedback_text"].apply(check_emoji_only)
    report["emoji_only_count"] = int(emoji_only_mask.sum())
    report["emoji_only_pct"] = float((emoji_only_mask.sum() / total_rows) * 100) if total_rows > 0 else 0.0

    # 7. Junk / Meaningless records
    # Meaningless includes very short strings (< 3 chars, ignoring spaces), repetitive characters, or basic gibberish
    def is_junk_feedback(text):
        if pd.isna(text) or str(text).strip() == "":
            return False
        clean = str(text).strip()
        # Emojis only is not junk, it carries sentiment, so we exclude emoji-only from pure junk
        if check_emoji_only(clean):
            return False
        # Too short (e.g. "a", "ok", "no", "x", "12")
        if len(clean) < 3:
            return True
        # Purely numeric or special characters (e.g. "!!!", "123456")
        if re.match(r'^[0-9\W_]+$', clean):
            return True
        # Gibberish patterns like repeating letters (e.g. "asdfasdf", "xxxxx", "blahblahblah")
        # Check if characters are highly repetitive
        unique_chars = set(clean.lower().replace(" ", ""))
        if len(unique_chars) <= 2 and len(clean.replace(" ", "")) > 5:
            return True
        # Check if matches specific gibberish keyboards smash e.g. "asdf", "qwerty"
        if clean.lower() in ["asdf", "asdfg", "qwerty", "zxcv", "ghjkl"]:
            return True
        return False

    junk_mask = df["feedback_text"].apply(is_junk_feedback)
    report["junk_count"] = int(junk_mask.sum())
    report["junk_pct"] = float((junk_mask.sum() / total_rows) * 100) if total_rows > 0 else 0.0

    # 8. Inconsistent or unparseable timestamps
    def is_inconsistent_timestamp(val):
        if pd.isna(val) or str(val).strip() in ["", "NaN", "nan", "None", "null"]:
            return False  # Missing is captured separately
        try:
            pd.to_datetime(val)
            return False
        except (ValueError, TypeError):
            return True
            
    inconsistent_ts_mask = df["timestamp"].apply(is_inconsistent_timestamp)
    report["inconsistent_timestamp_count"] = int(inconsistent_ts_mask.sum())
    report["inconsistent_timestamp_pct"] = float((inconsistent_ts_mask.sum() / total_rows) * 100) if total_rows > 0 else 0.0

    # Data Quality Health Score calculation (weighted deduction system)
    # Deduct points for each data issue
    score = 100.0
    if total_rows > 0:
        score -= (report["missing_feedback_count"] / total_rows) * 100.0 * 1.5
        score -= (report["missing_rating_count"] / total_rows) * 100.0 * 0.8
        score -= (report["missing_timestamp_count"] / total_rows) * 100.0 * 0.5
        score -= (report["exact_duplicates_count"] / total_rows) * 100.0 * 0.5
        score -= (report["invalid_rating_count"] / total_rows) * 100.0 * 1.0
        score -= (report["junk_count"] / total_rows) * 100.0 * 1.2
        score -= (report["inconsistent_timestamp_count"] / total_rows) * 100.0 * 0.5
    
    report["quality_health_score"] = max(0.0, round(score, 1))
    
    return report
