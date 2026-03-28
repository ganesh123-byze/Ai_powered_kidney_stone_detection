"""
Kidney Ultrasound Classification - Inference Service
Model inference with Grad-CAM support.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, TYPE_CHECKING
import json

import numpy as np
import cv2
from PIL import Image
from loguru import logger

if TYPE_CHECKING:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

from app.models.model_loader import get_model_loader, ModelLoader
from app.services.preprocessing import get_preprocessor, ImagePreprocessor


class GradCAM:
    """
    Gradient-weighted Class Activation Mapping for model interpretability.
    """
    
    def __init__(self, model: Any, target_layer: Any):  # nn.Module, nn.Module
        """
        Initialize Grad-CAM.
        
        Args:
            model: The model to visualize
            target_layer: The layer to generate CAM from (usually last conv layer)
        """
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        # Register hooks
        self._register_hooks()
    
    def _register_hooks(self):
        """Register forward and backward hooks."""
        def forward_hook(module, input, output):
            self.activations = output.detach()
        
        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()
        
        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)
    
    def generate(
        self,
        input_tensor: Any,  # torch.Tensor
        target_class: Optional[int] = None
    ) -> Tuple[np.ndarray, int, float]:
        """
        Generate Grad-CAM heatmap.
        
        Args:
            input_tensor: Preprocessed input tensor
            target_class: Class to generate CAM for (None = predicted class)
        
        Returns:
            heatmap, predicted_class, confidence
        """
        import torch.nn.functional as F
        
        self.model.eval()
        
        # Forward pass
        output = self.model(input_tensor)
        
        # Get predicted class if not specified
        if target_class is None:
            target_class = output.argmax(dim=1).item()
        
        # Get confidence
        probs = F.softmax(output, dim=1)
        confidence = probs[0, target_class].item()
        
        # Backward pass
        self.model.zero_grad()
        output[0, target_class].backward()
        
        # Generate CAM
        gradients = self.gradients[0]  # (C, H, W)
        activations = self.activations[0]  # (C, H, W)
        
        # Global average pooling of gradients
        weights = gradients.mean(dim=(1, 2), keepdim=True)  # (C, 1, 1)
        
        # Weighted combination of activations
        cam = (weights * activations).sum(dim=0)  # (H, W)
        
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
