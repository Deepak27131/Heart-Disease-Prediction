# Deployment Guide: Heart Disease Prediction App

This guide explains how to deploy your Flask application for free using **PythonAnywhere**.

**Why PythonAnywhere?**
Your application uses an SQLite database (`store.db`). Many free cloud platforms (like Render or Vercel) have "ephemeral" file systems, meaning your database would be wiped every time the app restarts. PythonAnywhere provides persistent storage, making it perfect for your SQLite setup.

## Prerequisites

1.  **GitHub Account**: You need to upload your project to GitHub.
2.  **PythonAnywhere Account**: Sign up for a free "Beginner" account at [www.pythonanywhere.com](https://www.pythonanywhere.com/).

## Step 1: Prepare Your Code (Already Done)

I have already:

- created a `requirements.txt` file with all necessary libraries.
- configured `app.py` to run correctly.

**Important**: Ensure `app.py` is the main entry point (which it is).

## Step 2: Upload to GitHub

1.  Initialize a git repository in your project folder if you haven't already.
2.  Commit your files (`app.py`, `requirements.txt`, `Model/`, `templates/`, `store.db`).
    - _Note: If `store.db` contains test data you want to keep, commit it. Otherwise, the app will create a new one._
3.  Push to a new GitHub repository.

## Step 3: Deploy on PythonAnywhere

1.  **Log in** to PythonAnywhere.
2.  **Open a Bash Console** (from the Dashboard).
3.  **Clone your repository**:
    ```bash
    git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
    ```
4.  **Create a Virtual Environment**:
    ```bash
    cd YOUR_REPO_NAME
    mkvirtualenv --python=/usr/bin/python3.10 my-virtualenv
    pip install -r requirements.txt
    ```
5.  **Configure the Web App**:
    - Go to the **Web** tab on PythonAnywhere dashboard.
    - Click **Add a new web app**.
    - Select **Flask** -> **Python 3.10**.
    - **Path to your app**: Enter the path to your cloned folder (e.g., `/home/yourusername/YOUR_REPO_NAME/app.py`).

6.  **WSGI Configuration File**:
    - In the Web tab, look for the "Code" section and click the link to edit the **WSGI configuration file**.
    - Delete the default content and paste this (replace `yourusername` and `YOUR_REPO_NAME`):

      ```python
      import sys
      import os

      # Add your project directory to the sys.path
      project_home = '/home/yourusername/YOUR_REPO_NAME'
      if project_home not in sys.path:
          sys.path = [project_home] + sys.path

      # Set environment variables (if allowed in free tier, otherwise hardcode or use .env with python-dotenv)
      os.environ["GENAI_API_KEY"] = "YOUR_API_KEY_HERE"

      # Import flask app but need to call it "application" for WSGI to work
      from app import app as application
      ```

    - _Tip: Since you use `load_dotenv` in `app.py`, you can also upload your `.env` file to the server folder, and the app will read it automatically._

7.  **Virtualenv Mapping**:
    - In the Web tab -> "Virtualenv" section, enter the path: `/home/yourusername/.virtualenvs/my-virtualenv`

8.  **Reload**:
    - Click the green **Reload** button at the top of the Web tab.

## Step 4: Verify

- Click the link provided (e.g., `yourusername.pythonanywhere.com`).
- Your app should be live!

## Troubleshooting

- **Error Logs**: Check the "Error log" link in the Web tab if something goes wrong.
- **Database**: Ensure the path to `store.db` in `app.py` uses `os.path.join(BASE, "store.db")`, which we already fixed!
