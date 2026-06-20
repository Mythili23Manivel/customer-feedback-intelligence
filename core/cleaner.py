import pandas as pd
import numpy as np
import re
from typing import Dict, Any, List, Tuple
from core.quality import analyze_data_quality

def clean_feedback_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Cleans the raw customer feedback dataset based on strict enterprise data rules:
    1. Keeps original structure trustworthy - does NOT impute missing ratings.
    2. Flags missing ratings with 'rating_missing = True/False'.
    3. Flags missing timestamps with 'timestamp_missing = True/False'.
    4. Removes only exact duplicate rows to preserve multiple independent reports.
    5. Flags duplicate feedback text using 'duplicate_feedback_flag = True/False'.
    6. Permanently deletes records ONLY if feedback_text is missing or is meaningless junk.
    7. Normalizes text (whitespace, capitalization, handles emojis).
    8. Standardizes timestamps into standard ISO 8601-like formats (YYYY-MM-DD HH:MM:SS).
    
    Returns:
    - cleaned_df: Cleaned and flagged DataFrame.
    - audit_log: List of strings describing each cleaning step and rows affected.
    """
    audit_log = []
    initial_rows = len(df)
    audit_log.append(f"Starting cleaning pipeline with {initial_rows} raw records.")
    
    # Work on a copy of the dataframe to prevent SettingWithCopyWarning
    cleaned_df = df.copy()
    
    # Ensure standard column names exist, if not, align them
    required_cols = ["id", "timestamp", "source", "rating", "feedback_text"]
    for col in required_cols:
        if col not in cleaned_df.columns:
            cleaned_df[col] = np.nan
            audit_log.append(f"Missing column '{col}' initialized with NaN.")

    # 1. Flag missing ratings
    # Convert empty ratings to NaN
    cleaned_df["rating"] = pd.to_numeric(cleaned_df["rating"], errors="coerce")
    cleaned_df["rating_missing"] = cleaned_df["rating"].isna()
    missing_ratings_count = cleaned_df["rating_missing"].sum()
    audit_log.append(f"Identified {missing_ratings_count} records with missing/invalid ratings. Created 'rating_missing' flag.")

    # 2. Flag missing timestamps
    cleaned_df["timestamp_missing"] = cleaned_df["timestamp"].isna() | (cleaned_df["timestamp"].astype(str).str.strip().isin(["", "NaN", "nan", "None", "null"]))
    missing_timestamps_count = cleaned_df["timestamp_missing"].sum()
    audit_log.append(f"Identified {missing_timestamps_count} records with missing timestamps. Created 'timestamp_missing' flag.")

    # 3. Text Normalization & Junk Detection
    # Clean text: trim whitespace, normalize spacing, keep emojis intact
    def pre_normalize_text(val):
        if pd.isna(val):
            return ""
        text = str(val).strip()
        # Replace multiple spaces/newlines with a single space
        text = re.sub(r'\s+', ' ', text)
        return text

    cleaned_df["feedback_text"] = cleaned_df["feedback_text"].apply(pre_normalize_text)

    # Re-evaluate missing feedback (after whitespace stripping)
    empty_feedback_mask = cleaned_df["feedback_text"] == ""
    empty_count = empty_feedback_mask.sum()
    
    # Define meaningless junk
    emoji_pattern = re.compile(
        r'^[\s\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b50\u2b06\u2b07\u2190-\u21ff\u2900-\u297f\u3030\u303d\u3297\u3299\u3030]+$'
    )
    
    def is_junk_text(text):
        if text == "":
            return False
        # If emoji only, it is NOT junk (preserves emoji feedback)
        if emoji_pattern.match(text):
            return False
        # Too short (< 3 characters)
        if len(text) < 3:
            return True
        # Purely numbers and punctuation
        if re.match(r'^[0-9\W_]+$', text):
            return True
        # Keyboard smash patterns
        if text.lower() in ["asdf", "asdfg", "qwerty", "zxcv", "ghjkl"]:
            return True
        # High repetition of unique characters
        unique_chars = set(text.lower().replace(" ", ""))
        if len(unique_chars) <= 2 and len(text.replace(" ", "")) > 5:
            return True
        return False

    junk_mask = cleaned_df["feedback_text"].apply(is_junk_text)
    junk_count = junk_mask.sum()

    # Filter out empty and junk records
    delete_mask = empty_feedback_mask | junk_mask
    deleted_count = delete_mask.sum()
    
    cleaned_df = cleaned_df[~delete_mask].copy()
    audit_log.append(f"Removed {empty_count} records with empty feedback and {junk_count} meaningless/junk feedback records. Total filtered: {deleted_count} records.")

    # 4. Remove ONLY exact duplicate rows (preserving independent identical messages)
    before_exact_dup = len(cleaned_df)
    cleaned_df = cleaned_df.drop_duplicates(keep="first")
    exact_dup_removed = before_exact_dup - len(cleaned_df)
    audit_log.append(f"Deduplicated dataset: Removed {exact_dup_removed} exact duplicate rows. Retained first occurrences.")

    # 5. Flag duplicate feedback text (to allow business dashboard to report repeated complaint volume)
    # Marks True if the feedback text has been seen before in the dataset, but keeps the row in the df
    cleaned_df["duplicate_feedback_flag"] = cleaned_df.duplicated(subset=["feedback_text"], keep="first")
    duplicate_feedback_text_count = cleaned_df["duplicate_feedback_flag"].sum()
    audit_log.append(f"Identified {duplicate_feedback_text_count} instances of duplicate feedback text. Tagged with 'duplicate_feedback_flag = True'.")

    # 6. Standardize Timestamps
    # Parse dates safely, using pandas datetime features, fallback to NaT
    def parse_and_standardize_timestamp(val):
        if pd.isna(val) or str(val).strip() in ["", "NaN", "nan", "None", "null"]:
            return pd.NaT
        val_str = str(val).strip()
        
        # Check if Unix Epoch timestamp (10 or 13 digits)
        if val_str.isdigit():
            try:
                num = int(val_str)
                if len(val_str) == 13: # milliseconds
                    return pd.to_datetime(num, unit='ms')
                elif len(val_str) == 10: # seconds
                    return pd.to_datetime(num, unit='s')
            except Exception:
                pass
                
        # Standard pandas parsing with format inferencing
        try:
            return pd.to_datetime(val_str, errors="coerce")
        except Exception:
            return pd.NaT

    cleaned_df["cleaned_timestamp"] = cleaned_df["timestamp"].apply(parse_and_standardize_timestamp)
    
    # Format cleaned timestamps as string YYYY-MM-DD HH:MM:SS, keeping NaT as NaT/None
    def format_timestamp(dt):
        if pd.isna(dt):
            return None
        return dt.strftime("%Y-%m-%d %H:%M:%S")
        
    cleaned_df["standardized_timestamp"] = cleaned_df["cleaned_timestamp"].apply(format_timestamp)
    # Drop the temporary datetime column
    cleaned_df = cleaned_df.drop(columns=["cleaned_timestamp"])
    
    # Record timestamp normalization results
    unparseable_timestamps = cleaned_df["standardized_timestamp"].isna().sum() - cleaned_df["timestamp_missing"].sum()
    audit_log.append(f"Standardized timestamps to ISO-like format. (Unparseable timestamps set to NULL: {unparseable_timestamps})")

    # Final summary in audit log
    final_rows = len(cleaned_df)
    audit_log.append(f"Cleaning pipeline completed. Total records processed from {initial_rows} to {final_rows} (Net removal: {initial_rows - final_rows} rows).")
    
    return cleaned_df, audit_log
