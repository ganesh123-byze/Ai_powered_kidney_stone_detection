"""
Kidney Ultrasound Classification - Training Utilities
Production-grade metrics, early stopping, checkpointing, and logging utilities.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score, 
    f1_score, 
    confusion_matrix, 
    classification_report,
    precision_recall_fscore_support,
    roc_auc_score
)
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import seaborn as sns
from loguru import logger
from datetime import datetime


class EarlyStopping:
    """
    Early stopping to prevent overfitting.
    Monitors validation loss and stops training when no improvement.
    """
    
    def __init__(
        self,
        patience: int = 10,
        min_delta: float = 1e-4,
        mode: str = 'min',
        verbose: bool = True
    ):
        """
        Args:
            patience: Number of epochs to wait before stopping
            min_delta: Minimum change to qualify as improvement
            mode: 'min' for loss (lower is better), 'max' for accuracy
            verbose: Whether to print messages
        """
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.verbose = verbose
        
        self.counter = 0
        self.best_score = None
        self.early_stop = False
        self.best_epoch = 0
    
    def __call__(self, score: float, epoch: int) -> bool:
        """
        Check if training should stop.
        
        Args:
            score: Current validation metric
            epoch: Current epoch number
        
        Returns:
            True if training should stop
        """
        if self.mode == 'min':
            current_score = -score
        else:
            current_score = score
        
        if self.best_score is None:
            self.best_score = current_score
            self.best_epoch = epoch
        elif current_score < self.best_score + self.min_delta:
            self.counter += 1
            if self.verbose:
                logger.info(f"EarlyStopping counter: {self.counter}/{self.patience}")
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_score = current_score
            self.best_epoch = epoch
            self.counter = 0
        
        return self.early_stop


class ModelCheckpoint:
    """
    Save model checkpoints during training.
    """
    
    def __init__(
        self,
        save_dir: str,
        filename: str = 'best_model.pth',
        monitor: str = 'val_loss',
        mode: str = 'min',
        save_best_only: bool = True,
        verbose: bool = True
    ):
        """
        Args:
            save_dir: Directory to save checkpoints
            filename: Checkpoint filename
            monitor: Metric to monitor
            mode: 'min' or 'max'
            save_best_only: Only save when metric improves
            verbose: Whether to print messages
        """
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.filename = filename
        self.monitor = monitor
        self.mode = mode
        self.save_best_only = save_best_only
        self.verbose = verbose
        
        self.best_score = None
    
    def __call__(
        self,
        model: nn.Module,
        optimizer: torch.optim.Optimizer,
        epoch: int,
        metrics: Dict[str, float],
        class_names: List[str],
        scheduler: Optional[Any] = None
    ) -> bool:
        """
        Save checkpoint if conditions are met.
        
        Returns:
            True if checkpoint was saved
        """
        current_score = metrics.get(self.monitor, None)
        if current_score is None:
            logger.warning(f"Metric {self.monitor} not found in metrics")
            return False
        
        save = False
        
        if not self.save_best_only:
            save = True
        elif self.best_score is None:
            save = True
        elif self.mode == 'min' and current_score < self.best_score:
            save = True
        elif self.mode == 'max' and current_score > self.best_score:
            save = True
        
        if save:
            self.best_score = current_score
            checkpoint = {
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'metrics': metrics,
                'class_names': class_names,
                'best_score': self.best_score,
                'timestamp': datetime.now().isoformat()
            }
            
            if scheduler is not None:
                checkpoint['scheduler_state_dict'] = scheduler.state_dict()
            
            save_path = self.save_dir / self.filename
            torch.save(checkpoint, save_path)
            
            if self.verbose:
                logger.info(f"Checkpoint saved: {save_path} ({self.monitor}: {current_score:.4f})")
            
            # Also save class names separately for inference
            class_names_path = self.save_dir / 'class_names.json'
            with open(class_names_path, 'w') as f:
                json.dump({'classes': class_names}, f, indent=2)
        
        return save


class MetricsTracker:
    """
    Track and compute training metrics.
    """
    
    def __init__(self, class_names: List[str]):
        self.class_names = class_names
        self.reset()
    
    def reset(self):
        """Reset all accumulated values."""
        self.predictions = []
        self.targets = []
        self.losses = []
    
    def update(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor,
        loss: float
    ):
        """
        Update with batch results.
        
        Args:
            predictions: Model predictions (logits or probabilities)
            targets: Ground truth labels
            loss: Batch loss value
        """
        # Get predicted classes
        if predictions.dim() > 1:
            preds = predictions.argmax(dim=1)
        else:
            preds = predictions
        
        self.predictions.extend(preds.cpu().numpy())
        self.targets.extend(targets.cpu().numpy())
        self.losses.append(loss)
    
    def compute(self) -> Dict[str, float]:
        """
        Compute all metrics.
        
        Returns:
            Dictionary of metric names and values
        """
        preds = np.array(self.predictions)
        targets = np.array(self.targets)
        
        accuracy = accuracy_score(targets, preds)
        
        # Handle multi-class F1
        f1_macro = f1_score(targets, preds, average='macro', zero_division=0)
        f1_weighted = f1_score(targets, preds, average='weighted', zero_division=0)
        
        # Per-class metrics
        precision, recall, f1_per_class, support = precision_recall_fscore_support(
            targets, preds, average=None, zero_division=0
        )
        
        avg_loss = np.mean(self.losses) if self.losses else 0.0
        
        metrics = {
            'loss': avg_loss,
            'accuracy': accuracy,
            'f1_macro': f1_macro,
            'f1_weighted': f1_weighted,
        }
        
        # Add per-class F1
        for i, class_name in enumerate(self.class_names):
            if i < len(f1_per_class):
                metrics[f'f1_{class_name}'] = f1_per_class[i]
        
        return metrics
    
    def get_confusion_matrix(self) -> np.ndarray:
        """Get confusion matrix."""
        return confusion_matrix(self.targets, self.predictions)
    
    def get_classification_report(self) -> str:
        """Get detailed classification report."""
        return classification_report(
            self.targets, 
            self.predictions, 
            target_names=self.class_names,
            zero_division=0
        )


def plot_confusion_matrix(
    cm: np.ndarray,
    class_names: List[str],
    save_path: Optional[str] = None,
    title: str = 'Confusion Matrix',
    figsize: Tuple[int, int] = (10, 8)
) -> plt.Figure:
    """
    Plot confusion matrix.
    
    Args:
        cm: Confusion matrix array
        class_names: List of class names
        save_path: Path to save the figure
        title: Plot title
        figsize: Figure size
    
    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Normalize
    cm_normalized = cm.astype('float') / (cm.sum(axis=1, keepdims=True) + 1e-10)
    
    # Plot
    sns.heatmap(
        cm_normalized,
        annot=True,
        fmt='.2%',
        cmap='Blues',
        xticklabels=class_names,
        yticklabels=class_names,
        ax=ax
    )
    
    ax.set_xlabel('Predicted Label')
    ax.set_ylabel('True Label')
    ax.set_title(title)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Confusion matrix saved to {save_path}")
    
    return fig


