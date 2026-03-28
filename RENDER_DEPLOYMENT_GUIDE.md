# 🚀 RENDER DEPLOYMENT GUIDE - STEP BY STEP (ZERO-COST)

**Target Cost:** $0/month  
**Estimated Time:** 30-40 minutes  
**Difficulty:** Beginner-friendly with error prevention

---

## ✅ PRE-DEPLOYMENT CHECKLIST

Before starting, verify these prerequisites:

```bash
# 1. Check Git is configured
git config --global user.name
git config --global user.email

# 2. Verify repository is pushed
cd "d:\Kidney Detection"
git status           # Should show "On branch main" and "nothing to commit"
git log --oneline -5 # Should show recent commits

# 3. Check GitHub repository is public
# Visit: https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection
# Verify it's public (not private)
```

**All Good?** ✅ Continue to Step 1

---

## STEP 1: CREATE RENDER ACCOUNT & CONNECT GITHUB

### 1.1 Create Render Account
1. Go to https://render.com
2. Click **"Sign Up"** (top right)
3. Choose **"GitHub"** to sign in with GitHub (easiest)
4. Authorize Render to access your GitHub account
5. Select **Free Tier** when prompted

### 1.2 Verify Connection
- Dashboard should show: "GitHub repositories" with your project listed
- If not showing, click **"Connect Repository"** and search for:
  ```
  Ai_powered_kidney_stone_detection
  ```

**Status:** ✅ Render account ready with GitHub connected

---

## STEP 2: DEPLOY BACKEND (MOST CRITICAL - PREVENT ERRORS HERE)

### ⚠️ CRITICAL: Prevent PyTorch Error on Deploy

The backend uses PyTorch which is large. Render needs proper configuration. We've already fixed this in your code, but Render configuration is crucial.

### 2.1 Create Backend Service

