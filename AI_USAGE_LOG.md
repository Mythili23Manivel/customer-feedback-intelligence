# AI Usage Log & Iterative Corrections

This log details the collaborative development process between the AI coding assistant and the Senior Engineer for the **Customer Feedback Intelligence System**, specifically documenting technical assumptions, errors made by the AI, and the resolutions applied to bring the software to production standard.

---

## 🛠️ AI Development Contributions

| Module | Contribution of AI | Design Decisions Guided by AI |
| :--- | :--- | :--- |
| **`core/quality.py`** | Drafted pandas filtering rules for missing values, invalid rating thresholds, and emoji/junk matching patterns. | Recommended using specific Unicode regex ranges for emoji-only reviews to avoid conflating them with normal text. |
| **`core/cleaner.py`** | Generated ISO conversion functions for multiple timestamp formats and string spacing normalization. | Guided the implementation of boolean flags (`rating_missing`, `timestamp_missing`) to keep the source columns raw and audit-ready. |
| **`core/enrichment.py`** | Programmed VADER sentiment pipeline, sarcasm heuristic routines, category keyword scoring, and template-based summaries. | Implemented automatic NLTK download logic so the web app can run headless in any environment without developer setup. |
| **`core/exporter.py`** | Created `openpyxl` styling scripts, title sheets, header formatting, and autowidth calculations. | Ensured download files are generated using in-memory byte buffers (`io.BytesIO`) to support cloud hosting. |
| **`app.py`** | Built Streamlit tabs, custom HTML metric styling, and Plotly Express visualizations. | Constructed the **Interactive Demo Dataset** generator using precise math to match the 1,810-row dataset findings. |

---

## ⚠️ AI Mistakes & Technical Corrections

### 1. Sarcasm Misclassification (False Negatives)
* **Mistake**: The AI's initial sarcasm detector relied strictly on rating mismatch (e.g. rating <= 2 combined with positive VADER sentiment). VADER sentiment failed to calculate as positive for short phrases like *"Oh great, crashed again"* because "crashed" is heavily weighted negative, resulting in a negative sentiment, which bypassed the rating mismatch rule.
* **Correction**: We added a **sarcastic expression regex list** (e.g. `\boh\s+great\b`, `\bthanks\s+for\s+nothing\b`) that flags sarcasm *regardless* of VADER's numerical output, combined with contextual check rules for billing and support delay complaints.

### 2. Aggressive Duplicate Removal
* **Mistake**: In the first draft of `core/cleaner.py`, the AI used `df.drop_duplicates(subset=["feedback_text"])` to deduplicate. This deleted separate customers who had submitted identical short complaints (e.g., two different customers writing *"Food was cold"* at different times).
* **Correction**: Corrected the logic to **only remove exact duplicate rows** (where timestamp, rating, source, and text are identical). Created a separate `duplicate_feedback_flag` to identify repeated feedback text for volume analysis while preserving the rows.

### 3. Wrong Category Assignments
* **Mistake**: The AI used a basic substring match (`in text`) for classification. This caused false matches on compound terms. For example, *"I want to pay"* (Billing) was matched with App Bug because of *"app"* in "pay" (or *"delivery"* inside "delivery fee" matching Billing instead of Delivery).
* **Correction**: Implemented word-boundary regex matches (`\bkeyword\b`) and a multi-category scoring system. The category with the highest matching keyword count is selected. If no keywords match, the default category is set to `"Other"`.

### 4. Excel Styling Layout Issues
* **Mistake**: The initial Excel generation script set static column widths, cutting off long text strings, and hid the workbook gridlines.
* **Correction**: Overhauled `core/exporter.py` to iterate through the cells, dynamically calculate the maximum cell length per column, apply a safety buffer, and explicitly enable `showGridLines = True` on all sheets.
