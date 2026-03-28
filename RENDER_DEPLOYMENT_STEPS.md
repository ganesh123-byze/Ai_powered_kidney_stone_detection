## 🎯 Render Deployment: Step-by-Step Guide

Your model is uploaded to GitHub and code is ready. Follow these exact steps to deploy on Render.

---

## 1️⃣ Create Render Account (If needed)

**URL**: https://render.com

- Click **"Sign Up"**
- Use GitHub login (easiest method)
- Authorize access to your repositories
- Verify email

---

## 2️⃣ Create Web Service for Backend

### ✅ Step 1: New Service

1. Go to **Render Dashboard**: https://dashboard.render.com
2. Click **"New +"** button → **"Web Service"**

```
┌─────────────────────────────┐
│ Render Dashboard            │
├─────────────────────────────┤
│ ➕ New +                    │
│    ├─ Web Service          │ ← Click Here
│    ├─ Static Site          │
│    ├─ Private Service      │
│    └─ PostgreSQL Database  │
└─────────────────────────────┘
```

### ✅ Step 2: Select Repository

1. **Connect GitHub Repository:**
   - Click "Connect your GitHub account" (if not already)
   - Search: `kidney-stone-detection` or `Ai_powered`
   - Select: `ganesh123-byze/Ai_powered_kidney_stone_detection`
   - Authorize access (if prompted)

2. **Select Repository:**
   ```
   Repository: Ai_powered_kidney_stone_detection ✓
   Branch: main ✓
   Auto-deploy: Yes
   ```

3. Click **"Connect"**

### ✅ Step 3: Basic Settings

Fill in the basic configuration:

```
┌─────────────────────────────────────────────────┐
│ Basic Settings                                  │
├─────────────────────────────────────────────────┤
│ Name                   │ kidney-detection-backend│
│ Environment            │ Python 3               │
│ Region                 │ Singapore (or closest) │
│ Branch                 │ main                   │
│ Root Directory         │ backend                │
│ Runtime                │ Python 3               │
└─────────────────────────────────────────────────┘
```

### ✅ Step 4: Build & Start Commands

```
Build Command:
pip install -r requirements.txt && \
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118 && \
python download_model.py

Start Command:
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### ✅ Step 5: Choose Plan

```
┌─────────────────────────────────────────┐
│ Instance Type                           │
├─────────────────────────────────────────┤
│ ⭕ Free (Recommended for testing)       │
│    - Spins down after 15 min            │
│    - 512MB RAM                          │
│                                         │
│ ⭕ Starter ($7/month) (Recommended)     │
│    - Always running ✓                   │
│    - 512MB RAM                          │
│    - Good for production                │
│                                         │
│ ⭕ Standard ($12/month)                 │
│    - 1GB+ RAM                           │
│    - For heavy workloads                │
└─────────────────────────────────────────┘

Recommendation: Choose "Starter" for reliable deployment
```

### ✅ Step 6: Create Service

1. **Scroll down** and click **"Create Web Service"**
2. Render will start building (watch the **"Logs"** tab)

---

## 3️⃣ Monitor Build Progress

### Expected Build Logs

Watch the Logs tab. It should show:

```
=== Build Started ===
[1/5] Building Docker image...
[2/5] Installing Python dependencies...
     ✓ fastapi
     ✓ uvicorn
     ✓ torch (this takes 5-8 min)
     ✓ pillow, opencv-python, etc.

[3/5] Downloading model...
     📥 Downloading from: https://github.com/...
     Progress: 100% (269.51MB / 269.51MB)
     ✓ Model downloaded successfully

[4/5] Starting Uvicorn server...
     INFO: Uvicorn running on http://0.0.0.0:PORT
     ✓ Application startup complete

=== Build Successful ===
```

**⏱️ Expected Timeline:**
- First 2 min: Docker setup
- Next 5-8 min: PyTorch installation (this is slow!)
- Next 2-4 min: Model download
- Next 1-2 min: Service startup
- **Total: 10-20 minutes**

If the build seems stuck at "Downloading torch", it's normal - just wait!

### ⚠️ Build Failed?

If you see errors:
1. **Check Logs tab** for error message
2. **Common issues:**
   - `ModuleNotFoundError`: Missing dependency → Already in requirements.txt ✓
   - `Connection timeout`: Network issue → Retry build
   - `FileNotFoundError best_model.pth`: Model URL wrong → Check GitHub release URL

---

## 4️⃣ Configure Environment Variables

Once build succeeds, add environment variables:

### ✅ Navigate to Environment

1. Service Dashboard → **"Environment"** tab
2. Click **"Add Environment Variable"**

### ✅ Add Variables

Add these one by one:

| Variable | Value | Purpose |
|----------|-------|---------|
| `API_HOST` | `0.0.0.0` | Listen on all interfaces |
| `MODEL_ARCHITECTURE` | `resnet50` | Model type |
| `DEVICE` | `cpu` | Use CPU (free tier limitation) |
| `USE_AMP` | `true` | Enable mixed precision |
| `LOG_LEVEL` | `INFO` | Log level |
| `NUM_WORKERS` | `1` | Parallel workers |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Allowed frontends |

**Example adding a variable:**
```
┌─────────────────────────────────────────┐
│ Add Environment Variable                │
├─────────────────────────────────────────┤
│ Key:    API_HOST                        │
│ Value:  0.0.0.0                         │
│ [Add Variable]                          │
└─────────────────────────────────────────┘
```

### ✅ Save

Once all variables are added, click **"Save"**

⚠️ Service will automatically restart with new variables (wait 1-2 min)

---

## 5️⃣ Get Your Backend URL

Once service is deployed, Render assigns a URL:

```
Your Backend URL:
https://kidney-detection-backend.onrender.com
```

**📌 SAVE THIS URL** - You'll need it for frontend deployment!

---

## 6️⃣ Test Backend API

Test your deployed backend:

### Health Check

```bash
curl https://kidney-detection-backend.onrender.com/api/v1/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "gpu_available": false,
  "timestamp": "2026-03-28T20:00:00Z"
}
```

### Check Logs

1. Service Dashboard → **"Logs"** tab
2. Should see: `INFO: Application startup complete`
3. No critical errors

---

## 7️⃣ Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| ❌ Build timeout | Build is long on free tier. Wait and retry. |
| ❌ Model download fails | Verify GitHub release URL is correct |
| ❌ Service won't start | Check logs for errors, retry build |
| ❌ Health check fails | Wait for service to fully start (1-2 min) |
| ❌ 502 Bad Gateway | Service is restarting. Wait a minute. |
| ⚠️ Spins down (free tier) | Upgrade to Starter plan or use monitoring service |

---

## ✅ Success Checklist

- [x] Model uploaded to GitHub ✓
- [ ] Render account created
- [ ] Web Service created
- [ ] Build completed successfully
- [ ] Environment variables configured
- [ ] Health check responds 200 OK
- [ ] Backend URL saved
- [ ] No errors in logs

---

## 🔗 Important Links

**Render Dashboard:**
```
https://dashboard.render.com
```

**Your Backend Service:**
```
https://kidney-detection-backend.onrender.com
```

**GitHub Release:**
```
https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection/releases/tag/v1.0.0
```

---

## ⏭️ Next Steps

Once backend is deployed and tested:

1. ✅ Save your backend URL
2. ➡️ **Phase 3**: Deploy frontend to Render
3. Connect frontend to backend
4. Test full system

---

**Status**: Ready to deploy to Render 🚀
