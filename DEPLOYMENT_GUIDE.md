# Deployment Guide

This guide provides step-by-step instructions for hosting and deploying the **Customer Feedback Intelligence System** on three major hosting platforms.

---

## ☁️ Option 1: Streamlit Community Cloud (Recommended)

Streamlit Cloud is the easiest and most performant platform for hosting Streamlit applications. It connects directly to your GitHub repository and deploys automatically upon code commits.

### Prerequisites
* A GitHub account with the project code pushed to a public/private repository.
* A Streamlit Community Cloud account (linked to GitHub).

### Deployment Steps
1. Log in to [Streamlit Community Cloud](https://share.streamlit.io/).
2. Click the **"New app"** button in the dashboard.
3. Select your repository, branch (e.g. `main`), and specify the main file path:
   * **Main file path**: `app.py`
4. Expand the **Advanced settings** (optional):
   * Python Version: Select `3.9` or `3.10`.
5. Click **"Deploy!"**.
6. The platform will read `requirements.txt`, install dependencies, apply the `.streamlit/config.toml` dark theme, and launch the app in 1-2 minutes.

---

## 🚀 Option 2: Render

Render is a unified cloud platform where you can build and run applications. Streamlit apps can be hosted as a **Web Service**.

### Prerequisites
* A Render account.
* The project pushed to GitHub.

### Deployment Steps
1. Log in to the [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository.
4. Configure the Web Service settings:
   * **Name**: `feedback-intelligence-system`
   * **Region**: Select the closest region (e.g., Oregon or Frankfurt).
   * **Branch**: `main`
   * **Runtime**: `Python`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
5. Select the **Free** instance type (512MB RAM, which is plenty for our lightweight VADER-based engine!).
6. Click **Create Web Service**.
7. Render will build and deploy your app. The dashboard will show a live URL (e.g. `https://your-app.onrender.com`).

---

## 🤗 Option 3: Hugging Face Spaces

Hugging Face Spaces is a popular free hosting platform for AI/ML demonstrations and web apps.

### Prerequisites
* A Hugging Face account.
* Git installed locally.

### Deployment Steps
1. Log in to [Hugging Face](https://huggingface.co/).
2. Click on your profile icon in the top right and select **"New Space"**.
3. Configure the Space:
   * **Owner**: Select your username.
   * **Space Name**: `customer-feedback-intelligence`
   * **SDK**: Select **Streamlit** (this is a native option).
   * **Space License**: `Apache 2.0` (or leave default).
   * **Public/Private**: Public (for sharing).
4. Click **Create Space**.
5. Clone the space repository locally or upload files via the web interface.
6. Commit and push the files from your local workspace to the Hugging Face repository:
   * Add `app.py`
   * Add `requirements.txt`
   * Add the `.streamlit/config.toml`
   * Add the `core/` folder containing quality, cleaning, enrichment, and exporting modules.
7. Hugging Face Spaces will automatically detect the files, build the environment, and run the Streamlit app.
