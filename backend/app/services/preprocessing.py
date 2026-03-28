"""
Kidney Ultrasound Classification - Image Preprocessing Service
OpenCV-based preprocessing for inference.
"""

import io
from pathlib import Path
from typing import Tuple, Union, Optional, TYPE_CHECKING, Any

import cv2
import numpy as np
from PIL import Image
from loguru import logger


class ImagePreprocessor:
    """
    Image preprocessing service for kidney ultrasound images.
    Uses OpenCV for efficient image processing.
    """
    
    # ImageNet normalization values
    IMAGENET_MEAN = [0.485, 0.456, 0.406]
    IMAGENET_STD = [0.229, 0.224, 0.225]
    
    def __init__(
        self,
        image_size: int = 224,
        use_clahe: bool = True,
        clahe_clip_limit: float = 2.0,
        clahe_grid_size: Tuple[int, int] = (8, 8)
    ):
        """
        Initialize the preprocessor.
        
        Args:
            image_size: Target image size (square)
            use_clahe: Whether to apply CLAHE enhancement
            clahe_clip_limit: CLAHE clip limit
            clahe_grid_size: CLAHE grid size
        """
        self.image_size = image_size
        self.use_clahe = use_clahe
        self.clahe_clip_limit = clahe_clip_limit
        self.clahe_grid_size = clahe_grid_size
        
        # Create CLAHE object
        if use_clahe:
            self.clahe = cv2.createCLAHE(
                clipLimit=clahe_clip_limit,
                tileGridSize=clahe_grid_size
            )
        
        logger.info(f"ImagePreprocessor initialized (size={image_size}, clahe={use_clahe})")
    
    def load_image(
        self,
        source: Union[str, Path, bytes, np.ndarray, Image.Image]
    ) -> np.ndarray:
        """
        Load image from various sources.
        
        Args:
            source: Image path, bytes, numpy array, or PIL Image
        
        Returns:
            Image as BGR numpy array (OpenCV format)
        """
        if isinstance(source, (str, Path)):
            image = cv2.imread(str(source))
            if image is None:
                raise ValueError(f"Failed to load image from: {source}")
        
        elif isinstance(source, bytes):
            nparr = np.frombuffer(source, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("Failed to decode image from bytes")
        
        elif isinstance(source, np.ndarray):
            if len(source.shape) == 2:
                image = cv2.cvtColor(source, cv2.COLOR_GRAY2BGR)
            elif source.shape[2] == 4:
                image = cv2.cvtColor(source, cv2.COLOR_RGBA2BGR)
            elif source.shape[2] == 3:
                image = source.copy()
            else:
                raise ValueError(f"Unexpected image shape: {source.shape}")
        
        elif isinstance(source, Image.Image):
            image = np.array(source.convert('RGB'))
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        else:
            raise TypeError(f"Unsupported image source type: {type(source)}")
        
        return image
    
    def apply_clahe(self, image: np.ndarray) -> np.ndarray:
        """Apply CLAHE enhancement."""
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l = self.clahe.apply(l)
        lab = cv2.merge([l, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    def preprocess(
        self,
        source: Union[str, Path, bytes, np.ndarray, Image.Image],
        return_original: bool = False
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        Preprocess image for model inference.
        Returns a normalized numpy array (C, H, W) for ONNX Runtime.
        """
        # Load image
        image = self.load_image(source)
        
        # Apply CLAHE if enabled
        if self.use_clahe:
            image = self.apply_clahe(image)
        
        # Resize
        image = cv2.resize(image, (self.image_size, self.image_size))
        
        # Keep original for visualization if needed
        original = image.copy() if return_original else None
        
        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Convert to float32 and normalize to [0, 1]
        image = image.astype(np.float32) / 255.0
        
        # Normalize with ImageNet values: (img - mean) / std
        for i in range(3):
            image[:, :, i] = (image[:, :, i] - self.IMAGENET_MEAN[i]) / self.IMAGENET_STD[i]
        
        # Transpose (H, W, C) -> (C, H, W) for ONNX Runtime
        tensor = image.transpose(2, 0, 1)
        
        if return_original:
            return tensor, original
        return tensor
    
    def validate_image(
        self,
        source: Union[str, Path, bytes, np.ndarray, Image.Image]
    ) -> Tuple[bool, Optional[str]]:
        """Validate if image can be processed."""
        try:
            image = self.load_image(source)
            if image.shape[0] < 10 or image.shape[1] < 10:
                return False, "Image is too small (minimum 10x10 pixels)"
            return True, None
        except Exception as e:
            return False, str(e)


# Global instance
_preprocessor: Optional[ImagePreprocessor] = None


def get_preprocessor(
    image_size: int = 224,
    use_clahe: bool = True
) -> ImagePreprocessor:
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = ImagePreprocessor(image_size=image_size, use_clahe=use_clahe)
    return _preprocessor
