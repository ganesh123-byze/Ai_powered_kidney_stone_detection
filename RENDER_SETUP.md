# 🚀 Render Backend Deployment Guide

Complete step-by-step guide to deploy the Kidney Stone Detection backend on Render.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Upload Model to GitHub](#step-1-upload-model-to-github-releases)
3. [Step 2: Create Render Account](#step-2-create-render-account)
4. [Step 3: Deploy Web Service](#step-3-deploy-web-service-backend)
5. [Step 4: Configure Environment Variables](#step-4-configure-environment-variables)
6. [Step 5: Monitor & Test](#step-5-monitor--test)
7. [Step 6: Production Optimization](#step-6-production-optimization)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

✅ GitHub repository with code pushed (from Phase 1)  
✅ GitHub account with release creation permissions  
✅ Render account (free tier available)  
✅ Model file locally: `backend/saved_models/best_model.pth`  

---

## Step 1: Upload Model to GitHub Releases

The model file is too large for GitHub's standard file limit, so we store it in GitHub **Releases**.

### 1.1 Create GitHub Release

1. Go to: https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection/releases/new

2. **Fill in Release Details:**
   - Tag version: `v1.0.0`
   - Release title: `Model v1.0.0`
   - Description:
     ```
     Initial pre-trained model checkpoint
     - Architecture: ResNet50
     - Dataset: Kidney Ultrasound Images
     - Accuracy: [your accuracy]%
     ```

3. **Upload Model File:**
   - Click "Attach binaries by dropping them here or selecting them"
   - Select: `backend/saved_models/best_model.pth`
   - Wait for upload to complete

4. **Publish Release:**
   - Click "Publish release"

### 1.2 Verify Model URL

After release is published:
1. Go to release page
2. Right-click on `best_model.pth` → Copy link
3. URL should look like:
   ```
   https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection/releases/download/v1.0.0/best_model.pth
   ```

4. Update `backend/download_model.py`:
   ```python
   GITHUB_RELEASE_URL = "YOUR_ACTUAL_URL_HERE"
   ```

5. Commit and push:
   ```bash
   git add backend/download_model.py
   git commit -m "Update model download URL"
   git push
   ```

---

## Step 2: Create Render Account

1. Go to https://render.com
2. **Sign up** with GitHub (recommended - easier deployment)
3. Authorize `ganesh123-byze` access to your repositories
4. Verify email address

---

## Step 3: Deploy Web Service (Backend)

### 3.1 Create New Service

1. Log in to Render Dashboard: https://dashboard.render.com

2. Click **"New +"** → **"Web Service"**

3. **Select Repository:**
   - Choose: `Ai_powered_kidney_stone_detection`
   - Branch: `main`
   - Click "Connect"

### 3.2 Configure Service

**Basic Settings:**

| Field | Value |
|-------|-------|
| **Name** | `kidney-detection-backend` |
| **Environment** | `Python 3` |
| **Region** | Choose closest to you (e.g., `Singapore`, `US East`) |
| **Branch** | `main` |

**Build & Deploy:**

| Field | Value |
|-------|-------|
| **Root Directory** | `backend` |
| **Build Command** | `pip install -r requirements.txt && pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118 && python download_model.py` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

**Instance Type:**

⭐ **Free Tier:**
- Shuts down after 15 min inactivity
- 512MB RAM (works for small images)
- Good for testing

💰 **Starter ($7/month):**
- Always running
- 512MB RAM
- 0.5 vCPU
- **Recommended for production**

💪 **Standard ($12/month+):**
- 1GB RAM or more
- 1+ vCPU
- For heavy workloads

3. **Click "Create Web Service"**
   - Render will start the deployment process
   - Check the "Logs" tab to monitor build progress

### 3.3 Wait for Deployment

Expected timeline:
- Build: 8-15 minutes (PyTorch is large)
- Model download: 2-5 minutes
- Total: 10-20 minutes

In the logs, you should see:
```
Building Docker image...
Step 1/5: Installing Python dependencies...
Step 2/5: Installing PyTorch...
Step 3/5: Downloading model...
📥 Downloading from: https://github.com/...
✓ Model downloaded successfully
Step 4/5: Starting Uvicorn...
INFO:     Uvicorn running on http://0.0.0.0:PORT
```

If stuck on "Building Docker image", check the logs for errors.

---

## Step 4: Configure Environment Variables

Once deployment is successful, set environment variables:

### 4.1 Access Environment Settings

1. In Render Dashboard → Your Service → **Environment**
2. Add these variables:

### 4.2 Environment Variables

```
# API Configuration
API_HOST = 0.0.0.0
MODEL_ARCHITECTURE = resnet50
DEVICE = cpu
USE_AMP = true

# Server Configuration
LOG_LEVEL = INFO
NUM_WORKERS = 1

# CORS - Add your frontend URL here (after frontend is deployed)
CORS_ORIGINS = http://localhost:5173,http://localhost:3000
# After frontend deployment, update to:
# CORS_ORIGINS = https://kidney-detection-frontend.onrender.com,https://yourdomain.com

# Model Path
MODEL_PATH = saved_models/best_model.pth
```

3. **Click "Save"** - Service will automatically restart with new variables

---

## Step 5: Monitor & Test

### 5.1 Get Service URL

1. In Dashboard, find your service URL:
   ```
   https://kidney-detection-backend.onrender.com
   ```

2. Copy this URL - you'll need it for the frontend

### 5.2 Test API Endpoints

**Health Check:**
```bash
curl https://kidney-detection-backend.onrender.com/api/v1/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "gpu_available": false,
  "timestamp": "2026-03-28T20:00:00Z"
}
```

**Test with Image Upload:**
```bash
# Requires a valid kidney ultrasound image
curl -X POST https://kidney-detection-backend.onrender.com/api/v1/predict/upload \
  -F "file=@path/to/test_image.jpg"
```

Expected response:
```json
{
  "prediction": {
    "class": "Normal",
    "confidence": 0.95,
    "severity": "Normal"
  },
  "file_id": "abc123"
}
```

### 5.3 View Real-Time Logs

In Dashboard → Your Service → **Logs** tab:
- Watch incoming requests
- Monitor errors
- Verify model loading

---

## Step 6: Production Optimization

### 6.1 Enable Auto-Deploy

Services auto-redeploy when you push to `main` branch. To disable:
1. Service Settings → Auto-Deploy → Toggle OFF

### 6.2 Scale Instance (Optional)

If API is slow:
1. Service Settings → Plan
2. Upgrade to **Starter** ($7/mo) or higher
3. Provides more CPU & RAM

### 6.3 Set Up Custom Domain (Optional)

1. Service Settings → Custom Domain
2. Add your domain: `api.yourdomain.com`
3. Update DNS records to point to Render IP
4. Update frontend `VITE_API_URL` with custom domain

---

## Troubleshooting

### ❌ Build Fails with PyTorch Error

```
ERROR: No matching distribution found for torch
```

**Solution**: PyTorch download might be slow on free tier. This is normal - wait and retry deployment.

### ❌ Model Download Fails

```
urllib.error.URLError: HTTP 404
```

**Solution**:
1. Verify model uploaded to GitHub Releases
2. Copy exact download URL from GitHub
3. Update `backend/download_model.py`:
   ```python
   GITHUB_RELEASE_URL = "YOUR_ACTUAL_URL"
   ```
4. Commit and push
5. Click "Manual Deploy" in Render Dashboard

### ❌ Service Shuts Down (Free Tier)

```
Service is inactive (free tier after 15 min inactivity)
```

**Solution**:
- Upgrade to Starter plan ($7/month) for always-on
- Or use external service to ping the API every 10 minutes

### ❌ API Returns 503 Service Unavailable

```
Service Unavailable - Backend is starting up
```

**Solution**: Wait 1-2 minutes for build to complete. Check logs.

### ❌ CORS Error in Frontend

```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution**:
1. Go to Service Environment settings
2. Update `CORS_ORIGINS`:
   ```
   https://kidney-detection-frontend.onrender.com,https://yourdomain.com
   ```
3. Save and wait for restart

### ❌ Slow API Responses

**Solution**:
1. Try CPU optimization: `USE_AMP=true`, `NUM_WORKERS=1`
2. Upgrade plan for more CPU
3. Reduce image size in preprocessing

---

## 📊 Performance Expectations

| Aspect | Free | Starter | Standard |
|--------|------|---------|----------|
| Build time | 15-20 min | 10-15 min | 8-10 min |
| First request | 30-60 sec | 5-10 sec | 2-5 sec |
| Inference time | 5-15 sec | 3-8 sec | 1-3 sec |
| Concurrent users | 5-10 | 20-50 | 100+ |
| Uptime | ~95% | 99.5% | 99.9% |

---

## 🔐 Security Best Practices

1. **Never commit `.env` files** - Use Render's environment variables
2. **Use HTTPS only** - Render provides free SSL
3. **Rotate API keys regularly** - If you add authentication later
4. **Monitor access logs** - Check for suspicious activity

---

## 📞 Support Resources

- **Render Docs**: https://render.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **PyTorch Docs**: https://pytorch.org/docs
- **GitHub Issues**: https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection/issues

---

## Next Steps

✅ **Backend deployed on Render**

Next: Deploy frontend on Render (Phase 3)

See `DEPLOYMENT.md` → Frontend Deployment section

---

**Last Updated**: March 2026  
**Version**: 1.0.0
