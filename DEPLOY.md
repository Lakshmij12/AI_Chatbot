# Put your chatbot on the internet (free)

This guide deploys the web app (`streamlit_app.py`) to **Streamlit Community
Cloud** so anyone with the link can use it — while keeping your API key private.

## What you need

- Your code on **GitHub** (you already have `Lakshmij12/AI_Chatbot` ✅)
- A free **Streamlit Community Cloud** account: https://share.streamlit.io
- Your **Anthropic API key**

## Step 1 — Make sure your repo is ready

Your repo already has everything needed:
- `streamlit_app.py` (the app)
- `requirements.txt` (lists `streamlit`, `anthropic`, `pypdf`, …)
- `.streamlit/config.toml` (the theme)

Nothing to change — just make sure your latest code is pushed to GitHub.

## Step 2 — Sign in to Streamlit Community Cloud

1. Go to https://share.streamlit.io
2. Click **Continue with GitHub** and authorize it.

## Step 3 — Create the app

1. Click **Create app** → **Deploy a public app from GitHub**.
2. Fill in:
   - **Repository:** `Lakshmij12/AI_Chatbot`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
3. **Before clicking Deploy**, open **Advanced settings → Secrets** and paste:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-your-real-key"

   # Optional but recommended for a public app — see Step 5:
   # APP_PASSWORD = "choose-a-password"
   ```
4. Click **Deploy**. First build takes a couple of minutes.

You'll get a public URL like `https://your-app-name.streamlit.app` — that's your
shareable link! 🎉

## Step 4 — Keeping your key private

- Your API key lives in Streamlit's **Secrets** store, **not** in your code, and
  is never shown to visitors. ✅
- `.streamlit/secrets.toml` is git-ignored, so a real secrets file is never
  pushed to GitHub.

## Step 5 — Protect your API credits (important!)

A **public** app means *anyone with the link* can chat — and every chat uses
**your** Anthropic credits. Two ways to stay safe:

- **Add a password.** Put `APP_PASSWORD = "something"` in your Secrets (Step 3).
  The app will then ask for that password before anyone can use it. Share the
  password only with people you trust.
- **Watch your balance.** Keep an eye on usage at
  https://console.anthropic.com and top up small amounts.

## Updating your deployed app

Streamlit Cloud auto-redeploys whenever you push new code to the `main` branch
on GitHub. Just merge your changes and the live app updates in a minute or two.

## Common problems

- **App won't start / "ModuleNotFoundError"** → make sure the missing package
  is listed in `requirements.txt`, then push again.
- **"No API key found"** → you didn't add `ANTHROPIC_API_KEY` to the app's
  Secrets (Step 3). Add it in the app's **Settings → Secrets** and reboot.
- **Password box won't accept your password** → the `APP_PASSWORD` in Secrets
  must match exactly what you type.
