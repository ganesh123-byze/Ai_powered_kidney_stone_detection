"""
Kidney Ultrasound Classification - Dataset Module
Production-grade PyTorch Dataset with proper train/val/test splits.
FIXES: Deterministic ordering, no data leakage, proper stratified splits.
"""

import os
import sys
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import torch
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler, Subset
from PIL import Image
import numpy as np
from collections import Counter
from loguru import logger


class KidneyUltrasoundDataset(Dataset):
    """
    PyTorch Dataset for kidney ultrasound images.
    
    IMPORTANT: Uses deterministic sorted ordering to prevent data leakage.
    
    Expects folder structure:
        data_dir/
            class_1/
                image1.jpg
                image2.png
            class_2/
                image1.jpg
            ...
    """
    
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    def __init__(
        self,
        data_dir: str,
        transform=None,
        target_transform=None,
        samples: Optional[List[Tuple[Path, int]]] = None,
        class_names: Optional[List[str]] = None
    ):
        """
        Initialize the dataset.
        
        Args:
            data_dir: Root directory containing class folders
            transform: Transforms to apply to images
            target_transform: Transforms to apply to labels
            samples: Pre-computed list of (path, label) tuples (for splits)
            class_names: Pre-computed class names (required if samples provided)
        """
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.target_transform = target_transform
        
        if samples is not None and class_names is not None:
            # Use provided samples (for train/val/test splits)
            self.samples = samples
            self.classes = class_names
            # Ensure mappings exist
            self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}
            self.idx_to_class = {idx: cls for cls, idx in self.class_to_idx.items()}
        else:
            # Auto-detect classes
            self.classes = self._discover_classes()
            # Create mappings before loading samples (required by _load_samples)
            self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}
            self.idx_to_class = {idx: cls for cls, idx in self.class_to_idx.items()}
            # Load samples deterministically
            self.samples = self._load_samples()
        
        logger.info(f"Dataset initialized: {len(self.samples)} samples, {len(self.classes)} classes")
    
    def _discover_classes(self) -> List[str]:
        """Discover class names from folder structure (SORTED for determinism)."""
        classes = []
        for item in sorted(self.data_dir.iterdir()):  # SORTED!
            if item.is_dir() and not item.name.startswith('.'):
                classes.append(item.name)
        
        if not classes:
            raise ValueError(f"No class folders found in {self.data_dir}")
        
        return classes
    
    def _load_samples(self) -> List[Tuple[Path, int]]:
        """Load all image paths and labels with DETERMINISTIC ordering."""
        samples = []
        
        for class_name in self.classes:  # Already sorted
            class_dir = self.data_dir / class_name
            class_idx = self.class_to_idx[class_name]
            
            # CRITICAL: Sort files for deterministic ordering
            for img_path in sorted(class_dir.iterdir()):
                if img_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    samples.append((img_path, class_idx))
        
        if not samples:
            raise ValueError(f"No valid images found in {self.data_dir}")
        
        return samples
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        img_path, label = self.samples[idx]
        
        try:
            image = Image.open(img_path).convert('RGB')
        except Exception as e:
            logger.error(f"Error loading image {img_path}: {e}")
            image = Image.new('RGB', (224, 224), color='gray')
        
        if self.transform:
            image = self.transform(image)
        
        if self.target_transform:
            label = self.target_transform(label)
        
        return image, label
    
    def get_class_distribution(self) -> Dict[str, int]:
        """Get the distribution of samples across classes."""
        labels = [label for _, label in self.samples]
        counts = Counter(labels)
        return {self.idx_to_class[idx]: count for idx, count in counts.items()}
    
    def get_class_weights(self) -> torch.Tensor:
        """Calculate inverse-frequency class weights for imbalanced datasets."""
        labels = [label for _, label in self.samples]
        counts = Counter(labels)
        total = len(labels)
        
        weights = []
        for i in range(len(self.classes)):
            if counts[i] > 0:
                weights.append(total / (len(self.classes) * counts[i]))
            else:
                weights.append(1.0)
        
        return torch.FloatTensor(weights)
    
    def get_sample_weights(self) -> List[float]:
        """Get per-sample weights for WeightedRandomSampler."""
        class_weights = self.get_class_weights()
        return [class_weights[label].item() for _, label in self.samples]


