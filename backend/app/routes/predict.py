"""
Kidney Ultrasound Classification - Predict Route
API endpoints for model inference.
"""

import os
import base64
from pathlib import Path
from typing import Optional
import io

from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Form, Depends
from loguru import logger

from app.schemas.request import PredictionRequest, ModelLoadRequest
from app.schemas.response import (
    PredictionResponse, 
    ErrorResponse, 
    ModelInfoResponse,
    BatchPredictionResponse
)
from app.services.inference import get_inference_service, initialize_inference_service


router = APIRouter(prefix="/predict", tags=["Prediction"])


def get_service():
    """Dependency to get inference service."""
    return get_inference_service()


@router.post(
    "",
    response_model=PredictionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid image"},
        500: {"model": ErrorResponse, "description": "Prediction failed"},
        503: {"model": ErrorResponse, "description": "Model not loaded"}
    },
    summary="Predict kidney condition from ultrasound image",
    description="Upload an ultrasound image and get classification results"
)
async def predict(
    file: UploadFile = File(..., description="Ultrasound image file"),
    return_all_probs: bool = Query(
        False, 
        description="Return probabilities for all classes"
    ),
    generate_gradcam: bool = Query(
        False, 
        description="Generate Grad-CAM visualization"
    )
):
    """
    Predict kidney condition from an ultrasound image.
    
    Returns:
    - **class**: Predicted class name (e.g., "CKD Stage 3")
    - **confidence**: Confidence score (0-1)
    - **severity**: Severity level (Normal, Mild, Moderate, Severe)
    """
    service = get_inference_service()
    
    # Check if model is loaded
    if not service.model_loader.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please load a model first using /model/load endpoint"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Run prediction
        result = service.predict(
            image_source=content,
            return_all_probs=return_all_probs,
            generate_gradcam=generate_gradcam
        )
        
        logger.info(f"Prediction: {result['class']} ({result['confidence']:.2%})")
        
        return PredictionResponse(
            success=True,
            **{k: v for k, v in result.items() if k != 'class'},
            class_name=result['class']
        )
        
    except ValueError as e:
        logger.warning(f"Invalid image: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
    finally:
        await file.close()


@router.post(
    "/base64",
    response_model=PredictionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid image"},
        500: {"model": ErrorResponse, "description": "Prediction failed"},
        503: {"model": ErrorResponse, "description": "Model not loaded"}
    },
    summary="Predict from base64 encoded image",
    description="Submit a base64 encoded image for classification"
)
async def predict_base64(request: PredictionRequest):
    """
    Predict kidney condition from a base64 encoded image.
    
    Useful for web applications that encode images in base64.
    """
    service = get_inference_service()
    
    if not service.model_loader.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please load a model first"
        )
    
    if not request.image_base64:
        raise HTTPException(status_code=400, detail="No image data provided")
    
    try:
        # Decode base64
        image_data = base64.b64decode(request.image_base64)
        
        # Run prediction
        result = service.predict(
            image_source=image_data,
            return_all_probs=request.return_all_probs,
            generate_gradcam=request.generate_gradcam
        )
        
        return PredictionResponse(
            success=True,
            **{k: v for k, v in result.items() if k != 'class'},
            class_name=result['class']
        )
        
    except base64.binascii.Error:
        raise HTTPException(status_code=400, detail="Invalid base64 encoding")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post(
    "/path",
    response_model=PredictionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid path"},
        404: {"model": ErrorResponse, "description": "File not found"},
        500: {"model": ErrorResponse, "description": "Prediction failed"}
    },
    summary="Predict from file path",
    description="Predict from an image file already on the server"
)
async def predict_from_path(
    file_path: str = Form(..., description="Path to the image file"),
    return_all_probs: bool = Form(False),
    generate_gradcam: bool = Form(False)
):
    """
    Predict kidney condition from a file path.
    
    Useful for processing images that have been uploaded via the /upload endpoint.
    """
    service = get_inference_service()
    
    if not service.model_loader.is_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    path = Path(file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    
    try:
        result = service.predict(
            image_source=str(path),
            return_all_probs=return_all_probs,
            generate_gradcam=generate_gradcam
        )
        
        return PredictionResponse(
            success=True,
            **{k: v for k, v in result.items() if k != 'class'},
            class_name=result['class']
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get(
    "/model/info",
    response_model=ModelInfoResponse,
    summary="Get model information",
    description="Get information about the currently loaded model"
)
async def get_model_info():
    """Get information about the loaded model."""
    service = get_inference_service()
    info = service.get_model_info()
    return ModelInfoResponse(**info)


@router.post(
    "/model/load",
    response_model=ModelInfoResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Model file not found"},
        500: {"model": ErrorResponse, "description": "Load failed"}
    },
    summary="Load a model",
    description="Load a trained model from a checkpoint file"
)
async def load_model(request: ModelLoadRequest):
    """
    Load a model from a checkpoint file.
    
    - **model_path**: Path to the .pth checkpoint file
    - **model_name**: Architecture ('resnet50' or 'densenet121')
    - **device**: Device to load on ('cuda', 'cpu', or None for auto)
    """
    path = Path(request.model_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Model file not found: {request.model_path}")
    
    try:
        service = initialize_inference_service(
            model_path=str(path),
            model_name=request.model_name,
            device=request.device
        )
        
        info = service.get_model_info()
        logger.info(f"Model loaded: {request.model_path}")
        
        return ModelInfoResponse(**info)
        
    except Exception as e:
        logger.error(f"Model load error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")


@router.post(
    "/model/unload",
    response_model=dict,
    summary="Unload the model",
    description="Unload the current model and free memory"
)
async def unload_model():
    """Unload the current model and free GPU memory."""
    service = get_inference_service()
    service.model_loader.unload_model()
    return {"success": True, "message": "Model unloaded"}
