# 🎯 RENDER DEPLOYMENT CHECKLIST (Quick Reference)

Copy & paste exact values. Follow in order.

---

## ✅ PRE-DEPLOYMENT (5 minutes)

```powershell
# Terminal - verify Git status
cd "d:\Kidney Detection"
git status                    # Should be "nothing to commit"
git log --oneline -1          # Shows latest commit
```

**Verify:**
- [ ] Git shows no changes
- [ ] GitHub repo is PUBLIC (check https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection)

---

## ✅ BACKEND DEPLOYMENT (Render Dashboard)

### Create Web Service

| Field | Exact Value |
|-------|-------------|
| **Service Name** | `kidney-detection-backend` |
| **Repository** | `Ai_powered_kidney_stone_detection` |
| **Branch** | `main` |
| **Root Directory** | `backend` ← **CRITICAL** |
| **Runtime** | `python 3.11` |

### Build Command (COPY EXACTLY - don't edit)

```bash
pip install --upgrade pip setuptools wheel && pip install -r requirements-render.txt && python -c "import sys; sys.path.insert(0, '/opt/render/project/backend'); from app.main import app; print('✓ Backend imports verified')" && chmod +x startup-final.sh
```

**✅ Paste into:** Render Build Command field

### Start Command (COPY EXACTLY)

```bash
./startup-final.sh
```

**✅ Paste into:** Render Start Command field

### Environment Variables

Click "Advanced" → Add these (copy one at a time):

| Key | Value |
|-----|-------|
| `RENDER` | `true` |
| `PYTHONUNBUFFERED` | `true` |

### Plan Selection

- [ ] Select **`Free`** (NOT Starter!)
- [ ] Click **"Create Web Service"**
- [ ] ⏱️ Wait 3-5 minutes

### ✅ Backend Success Indicators

- [ ] Status shows **"Live"** (green)
- [ ] Logs display: `✓ Backend imports verified`
- [ ] Logs display: `INFO: Uvicorn running on 0.0.0.0:10000`
- [ ] Backend URL appears (e.g., `https://kidney-detection-backend.onrender.com`)

---

## ✅ BACKEND VALIDATION TEST

```bash
# Copy backend URL from Render dashboard

# Test 1: Health check (paste in browser or Terminal)
https://kidney-detection-backend.onrender.com/health

# Should see: {"status": "healthy", "torch_available": true, ...}

# Test 2: If you see "initializing" status
# Wait 10 seconds and refresh
```

**✅ Checks:**
- [ ] Health endpoint returns JSON (not error)
- [ ] `"torch_available": true`
- [ ] `"status": "healthy"`

---

## ✅ FRONTEND DEPLOYMENT (Render Dashboard)

### Create Static Site

| Field | Exact Value |
|-------|-------------|
| **Service Name** | `kidney-detection-frontend` |
| **Repository** | `Ai_powered_kidney_stone_detection` |
| **Branch** | `main` |
| **Root Directory** | `frontend` ← **CRITICAL** |
| **Build Command** | `npm install && npm run build` |
| **Publish Directory** | `dist` |

### Environment Variables

Click "Advanced" → Add this:

| Key | Value |
|-----|-------|
| `VITE_API_BASE_URL` | Copy backend URL:<br/>`https://kidney-detection-backend.onrender.com` |

**⚠️ IMPORTANT:** No trailing slash!

### Plan Selection

- [ ] Select **`Free`** (NOT Starter!)
- [ ] Click **"Create Static Site"**
- [ ] ⏱️ Wait 2-3 minutes

### ✅ Frontend Success Indicators

- [ ] Status shows **"Live"** (green)
- [ ] Logs display: `build succeeded`
- [ ] Frontend URL appears (e.g., `https://kidney-detection-frontend.onrender.com`)

---

## ✅ FULL SYSTEM TEST (Most Important!)

1. **Open frontend URL in browser:**
   ```
   https://kidney-detection-frontend.onrender.com
   ```

2. **Verify page loads:**
   - [ ] See page title "Kidney Stone Detection"
   - [ ] Upload button visible
   - [ ] Open DevTools (F12) → Console should have NO RED ERRORS

3. **Upload test image:**
   - [ ] Select any image file
   - [ ] Click upload
   - [ ] Spinner appears (wait 2-5 seconds)
   - [ ] Result displays (e.g., "Normal" or "Stone Detected")
   - [ ] Confidence percentage shown
   - [ ] No errors in console

4. **Upload second image:**
   - [ ] Should be faster (1-3 seconds, not 30+ seconds)
   - [ ] Result displays correctly

**✅ If all above work:**
```
🎉 YOUR APP IS LIVE AND WORKING! 🎉
```

---

## ❌ CRITICAL ERROR FIXES

### Error: Backend shows RED status

**Fix:**
1. Click backend service
2. Check **Logs** tab for errors
3. If you see "startup-final.sh not found":
   - Settings → Verify Root Directory = `backend`
   - Click **"Redeploy"** (top right)
   - Wait 5 minutes

### Error: Frontend blank page + console errors about API

**Fix:**
1. Check VITE_API_BASE_URL environment variable is set correctly
2. Verify backend is showing GREEN "Live" status
3. Redeploy frontend (click Redeploy button)
4. Check backend URL has no trailing slash

### Error: Upload returns error 500

**Fix:**
1. Wait 2 minutes (model downloads on first deploy)
2. Try uploading different image
3. Check backend logs for errors
4. Restart backend service (Redeploy button)

### Error: First upload takes 30+ seconds

**This is NORMAL:** Free Tier hibernates after inactivity. First wake takes 30-45 seconds.

**Fix:**
- Second upload should be fast (2-5 seconds)
- Keep-alive workflow will prevent future hibernation (runs every 14 min)
- After 2 hours, becomes instant

---

## ✅ FINAL CHECKLIST

Before celebrating:

- [ ] Backend health endpoint works (returns JSON)
- [ ] Frontend page loads (no blank screen)
- [ ] Image upload works
- [ ] Prediction appears with confidence
- [ ] Second upload is faster than first
- [ ] No red errors in browser console (F12)
- [ ] Can view deployment in Render dashboard

---

## 💰 COST VERIFICATION

```
Backend:  Free Tier  = $0
Frontend: Free Tier  = $0
Total:              = $0/month ✅
```

**Verify in Render:** Click your avatar → Billing → Should show "free plan"

---

## 📋 DEPLOYMENT TIME ESTIMATES

| Phase | Duration | Notes |
|-------|----------|-------|
| Pre-check | 2 min | Git verification |
| Backend create | 1 min | Click/paste settings |
| Backend build | 3-5 min | First deploy longer (PyTorch) |
| Backend test | 1 min | Health endpoint check |
| Frontend create | 1 min | Click/paste settings |
| Frontend build | 2-3 min | npm install + build |
| Full test | 2 min | Upload image, verify |
| **TOTAL** | **15-20 min** | All three services live |

---

## 🚀 YOU'RE READY!

**Next Step:** Open Render dashboard and follow exact values from tables above.

**Questions?** Go to: `RENDER_DEPLOYMENT_GUIDE.md` (detailed version)
