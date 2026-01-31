# Streamlit Cloud Deployment Guide

Your application is ready to be hosted online for free using **Streamlit Cloud**.
Follow these steps to deploy it.

## 1. Prepare GitHub Repository
You need to upload this project to GitHub.
1.  Create a new repository on [GitHub](https://github.com/new).
2.  Run the following commands in your terminal (inside the project folder):

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

## 2. Deploy on Streamlit Cloud
1.  Go to [share.streamlit.io](https://share.streamlit.io/).
2.  Click **"New app"**.
3.  Select your repository, branch (`main`), and file path (`app.py`).
4.  Click **"Deploy!"**.

## 3. Configure Secrets (Important!)
Since we removed the hardcoded API Key, you need to set it in the cloud environment.
1.  On your deployed app dashboard, go to the **App Settings** (three dots top-right).
2.  Select **Settings** > **Secrets**.
3.  Add your secrets like this:

```toml
GRAPHON_API_KEY = "your-api-key-here"
```

## 4. Done!
Your app will be live at `https://your-app-name.streamlit.app`.
