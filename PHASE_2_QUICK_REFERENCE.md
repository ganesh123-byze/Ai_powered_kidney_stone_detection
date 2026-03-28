# 🚀 Phase 2: Backend Deployment - Quick Reference

Fast reference guide for deploying backend on Render.

---

## 📋 Quick Steps

### 1️⃣ Upload Model to GitHub (5 min)

```bash
# Navigate to:
https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection/releases/new

# Create release:
Tag: v1.0.0
Title: Model v1.0.0
Upload file: backend/saved_models/best_model.pth

# Copy download URL and update Python script:
backend/download_model.py → GITHUB_RELEASE_URL = "YOUR_URL"

git add backend/download_model.py
git commit -m "Update model URL"
git push
```

### 2️⃣ Create Render Service (10 min)

```
Render Dashboard → New + → Web Service
├─ Repository: Ai_powered_kidney_stone_detection
├─ Name: kidney-detection-backend
├─ Root Directory: backend
├─ Environment: Python 3
├─ Build: pip install -r requirements.txt && pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118 && python download_model.py
├─ Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
└─ Plan: Starter ($7/mo)
```

### 3️⃣ Wait for Build & Deploy (15-20 min)

Monitor in Render Logs tab. Look for:
```
✅ Installing dependencies
✅ Installing PyTorch
✅ Downloading model
✅ Starting Uvicorn
```

### 4️⃣ Set Environment Variables (2 min)

```
Environment Tab → Add Variables:

API_HOST=0.0.0.0
MODEL_ARCHITECTURE=resnet50
DEVICE=cpu
USE_AMP=true
LOG_LEVEL=INFO
NUM_WORKERS=1
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 5️⃣ Test API (2 min)

```bash
# Health check
curl https://kidney-detection-backend.onrender.com/api/v1/health

# Should return:
{"status": "ok", "version": "1.0.0", "gpu_available": false}
```

---

## 🔗 Important URLs to Save

```
Backend URL: https://kidney-detection-backend.onrender.com
Dashboard: https://dashboard.render.com
GitHub Releases: https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection/releases
```

---

## 📊 Files Created for Phase 2

| File | Purpose |
|------|---------|
| `render.yaml` | Infrastructure as code for Render services |
| `backend/download_model.py` | Automated model download during build |
| `backend/build.sh` | Build script (Unix/Linux) |
| `backend/build.bat` | Build script (Windows) |
| `RENDER_SETUP.md` | Detailed Render setup guide |
| `PHASE_2_CHECKLIST.md` | Step-by-step checklist |
| `backend/requirements.txt` (updated) | Added `requests` for downloads |
| `backend/.env.example` (updated) | Render-specific configuration |

---

## ⏱️ Typical Timeline

| Task | Duration |
|------|----------|
| Upload model to GitHub | 5 min |
| Create Render service | 5 min |
| Build on Render | 15-20 min |
| Set environment vars | 2 min |
| Test API | 2 min |
| **Total** | **30-35 min** |

---

## 🐛 Quick Troubleshooting

| Error | Solution |
|-------|----------|
| Build timeout | Upgrade to Starter plan |
| Model download fails | Check GitHub release URL is correct |
| Service won't start | Check Start Command in settings |
| CORS errors | Add frontend URL to CORS_ORIGINS |
| Slow inference | Upgrade plan or optimize image size |

---

## ✅ Success Indicators

✅ Health check returns 200 OK  
✅ No errors in Render logs  
✅ Model loaded successfully (see logs)  
✅ Service URL is stable  
✅ Can test with sample image  

---

## 🎯 Next Phase

Once backend is deployed:
1. **Phase 3**: Deploy frontend on Render
2. Connect frontend to backend API
3. Full system testing

See: `DEPLOYMENT.md`

---

**Status**: Phase 2 Ready to Deploy 🚀
