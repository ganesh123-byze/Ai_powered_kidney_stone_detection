# 🏃 Quick Start Guide

Get the Kidney Stone Detection system running locally in minutes.

---

## 📋 Prerequisites

- **Python 3.11+** (download from https://python.org)
- **Node.js 18+** (download from https://nodejs.org)
- **NVIDIA GPU** (optional, but recommended for inference speed)
- **Git** (https://git-scm.com)

---

## 🚀 Backend Setup

### 1. Create Virtual Environment

```bash
cd backend

# Windows
python -m venv venv
venv\Scripts\activate

# MacOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Install PyTorch

```bash
# With CUDA 11.8 (NVIDIA GPU):
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# CPU only:
pip install torch torchvision
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up Environment Variables

```bash
# Copy template file
cp .env.example .env

# Edit .env with your settings
# For local development, defaults should work
```

### 5. Run Backend

```bash
# Option 1: Direct with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Option 2: Use PowerShell script (Windows)
.\run.ps1
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Test API:**
```bash
curl http://localhost:8000/api/v1/health
```

---

## 🎨 Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Set up Environment Variables

```bash
# Copy template file
cp .env.example .env.local

# For local development:
# VITE_API_URL=http://localhost:8000
```

### 3. Run Development Server

```bash
npm run dev
```

**Expected output:**
```
VITE v5.0.0  ready in XXX ms

➜  Local:   http://localhost:5173/
```

Visit `http://localhost:5173` in your browser!

---

## 🧪 Test the System

### Upload a Test Image

1. Open `http://localhost:5173`
2. Click "Upload Image"
3. Select a kidney ultrasound image
4. Wait for prediction

### API Testing

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Load model
curl -X POST http://localhost:8000/api/v1/predict/model/load \
  -H "Content-Type: application/json" \
  -d '{"model_path": "saved_models/best_model.pth", "architecture": "resnet50"}'

# Upload and predict
curl -X POST http://localhost:8000/api/v1/predict/upload \
  -F "file=@path/to/image.jpg"
```

---

## 📊 Project Structure Reference

```
kidney-detection/
├── backend/              # FastAPI backend
│   ├── app/             # Main application
│   ├── training/        # Training scripts
│   ├── saved_models/    # Pre-trained models
│   └── requirements.txt # Python dependencies
│
├── frontend/            # React + Vite frontend
│   ├── src/            # Source code
│   ├── package.json    # npm dependencies
│   └── vite.config.ts  # Vite configuration
│
└── DEPLOYMENT.md       # Deployment guide
```

---

## 🐛 Common Issues

### PyTorch won't install
```
Error: No matching distribution found for torch
↓
Solution: Use official PyTorch index:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Backend won't start
```
Error: ModuleNotFoundError: No module named 'fastapi'
↓
Solution: Ensure venv is activated and requirements installed
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Frontend can't connect to backend
```
Error: Network Error (CORS)
↓
Solution: Check backend is running on port 8000:
curl http://localhost:8000/api/v1/health

Then update VITE_API_URL in .env.local:
VITE_API_URL=http://localhost:8000
```

### Model not loading
```
Error: FileNotFoundError: saved_models/best_model.pth
↓
Solution: Check file exists:
ls backend/saved_models/best_model.pth

If missing, train a new model or download from releases
```

---

## 📚 Next Steps

1. ✅ Backend running on `localhost:8000`
2. ✅ Frontend running on `localhost:5173`
3. 📖 Read [DEPLOYMENT.md](DEPLOYMENT.md) for cloud deployment
4. 🔧 Read [README.md](README.md) for full documentation
5. 🚀 Deploy to Render following DEPLOYMENT.md

---

## 💡 Useful Commands

```bash
# Backend
cd backend
python -m venv venv              # Create virtual environment
source venv/bin/activate         # Activate venv (Linux/Mac)
venv\Scripts\activate            # Activate venv (Windows)
pip install -r requirements.txt  # Install dependencies
uvicorn app.main:app --reload    # Run with hot reload

# Frontend
cd frontend
npm install                       # Install dependencies
npm run dev                       # Development server
npm run build                     # Build for production
npm run preview                   # Preview build

# Git
git status                        # Check status
git add .                         # Stage changes
git commit -m "message"           # Commit
git push                          # Push to GitHub
```

---

## 📞 Support

- **Backend Issues**: Check `backend/logs/app.log`
- **Frontend Issues**: Check browser console (F12)
- **GitHub**: Open an issue for bugs or questions
- **Render Docs**: https://render.com/docs

---

**Last Updated**: March 2026
**Version**: 1.0.0
