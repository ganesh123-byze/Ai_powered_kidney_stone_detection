"""
Kidney Ultrasound Classification - Pydantic Response Schemas
Response validation models for API endpoints.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    """Response schema for prediction endpoint (Binary: Normal vs Stone)."""
    
    success: bool = Field(
        ...,
        description="Whether the prediction was successful"
    )
    class_name: str = Field(
        ...,
        alias="class",
        description="Predicted class: 'Normal' or 'stone'"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)"
    )
    severity: str = Field(
        ...,
        description="Status: 'Normal' (no stone) or 'Detected' (stone present)"
    )
    class_index: Optional[int] = Field(
        None,
        description="Index of predicted class (0=Normal, 1=stone)"
    )
    all_probabilities: Optional[Dict[str, float]] = Field(
        None,
        description="Probabilities for all classes"
    )
    gradcam: Optional[Dict[str, Any]] = Field(
        None,
        description="Grad-CAM visualization data"
    )
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "success": True,
                "class": "stone",
                "confidence": 0.92,
                "severity": "Detected",
                "class_index": 1,
                "all_probabilities": {
                    "Normal": 0.08,
                    "stone": 0.92
                }
            }
        }


class UploadResponse(BaseModel):
    """Response schema for upload endpoint."""
    
    success: bool = Field(
        ...,
        description="Whether the upload was successful"
    )
    filename: str = Field(
        ...,
        description="Saved filename"
    )
    file_path: str = Field(
        ...,
        description="Path where file was saved"
    )
    file_size: int = Field(
        ...,
        description="File size in bytes"
    )
    message: str = Field(
        ...,
        description="Status message"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "filename": "kidney_scan_001.jpg",
                "file_path": "/tmp/uploads/kidney_scan_001.jpg",
                "file_size": 102400,
                "message": "File uploaded successfully"
            }
        }


class ErrorResponse(BaseModel):
    """Response schema for errors."""
    
    success: bool = Field(
        False,
        description="Always False for errors"
    )
    error: str = Field(
        ...,
        description="Error message"
    )
    detail: Optional[str] = Field(
        None,
        description="Detailed error information"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Invalid image format",
                "detail": "The uploaded file is not a valid image"
            }
        }


class ModelInfoResponse(BaseModel):
    """Response schema for model information."""
    
    loaded: bool = Field(
        ...,
        description="Whether a model is loaded"
    )
    model_path: Optional[str] = Field(
        None,
        description="Path to loaded model"
    )
    device: Optional[str] = Field(
        None,
        description="Device model is on"
    )
    num_classes: Optional[int] = Field(
        None,
        description="Number of output classes (2 for binary: Normal, stone)"
    )
    class_names: Optional[List[str]] = Field(
        None,
        description="List of class names"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "loaded": True,
                "model_path": "saved_models/best_model.pth",
                "device": "cuda",
                "num_classes": 2,
                "class_names": ["Normal", "stone"]
            }
        }


class HealthResponse(BaseModel):
    """Response schema for health check endpoint."""
    
    status: str = Field(
        ...,
        description="Service status"
    )
    version: str = Field(
        ...,
        description="API version"
    )
    model_loaded: bool = Field(
        ...,
        description="Whether model is loaded"
    )
    cuda_available: bool = Field(
        ...,
        description="Whether CUDA is available"
    )
    model_info: Optional[ModelInfoResponse] = Field(
        None,
        description="Model information if requested"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "model_loaded": True,
                "cuda_available": True
            }
        }


class BatchPredictionResponse(BaseModel):
    """Response schema for batch prediction."""
    
    success: bool = Field(
        ...,
        description="Whether batch prediction was successful"
    )
    total: int = Field(
        ...,
        description="Total number of images processed"
    )
    successful: int = Field(
        ...,
        description="Number of successful predictions"
    )
    failed: int = Field(
        ...,
        description="Number of failed predictions"
    )
    results: List[Dict[str, Any]] = Field(
        ...,
        description="List of prediction results"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total": 3,
                "successful": 3,
                "failed": 0,
                "results": [
                    {"class": "Normal", "confidence": 0.95, "severity": "Normal"},
                    {"class": "stone", "confidence": 0.88, "severity": "Detected"},
                    {"class": "stone", "confidence": 0.92, "severity": "Detected"}
                ]
            }
        }
