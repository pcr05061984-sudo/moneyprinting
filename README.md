# MoneyPrinterTurbo - Render.com & GitHub Production Deployment

This package contains the production files for deploying **MoneyPrinterTurbo** with:
1. 24/7 FastAPI server with `/health` uptime monitoring endpoint.
2. 24/7 VIP Telegram Controller Bot (`telegram_bot.py`) with PIN protection & Auto-Lock.
3. YouTube direct video uploader & Hinglish viral SEO engine.

## 🚀 How to Push this Folder to GitHub

Open a terminal inside this `render` folder:

```powershell
# 1. Initialize git repository
git init

# 2. Add all production files
git add .

# 3. Commit
git commit -m "Production release for Render.com"

# 4. Link to your GitHub repository
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

## 🌐 How to Deploy on Render.com

1. Go to [dashboard.render.com](https://dashboard.render.com).
2. Click **New +** -> **Web Service**.
3. Select your GitHub repository.
4. Settings:
   - **Environment:** `Docker`
   - **Instance Type:** `Free`
   - **Health Check Path:** `/health`
5. Under **Environment Variables**, add:
   - `PORT`: `8080`
6. Click **Deploy Web Service**!

## ⚡ Keep Render Alive 24/7 (Free)
1. Go to [uptimerobot.com](https://uptimerobot.com).
2. Add a new monitor for URL: `https://your-render-app.onrender.com/health`
3. Interval: 10 minutes.
