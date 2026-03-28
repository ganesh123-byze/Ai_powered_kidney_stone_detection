# Professional Deployment Guide - Kidney Stone Detection System

**Last Updated:** March 28, 2026  
**Status:** Production Ready  
**Platform:** Render (https://render.com)

---

## 🎯 Executive Summary

This guide provides step-by-step instructions for deploying the Kidney Stone Detection system to Render in a professional, production-ready manner. The system architecture consists of:

- **Backend:** FastAPI (Python) with PyTorch ML inference
- **Frontend:** React + TypeScript + Vite
- **Database:** Optional (currently stateless)
- **Infrastructure:** Render Web Services & Static Sites

**Deployment Time:** ~25-30 minutes  
**Cost:** Free tier available ($0-7/month for both services)  
**Uptime SLA:** 99.9% (paid tier) / Best effort (free tier)

---

## 📋 Pre-Deployment Checklist

- [ ] GitHub repository created and all code pushed (`https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection`)
- [ ] Model file (269MB `best_model.pth`) uploaded to GitHub Releases (v1.0.0)
- [ ] `.env` files created locally (NOT committed to git)
- [ ] Render account created (`https://dashboard.render.com`)
- [ ] All environment variables configured
- [ ] SSL certificate ready (Render provides free SSL)

---

## 🔑 Phase 1: Backend Deployment (FastAPI + PyTorch)

### Step 1.1: Create Render Web Service

1. Go to **Render Dashboard** → Click **"New +"** → Select **"Web Service"**

2. Connect GitHub repository:
   - Repository: `Ai_powered_kidney_stone_detection`
   - Branch: `main`
   - Runtime: `Python 3.11`

3. Configure Service:

| Setting | Value |
|---------|-------|
| **Name** | `kidney-detection-backend` |
| **Root Directory** | `backend` |
| **Build Command** | See Section 1.2 |
| **Start Command** | See Section 1.2 |
| **Plan** | `Starter` ($7/month minimum) or `Free` (512MB RAM, shared CPU) |
| **Auto-Deploy** | Enabled (auto-deploys on git push) |

### Step 1.2: Configure Build & Start Commands

**Build Command:**
```bash
pip install --upgrade pip setuptools wheel && \
pip install --no-cache-dir -r requirements-render.txt && \
python download_model.py && \
chmod +x startup-final.sh
```

**Start Command:**
```
./startup-final.sh
```

### Step 1.3: Set Environment Variables

Click **Environment** section and add:

```
PYTHONUNBUFFERED=true
PYTHONDONTWRITEBYTECODE=true
API_HOST=0.0.0.0
MODEL_ARCHITECTURE=resnet50
DEVICE=cpu
USE_AMP=true
LOG_LEVEL=INFO
NUM_WORKERS=1
CORS_ORIGINS=https://kidney-detection-frontend.onrender.com,http://localhost:5173
PORT=8000
```

### Step 1.4: Create Persistent Disk (Optional)

For model caching to improve cold boot time:

- **Name:** `model-storage`
- **Mount Path:** `/persistent`
- **Size:** `5 GB`

### Step 1.5: Deploy and Monitor

1. Click **Create Web Service**
2. Monitor build logs in real-time
3. Expected build time: **12-17 minutes** (PyTorch installation is slowest)

**Success Indicators:**
```
✅ Startup check complete!
Starting Uvicorn server...
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Step 1.6: Test Backend API

Once deployment completes, test endpoints:

```bash
# Health check
curl https://kidney-detection-backend.onrender.com/health

# Expected response:
# {"status": "healthy", "version": "1.0.0"}

# Get model info
curl https://kidney-detection-backend.onrender.com/model-info

# Upload and predict (requires image file)
curl -X POST \
  -F "file=@path/to/ultrasound.jpg" \
  https://kidney-detection-backend.onrender.com/predict
```

---

## 🎨 Phase 2: Frontend Deployment (React + Vite)

### Step 2.1: Create Static Site

1. Go to **Render Dashboard** → Click **"New +"** → Select **"Static Site"**

2. Connect GitHub repository:
   - Repository: `Ai_powered_kidney_stone_detection`
   - Branch: `main`

3. Configure Service:

| Setting | Value |
|---------|-------|
| **Name** | `kidney-detection-frontend` |
| **Root Directory** | `frontend` |
| **Build Command** | See Section 2.2 |
| **Publish Directory** | `dist` |
| **Plan** | `Free` (unlimited bandwidth, free SSL) |
| **Auto-Deploy** | Enabled |

### Step 2.2: Configure Build Command

```bash
npm install && npm run build
```

### Step 2.3: Set Environment Variables

Click **Environment** section and add:

```
VITE_API_URL=https://kidney-detection-backend.onrender.com
VITE_ENVIRONMENT=production
VITE_DEBUG=false
```

### Step 2.4: Deploy

1. Click **Create Static Site**
2. Expected build time: **3-5 minutes**
3. Your frontend will be available at `https://kidney-detection-frontend.onrender.com`

---

## 🧪 Phase 3: Integration Testing

### Step 3.1: Test API Connectivity

From frontend browser console:

```javascript
// Test API connection
fetch('https://kidney-detection-backend.onrender.com/health')
  .then(r => r.json())
  .then(console.log)
  // Should show: {status: "healthy", version: "1.0.0"}
```

### Step 3.2: Test Full Prediction Workflow

1. Navigate to `https://kidney-detection-frontend.onrender.com`
2. Upload a sample ultrasound image
3. Verify:
   - Image appears on screen
   - Prediction result displays
   - No CORS errors in browser console
   - Loading indicator shows during processing

### Step 3.3: Monitor Backend Logs

In Render Dashboard:
1. Select `kidney-detection-backend` service
2. Click **Logs** tab
3. Look for successful prediction requests:
   ```
   INFO: POST /predict HTTP/1.1" 200
   INFO: Prediction completed: class=Normal, confidence=0.95
   ```

---

## 🚨 Troubleshooting Common Issues

### Issue: `ModuleNotFoundError: No module named 'torch'`

**Status:** ✅ FIXED in code (commits 0feb600, fa39507)

- App now starts independently of torch installation
- `startup-final.sh` ensures torch is ready before requests arrive
- If still occurs: Check Build Command is correctly configured

**Solution:**
```bash
# In Render Settings → update Build Command:
pip install --upgrade pip setuptools wheel && \
pip install --no-cache-dir -r requirements-render.txt && \
python download_model.py && \
chmod +x startup-final.sh
```

### Issue: `CORS errors` when frontend calls backend

**Status:** Common on first deployment

**Solution:**
1. Get your frontend URL (e.g., `https://kidney-detection-frontend.onrender.com`)
2. Go to backend service → Environment
3. Update `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=https://kidney-detection-frontend.onrender.com,http://localhost:5173
   ```
4. Click **Save** and wait for auto-deploy (~2 minutes)

### Issue: `503 Service Unavailable`

**Status:** Usually means backend is cold-starting

**Solutions:**
- Wait 1-2 minutes for cold start
- On Render free tier: Server hibernates after 15 min inactivity
- Upgrade to **Starter** plan for always-on service
- Add `?timeout=60` to database connection strings if applicable

### Issue: Frontend shows `Cannot connect to API`

**Status:** Usually incorrect `VITE_API_URL`

**Solution:**
1. Check frontend environment variable in Render:
   ```
   VITE_API_URL=https://kidney-detection-backend.onrender.com
   ```
2. NOT: `http://localhost:8000` (this is for local dev only)
3. Rebuild frontend with correct URL

### Issue: Model download fails during build

**Status:** GitHub rate limiting

**Solution:**
1. Model already cached in first successful build
2. If rebuild needed, upgrade to Starter plan
3. Or download model locally and add to persistent disk

---

## 📊 Performance Considerations

### Backend

- **Cold Start Time:** 30-45 seconds (first request after inactivity)
- **Warm Request Time:** 2-5 seconds (including image preprocessing)
- **Concurrent Users:** Free tier = ~5-10 / Starter = ~50-100
- **Memory Usage:** 900-1100 MB (PyTorch model + app overhead)

### Frontend

- **Build Time:** 2-4 minutes
- **Page Load:** <1 second (static site hosted on CDN)
- **Bundle Size:** ~400 KB (gzipped)

### Optimization Tips

1. **Backend:**
   - Use Starter plan for production (consistent performance)
   - Enable persistent disk for model caching
   - Monitor logs for slow requests

2. **Frontend:**
   - Already optimized (Vite + React)
   - Static site = no cold starts
   - Consider image compression on client side

---

## 🔐 Security Checklist

- [ ] Backend uses HTTPS only (Render provides free SSL)
- [ ] CORS configured correctly (not `*`)
- [ ] Model download URL is public (GitHub Releases)
- [ ] Sensitive environment variables NOT in code
- [ ] `.env` files added to `.gitignore`
- [ ] No hardcoded API keys or secrets
- [ ] Regular backups of model file on Render persistent disk
- [ ] Monitor Render logs for unauthorized access attempts

---

## 📈 Monitoring & Maintenance

### Daily Checks

1. **Backend Health:** `curl https://kidney-detection-backend.onrender.com/health`
2. **Check Logs:** Look for errors or warnings
3. **Test Prediction:** Upload a test image

### Weekly Tasks

1. Review Render metrics (CPU, memory, requests)
2. Check GitHub for new issues
3. Monitor model prediction accuracy on real data

### Monthly Tasks

1. Update dependencies (check for security patches)
2. Review and archive logs
3. Backup model weights to a secure location
4. Review user analytics

---

## 🔄 Deployment Checklist (Final)

**Before Going Live:**

- [ ] Both services deploy successfully without errors
- [ ] Backend `/health` endpoint returns 200
- [ ] Frontend loads and displays correctly
- [ ] Upload + predict workflow works end-to-end
- [ ] No CORS errors in browser console
- [ ] Backend logs show successful predictions
- [ ] Environment variables correctly set in both services
- [ ] Auto-deploy enabled for both services
- [ ] Persistent disk configured for caching (optional but recommended)

**Post-Deployment:**

- [ ] Share frontend URL with users: `https://kidney-detection-frontend.onrender.com`
- [ ] Test from multiple browser types (Chrome, Firefox, Safari, Edge)
- [ ] Test from multiple devices (Desktop, Mobile, Tablet)
- [ ] Document any custom modifications for future deployments
- [ ] Set up monitoring/alerting (optional: Sentry, DataDog, etc.)

---

## 🎓 Additional Resources

- **Render Docs:** https://render.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **React Docs:** https://react.dev/
- **GitHub Releases:** https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection/releases
- **Repository:** https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection

---

## 📞 Support

If deployment fails:

1. Check the **Build Logs** in Render Dashboard
2. Search for the error message in this guide (Troubleshooting section)
3. Check GitHub repository Issues
4. Verify all environment variables are set correctly
5. Try Manual Deploy from Render dashboard

---

## ✅ Deployment Complete!

Once both services are running and tests pass, your system is **production-ready**.

**Next Steps:**
- Monitor real-world usage
- Collect user feedback
- Plan for scaling if needed
- Consider upgrading from FREE → STARTER tier for production reliability

---

**Version:** 1.0.0  
**Last Updated:** March 28, 2026  
**Tested On:** Render Platform  
**Status:** ✅ Production Ready