def check_duplicates(samples: List[Tuple[Path, int]]) -> List[Tuple[str, str]]:
    """
    Check for duplicate images using MD5 hash.
    Returns list of duplicate pairs.
    """
    hashes = {}
    duplicates = []
    
    for path, _ in samples:
        try:
            file_hash = hashlib.md5(path.read_bytes()).hexdigest()
            if file_hash in hashes:
                duplicates.append((str(path), str(hashes[file_hash])))
            else:
                hashes[file_hash] = path
        except Exception as e:
            logger.warning(f"Could not hash {path}: {e}")
    
    return duplicates


def create_stratified_splits(
    samples: List[Tuple[Path, int]],
    class_names: List[str],
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42
) -> Tuple[List[Tuple[Path, int]], List[Tuple[Path, int]], List[Tuple[Path, int]]]:
    """
    Create stratified train/val/test splits with NO DATA LEAKAGE.
    
    Args:
        samples: List of (path, label) tuples
        class_names: List of class names
        val_ratio: Fraction for validation
        test_ratio: Fraction for test
        seed: Random seed
    
    Returns:
        train_samples, val_samples, test_samples
    """
    np.random.seed(seed)
    
    # Group by class
    class_to_samples = {i: [] for i in range(len(class_names))}
    for path, label in samples:
        class_to_samples[label].append((path, label))
    
    train_samples = []
    val_samples = []
    test_samples = []
    
    for class_idx, class_samples in class_to_samples.items():
        # Shuffle within class (deterministic due to seed)
        indices = np.arange(len(class_samples))
        np.random.shuffle(indices)
        
        n = len(class_samples)
        n_test = int(n * test_ratio)
        n_val = int(n * val_ratio)
        n_train = n - n_test - n_val
        
        # Split indices
        train_idx = indices[:n_train]
        val_idx = indices[n_train:n_train + n_val]
        test_idx = indices[n_train + n_val:]
        
        train_samples.extend([class_samples[i] for i in train_idx])
        val_samples.extend([class_samples[i] for i in val_idx])
        test_samples.extend([class_samples[i] for i in test_idx])
    
    # Final shuffle (deterministic)
    np.random.shuffle(train_samples)
    np.random.shuffle(val_samples)
    np.random.shuffle(test_samples)
    
    return train_samples, val_samples, test_samples


def verify_no_leakage(
    train_samples: List[Tuple[Path, int]],
    val_samples: List[Tuple[Path, int]],
    test_samples: List[Tuple[Path, int]]
) -> bool:
    """Verify there's no overlap between splits."""
    train_paths = {str(p) for p, _ in train_samples}
    val_paths = {str(p) for p, _ in val_samples}
    test_paths = {str(p) for p, _ in test_samples}
    
    train_val_overlap = train_paths & val_paths
    train_test_overlap = train_paths & test_paths
    val_test_overlap = val_paths & test_paths
    
    if train_val_overlap:
        logger.error(f"LEAKAGE: {len(train_val_overlap)} samples in both train and val!")
        return False
    if train_test_overlap:
        logger.error(f"LEAKAGE: {len(train_test_overlap)} samples in both train and test!")
        return False
    if val_test_overlap:
        logger.error(f"LEAKAGE: {len(val_test_overlap)} samples in both val and test!")
        return False
    
    logger.info("✓ No data leakage detected between splits")
    return True