def plot_training_history(
    history: Dict[str, List[float]],
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (14, 5)
) -> plt.Figure:
    """
    Plot training history (loss and accuracy curves).
    
    Args:
        history: Dictionary with 'train_loss', 'val_loss', 'train_acc', 'val_acc'
        save_path: Path to save the figure
        figsize: Figure size
    
    Returns:
        Matplotlib figure
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    epochs = range(1, len(history.get('train_loss', [])) + 1)
    
    # Loss plot
    if 'train_loss' in history:
        axes[0].plot(epochs, history['train_loss'], 'b-', label='Train Loss')
    if 'val_loss' in history:
        axes[0].plot(epochs, history['val_loss'], 'r-', label='Val Loss')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training and Validation Loss')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Accuracy plot
    if 'train_acc' in history:
        axes[1].plot(epochs, history['train_acc'], 'b-', label='Train Accuracy')
    if 'val_acc' in history:
        axes[1].plot(epochs, history['val_acc'], 'r-', label='Val Accuracy')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy')
    axes[1].set_title('Training and Validation Accuracy')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Training history saved to {save_path}")
    
    return fig


def get_lr(optimizer: torch.optim.Optimizer) -> float:
    """Get current learning rate from optimizer."""
    for param_group in optimizer.param_groups:
        return param_group['lr']
    return 0.0


def count_parameters(model: nn.Module) -> Tuple[int, int]:
    """
    Count model parameters.
    
    Returns:
        total_params, trainable_params
    """
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total, trainable


def seed_everything(seed: int = 42):
    """Set random seeds for reproducibility."""
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    # Note: deterministic=True can slow down training significantly
    # Only enable if exact reproducibility is critical
    # torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = True  # Faster, but slightly non-deterministic
    os.environ['PYTHONHASHSEED'] = str(seed)
