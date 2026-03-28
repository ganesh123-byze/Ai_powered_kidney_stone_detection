"""
Kidney Ultrasound Classification - Inference Service
Lightweight CPU-only inference using ONNX Runtime (no PyTorch needed).
Binary classification: Normal vs Stone (kidney stone detection).
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
import json

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
    
    def load_model(self, model_path: str):
        """
        Load ONNX model.
        
        Args:
            model_path: Path to model (.onnx or .pth file)
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
        
        Args:
            class_name: Predicted class name
        
        Returns:
            User-friendly label
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
    ) -> Dict[str, Any]:
        """
        Run inference on an image using ONNX Runtime.
        
        Args:
            image_source: Image source (path, bytes, array, or PIL Image)
            return_all_probs: Return probabilities for all classes
        
        Returns:
            Dictionary with prediction results:
            {
                'prediction': 'Normal' or 'Detected',
                'confidence': 0.0-1.0,
                'class_index': 0 or 1,
                'all_probabilities': [prob_class0, prob_class1],
                'processing_time': seconds,
                'engine': 'ONNX Runtime'
            }
        """
        import time
        
        if self.session is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        start_time = time.time()
        
        # Validate image
        is_valid, error_msg = self.preprocessor.validate_image(image_source)
        if not is_valid:
            raise ValueError(f"Invalid image: {error_msg}")
        
        # Preprocess image to tensor
        input_tensor = self.preprocessor.preprocess(image_source)
        
        # Convert to float32 if needed
        if input_tensor.dtype != np.float32:
            input_tensor = input_tensor.astype(np.float32)
        
        # Ensure correct shape: (1, 3, 224, 224)
        if len(input_tensor.shape) == 3:
            input_tensor = np.expand_dims(input_tensor, 0)
        
        logger.debug(f"Input tensor shape: {input_tensor.shape}, dtype: {input_tensor.dtype}")
        
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
            'prediction': prediction_label,
            'predicted_class': class_name,
            'class_index': class_idx,
            'confidence': confidence,
            'processing_time': round(processing_time, 3),
            'engine': 'ONNX Runtime (CPU)',
        }
        
        # Add all probabilities if requested
        if return_all_probs:
            result['all_probabilities'] = [float(p) for p in probs]
            result['classes'] = class_names
        
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
        
        # ReLU
        cam = F.relu(cam)
        
        # Normalize
        cam = cam - cam.min()
        if cam.max() > 0:
            cam = cam / cam.max()
        
        # Convert to numpy and resize
        cam = cam.cpu().numpy()
        
        return cam, target_class, confidence


