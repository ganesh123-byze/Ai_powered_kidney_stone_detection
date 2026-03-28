# 🚀 RENDER DEPLOYMENT - QUICK REFERENCE CARD

**Project:** Kidney Stone Detection | **Platform:** Render.com | **Date:** March 28, 2026

---

## 📋 QUICK LINKS

- **GitHub Repo:** https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection
- **Render Dashboard:** https://dashboard.render.com
- **Full Guide:** See PROFESSIONAL_DEPLOYMENT_GUIDE.md in repo

---

## ⚡ BACKEND DEPLOYMENT (5 min)

### 1️⃣ Connect Repository
```
Render Dashboard → New + → Web Service
Repository: Ai_powered_kidney_stone_detection
Branch: main
```

### 2️⃣ Configure Service
```
Name:              kidney-detection-backend
Root Directory:    backend
Runtime:           Python 3.11
Plan:              Starter ($7/month)
Auto-Deploy:       Enabled
```

### 3️⃣ Build Command
```bash
pip install --upgrade pip setuptools wheel && \
pip install --no-cache-dir -r requirements-render.txt && \
python download_model.py && \
chmod +x startup-final.sh
```

### 4️⃣ Start Command
```
./startup-final.sh
```

### 5️⃣ Environment Variables
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

### 6️⃣ Deploy & Wait
- Expected time: **12-17 minutes** (PyTorch install is slowest)
- Monitor logs: Should see "✅ Startup check complete!"

### 7️⃣ Test
```bash
curl https://kidney-detection-backend.onrender.com/health
# Expected: {"status": "healthy", "version": "1.0.0"}
```

---

## 🎨 FRONTEND DEPLOYMENT (3 min)

### 1️⃣ Connect Repository
```
Render Dashboard → New + → Static Site
Repository: Ai_powered_kidney_stone_detection
Branch: main
```

### 2️⃣ Configure Service
```
Name:                    kidney-detection-frontend
Root Directory:          frontend
Build Command:           npm install && npm run build
Publish Directory:       dist
Plan:                    Free (unlimited)
Auto-Deploy:             Enabled
```

### 3️⃣ Environment Variables
```
VITE_API_URL=https://kidney-detection-backend.onrender.com
VITE_ENVIRONMENT=production
VITE_DEBUG=false
```

### 4️⃣ Deploy & Wait
- Expected time: **2-4 minutes**
- Monitor logs: Should see build success

### 5️⃣ Access
```
https://kidney-detection-frontend.onrender.com
```

---

## 🧪 TESTING (5 min)

### Backend API
```javascript
// Browser console:
fetch('https://kidney-detection-backend.onrender.com/health')
  .then(r => r.json())
  .then(console.log)
```

### Full Workflow
1. Open frontend URL
2. Upload ultrasound image
3. Verify prediction appears
4. Check browser console (no CORS errors)
5. Check backend logs

---

## 🆘 QUICK TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| **Build fails** | Check logs, verify build command exact |
| **503 error** | Cold start - wait 1-2 min |
| **CORS errors** | Update CORS_ORIGINS env var in backend |
| **"torch" not found** | Already fixed - use correct build command |
| **Model download fails** | First build caches it - rebuild to use cache |

---

## 📊 EXPECTED TIMES

| Task | Duration |
|------|----------|
| Backend build | 12-17 min |
| Backend cold start | 30-45 sec |
| Backend warm request | 2-5 sec |
| Frontend build | 2-4 min |
| Frontend page load | <1 sec |

---

## 💰 PRICING

| Service | Plan | Cost | Performance |
|---------|------|------|-------------|
| Backend | Starter | $7/month | Good ⭐⭐⭐ |
| Backend | Free | $0 | Sleep after 15 min ⭐ |
| Frontend | Free | $0 | Always on ⭐⭐⭐ |
| **Total** | **Recommended** | **$7/month** | **Production Ready** |

---

## 📱 USEFUL URLS (After Deployment)

```
Backend Health:     https://kidney-detection-backend.onrender.com/health
Backend API Docs:   https://kidney-detection-backend.onrender.com/docs
Backend OpenAPI:    https://kidney-detection-backend.onrender.com/openapi.json
Frontend App:       https://kidney-detection-frontend.onrender.com
Render Dashboard:   https://dashboard.render.com
```

---

## ✅ SIGN-OFF

- [ ] Both services deployed successfully
- [ ] /health endpoint returns 200
- [ ] Frontend loads without errors
- [ ] Prediction workflow works end-to-end
- [ ] No CORS errors in console
- [ ] Ready for production use

---

**Total Deployment Time:** ~30 minutes  
**Difficulty:** Easy ⭐⭐  
**Documentation:** See PROFESSIONAL_DEPLOYMENT_GUIDE.md

**Status:** ✅ READY TO DEPLOY
