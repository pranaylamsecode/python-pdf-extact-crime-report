# 🚀 Render.com Deployment Guide

## Quick Deployment Steps

### Step 1: Push to GitHub

```bash
cd c:\Users\VeerITians\Desktop\python-pdf-extact-crime-report
git init
git add .
git commit -m "Initial commit: PDF extraction API"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pdf-extraction-api.git
git push -u origin main
```

### Step 2: Deploy on Render

1. Go to 👉 **[render.com](https://render.com)** and sign up (no credit card needed!)

2. Click **"New +"** → **"Web Service"**

3. Click **"Connect account"** to link your GitHub

4. Select your `pdf-extraction-api` repository

5. Configure the service:
   - **Name**: `pdf-extractor` (or your choice)
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: (Leave blank, we use `render.yaml`)
   - **Start Command**: (Leave blank, we use `render.yaml`)
   - **Plan**: **Free** ✅

6. Click **"Create Web Service"**

### Step 3: Wait for Deployment

⏱️ **Deployment Time**: ~5-10 minutes

Render will:
- Install Java (required for tabula-py)
- Install Python dependencies
- Start the server on port 10000
- Assign a public URL

### Step 4: Get Your API URL

After deployment, your URL will be:
```
https://pdf-extractor.onrender.com
```

---

## 🧪 Test Your Deployment

### Health Check
```bash
curl https://pdf-extractor.onrender.com/health
```

**Expected response:**
```json
{"status": "healthy"}
```

### Extract Tables from PDF
```bash
curl -X POST https://pdf-extractor.onrender.com/extract \
  -F "file=@your-file.pdf"
```

---

## 🔍 Monitoring

### View Logs
1. Go to Render Dashboard
2. Click on your service
3. Click **"Logs"** tab
4. Monitor real-time logs

### Check Events
Click **"Events"** tab to see:
- Deployments
- Build status
- Service restarts

---

## ⚙️ Configuration Details

The `render.yaml` file contains:

- **Java Installation**: Installs `default-jre` (required for tabula-py)
- **Python 3.11**: Modern Python runtime
- **Port 10000**: Render's default port
- **Health Check**: `/health` endpoint
- **Auto-deploy**: Updates automatically on Git push

---

## 💰 Free Tier Limits

Render.com Free Tier includes:
- ✅ 750 hours/month
- ✅ No credit card required
- ✅ Automatic HTTPS
- ✅ Custom domains
- ⚠️ Service **spins down** after 15 minutes of inactivity
- ⚠️ **Cold starts** take ~30 seconds to wake up

### Cold Start Note
First request after inactivity will be slow (~30s). Subsequent requests are fast.

---

## 🔗 Laravel Integration

Use your Render URL in Laravel:

### .env
```env
PDF_EXTRACTOR_API_URL=https://pdf-extractor.onrender.com
```

### Example Usage
```php
use Illuminate\Support\Facades\Http;

$response = Http::timeout(60) // Important: increase timeout for cold starts
    ->attach('file', fopen($path, 'r'), 'report.pdf')
    ->post(env('PDF_EXTRACTOR_API_URL') . '/extract');

$data = $response->json();
```

---

## 🛠️ Troubleshooting

### Build Fails

**Issue**: Java installation fails  
**Solution**: Check Render logs. The build command should show Java installation.

### Service Won't Start

**Issue**: Port binding error  
**Solution**: Ensure `startCommand` uses `--port 10000` (Render's default)

### Slow First Request

**Issue**: 30-second delay on first request  
**Solution**: This is normal for free tier (cold start). Consider:
- Upgrading to paid plan ($7/month)
- Using a cron job to ping `/health` every 10 minutes
- Accepting the delay for testing purposes

### Health Check Fails

**Issue**: Render shows "Unhealthy"  
**Solution**: 
1. Check `/health` endpoint returns 200 status
2. Verify CORS settings if needed
3. Check logs for errors

---

## 📊 Keep Service Awake (Optional)

To prevent cold starts, ping your service every 10-14 minutes:

### Using Cron-Job.org (Free)

1. Go to [cron-job.org](https://cron-job.org)
2. Create free account
3. Add new cron job:
   - **URL**: `https://pdf-extractor.onrender.com/health`
   - **Interval**: Every 10 minutes
   - **Method**: GET

### Using Laravel Scheduler

```php
// app/Console/Kernel.php
protected function schedule(Schedule $schedule)
{
    $schedule->call(function () {
        Http::get(env('PDF_EXTRACTOR_API_URL') . '/health');
    })->everyTenMinutes();
}
```

---

## 🎯 Alternative: Railway

If you prefer Railway over Render:
- See `README.md` for Railway instructions
- Railway uses `railway.json` and `nixpacks.toml`
- Railway also offers free tier with $5 monthly credit

---

## ✅ Deployment Checklist

- [ ] Push code to GitHub
- [ ] Sign up on Render.com
- [ ] Create new Web Service
- [ ] Connect GitHub repository
- [ ] Select Free plan
- [ ] Wait for deployment (~5-10 min)
- [ ] Test health check endpoint
- [ ] Test PDF extraction
- [ ] Update Laravel `.env` with Render URL
- [ ] Test Laravel integration

---

## 🆘 Need Help?

- **Render Docs**: [https://render.com/docs](https://render.com/docs)
- **Check Logs**: Render Dashboard → Your Service → Logs
- **Build Issues**: Review "Events" tab for error messages

---

**Happy Deploying! 🚀**
