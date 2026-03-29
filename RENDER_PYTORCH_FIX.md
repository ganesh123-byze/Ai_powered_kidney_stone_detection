# Render Deployment Fix - PyTorch Removal Issue

## Problem
You removed PyTorch from `requirements-render.txt` to reduce slug size, but the code tries to auto-convert `.pth` → `.onnx` using PyTorch if the ONNX file doesn't exist.

## Solution: Pick One Option

### ✅ OPTION 1: Use ONNX Model (RECOMMENDED - Production Ready)

**Best for:** Production deployments, zero PyTorch dependency

#### Step 1: Convert locally
```bash
# Install torch temporarily (local only)
pip install torch torchvision

# Run conversion script
python backend/convert_model_to_onnx.py

# Creates: backend/saved_models/best_model.onnx
```

#### Step 2: Upload to GitHub Releases
1. Go to: https://github.com/ganesh123-byze/Ai_powered_kidney_stone_detection/releases
2. Create new release `v1.0.1`
3. Upload `backend/saved_models/best_model.onnx`
4. Copy download URL

#### Step 3: Update download script
Edit `backend/download_model.py` - change URL:
```python
GITHUB_RELEASE_URL = "https://github.com/.../releases/download/v1.0.1/best_model.onnx"
```

#### Step 4: Deploy to Render
```bash
git add .
git commit -m "Deploy: Update to ONNX model for production"
git push origin main
```
Render will auto-deploy. The `download_model.py` runs during build and downloads the lightweight ONNX.

**Result:** ✅ No PyTorch installed. Fast inference on Render Free Tier.

---

### 🟡 OPTION 2: Temporary PyTorch for Build (Quick Fix)

**Best for:** Quick testing, if you can't convert locally

#### Step 1: Add torch to requirements (temporarily)
Edit `requirements-render.txt`:
```txt
# Temporary: Only for .pth → .onnx conversion during build
# Remove this after first successful deployment
torch>=2.0.0,<3.0.0
torchvision>=0.15.0,<1.0.0

# Lightweight inference (primary)
onnxruntime>=1.16.0
```

#### Step 2: Update render.yaml build process
Already done! It will now:
1. Install torch temporarily
2. Auto-convert `.pth` → `.onnx` during startup
3. Model runs on ONNX Runtime (not torch)

#### Step 3: After successful deployment, remove torch
```bash
# Edit requirements-render.txt - comment out torch/torchvision
# Commit and push
git push origin main
```
Render will rebuild without torch. The `.onnx` file stays cached.

**Result:** ⚠️ First deploy takes longer (torch install ~100MB), but works.

---

### ❌ OPTION 3: Keep PyTorch (NOT RECOMMENDED)

**Only if:** You need it for other reasons

Just keep torch in `requirements-render.txt`. This works but:
- Adds 1-2GB to build slug
- Slower deployments
- Wastes disk/memory on Render free tier
- ❌ Will likely fail on free tier (slug size limit)

---

## Immediate Actions (Next 5 min)

### If you have ONNX ready:
```bash
# Option 1 (RECOMMENDED)
git add .
git commit -m "Fix: Use ONNX model for Render, graceful torch error handling"
git push origin main
```

### If you don't have ONNX yet:
```bash
# Option 2 - Temporary torch for build
cd backend
pip install torch torchvision
python convert_model_to_onnx.py
# Check created: backend/saved_models/best_model.onnx

# Then upload to releases and do Option 1
```

---

## What Was Fixed

1. **model_loader.py:** Graceful error if PyTorch not available (clear message)
2. **download_model.py:** 
   - Tries `.onnx` first (production-ready)
   - Falls back to `.pth` (if torch available)
   - Better error messages
3. **render.yaml:** Runs `download_model.py` during build
4. **New script:** `convert_model_to_onnx.py` for local conversion

---

## Testing Locally (Before Deployment)

```bash
cd backend

# Test with just ONNX Runtime (no torch)
python -c "from app.models.model_loader import ModelLoader; m = ModelLoader(); print(m.load_model('saved_models/best_model.onnx'))"

# Should work without errors or torch import
```

---

## Deployment URLs (After Fix)

- Frontend: `https://kidney-detection-frontend.onrender.com`
- Backend API: `https://kidney-detection-backend.onrender.com`
- API Docs: `https://kidney-detection-backend.onrender.com/docs`
- Health Check: `https://kidney-detection-backend.onrender.com/health`

---

## Questions?

**Error during conversion?** → Follow Option 1 carefully, all steps needed
**Build still fails?** → Check Render logs for specific error
**Need PyTorch for training?** → Keep it only in local `requirements.txt`, use `requirements-render.txt` for production
