"""
Kidney Ultrasound Classification - Model Loader
Singleton pattern for loading and caching models.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
import json
import threading
from loguru import logger

if TYPE_CHECKING:
    import torch
    import torch.nn as nn


class ModelLoader:
    """
    Singleton class for loading and caching trained models.
    Ensures model is loaded only once and shared across requests.
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
        
        self._model: Optional[Any] = None  # Optional[nn.Module]
        self._class_names: List[str] = []
        self._device: Optional[Any] = None  # torch.device, initialized on first use
        self._model_path: Optional[str] = None
        self._initialized = True
        
        logger.info("ModelLoader singleton initialized")
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None
    
    @property
    def model(self) -> Optional[nn.Module]:
        """Get the loaded model."""
        return self._model
    
    @property
    def class_names(self) -> List[str]:
        """Get class names."""
        return self._class_names
    
    @property
    def num_classes(self) -> int:
        """Get number of classes."""
        return len(self._class_names)
    
    @property
    def device(self) -> Any:  # torch.device
        """Get the device model is on."""
        if self._device is None:
            import torch
            self._device = torch.device('cpu')
        return self._device
    
    def _create_model(
        self,
        model_name: str,
        num_classes: int
    ) -> Any:  # nn.Module
        """
        Create model architecture.
        
        Args:
            model_name: 'resnet50' or 'densenet121'
            num_classes: Number of output classes
        
        Returns:
            Model with correct architecture
        """
        import torch
        import torch.nn as nn
        import torchvision.models as models
        
        if model_name == 'resnet50':
            model = models.resnet50(weights=None)
            num_features = model.fc.in_features
            model.fc = nn.Sequential(
                nn.Dropout(0.5),
                nn.Linear(num_features, num_classes)
            )
        elif model_name == 'densenet121':
            model = models.densenet121(weights=None)
            num_features = model.classifier.in_features
            model.classifier = nn.Sequential(
                nn.Dropout(0.5),
                nn.Linear(num_features, num_classes)
            )
        else:
            raise ValueError(f"Unknown model architecture: {model_name}")
        
        return model
    
    def load_model(
        self,
        model_path: str,
        model_name: str = 'resnet50',
        device: Optional[str] = None,
        force_reload: bool = False
    ) -> Any:  # nn.Module:
        """
        Load a trained model from checkpoint.
        
        Args:
            model_path: Path to model checkpoint (.pth file)
            model_name: Model architecture ('resnet50' or 'densenet121')
            device: Device to load model on ('cuda', 'cpu', or None for auto)
            force_reload: Force reload even if model is already loaded
        
        Returns:
            Loaded model in eval mode
        """
        import torch
        
        # Skip if already loaded with same path
        if self._model is not None and self._model_path == model_path and not force_reload:
            logger.info("Model already loaded, returning cached model")
            return self._model
        
        with self._lock:
            # Double-check after acquiring lock
            if self._model is not None and self._model_path == model_path and not force_reload:
                return self._model
            
            # Determine device
            if device is None:
                self._device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            else:
                self._device = torch.device(device)
            
            logger.info(f"Loading model from: {model_path}")
            logger.info(f"Using device: {self._device}")
            
            # Load checkpoint
            model_path = Path(model_path)
            if not model_path.exists():
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            # weights_only=False needed for PyTorch 2.6+ (our checkpoint includes numpy arrays)
            checkpoint = torch.load(model_path, map_location=self._device, weights_only=False)
            
            # Get class names
            if 'class_names' in checkpoint:
                self._class_names = checkpoint['class_names']
            else:
                # Try loading from separate file
                class_names_path = model_path.parent / 'class_names.json'
                if class_names_path.exists():
                    with open(class_names_path, 'r') as f:
                        data = json.load(f)
                        self._class_names = data.get('classes', [])
                else:
                    logger.warning("Class names not found, using generic names")
                    # Try to infer from model output size
                    state_dict = checkpoint.get('model_state_dict', checkpoint)
                    for key in state_dict:
                        if 'fc' in key and 'weight' in key:
                            num_classes = state_dict[key].shape[0]
                            self._class_names = [f'Class_{i}' for i in range(num_classes)]
                            break
            
            num_classes = len(self._class_names)
            logger.info(f"Number of classes: {num_classes}")
            logger.info(f"Class names: {self._class_names}")
            
            # Create model architecture
            self._model = self._create_model(model_name, num_classes)
            
            # Load weights
            state_dict = checkpoint.get('model_state_dict', checkpoint)
            self._model.load_state_dict(state_dict)
            
            # Move to device and set to eval mode
            self._model = self._model.to(self._device)
            self._model.eval()
            
            # Store path for caching
            self._model_path = str(model_path)
            
            # Clear CUDA cache
            if self._device.type == 'cuda':
                torch.cuda.empty_cache()
            
            logger.info("Model loaded successfully")
            
            return self._model
    
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
        if self._model is None:
            return {'loaded': False}
        
        return {
            'loaded': True,
            'model_path': self._model_path,
            'device': str(self._device),
            'num_classes': self.num_classes,
            'class_names': self._class_names,
        }


# Global singleton instance
_model_loader: Optional[ModelLoader] = None


def get_model_loader() -> ModelLoader:
    """Get the global ModelLoader singleton instance."""
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader()
    return _model_loader
