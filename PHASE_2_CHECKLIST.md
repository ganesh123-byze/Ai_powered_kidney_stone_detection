## ✅ Phase 2: Backend Deployment Checklist

Use this checklist to ensure all Phase 2 steps are completed.

---

### Step 1: Prepare Code ✅
- [x] Create `download_model.py` for automated model downloading
- [x] Create `render.yaml` with service configuration
- [x] Update `requirements.txt` with `requests` library
- [x] Create `build.sh` and `build.bat` scripts
- [x] Update `.env.example` with Render variables

### Step 2: Upload Model to GitHub
- [ ] Navigate to: https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection/releases/new
- [ ] Create release tag: `v1.0.0`
- [ ] Upload file: `backend/saved_models/best_model.pth`
- [ ] Copy download URL from GitHub release
- [ ] Update `GITHUB_RELEASE_URL` in `backend/download_model.py`
- [ ] Commit and push the updated `download_model.py`:
  ```bash
  git add backend/download_model.py
  git commit -m "Update model download URL from GitHub release"
  git push
  ```

### Step 3: Create Render Service
- [ ] Sign up/Login to Render: https://render.com
- [ ] Create new Web Service:
  - [ ] Connect GitHub repository: `Ai_powered_kidney_stone_detection`
  - [ ] Name: `kidney-detection-backend`
  - [ ] Root Directory: `backend`
  - [ ] Build Command: `pip install -r requirements.txt && pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118 && python download_model.py`
  - [ ] Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - [ ] Plan: Choose Starter ($7/mo) for reliable deployment

### Step 4: Wait for Initial Deployment
- [ ] Monitor build in Render logs (10-20 minutes expected)
- [ ] Verify no build errors
- [ ] Model downloads successfully (should see "✓ Model downloaded")
- [ ] Backend starts with Uvicorn (see "Uvicorn running")
- [ ] Copy the service URL (e.g., `https://kidney-detection-backend.onrender.com`)

### Step 5: Set Environment Variables
- [ ] Go to Service → Environment tab
- [ ] Add variables:
  ```
  API_HOST=0.0.0.0
  MODEL_ARCHITECTURE=resnet50
  DEVICE=cpu
  USE_AMP=true
  LOG_LEVEL=INFO
  NUM_WORKERS=1
  CORS_ORIGINS=http://localhost:5173,http://localhost:3000
  ```
- [ ] Click Save (service auto-restarts)
- [ ] Wait for restart to complete

### Step 6: Test Backend API
- [ ] Health check:
  ```bash
  curl https://kidney-detection-backend.onrender.com/api/v1/health
  ```
  Expected: `{"status": "ok", "version": "1.0.0"}`

- [ ] Check logs for any errors
- [ ] Test with a sample image (optional)

### Step 7: Complete Phase 2
- [ ] Backend is running and accessible from internet
- [ ] API responds to requests
- [ ] Model is loaded successfully
- [ ] Logs show no critical errors
- [ ] Service URL is stable

---

## 🔗 Important URLs

**Your Backend Service:**
```
https://kidney-detection-backend.onrender.com
```
Save this URL - needed for frontend deployment!

**Render Dashboard:**
```
https://dashboard.render.com
```

**GitHub Release Page:**
```
https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection/releases
```

---

## 📊 Expected Build Timeline

| Stage | Time | Notes |
|-------|------|-------|
| Docker build | 2-3 min | Building container image |
| Dependency install | 3-5 min | Python packages |
| PyTorch install | 5-8 min | Large library, takes time |
| Model download | 2-4 min | From GitHub releases |
| Service startup | 1-2 min | Uvicorn initialization |
| **Total** | **13-22 min** | Typical first deployment |

---

## 🐛 Common Issues

### Build Timeout
- **Issue**: Build takes >30 minutes
- **Solution**: 
  - Check Render logs for stuck steps
  - Restart the build: Manual Deploy button
  - Upgrade to Starter plan for more resources

### Model Download Fails
- **Issue**: `urllib.error.URLError: HTTP 404`
- **Solution**:
  - Verify model is uploaded to GitHub releases
  - Copy correct download URL
  - Update `backend/download_model.py`
  - Re-deploy with `Manual Deploy`

### Service Won't Start
- **Issue**: "Service is starting..." for >5 minutes
- **Solution**:
  - Check Start Command is correct: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - View logs for errors
  - Check all dependencies in requirements.txt

### CORS Errors
- **Issue**: Browser blocks API calls
- **Solution**:
  - Add frontend URL to `CORS_ORIGINS` environment variable
  - Example: `https://kidney-detection-frontend.onrender.com`

---

## ✨ Next Phase

Once Phase 2 is complete, proceed to **Phase 3: Frontend Deployment**

See: `DEPLOYMENT.md` - Frontend Deployment on Render

---

**Updated**: March 2026  
**Phase Status**: In Progress 🚀
