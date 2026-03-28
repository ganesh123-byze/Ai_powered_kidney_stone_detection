"""
Kidney Ultrasound Classification - Training Transforms
Data augmentation and preprocessing transforms for training and validation.
"""

import torch
from torchvision import transforms
from PIL import Image
import numpy as np
import cv2
from typing import Tuple, Optional


class GaussianNoise:
    """Add Gaussian noise to image for data augmentation."""
    
    def __init__(self, mean: float = 0.0, std: float = 0.05):
        self.mean = mean
        self.std = std
    
    def __call__(self, tensor: torch.Tensor) -> torch.Tensor:
        noise = torch.randn(tensor.size()) * self.std + self.mean
        return torch.clamp(tensor + noise, 0.0, 1.0)


class CLAHETransform:
    """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) for ultrasound enhancement."""
    
    def __init__(self, clip_limit: float = 2.0, tile_grid_size: Tuple[int, int] = (8, 8)):
        self.clip_limit = clip_limit
        self.tile_grid_size = tile_grid_size
    
    def __call__(self, img: Image.Image) -> Image.Image:
        img_array = np.array(img)
        
        if len(img_array.shape) == 3:
            lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=self.clip_limit, tileGridSize=self.tile_grid_size)
            l = clahe.apply(l)
            lab = cv2.merge([l, a, b])
            img_array = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        else:
            clahe = cv2.createCLAHE(clipLimit=self.clip_limit, tileGridSize=self.tile_grid_size)
            img_array = clahe.apply(img_array)
        
        return Image.fromarray(img_array)


class SpeckleNoiseReduction:
    """Reduce speckle noise common in ultrasound images."""
    
    def __init__(self, kernel_size: int = 5):
        self.kernel_size = kernel_size
    
    def __call__(self, img: Image.Image) -> Image.Image:
        img_array = np.array(img)
        
        if len(img_array.shape) == 3:
            denoised = cv2.bilateralFilter(img_array, self.kernel_size, 75, 75)
        else:
            denoised = cv2.bilateralFilter(img_array, self.kernel_size, 75, 75)
        
        return Image.fromarray(denoised)


def get_train_transforms(
    image_size: int = 224,
    use_clahe: bool = True,
    use_noise_reduction: bool = False,
    augmentation_strength: str = "medium"
) -> transforms.Compose:
    """
    Get training transforms with data augmentation.
    
    Args:
        image_size: Target image size (default 224 for ResNet/DenseNet)
        use_clahe: Whether to apply CLAHE enhancement
        use_noise_reduction: Whether to apply speckle noise reduction
        augmentation_strength: 'light', 'medium', or 'heavy'
    
    Returns:
        Composed transforms for training
    """
    transform_list = []
    
    # Pre-processing for ultrasound images
    if use_noise_reduction:
        transform_list.append(SpeckleNoiseReduction(kernel_size=5))
    
    if use_clahe:
        transform_list.append(CLAHETransform(clip_limit=2.0))
    
    # Resize
    transform_list.append(transforms.Resize((image_size, image_size)))
    
    # Data augmentation based on strength
    if augmentation_strength == "light":
        transform_list.extend([
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=10),
        ])
    elif augmentation_strength == "medium":
        transform_list.extend([
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.3),
            transforms.RandomRotation(degrees=15),
            transforms.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.9, 1.1)),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
        ])
    elif augmentation_strength == "heavy":
        transform_list.extend([
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.5),
            transforms.RandomRotation(degrees=30),
            transforms.RandomAffine(degrees=0, translate=(0.15, 0.15), scale=(0.8, 1.2)),
            transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
            transforms.RandomPerspective(distortion_scale=0.2, p=0.3),
        ])
    
    # Convert to tensor and normalize
    transform_list.extend([
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],  # ImageNet normalization
            std=[0.229, 0.224, 0.225]
        ),
    ])
    
    # Add Gaussian noise for medium and heavy augmentation
    if augmentation_strength in ["medium", "heavy"]:
        transform_list.append(GaussianNoise(mean=0.0, std=0.02))
    
    return transforms.Compose(transform_list)


def get_val_transforms(
    image_size: int = 224,
    use_clahe: bool = True,
    use_noise_reduction: bool = False
) -> transforms.Compose:
    """
    Get validation/test transforms (no augmentation).
    
    Args:
        image_size: Target image size
        use_clahe: Whether to apply CLAHE enhancement
        use_noise_reduction: Whether to apply speckle noise reduction
    
    Returns:
        Composed transforms for validation/testing
    """
    transform_list = []
    
    if use_noise_reduction:
        transform_list.append(SpeckleNoiseReduction(kernel_size=5))
    
    if use_clahe:
        transform_list.append(CLAHETransform(clip_limit=2.0))
    
    transform_list.extend([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
    ])
    
    return transforms.Compose(transform_list)


def get_inference_transforms(image_size: int = 224) -> transforms.Compose:
    """
    Get inference transforms for production use.
    Minimal preprocessing for fast inference.
    
    Args:
        image_size: Target image size
    
    Returns:
        Composed transforms for inference
    """
    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
    ])


# Inverse normalization for visualization
def denormalize(tensor: torch.Tensor) -> torch.Tensor:
    """
    Denormalize a tensor for visualization.
    
    Args:
        tensor: Normalized tensor
    
    Returns:
        Denormalized tensor
    """
    mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
    
    if tensor.device.type == 'cuda':
        mean = mean.to(tensor.device)
        std = std.to(tensor.device)
    
    return torch.clamp(tensor * std + mean, 0, 1)
