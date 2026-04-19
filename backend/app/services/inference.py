"""
Kidney Ultrasound Classification - Inference Service
Lightweight CPU-only inference using ONNX Runtime (no PyTorch needed).
Binary classification: Normal vs Stone (kidney stone detection).
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

import numpy as np
import cv2
from PIL import Image
from loguru import logger
import onnxruntime as rt

from app.models.model_loader import get_model_loader
from app.services.preprocessing import get_preprocessor


class InferenceService:
    """
    Service for running model inference on kidney ultrasound images.
    Uses ONNX Runtime for CPU-only inference (Render Free Tier compatible).
    Binary classification: Normal vs Stone (kidney stone detection).
    """
    
    # Class mapping for binary stone detection
    CLASS_MAPPING = {
        'normal': 'Normal',
        'healthy': 'Normal',
        'stone': 'Detected',
        'detected': 'Detected',
    }
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the inference service.
        
        Args:
            model_path: Path to ONNX model (.onnx or .pth file)
        """
        self.model_loader = get_model_loader()
        self.preprocessor = get_preprocessor()
        self.session: Optional[rt.InferenceSession] = None
        self.input_name: Optional[str] = None
        self.output_name: Optional[str] = None
        
        # Load model if path provided
        if model_path:
            self.load_model(model_path)
    
    def load_model(self, model_path: str, model_name: str = 'resnet50', device: Optional[str] = None):
        """
        Load ONNX model.
        
        Args:
            model_path: Path to model (.onnx or .pth file)
            model_name: Ignored in ONNX version, for compatibility
            device: Ignored in ONNX version, for compatibility
        """
        logger.info(f"Loading model from: {model_path}")
        
        # Use ModelLoader to handle .pth conversion if needed
        session = self.model_loader.load_model(model_path)
        self.session = session
        
        # Get input/output names
        input_names = session.get_inputs()
        output_names = session.get_outputs()
        
        if not input_names or not output_names:
            raise ValueError("ONNX model has no inputs or outputs")
        
        self.input_name = input_names[0].name
        self.output_name = output_names[0].name
        
        logger.info(f"✓ Model loaded successfully")
        logger.info(f"  Input: {self.input_name}")
        logger.info(f"  Output: {self.output_name}")
        logger.info(f"  Classes: {self.model_loader.class_names}")
    
    def _get_class_label(self, class_name: str) -> str:
        """
        Map class name to user-friendly label.
        
        For binary stone detection:
        - Normal -> 'Normal' (no stone)
        - Stone -> 'Detected' (stone present)
        """
        class_lower = class_name.lower().replace(' ', '_')
        
        for key, label in self.CLASS_MAPPING.items():
            if key in class_lower:
                return label
        
        # Fallback for binary classification
        return 'Normal' if 'normal' in class_lower else 'Detected'
    
    def predict(
        self,
        image_source: Union[str, Path, bytes, np.ndarray, Image.Image],
        return_all_probs: bool = False,
        generate_gradcam: bool = False,
    ) -> Dict[str, Any]:
        """
        Run inference on an image using ONNX Runtime.
        
        Args:
            image_source: Image source (path, bytes, array, or PIL Image)
            return_all_probs: Return probabilities for all classes
            generate_gradcam: Placeholder for Grad-CAM (not supported in ONNX yet)
        
        Returns:
            Dictionary with prediction results
        """
        if self.session is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        start_time = time.time()
        
        # Validate image
        is_valid, error_msg = self.preprocessor.validate_image(image_source)
        if not is_valid:
            raise ValueError(f"Invalid image: {error_msg}")

        # Enforce ultrasound-only inputs (reject natural photos, etc.)
        is_ultrasound, us_error = self.preprocessor.validate_ultrasound(image_source)
        if not is_ultrasound:
            raise ValueError(us_error or "Please upload ultrasound image")
        
        # Preprocess image to tensor (numpy array for ONNX)
        input_tensor = self.preprocessor.preprocess(image_source)
        
        # Ensure correct shape: (1, 3, 224, 224)
        if len(input_tensor.shape) == 3:
            input_tensor = np.expand_dims(input_tensor, 0)
        
        # Run inference using ONNX Runtime
        try:
            outputs = self.session.run(
                [self.output_name],
                {self.input_name: input_tensor}
            )
            logits = outputs[0]  # Output logits
        except Exception as e:
            logger.error(f"ONNX Runtime inference failed: {e}")
            raise RuntimeError(f"Model inference failed: {e}")
        
        # Process outputs
        logits = logits[0]  # Remove batch dimension
        
        # Convert to probabilities (softmax)
        exp_logits = np.exp(logits - np.max(logits))  # Numerical stability
        probs = exp_logits / np.sum(exp_logits)
        
        # Get top prediction
        class_idx = int(np.argmax(probs))
        confidence = float(probs[class_idx])
        
        class_names = self.model_loader.class_names
        if not class_names or len(class_names) == 0:
            class_names = ['Normal', 'Stone']  # Default fallback
        
        class_name = class_names[class_idx] if class_idx < len(class_names) else f"Class_{class_idx}"
        prediction_label = self._get_class_label(class_name)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Build result dictionary
        result = {
            'class': class_name,  # predict.py expects 'class'
            'prediction': prediction_label,
            'confidence': confidence,
            'severity': prediction_label,  # Use prediction_label as severity for binary
            'class_index': class_idx,
            'processing_time': round(processing_time, 3),
            'engine': 'ONNX Runtime (CPU)',
        }
        
        # Add all probabilities if requested - as dictionary mapping class names to probabilities
        if return_all_probs:
            result['all_probabilities'] = {name: float(p) for name, p in zip(class_names, probs)}
        
        # Grad-CAM not supported in ONNX lightweight mode
        if generate_gradcam:
            logger.warning("Grad-CAM visualization is not currently supported in lightweight ONNX mode")
            result['gradcam'] = None
            
        logger.info(
            f"Prediction: {prediction_label} "
            f"(confidence: {confidence:.3f}, "
            f"time: {processing_time:.3f}s)"
        )
        
        return result
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        if self.session is None:
            return {'loaded': False, 'engine': 'ONNX Runtime'}
        
        return {
            'loaded': True,
            'engine': 'ONNX Runtime (CPU)',
            'classes': self.model_loader.class_names,
            'num_classes': self.model_loader.num_classes,
            **self.model_loader.get_model_info()
        }


# Global singleton instance
_inference_service: Optional[InferenceService] = None


def get_inference_service() -> InferenceService:
    """Get or create the global InferenceService singleton."""
    global _inference_service
    if _inference_service is None:
        _inference_service = InferenceService()
    return _inference_service


def initialize_inference_service(
    model_path: str,
    model_name: str = 'resnet50',
    device: Optional[str] = None
) -> InferenceService:
    """Initialize the global inference service with a model."""
    global _inference_service
    if _inference_service is None:
        _inference_service = InferenceService()
    
    _inference_service.load_model(model_path, model_name, device)
    return _inference_service
