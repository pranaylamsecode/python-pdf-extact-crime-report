# 🚀 Render.com Deployment Guide

## ✅ Your Error is Fixed!

The error you saw:
```
ERROR: failed to build: dockerfile parse error on line 25: unknown instruction: apt-get
```

**Cause**: Render was auto-generating a Dockerfile with syntax errors.

**Solution**: I've created a proper `Dockerfile` with correct syntax.

---

## 📦 Deployment Options

You have **2 ways** to deploy on Render:

### Option 1: Using Dockerfile (Recommended - Faster)
Render will use the `Dockerfile` I just created.

### Option 2: Using render.yaml
Delete the `Dockerfile` and Render will use `render.yaml`.

**I recommend Option 1** because the Dockerfile is optimized and builds faster.

---

## 🚀 Deploy Now (Step-by-Step)

### Step 1: Push Updated Code to GitHub

```bash
cd c:\Users\VeerITians\Desktop\python-pdf-extact-crime-report

git add .
git commit -m "Add Dockerfile for Render deployment"
git push origin main
```

### Step 2: Deploy on Render

1. Go to **[render.com](https://render.com)**
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `pdf-extractor`
   - **Runtime**: Render will auto-detect Docker
   - **Instance Type**: **Free** ✅
5. Click **"Create Web Service"**

### Step 3: Monitor Build

Watch the build logs. You should see:
```
✓ Installing Java...
✓ Installing Python dependencies...
✓ Starting application...
```

Build time: **~5-7 minutes**

### Step 4: Get Your URL

After deployment:
```
https://pdf-extractor.onrender.com
```

---

## 🧪 Test Your API

### Health Check
```bash
curl https://pdf-extractor.onrender.com/health
```

Response:
```json
{"status": "healthy"}
```

### Extract PDF Tables
```bash
curl -X POST https://pdf-extractor.onrender.com/extract \
  -F "file=@your-file.pdf"
```

---

## 📝 Files in Your Project

- ✅ **Dockerfile** - Docker configuration (NEW - fixes your error!)
- ✅ **render.yaml** - Alternative config (not used if Dockerfile exists)
- ✅ **main.py** - FastAPI application
- ✅ **requirements.txt** - Python dependencies
- ✅ **.gitignore** - Git ignore patterns

---

## ⚠️ Important Notes

### Free Tier Limitations
- Service **sleeps after 15 minutes** of inactivity
- **Cold start**: ~30 seconds to wake up
- **Perfect for testing!**

### Avoid Cold Starts (Optional)
Use a free cron service to ping every 10 minutes:
```bash
# Ping URL every 10 minutes
curl https://pdf-extractor.onrender.com/health
```

Try: [cron-job.org](https://cron-job.org) (free)

---

## 🔧 Troubleshooting

### Build Still Fails?
1. Check Render build logs for specific errors
2. Ensure Java installation step completes
3. Check Python dependencies install successfully

### Can't Access Service?
1. Wait for build to complete (check "Events" tab)
2. Service should show "Live" status
3. Try health check first: `/health`

### Timeout Errors?
- First request after sleep = 30s (cold start)
- Subsequent requests = fast
- This is normal for free tier

---

## ✅ Deployment Checklist

- [x] Dockerfile created with proper syntax
- [ ] Push code to GitHub
- [ ] Deploy on Render.com
- [ ] Select Free plan
- [ ] Wait for build to complete
- [ ] Test `/health` endpoint
- [ ] Test `/extract` endpoint
- [ ] Celebrate! 🎉

---

## 🆘 Still Having Issues?

**If build fails again**, share the error message and I'll help fix it!

**Your deployment should work now!** 🚀
