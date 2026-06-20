# Customer Feedback Intelligence System

A production-ready, deployable Streamlit application designed for food and grocery delivery organizations. The system ingests noisy, unstructured customer feedback from support tickets, app reviews, and surveys, runs a data engineering pipeline to clean and flag quality anomalies, enriches the data using lightweight NLP, and displays interactive dashboards for executive decision-making.

---

## 📊 Core System Features

1. **Robust Ingestion & Quality Audit**
   * Computes a weighted **Data Quality Health Score** (0-100).
   * Identifies missing text, ratings, dates, and timestamp formatting errors.
   * Reports exact raw dataset findings for immediate review.

2. **Conservative Data Cleaning**
   * Normalizes text casing, removes unnecessary carriage returns, and preserves emoji characters.
   * Standardizes irregular date formats (ISO conversion).
   * Deduplicates ONLY exact duplicate rows.
   * Preserves missing ratings and timestamps as `NULL/NaN` to keep the raw data trustworthy, using boolean indicators (`rating_missing = True/False`).

3. **Hybrid AI & Heuristic Enrichment**
   * **Sentiment Classifier**: Analyzes sentiment (Positive, Negative, Neutral) using VADER, expanded with a customized emoji translation lexicon.
   * **Sarcasm Detection**: Identifies sarcastic customer complaints using context rules (e.g. positive phrasing with low ratings, e.g. *"Oh great, app crashed again"*).
   * **Rating Contradiction Detector**: Flags mismatches where ratings conflict with text sentiment (Rating = 5 but Sentiment = Negative, or Rating = 1 but Sentiment = Positive).
   * **Category Classifier**: Categorizes reviews into Billing, App Bug, Delivery, Staff/Support, or Other.
   * **Issue Summary Generator**: Formulates concise, business-friendly summaries for every review.

4. **Interactive BI Dashboard**
   * Custom glassmorphic KPI cards for executive metrics.
   * High-fidelity, interactive Plotly charts showing trends, category breakdowns, and sentiment distributions.
   * Actionable product insights generated automatically based on complaint categories.

5. **Flexible Data Explorer & Exports**
   * Multi-column search, sorting, and filtering.
   * Direct exports of `cleaned_feedback.csv`, `enriched_feedback.csv`, and a formatted multi-tab `summary_report.xlsx`.

---

## 📁 Repository Directory Structure

```text
customer_feedback_system/
├── .streamlit/
│   └── config.toml           # Theme configuration (custom slate/indigo colors)
├── core/
│   ├── __init__.py
│   ├── quality.py            # Data quality reporting & analysis
│   ├── cleaner.py            # Data cleaning & standardization
│   ├── enrichment.py         # Sentiment, category, sarcasm, & contradiction tagging
│   └── exporter.py          # CSV/Excel multi-tab generation and formatting
├── app.py                    # Streamlit entry point (multi-section UI dashboard)
├── requirements.txt          # Package dependencies
├── README.md                 # Project explanation and quickstart
├── AI_USAGE_LOG.md           # Log of how AI was used in developing the solution
├── DEPLOYMENT_GUIDE.md       # Deployment instructions (Streamlit, Render, Hugging Face)
└── INTERVIEW_EXPLANATION.md  # Architectural overview and senior interview guide
```

---

## 📈 Raw Dataset Audit Findings

The system is calibrated to detect and audit the following verified findings from the raw feedback dataset:
* **Total Rows**: 1,810
* **Missing Timestamps**: 223
* **Missing Ratings**: 439
* **Missing Feedback Texts**: 25
* **Duplicate Feedback Text Count**: 729

*These metrics are fully represented in the **Interactive Demo Dataset** built directly into the application for immediate demonstration.*

---

## ⚙️ Local Installation & Run Guide

### Prerequisites
* Python 3.9 or higher installed.

### Setup Steps
1. Clone or download this project directory.
2. Open a terminal (PowerShell, Command Prompt, or Bash) inside the project directory:
   ```bash
   cd customer_feedback_system
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```
5. The application will open automatically in your browser (usually at `http://localhost:8501`).
