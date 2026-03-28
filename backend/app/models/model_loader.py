"""
Kidney Ultrasound Classification - ONNX Model Loader
Lightweight inference using ONNX Runtime (CPU-only, no PyTorch needed).
Singleton pattern for loading and caching models.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import threading
import numpy as np
from loguru import logger

import onnxruntime as rt


class ModelLoader:
    """
    Singleton class for loading and caching ONNX models.
    Ensures model is loaded only once and shared across requests.
    CPU-only inference (perfect for Render Free Tier).
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._session: Optional[rt.InferenceSession] = None
        self._class_names: List[str] = []
        self._model_path: Optional[str] = None
        self._initialized = True
        
        logger.info("ModelLoader singleton initialized (ONNX Runtime - CPU only)")
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._session is not None
    
    @property
    def session(self) -> Optional[rt.InferenceSession]:
        """Get the loaded ONNX session."""
        return self._session
    
    @property
    def class_names(self) -> List[str]:
        """Get class names."""
        return self._class_names
    
    @property
    def num_classes(self) -> int:
        """Get number of classes."""
        return len(self._class_names)
    
    def _convert_pth_to_onnx(self, pth_path: str, onnx_path: str) -> None:
        """
        Convert PyTorch .pth model to ONNX format.
        Only called on first deployment if .onnx doesn't exist.
        """
        try:
            logger.info(f"Converting PyTorch model {pth_path} to ONNX...")
            
            import torch
            import torch.onnx
            from PIL import Image
            
            device = torch.device('cpu')
            
            # Load PyTorch checkpoint
            checkpoint = torch.load(pth_path, map_location=device, weights_only=False)
            
            # Determine model architecture from checkpoint
            state_dict = checkpoint.get('model_state_dict', checkpoint)
            
            # Infer architecture from state dict
            model_name = 'resnet50'  # default
            if 'features.0.weight' in state_dict:
                model_name = 'densenet121'
            
            # Infer number of classes
            num_classes = 2  # default
            for key in state_dict:
                if 'fc.1.weight' in key or 'classifier.1.weight' in key:
                    num_classes = state_dict[key].shape[0]
                    break
            
            # Create and load model
            import torchvision.models as models
            
            if model_name == 'resnet50':
                model = models.resnet50(weights=None)
                model.fc = torch.nn.Sequential(
                    torch.nn.Dropout(0.5),
                    torch.nn.Linear(2048, num_classes)
                )
            else:
                model = models.densenet121(weights=None)
                model.classifier = torch.nn.Sequential(
                    torch.nn.Dropout(0.5),
                    torch.nn.Linear(1024, num_classes)
                )
            
            model.load_state_dict(state_dict)
            model.eval()
            model.to(device)
            
            # Create dummy input
            dummy_input = torch.randn(1, 3, 224, 224, device=device)
            
            # Export to ONNX
            torch.onnx.export(
                model,
                dummy_input,
                onnx_path,
                input_names=['input'],
                output_names=['output'],
                opset_version=12,
                do_constant_folding=True,
            )
            
            logger.info(f"✓ Model converted successfully to {onnx_path}")
            
        except Exception as e:
            logger.error(f"Failed to convert PyTorch to ONNX: {e}")
            raise
    
    def load_model(
        self,
        model_path: str,
        device: str = 'cpu',
        force_reload: bool = False
    ) -> rt.InferenceSession:
        """
        Load an ONNX model using ONNX Runtime.
        Automatically converts .pth to .onnx if needed.
        
        Args:
            model_path: Path to model (.onnx or .pth file)
            device: Device to use ('cpu' only supported)
            force_reload: Force reload even if model is already loaded
        
        Returns:
            ONNX Runtime InferenceSession
        """
        
        # Skip if already loaded with same path
        if self._session is not None and self._model_path == model_path and not force_reload:
            logger.info("Model already loaded, returning cached session")
            return self._session
        
        with self._lock:
            # Double-check after acquiring lock
            if self._session is not None and self._model_path == model_path and not force_reload:
                return self._session
            
            model_path = Path(model_path)
            
            # Check if model exists
            if not model_path.exists():
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            # If .pth file, convert to .onnx
            if model_path.suffix == '.pth':
                onnx_path = model_path.parent / model_path.stem / '.onnx'
                if not onnx_path.exists():
                    logger.info(f"ONNX model not found, converting from PyTorch...")
                    self._convert_pth_to_onnx(str(model_path), str(onnx_path))
                model_path = onnx_path
            
            logger.info(f"Loading ONNX model from: {model_path}")
            
            # Create ONNX Runtime session (CPU only)
            providers = ['CPUExecutionProvider']
            self._session = rt.InferenceSession(
                str(model_path),
                providers=providers,
                sess_options=self._get_session_options()
            )
            
            # Load class names
            self._load_class_names(model_path)
            
            logger.info(f"✓ Model loaded successfully")
            logger.info(f"  Classes: {self._class_names}")
            logger.info(f"  CPU-only inference (ONNX Runtime)")
            
            # Store path for caching
            self._model_path = str(model_path)
            
            return self._session
    
    def _get_session_options(self) -> rt.SessionOptions:
        """Get optimized ONNX Runtime session options."""
        so = rt.SessionOptions()
        so.log_severity_level = 3  # Only errors
        so.inter_op_num_threads = 1  # Single thread for consistency
        so.intra_op_num_threads = 2  # Use 2 cores max (Render Free Tier limit)
        return so
    
    def _load_class_names(self, model_path: Path) -> None:
        """Load class names from JSON file or use defaults."""
        # Try loading from class_names.json in same directory
        class_names_path = model_path.parent / 'class_names.json'
        
        if class_names_path.exists():
            try:
                with open(class_names_path, 'r') as f:
                    data = json.load(f)
                    self._class_names = data.get('classes', data.get('class_names', []))
                    logger.info(f"Loaded {len(self._class_names)} classes from {class_names_path}")
                    return
            except Exception as e:
                logger.warning(f"Failed to load class names from JSON: {e}")
        
        # Default class names if not found
        self._class_names = ['Normal', 'Stone']
        logger.info(f"Using default class names: {self._class_names}")
    
    def unload_model(self):
        """Unload the model and free memory."""
        with self._lock:
            if self._session is not None:
                del self._session
                self._session = None
                self._model_path = None
                self._class_names = []
                
                logger.info("Model unloaded and memory freed")
    
    def unload_model(self):
        """Unload the model and free memory."""
        with self._lock:
            if self._model is not None:
                del self._model
                self._model = None
                self._model_path = None
                self._class_names = []
                
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except ImportError:
                    pass
                
                logger.info("Model unloaded and memory freed")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        if self._session is None:
            return {'loaded': False, 'engine': 'ONNX Runtime'}
        
        return {
            'loaded': True,
            'model_path': self._model_path,
            'device': 'cpu',
            'num_classes': self.num_classes,
            'class_names': self._class_names,
            'engine': 'ONNX Runtime (CPU-only)',
        }


# Global singleton instance
_model_loader: Optional[ModelLoader] = None


def get_model_loader() -> ModelLoader:
    """Get the global ModelLoader singleton instance."""
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader()
    return _model_loader