def create_data_loaders(
    data_dir: str,
    train_transform,
    val_transform,
    batch_size: int = 8,
    val_split: float = 0.15,
    test_split: float = 0.15,
    num_workers: int = 0,  # 0 for Windows compatibility
    use_weighted_sampling: bool = True,
    seed: int = 42,
    pin_memory: bool = True,
    check_for_duplicates: bool = True
) -> Tuple[DataLoader, DataLoader, DataLoader, KidneyUltrasoundDataset]:
    """
    Create train, validation, and test data loaders with proper splitting.
    
    PRODUCTION-GRADE:
    - Deterministic ordering (no leakage)
    - Stratified splits
    - Duplicate detection
    - Leakage verification
    - Windows-compatible (num_workers=0 by default)
    
    Args:
        data_dir: Root directory containing class folders
        train_transform: Transforms for training data
        val_transform: Transforms for validation/test data
        batch_size: Batch size (keep small for low VRAM)
        val_split: Fraction for validation
        test_split: Fraction for test (held-out)
        num_workers: Data loading workers (0 recommended for Windows)
        use_weighted_sampling: Use weighted sampling for class balance
        seed: Random seed for reproducibility
        pin_memory: Pin memory for faster GPU transfer
        check_for_duplicates: Check for duplicate images
    
    Returns:
        train_loader, val_loader, test_loader, full_dataset
    """
    # Set seeds for reproducibility
    np.random.seed(seed)
    torch.manual_seed(seed)
    
    # Create full dataset to get all samples with deterministic ordering
    logger.info(f"Loading data from: {data_dir}")
    full_dataset = KidneyUltrasoundDataset(data_dir, transform=None)
    
    # Check for duplicates
    if check_for_duplicates:
        logger.info("Checking for duplicate images...")
        duplicates = check_duplicates(full_dataset.samples)
        if duplicates:
            logger.warning(f"Found {len(duplicates)} duplicate image pairs!")
            for dup_a, dup_b in duplicates[:5]:
                logger.warning(f"  Duplicate: {dup_a} == {dup_b}")
            if len(duplicates) > 5:
                logger.warning(f"  ... and {len(duplicates) - 5} more")
        else:
            logger.info("✓ No duplicate images found")
    
    # Create stratified splits
    logger.info(f"Creating stratified splits: train={1-val_split-test_split:.0%}, val={val_split:.0%}, test={test_split:.0%}")
    train_samples, val_samples, test_samples = create_stratified_splits(
        samples=full_dataset.samples,
        class_names=full_dataset.classes,
        val_ratio=val_split,
        test_ratio=test_split,
        seed=seed
    )
    
    # Verify no leakage
    if not verify_no_leakage(train_samples, val_samples, test_samples):
        raise RuntimeError("Data leakage detected! Aborting.")
    
    # Create dataset objects for each split (using pre-computed samples)
    train_dataset = KidneyUltrasoundDataset(
        data_dir,
        transform=train_transform,
        samples=train_samples,
        class_names=full_dataset.classes
    )
    val_dataset = KidneyUltrasoundDataset(
        data_dir,
        transform=val_transform,
        samples=val_samples,
        class_names=full_dataset.classes
    )
    test_dataset = KidneyUltrasoundDataset(
        data_dir,
        transform=val_transform,  # No augmentation for test
        samples=test_samples,
        class_names=full_dataset.classes
    )
    
    # Log distributions
    logger.info(f"Train: {len(train_dataset)} samples - {train_dataset.get_class_distribution()}")
    logger.info(f"Val:   {len(val_dataset)} samples - {val_dataset.get_class_distribution()}")
    logger.info(f"Test:  {len(test_dataset)} samples - {test_dataset.get_class_distribution()}")
    
    # Create sampler for class balancing (train only)
    sampler = None
    shuffle = True
    
    if use_weighted_sampling:
        sample_weights = train_dataset.get_sample_weights()
        sampler = WeightedRandomSampler(
            weights=sample_weights,
            num_samples=len(sample_weights),
            replacement=True
        )
        shuffle = False
    
    # Windows-safe DataLoader settings
    # persistent_workers=False and num_workers=0 avoids multiprocessing issues on Windows
    is_windows = sys.platform == 'win32'
    if is_windows and num_workers > 0:
        logger.warning(f"Windows detected: setting num_workers=0 to avoid multiprocessing issues")
        num_workers = 0
    
    persistent = num_workers > 0 and not is_windows
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        sampler=sampler,
        num_workers=num_workers,
        pin_memory=pin_memory and torch.cuda.is_available(),
        drop_last=True,
        persistent_workers=persistent
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory and torch.cuda.is_available(),
        drop_last=False,
        persistent_workers=persistent
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory and torch.cuda.is_available(),
        drop_last=False,
        persistent_workers=persistent
    )
    
    logger.info(f"DataLoaders created: train={len(train_loader)} batches, val={len(val_loader)} batches, test={len(test_loader)} batches")
    
    return train_loader, val_loader, test_loader, full_dataset
