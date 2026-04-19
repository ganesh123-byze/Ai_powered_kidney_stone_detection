"""
Kidney Ultrasound Classification - FastAPI Main Application
Production-ready backend with async endpoints and proper error handling.
Lightweight CPU-only inference using ONNX Runtime.
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.routes import predict, upload
from app.schemas.response import HealthResponse, ErrorResponse, ModelInfoResponse
from app.services.inference import get_inference_service


# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

# API version and info
API_VERSION = "1.0.0"
API_TITLE = "Kidney Stone Detection API"
API_DESCRIPTION = """
## AI-Powered Kidney Stone Detection System

This API provides endpoints for:
- **Image Upload**: Upload kidney ultrasound images
- **Prediction**: Detect kidney stones using deep learning (Binary: Normal vs Stone)
- **Model Management**: Load/unload trained models

### Supported Models
- ResNet50 (default, recommended)
- DenseNet121

### Classification Output
- **Class**: 'Normal' or 'stone'
- **Confidence**: Prediction confidence (0-1)
- **Severity**: 'Normal' (no stone) or 'Detected' (stone present)

### Features
- Binary classification for kidney stone detection
- Grad-CAM visualization support
- GPU acceleration (CUDA)
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("="*50)
    logger.info(f"Starting {API_TITLE} v{API_VERSION}")
    logger.info("="*50)
    
    # Log system info
    logger.info(f"Python version: {sys.version}")
    logger.info("Engine: ONNX Runtime (CPU-only, lightweight)")
    logger.info("Model framework: ONNX (.onnx or auto-converted .pth)")
    
    # Create required directories
    Path("logs").mkdir(exist_ok=True)
    Path("data/uploads").mkdir(parents=True, exist_ok=True)
    
    # Auto-load model - check environment variable first, then default path
    model_path = os.getenv("MODEL_PATH", "saved_models/best_model.pth")
    if Path(model_path).exists():
        logger.info(f"Auto-loading model from: {model_path}")
        try:
            service = get_inference_service()
            service.load_model(model_path)
            logger.info(f"✓ Model loaded successfully: {model_path}")
        except Exception as e:
            logger.warning(f"Failed to auto-load model: {e}")
            logger.warning(f"Use /api/v1/predict/model/load to load a model manually")
    else:
        logger.warning(f"Model file not found at {model_path}")
        logger.warning(f"Use /api/v1/predict/model/load to load a model manually")
    
    logger.info("Application startup complete")
    logger.info("Engine ready for predictions (ONNX Runtime - CPU optimized)")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    
    # Unload model and free memory
    try:
        service = get_inference_service()
        service.model_loader.unload_model()
    except Exception:
        pass
    
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else None
        }
    )
 

# Include routers
app.include_router(predict.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")


# Root endpoint 
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


# Health check endpoint
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check",
    description="Check if the API is running and get system status"
)
async def health_check(include_model_info: bool = False):
    """
    Health check endpoint.
    
    Returns service status and optionally model information.
    """
    service = get_inference_service()
    
    response = HealthResponse(
        status="healthy",
        version=API_VERSION,
        model_loaded=service.model_loader.is_loaded,
        cuda_available=False  # ONNX Runtime uses CPU only
    )
    
    if include_model_info:
        info = service.get_model_info()
        response.model_info = ModelInfoResponse(**info)
    
    return response


# Quick predict endpoint at root level for convenience
@app.post(
    "/predict",
    response_model=dict,
    tags=["Prediction"],
    summary="Quick prediction endpoint",
    description="Shortcut to /api/v1/predict"
)
async def quick_predict(request: Request):
    """
    Quick prediction endpoint.
    Redirects to the main prediction endpoint.
    """
    # This is a convenience endpoint that forwards to the main API
    from fastapi import File, UploadFile
    from starlette.datastructures import FormData
    
    form = await request.form()
    
    if "file" not in form:
        raise HTTPException(status_code=400, detail="No file provided")
    
    service = get_inference_service()
    
    if not service.model_loader.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    file = form["file"]
    content = await file.read()
    
    try:
        result = service.predict(content)
        return {
            "success": True,
            "class": result["class"],
            "confidence": result["confidence"],
            "severity": result["severity"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Model endpoints at root level
@app.get(
    "/model",
    response_model=ModelInfoResponse,
    tags=["Model"],
    summary="Get model info"
)
async def model_info():
    """Get information about the loaded model."""
    service = get_inference_service()
    info = service.get_model_info()
    return ModelInfoResponse(**info)


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("DEBUG", "false").lower() == "true"
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=1,  # Single worker for model serving
        log_level="info"
    )