class InferenceService:
    """
    Service for running model inference on kidney ultrasound images.
    Binary classification: Normal vs Stone (kidney stone detection).
    """
    
    # Severity/status mapping for binary stone detection
    # Normal = no stone detected, Stone = stone detected (requires attention)
    SEVERITY_MAPPING = {
        'normal': 'Normal',
        'healthy': 'Normal',
        'stone': 'Detected',
    }
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        model_name: str = 'resnet50',
        device: Optional[str] = None,
        enable_gradcam: bool = True
    ):
        """
        Initialize the inference service.
        
        Args:
            model_path: Path to model checkpoint
            model_name: Model architecture
            device: Device to use
            enable_gradcam: Whether to enable Grad-CAM generation
        """
        self.model_loader = get_model_loader()
        self.preprocessor = get_preprocessor()
        self.model_name = model_name
        self.enable_gradcam = enable_gradcam
        self.gradcam: Optional[GradCAM] = None
        
        # Load model if path provided
        if model_path:
            self.load_model(model_path, model_name, device)
    
    def load_model(
        self,
        model_path: str,
        model_name: str = 'resnet50',
        device: Optional[str] = None
    ):
        """Load the model."""
        self.model_loader.load_model(model_path, model_name, device)
        self.model_name = model_name
        
        # Setup Grad-CAM
        if self.enable_gradcam:
            self._setup_gradcam()
    
    def _setup_gradcam(self):
        """Setup Grad-CAM for the loaded model."""
        model = self.model_loader.model
        if model is None:
            return
        
        # Get target layer based on architecture
        if self.model_name == 'resnet50':
            target_layer = model.layer4[-1]
        elif self.model_name == 'densenet121':
            target_layer = model.features.denseblock4
        else:
            logger.warning(f"Unknown model for Grad-CAM: {self.model_name}")
            return
        
        self.gradcam = GradCAM(model, target_layer)
        logger.info("Grad-CAM initialized")
    
    def _get_severity(self, class_name: str) -> str:
        """
        Get status/severity based on class name.
        
        For binary stone detection:
        - Normal -> 'Normal' (no stone)
        - Stone -> 'Detected' (stone present, requires medical attention)
        
        Args:
            class_name: Predicted class name
        
        Returns:
            Status string: 'Normal' or 'Detected'
        """
        class_lower = class_name.lower().replace(' ', '_')
        
        for key, severity in self.SEVERITY_MAPPING.items():
            if key in class_lower:
                return severity
        
        # Default for binary classification
        if 'normal' in class_lower or 'healthy' in class_lower:
            return 'Normal'
        elif 'stone' in class_lower:
            return 'Detected'
        
        return 'Unknown'
    
    def predict(
        self,
        image_source: Union[str, Path, bytes, np.ndarray, Image.Image],
        return_all_probs: bool = False,
        generate_gradcam: bool = False
    ) -> Dict[str, Any]:
        """
        Run inference on an image.
        
        Args:
            image_source: Image source (path, bytes, array, or PIL Image)
            return_all_probs: Return probabilities for all classes
            generate_gradcam: Generate Grad-CAM heatmap
        
        Returns:
            Dictionary with prediction results
        """
        import torch
        
        if not self.model_loader.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        model = self.model_loader.model
        device = self.model_loader.device
        class_names = self.model_loader.class_names
        
        # Validate image
        is_valid, error_msg = self.preprocessor.validate_image(image_source)
        if not is_valid:
            raise ValueError(f"Invalid image: {error_msg}")
        
        # Preprocess image
        if generate_gradcam and self.gradcam:
            tensor, original_image = self.preprocessor.preprocess(
                image_source, 
                return_original=True
            )
        else:
            tensor = self.preprocessor.preprocess(image_source)
            original_image = None
        
        tensor = tensor.to(device)
        
        # Generate Grad-CAM if requested
        gradcam_result = None
        if generate_gradcam and self.gradcam:
            # Need gradients for Grad-CAM, so temporarily enable
            with torch.enable_grad():
                tensor_grad = tensor.clone().requires_grad_(True)
                cam, pred_class, confidence = self.gradcam.generate(tensor_grad)
            
            # Create overlay
            if original_image is not None:
                cam_resized = cv2.resize(cam, (original_image.shape[1], original_image.shape[0]))
                heatmap = cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET)
                overlay = cv2.addWeighted(original_image, 0.5, heatmap, 0.5, 0)
                gradcam_result = {
                    'heatmap': cam_resized.tolist(),
                    'overlay': overlay.tolist()
                }
        
        # Run inference
        import torch.nn.functional as F
        
        model.eval()
        with torch.no_grad():
            outputs = model(tensor)
            probabilities = F.softmax(outputs, dim=1)
        
        # Get predictions
        probs = probabilities[0].cpu().numpy()
        pred_idx = int(np.argmax(probs))
        confidence = float(probs[pred_idx])
        pred_class = class_names[pred_idx]
        severity = self._get_severity(pred_class)
        
        # Build result
        result = {
            'class': pred_class,
            'confidence': round(confidence, 4),
            'severity': severity,
            'class_index': pred_idx
        }
        
        if return_all_probs:
            result['all_probabilities'] = {
                name: round(float(prob), 4) 
                for name, prob in zip(class_names, probs)
            }
        
        if gradcam_result:
            result['gradcam'] = gradcam_result
        
        return result
    
    def batch_predict(
        self,
        image_sources: List[Union[str, Path, bytes]],
        batch_size: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Run inference on multiple images.
        
        Args:
            image_sources: List of image sources
            batch_size: Batch size for inference
        
        Returns:
            List of prediction results
        """
        results = []
        
        for i in range(0, len(image_sources), batch_size):
            batch_sources = image_sources[i:i + batch_size]
            
            for source in batch_sources:
                try:
                    result = self.predict(source)
                    results.append(result)
                except Exception as e:
                    results.append({
                        'error': str(e),
                        'class': None,
                        'confidence': 0.0,
                        'severity': 'Error'
                    })
            
            # Clear cache after each batch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return self.model_loader.get_model_info()


# Global inference service instance
_inference_service: Optional[InferenceService] = None


def get_inference_service() -> InferenceService:
    """Get or create the global inference service instance."""
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
    _inference_service = InferenceService(
        model_path=model_path,
        model_name=model_name,
        device=device
    )
    return _inference_service
