"""
Kidney Ultrasound Classification - Pydantic Request Schemas
Request validation models for API endpoints.
"""

from typing import Optional
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Request schema for prediction endpoint when using JSON body."""
    
    image_base64: Optional[str] = Field(
        None,
        description="Base64 encoded image data"
    )
    return_all_probs: bool = Field(
        False,
        description="Return probabilities for all classes"
    )
    generate_gradcam: bool = Field(
        False,
        description="Generate Grad-CAM visualization"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_base64": "base64_encoded_image_string",
                "return_all_probs": False,
                "generate_gradcam": False
            }
        }


class ModelLoadRequest(BaseModel):
    """Request schema for loading a model."""
    
    model_path: str = Field(
        ...,
        description="Path to the model checkpoint file"
    )
    model_name: str = Field(
        "resnet50",
        description="Model architecture (resnet50 or densenet121)"
    )
    device: Optional[str] = Field(
        None,
        description="Device to load model on (cuda, cpu, or None for auto)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_path": "saved_models/best_model.pth",
                "model_name": "resnet50",
                "device": None
            }
        }


class HealthCheckRequest(BaseModel):
    """Request schema for health check."""
    
    include_model_info: bool = Field(
        False,
        description="Include model information in response"
    )
