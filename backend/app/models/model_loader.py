"""
Kidney Ultrasound Classification - ONNX Model Loader
Lightweight inference using ONNX Runtime (CPU-only, no PyTorch needed).
Singleton pattern for loading and caching models.
"""

import os
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any

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
        self._class_names: List[str] = ['Normal', 'Stone']
        self._model_path: Optional[str] = None
        self._initialized = True
        
        logger.info("ModelLoader singleton initialized (ONNX Runtime - CPU optimized)")
    
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
        Gracefully fails if PyTorch is not installed.
        """
        try:
            # Check if PyTorch is available
            try:
                import torch
                import torchvision.models as models
            except ImportError:
                logger.error("❌ PyTorch is not installed!")
                logger.error(f"Cannot convert {pth_path} to ONNX format.")
                logger.error("")
                logger.error("SOLUTION OPTIONS:")
                logger.error("  1. Pre-convert model locally: pip install torch torchvision")
                logger.error("     Then upload .onnx file to GitHub releases")
                logger.error("  2. Download pre-converted .onnx model from GitHub releases")
                logger.error("  3. Add torch to requirements.txt temporarily during build")
                logger.error("")
                raise RuntimeError(
                    f"Cannot load {pth_path}: PyTorch not installed. "
                    "Either provide a .onnx file or add torch to requirements.txt for conversion."
                )
            
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
            
            # Create dummy input
            dummy_input = torch.randn(1, 3, 224, 224, device=device)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(onnx_path), exist_ok=True)
            
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
        model_name: Optional[str] = None,
        device: str = 'cpu',
        force_reload: bool = False
    ) -> rt.InferenceSession:
        """
        Load an ONNX model using ONNX Runtime.
        Automatically converts .pth to .onnx if needed.
        """
        
        # Skip if already loaded with same path
        if self._session is not None and self._model_path == model_path and not force_reload:
            return self._session
        
        with self._lock:
            # Double-check after acquiring lock
            if self._session is not None and self._model_path == model_path and not force_reload:
                return self._session
            
            # Path handling
            path = Path(model_path)
            if not path.exists():
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            # Automatic .pth to .onnx conversion
            if path.suffix == '.pth':
                onnx_path = path.with_suffix('.onnx')
                if not onnx_path.exists():
                    self._convert_pth_to_onnx(str(path), str(onnx_path))
                path = onnx_path
            
            # Load session
            logger.info(f"Loading ONNX model: {path}")
            providers = ['CPUExecutionProvider']
            self._session = rt.InferenceSession(
                str(path),
                providers=providers,
                sess_options=self._get_session_options()
            )
            
            # Load class names
            self._load_class_names(path)
            self._model_path = str(model_path)
            
            return self._session
    
    def _get_session_options(self) -> rt.SessionOptions:
        """Get optimized ONNX Runtime session options."""
        so = rt.SessionOptions()
        so.log_severity_level = 3
        so.inter_op_num_threads = 1
        so.intra_op_num_threads = 1  # Safe default for shared CPU environments
        return so
    
    def _load_class_names(self, model_path: Path) -> None:
        """Load class names from JSON or use defaults."""
        class_names_path = model_path.parent / 'class_names.json'
        if class_names_path.exists():
            try:
                with open(class_names_path, 'r') as f:
                    data = json.load(f)
                    self._class_names = data.get('classes', data.get('class_names', ['Normal', 'Stone']))
                    return
            except Exception:
                pass
        self._class_names = ['Normal', 'Stone']
    
    def unload_model(self):
        """Unload the model and free memory."""
        with self._lock:
            if self._session is not None:
                del self._session
                self._session = None
            self._model_path = None
            self._class_names = ['Normal', 'Stone']
            logger.info("Model unloaded")

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            'loaded': self.is_loaded,
            'model_path': self._model_path,
            'device': 'cpu',
            'num_classes': self.num_classes,
            'class_names': self._class_names,
            'engine': 'ONNX Runtime (CPU-optimized)',
        }


# Global instance getter
_model_loader = None


def get_model_loader() -> ModelLoader:
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader()
    return _model_loader
