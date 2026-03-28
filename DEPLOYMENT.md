# 🚀 Deployment Guide - Kidney Stone Detection

Complete guide to deploy this project on **Render** (Backend + Frontend) and push to GitHub.

---

## 📋 Table of Contents

1. [GitHub Setup](#github-setup)
2. [Backend Deployment on Render](#backend-deployment)
3. [Frontend Deployment on Render](#frontend-deployment)
4. [Environment Variables](#environment-variables)
5. [Troubleshooting](#troubleshooting)
6. [Monitoring & Logs](#monitoring--logs)

---

## GitHub Setup

### Step 1: Create GitHub Repository

```bash
# Initialize git (already done)
git status

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Kidney stone detection system"

# Push to GitHub
# First, create a new repo on GitHub.com
# Then:
git remote add origin https://github.com/YOUR-USERNAME/kidney-detection.git
git branch -M main
git push -u origin main
```

### Step 2: Verify .gitignore

**Key files being ignored:**
- ✅ `best_model.pth` (too large)
- ✅ `.env` files (contain secrets)
- ✅ `node_modules/`, `venv/`
- ✅ `__pycache__/`

**Check what will be pushed:**
```bash
git status
```

---

## Backend Deployment

### Prerequisites
- Render account (https://render.com)
- GitHub repository connected to Render

### Step 1: Prepare Backend for Render

**Create backend-specific environment:**

1. Copy `.env.example` to understand variables:
```bash
cat backend/.env.example
```

2. These environment variables will be set in Render dashboard (not committed)

### Step 2: Create Backend Service on Render

1. **Log in to Render Dashboard**

2. **Click "New +" → "Web Service"**

3. **Connect your GitHub repository**

4. **Configure Service:**
   - **Name**: `kidney-detection-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```

5. **Select Plan**: 
   - **Free** (for testing)
   - **Starter** ($7/month) - Recommended (512MB RAM)
   - **Standard** ($12/month) - Better for production

### Step 3: Set Environment Variables

In Render Dashboard → Your Backend Service → Environment:

```
API_HOST=0.0.0.0
API_PORT=8000
MODEL_ARCHITECTURE=resnet50
DEVICE=auto
USE_AMP=true
LOG_LEVEL=INFO
NUM_WORKERS=2
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Step 4: Handle Model File

**Problem**: `best_model.pth` is large (~200MB+) - can't store on Render

**Solution A: Use URL Download (Recommended)**

Create `backend/download_model.py`:
```python
import os
import requests
from pathlib import Path

MODEL_URL = "https://github.com/YOUR-USERNAME/kidney-detection/releases/download/v1.0/best_model.pth"
MODEL_PATH = Path("saved_models/best_model.pth")

def download_model():
    if MODEL_PATH.exists():
        print("✓ Model already present")
        return
    
    print(f"Downloading model from {MODEL_URL}...")
    response = requests.get(MODEL_URL, stream=True)
    response.raise_for_status()
    
    MODEL_PATH.parent.mkdir(exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print("✓ Model downloaded successfully")

if __name__ == "__main__":
    download_model()
```

Update **Build Command** on Render:
```bash
pip install -r requirements.txt && python download_model.py
```

**Solution B: GitHub Releases**

1. Upload model to GitHub Releases (https://github.com/YOUR-USERNAME/kidney-detection/releases/new)
2. Use URL in build script above

**Solution C: Persistent Directory** (Paid plans only)

1. Use Render's persistent disk: `/persistent`
2. Set `MODEL_PATH=/persistent/best_model.pth` in environment

### Step 5: Test Backend

Once deployed, Render will give you a URL like:
```
https://kidney-detection-backend.onrender.com
```

Test the API:
```bash
curl https://kidney-detection-backend.onrender.com/api/v1/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

## Frontend Deployment

### Step 1: Create Frontend Service on Render

1. **Click "New +" → "Static Site"** (or "Web Service" for Node)

2. **Configure Service:**
   - **Name**: `kidney-detection-frontend`
   - **Root Directory**: `frontend`
   - **Build Command**:
     ```bash
     npm install && npm run build
     ```
   - **Publish Directory**: `dist`

3. **Select Plan**: Free tier is fine for frontend

### Step 2: Set Environment Variables

In Render Dashboard → Your Frontend Service → Environment:

```
VITE_API_URL=https://kidney-detection-backend.onrender.com
VITE_ENVIRONMENT=production
VITE_DEBUG=false
```

### Step 3: Wait for Build

Render will automatically:
1. Install dependencies (`npm install`)
2. Build the project (`npm run build`)
3. Deploy to CDN

### Step 4: Test Frontend

Render will give you a URL like:
```
https://kidney-detection-frontend.onrender.com
```

Visit it in your browser and test image upload!

---

## Environment Variables

### Backend (.env.example)

| Variable | Example | Purpose |
|----------|---------|---------|
| `API_HOST` | `0.0.0.0` | Listen on all interfaces |
| `API_PORT` | `8000` | FastAPI port |
| `MODEL_PATH` | `saved_models/best_model.pth` | Model checkpoint location |
| `DEVICE` | `auto` | Use GPU if available |
| `CORS_ORIGINS` | `https://yourdomain.com` | Frontend URL for CORS |
| `NUM_WORKERS` | `2` | Parallel inference workers |

### Frontend (.env.example)

| Variable | Example | Purpose |
|----------|---------|---------|
| `VITE_API_URL` | `https://backend-url.onrender.com` | Backend API endpoint |
| `VITE_ENVIRONMENT` | `production` | Environment type |
| `VITE_DEBUG` | `false` | Enable debug logging |

---

## Monitoring & Logs

### View Backend Logs

In Render Dashboard:
1. Go to Backend Service
2. Click "Logs" tab
3. See real-time logs and errors

**Common issues:**
```
ModuleNotFoundError: No module named 'torch'
→ Check requirements.txt includes torch with CUDA

Connection refused on port 8000
→ Check "Start Command" is correct

Model file not found
→ Verify MODEL_PATH environment variable
```

### View Frontend Logs

In Render Dashboard:
1. Go to Frontend Service
2. Click "Logs" tab
3. Check build logs if deployment fails

---

## Database Integration (Future)

Currently, this project uses file-based storage. For production:

- **PostgreSQL**: Render offers free PostgreSQL tier (90-day trial)
- **MongoDB**: MongoDB Atlas offers free tier
- **Storage**: Use Render Disk for persistent file storage

---

## SSL/HTTPS

✅ **Render automatically provides free SSL certificates**

Your services will be accessible at:
- Backend: `https://kidney-detection-backend.onrender.com`
- Frontend: `https://kidney-detection-frontend.onrender.com`

---

## Scaling Considerations

| Aspect | Free | Starter | Standard |
|--------|------|---------|----------|
| RAM | 512MB | 512MB | 1GB |
| vCPU | Shared | Shared | 0.5 |
| Requests/sec | Limited | ~100 | ~1000 |
| Price | Free | $7/mo | $12/mo |

**Recommendation**: Start with Free tier for testing, then upgrade to Starter for production.

---

## Custom Domain Setup

To connect your own domain:

1. **Get your domain** (GoDaddy, Namecheap, etc.)

2. **In Render Dashboard**:
   - Backend Service → Settings → Custom Domain
   - Add `api.yourdomain.com`

3. **Update DNS Records** to point to Render IP

4. **Update Frontend**:
   - Set `VITE_API_URL=https://api.yourdomain.com`
   - Redeploy

---

## Auto-Deploy Setup

✅ **Already configured in `.github/workflows`**

Every push to `main` branch will:
1. Run syntax checks
2. Trigger Render deployment (if connected)

---

## Troubleshooting

### Backend won't start
```bash
# Check logs on Render dashboard
# Look for: ModuleNotFoundError, torch not found

# Solution: Ensure requirements.txt has torch without version constraints
pip install -r requirements.txt --force-reinstall
```

### Frontend can't connect to backend
```
CORS error in browser console
↓
Check VITE_API_URL matches backend URL
↓
Check CORS_ORIGINS on backend includes frontend URL
```

### Model download fails during build
```bash
# Check model URL is accessible
curl -I https://your-model-url

# Solution: Use GitHub releases for reliable hosting
```

### Render free tier spins down
```
Issue: "Service Inactive" after 15 min inactivity
↓
Solution: Upgrade to Starter ($7/mo) or use external pings
```

---

## Next Steps

1. ✅ Push code to GitHub
2. ✅ Create Render Web Services
3. ✅ Set environment variables
4. ✅ Deploy backend & test API
5. ✅ Deploy frontend & test UI
6. 📊 Monitor with Render logs
7. 🎯 Collect feedback & iterate

---

## Support Resources

- **Render Docs**: https://render.com/docs
- **FastAPI**: https://fastapi.tiangolo.com
- **Vite**: https://vitejs.dev
- **GitHub Actions**: https://docs.github.com/en/actions

---

**Last Updated**: March 2026
**Version**: 1.0.0