1. **Go to Render Dashboard:** https://dashboard.render.com
2. **Click:** "New +" → **"Web Service"**
3. **Fill in:**
   - **Name:** `kidney-detection-backend` (lowercase, no spaces)
   - **Repository:** Select `Ai_powered_kidney_stone_detection`
   - **Branch:** `main`
   - **Root Directory:** `backend` (**CRITICAL - don't skip this**)
   - **Runtime:** `python 3.11`
   - **Build Command:** (copy exactly below)

### 2.2 Build Command (EXACT - don't modify)

```bash
pip install --upgrade pip setuptools wheel && pip install -r requirements-render.txt && python -c "import sys; sys.path.insert(0, '/opt/render/project/backend'); from app.main import app; print('✓ Backend imports verified')" && chmod +x startup-final.sh
```

**Why this command:**
- Upgrades pip/setuptools (prevents dependency conflicts)
- Installs requirements-render.txt (CPU PyTorch optimized)
- Verifies backend imports (catches errors before deployment)
- Makes startup script executable

### 2.3 Start Command (EXACT - don't modify)

```bash
./startup-final.sh
```

**Why:** This script verifies PyTorch one more time before starting the app

### 2.4 Environment Variables

Copy these values and add them to Render dashboard:

```
RENDER=true
PYTHONUNBUFFERED=true
```

**Add them:** Click "Advanced" → "Add Environment Variable"

### 2.5 Specify Plan (CRITICAL FOR $0 COST)

- **Instance Type:** `Free`
- **Do NOT select "Starter"** (would cost $7/month)

### 2.6 Health Check (Auto-enabled)

- **Path:** `/health`
- **Check Interval:** `30 seconds`
- **Timeout:** `10 seconds`

Leave defaults if not customizable on free tier.

### 2.7 Deploy

1. Scroll down → Click **"Create Web Service"**
2. **Wait 3-5 minutes** (first deploy takes longer)

### ✅ Deployment Success Signs:
- Logs show: `✓ Backend imports verified`
- Logs show: `INFO: Uvicorn running on 0.0.0.0:10000`
- Status badge shows: **"Live"** (green)
- Your backend URL appears (e.g., `https://kidney-detection-backend.onrender.com`)

### ❌ Common Errors & Fixes:

**Error 1: "ModuleNotFoundError: No module named 'torch'"**
- ✅ **FIXED by:** Deferred imports in your code (already in place)
- Verify: Logs show "✓ Backend imports verified" in build output
- If not: Restart deployment (button top-right)

**Error 2: "Command 'startup-final.sh' not found"**
- Cause: Script not executable during build
- ✅ **FIXED by:** `chmod +x startup-final.sh` in build command (already included)

**Error 3: Long build time (>10 minutes)**
- Normal for first PyTorch install
- Don't cancel - let it complete
- Subsequent deploys faster (cached dependencies)

**Error 4: "Build failed" with unclear error**
- Common cause: Requirements conflict
- Solution: Click **"Redeploy"** (top-right) and try again

---

## STEP 3: TEST BACKEND API

### 3.1 Get Backend URL

1. Go to Render Dashboard
2. Find "kidney-detection-backend" service
3. Copy the URL (gray text top, e.g., `https://kidney-detection-backend.onrender.com`)

### 3.2 Test Health Endpoint

Open in browser or terminal:

```bash
# Browser: Just visit this URL
https://kidney-detection-backend.onrender.com/health

# Terminal (PowerShell):
curl https://kidney-detection-backend.onrender.com/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-03-28T...",
  "torch_available": true,
  "service": "kidney_detection_api"
}
```

**Status Variations:**
- ✅ `"status": "healthy"` → Backend ready
- ⏳ `"status": "initializing"` → PyTorch still loading (wait 10 seconds, refresh)
- ❌ No response / error → Check backend logs (see Troubleshooting)

### 3.3 Test Prediction Endpoint (Optional)

```powershell
# Create a test image file or use existing image
# Then send to backend

# Example with curl:
curl -X POST `
  -F "file=@C:\path\to\image.jpg" `
  https://kidney-detection-backend.onrender.com/predict
```

Expected response:
```json
{
  "prediction": "normal",
  "confidence": 0.92,
  "processing_time": 0.34,
  "model": "best_model"
}
```

---

## STEP 4: DEPLOY FRONTEND

### 4.1 Create Frontend Service

1. **Go to Render Dashboard:** https://dashboard.render.com
2. **Click:** "New +" → **"Static Site"**
3. **Fill in:**
   - **Name:** `kidney-detection-frontend` (lowercase, no spaces)
   - **Repository:** Select `Ai_powered_kidney_stone_detection`
   - **Branch:** `main`
   - **Root Directory:** `frontend` (**CRITICAL**)
   - **Build Command:** (copy below)
   - **Publish Directory:** `dist`

### 4.2 Build Command (Frontend)

```bash
npm install && npm run build
```

This installs dependencies and builds optimized production bundle.

### 4.3 Environment Variables (Frontend)

Add this variable:

```
VITE_API_BASE_URL=https://kidney-detection-backend.onrender.com
```

**Why:** Tells frontend where to reach backend API

### 4.4 Specify Plan

- **Instance Type:** `Free`

### 4.5 Deploy

1. Scroll down → Click **"Create Static Site"**
2. **Wait 2-3 minutes** (first build slower)

### ✅ Deployment Success Signs:
- Logs show: `build succeeded`
- Status badge shows: **"Live"** (green)
- Your frontend URL appears (e.g., `https://kidney-detection-frontend.onrender.com`)

### ❌ Common Errors:

**Error 1: "npm: command not found"**
- ✅ FIXED: Render automatically includes Node.js
- Solution: Let Render auto-detect Node version from package.json

**Error 2: "VITE_API_BASE_URL not set"**
- ✅ FIXED: Add environment variable (see step 4.3)
- Verify: Frontend settings → Environment

**Error 3: CORS error in browser console**
- ✅ Backend already has CORS enabled
- Solution: Verify backend URL in VITE_API_BASE_URL (no trailing slash)

---

## STEP 5: END-TO-END TESTING

### 5.1 Test from Frontend

1. **Open frontend URL** in browser:
   ```
   https://kidney-detection-frontend.onrender.com
   ```

2. **You should see:**
   - Page loads with title "Kidney Stone Detection"
   - Upload button/area visible
   - No console errors (check browser DevTools: F12 → Console)

### 5.2 Upload Test Image

1. Click **"Upload Image"** button
2. Select any medical image from your computer
3. **Expected behavior:**
   - Spinner/loader shows (1-3 seconds)
   - Result appears: "Stone Detected" or "Normal"
   - Confidence percentage shown
   - Processing time shown

### 5.3 Validate Complete Flow

**Browser Console (F12 → Console tab):**
- Should show **NO red errors**
- May show blue info logs (normal)

**What should work:**
- ✅ Image uploads successfully
- ✅ Backend receives image
- ✅ PyTorch model processes
- ✅ Result returns to frontend
- ✅ Display shows prediction with confidence

---

## STEP 6: ENABLE KEEP-ALIVE (AUTOMATIC - NO ACTION NEEDED)

### 6.1 Verify Keep-Alive is Automatic

The GitHub Actions workflow is **already configured**. It will:

✅ **Automatically run every 14 minutes**  
✅ **Ping backend health endpoint**  
✅ **Prevent Free Tier hibernation**  
✅ **Cost $0** (uses free GitHub quota)

**No setup needed** - it's already in your repo at:
```
.github/workflows/keep-backend-warm.yml
```

### 6.2 Monitor Keep-Alive (Optional)

Go to your GitHub repo → **"Actions"** tab
- Should see "Keep Backend Warm" workflow
- Green checkmarks = runs successful
- If red: See Troubleshooting section

---

## TROUBLESHOOTING CHECKLIST

### ❓ Backend won't start (red status on Render)

**Check logs:**
1. Render Dashboard → kidney-detection-backend
2. Click **"Logs"** tab (top)
3. Look for errors about torch, imports, or Python

**If you see torch/import errors:**
- This should NOT happen (we fixed it)
- But if it does: Restart deployment (button top-right)
- If still fails: Check that root directory is set to `backend/`

**If you see "Command not found: ./startup-final.sh":**
- Root directory not set correctly
- Fix: Click "Settings" → Set "Root Directory" to `backend`
- Redeploy

### ❓ Frontend shows blank page or doesn't connect to backend

**Check browser console (F12):**
- Look for CORS errors or 404 errors
- Look for "Cannot connect to https://kidney-detection-backend..."

**Common fixes:**
1. **Verify backend is deployed and "Live"** (green status on Render)
2. **Verify VITE_API_BASE_URL environment variable:**
   - Frontend settings → Environment variables
   - Should be: `https://kidney-detection-backend.onrender.com`
   - No trailing slash!
3. **Verify domain names match:**
   - Copy exact URL from Render (includes .onrender.com)
   - No typos
4. **Verify backend /health endpoint works:**
   - Visit in browser: `https://kidney-detection-backend.onrender.com/health`
   - Should see JSON response
   - If nothing: Backend is hibernated, wait 30 seconds (keep-alive will wake it)

### ❓ First request to backend takes 30+ seconds

**This is NORMAL on Free Tier:**
- First wake from hibernation takes 30-45 seconds
- Keep-alive workflow prevents this after initial deploy
- Wait 1-2 hours for keep-alive to warm up backend

**Can speed up:**
- First manual request wakes backend
- Then subsequent requests are fast (2-5 seconds)
- Keep-alive prevents re-hibernation

### ❓ Upload returns error 500 from backend

**Check backend logs:**
1. Render → kidney-detection-backend → Logs
2. Look for error traces

**Common causes:**
- Model file not downloading: Wait 5 minutes for first deploy to complete
- PyTorch not available: Restart deployment
- Image format unsupported: Try different image (JPG/PNG)

**Solution:**
- Wait 2 minutes (model downloads on startup)
- Try uploading again
- If persists: Restart backend service

### ❓ Want to check what's happening live

**View backend logs (real-time):**
1. Render Dashboard → kidney-detection-backend
2. Click **"Logs"** → Text streams live
3. Upload image from frontend → Watch logs show processing

**View frontend deploy logs:**
1. Render Dashboard → kidney-detection-frontend
2. Click **"Logs"** → See build output
3. Redeploy to see new logs

---

## FINAL VALIDATION CHECKLIST

✅ Use this before declaring deployment complete:

```
☐ Backend URL works (health endpoint returns JSON)
☐ Frontend URL loads (page appears, no blank screen)
☐ Can upload image from frontend
☐ Backend processes image (returns prediction)
☐ Frontend shows prediction result with confidence
☐ Browser console has NO red errors
☐ Keep-alive workflow shows green checkmarks in GitHub Actions
☐ Can refresh frontend and upload another image
☐ Backend doesn't take 30+ seconds on second upload
```

All checked? ✅ **You're Live!**

---

## COST VERIFICATION

**Confirm $0/month deployment:**

```
Backend:     Free Tier    = $0
Frontend:    Free Tier    = $0
Keep-Alive:  GitHub free  = $0
─────────────────────────────
TOTAL:                      $0/month
```

**Verify in Render:**
1. Render Dashboard
2. Click your avatar → Billing
3. Should show: "You are on the free plan"

---

## NEXT STEPS

1. ✅ **Complete deployment using steps above**
2. ✅ **Test using Step 5 checklist**
3. ✅ **Monitor logs for 24 hours** (first 24h = important)
4. ✅ **Share your live app!**

If you want to upgrade later:
- Render → Backend service → Select plan "Starter" ($7/month) gets instant response
- But Free tier works great for development!

---

## QUICK REFERENCE DURING DEPLOYMENT

| Step | What | Exact Value |
|------|------|-------------|
| **Backend Root** | Directory | `backend` |
| **Backend Build Cmd** | Do this | `pip install --upgrade pip setuptools wheel && pip install -r requirements-render.txt && python -c "import sys; sys.path.insert(0, '/opt/render/project/backend'); from app.main import app; print('✓ Backend imports verified')" && chmod +x startup-final.sh` |
| **Backend Start Cmd** | Do this | `./startup-final.sh` |
| **Backend Plan** | CRITICAL | `Free` (not Starter!) |
| **Frontend Root** | Directory | `frontend` |
| **Frontend Build** | Do this | `npm install && npm run build` |
| **Frontend Publish** | Directory | `dist` |
| **Frontend Env** | VITE_API_BASE_URL | `https://kidney-detection-backend.onrender.com` |
| **Frontend Plan** | CRITICAL | `Free` |

---

## SUPPORT

If anything breaks:
1. Check "Troubleshooting" section above first
2. Check Render logs (most info there)
3. Verify all exact commands were used
4. Restart service (button on Render dashboard)

Good luck! 🚀
