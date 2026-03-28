"""
Kidney Ultrasound Classification - Training Pipeline
Production-grade training with proper train/val/test splits, gradient clipping,
and optimizations for GTX 1650 (4GB VRAM).

FIXES:
- Proper train/val/test split (no leakage)
- Gradient clipping for stability
- Windows-compatible data loading
- Optimized for speed
- Final test set evaluation
"""

import os
import sys
import argparse
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

import torch
import torch.nn as nn
import torch.optim as optim
from torch.cuda.amp import GradScaler, autocast
from torch.optim.lr_scheduler import CosineAnnealingLR, ReduceLROnPlateau, OneCycleLR
import torchvision.models as models
from loguru import logger
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from training.dataset import create_data_loaders, KidneyUltrasoundDataset
from training.transforms import get_train_transforms, get_val_transforms
from training.utils import (
    EarlyStopping,
    ModelCheckpoint,
    MetricsTracker,
    plot_confusion_matrix,
    plot_training_history,
    get_lr,
    count_parameters,
    seed_everything
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Train Kidney Ultrasound Classification Model',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Data arguments
    parser.add_argument(
        '--data_dir', 
        type=str, 
        required=True,
        help='Path to dataset directory with class subfolders'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='saved_models',
        help='Directory to save model checkpoints'
    )
    
    # Model arguments
    parser.add_argument(
        '--model',
        type=str,
        default='resnet50',
        choices=['resnet50', 'densenet121'],
        help='Model architecture'
    )
    parser.add_argument(
        '--pretrained',
        action='store_true',
        default=True,
        help='Use pretrained weights'
    )
    parser.add_argument(
        '--freeze_backbone',
        action='store_true',
        default=False,
        help='Freeze backbone layers (only train classifier)'
    )
    
    # Training arguments
    parser.add_argument(
        '--epochs',
        type=int,
        default=30,
        help='Number of training epochs'
    )
    parser.add_argument(
        '--batch_size',
        type=int,
        default=16,
        help='Batch size (will auto-reduce if OOM)'
    )
    parser.add_argument(
        '--accumulation_steps',
        type=int,
        default=2,
        help='Gradient accumulation steps'
    )
    parser.add_argument(
        '--lr',
        type=float,
        default=3e-4,
        help='Initial learning rate'
    )
    parser.add_argument(
        '--weight_decay',
        type=float,
        default=1e-4,
        help='Weight decay (L2 regularization)'
    )
    parser.add_argument(
        '--val_split',
        type=float,
        default=0.15,
        help='Validation split ratio'
    )
    parser.add_argument(
        '--test_split',
        type=float,
        default=0.15,
        help='Test split ratio (held-out)'
    )
    
    # Optimization arguments
    parser.add_argument(
        '--mixed_precision',
        action='store_true',
        default=False,
        help='Use mixed precision training (fp16) - can cause NaN, disable if unstable'
    )
    parser.add_argument(
        '--num_workers',
        type=int,
        default=0,
        help='Data loading workers (0 recommended for Windows)'
    )
    parser.add_argument(
        '--grad_clip',
        type=float,
        default=1.0,
        help='Gradient clipping max norm'
    )
    
    # Early stopping
    parser.add_argument(
        '--patience',
        type=int,
        default=7,
        help='Early stopping patience'
    )
    
    # Augmentation
    parser.add_argument(
        '--augmentation',
        type=str,
        default='light',
        choices=['light', 'medium', 'heavy'],
        help='Data augmentation strength'
    )
    
    # Other
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed'
    )
    parser.add_argument(
        '--use_clahe',
        action='store_true',
        default=False,
        help='Use CLAHE preprocessing (can slow down training)'
    )
    parser.add_argument(
        '--scheduler',
        type=str,
        default='onecycle',
        choices=['plateau', 'cosine', 'onecycle'],
        help='Learning rate scheduler'
    )
    
    return parser.parse_args()


def create_model(
    model_name: str,
    num_classes: int,
    pretrained: bool = True,
    freeze_backbone: bool = False
) -> nn.Module:
    """Create and configure the model."""
    if model_name == 'resnet50':
        if pretrained:
            weights = models.ResNet50_Weights.IMAGENET1K_V2
            model = models.resnet50(weights=weights)
        else:
            model = models.resnet50(weights=None)
        
        if freeze_backbone:
            for param in model.parameters():
                param.requires_grad = False
        
        num_features = model.fc.in_features
        model.fc = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(num_features, num_classes)
        )
        
    elif model_name == 'densenet121':
        if pretrained:
            weights = models.DenseNet121_Weights.IMAGENET1K_V1
            model = models.densenet121(weights=weights)
        else:
            model = models.densenet121(weights=None)
        
        if freeze_backbone:
            for param in model.parameters():
                param.requires_grad = False
        
        num_features = model.classifier.in_features
        model.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(num_features, num_classes)
        )
    
    else:
        raise ValueError(f"Unknown model: {model_name}")
    
    return model


def train_one_epoch(
    model: nn.Module,
    train_loader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    scaler: GradScaler,
    accumulation_steps: int,
    use_amp: bool,
    grad_clip: float,
    metrics_tracker: MetricsTracker,
    scheduler=None,
    use_onecycle: bool = False
) -> Dict[str, float]:
    """Train for one epoch with gradient accumulation, clipping, and optional AMP."""
    model.train()
    metrics_tracker.reset()
    optimizer.zero_grad()
    
    pbar = tqdm(train_loader, desc='Training', leave=False, ncols=100)
    
    for batch_idx, (images, targets) in enumerate(pbar):
        images = images.to(device, non_blocking=True)
        targets = targets.to(device, non_blocking=True)
        
        # Forward pass (with optional AMP)
        with autocast(enabled=use_amp):
            outputs = model(images)
            loss = criterion(outputs, targets)
            loss = loss / accumulation_steps
        
        # Check for NaN
        if torch.isnan(loss) or torch.isinf(loss):
            logger.warning(f"NaN/Inf loss at batch {batch_idx}, skipping...")
            optimizer.zero_grad()
            continue
        
        # Backward pass
        if use_amp:
            scaler.scale(loss).backward()
        else:
            loss.backward()
        
        # Update weights every accumulation_steps
        if (batch_idx + 1) % accumulation_steps == 0:
            if use_amp:
                scaler.unscale_(optimizer)
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=grad_clip)
            
            if use_amp:
                scaler.step(optimizer)
                scaler.update()
            else:
                optimizer.step()
            
            optimizer.zero_grad()
            
            # Step OneCycle scheduler per batch
            if use_onecycle and scheduler is not None:
                scheduler.step()
        
        # Track metrics
        metrics_tracker.update(
            outputs.detach(),
            targets,
            loss.item() * accumulation_steps
        )
        
        # Update progress bar
        pbar.set_postfix({'loss': f'{loss.item() * accumulation_steps:.4f}'})
    
    # Handle remaining gradients
    if len(train_loader) % accumulation_steps != 0:
        if use_amp:
            scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=grad_clip)
        if use_amp:
            scaler.step(optimizer)
            scaler.update()
        else:
            optimizer.step()
        optimizer.zero_grad()
    
    return metrics_tracker.compute()


@torch.no_grad()
def evaluate(
    model: nn.Module,
    data_loader,
    criterion: nn.Module,
    device: torch.device,
    metrics_tracker: MetricsTracker,
    desc: str = 'Validation'
) -> Dict[str, float]:
    """Evaluate the model (validation or test)."""
    model.eval()
    metrics_tracker.reset()
    
    pbar = tqdm(data_loader, desc=desc, leave=False, ncols=100)
    
    for images, targets in pbar:
        images = images.to(device, non_blocking=True)
        targets = targets.to(device, non_blocking=True)
        
        outputs = model(images)
        loss = criterion(outputs, targets)
        
        if not (torch.isnan(loss) or torch.isinf(loss)):
            metrics_tracker.update(outputs, targets, loss.item())
    
    return metrics_tracker.compute()


def main():
    """Main training function."""
    args = parse_args()
    
    # Create output directory first
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")
    logger.add(output_dir / "training.log", level="DEBUG")
    
    # Set random seed
    seed_everything(args.seed)
    
    # Device setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Device: {device}")
    
    if device.type == 'cuda':
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        logger.info(f"GPU: {gpu_name} ({vram_gb:.1f} GB VRAM)")
        
        # Optimize CUDA settings
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
    
    # Create transforms (disable CLAHE for speed unless explicitly enabled)
    train_transform = get_train_transforms(
        image_size=224,
        use_clahe=args.use_clahe,
        augmentation_strength=args.augmentation
    )
    val_transform = get_val_transforms(
        image_size=224,
        use_clahe=args.use_clahe
    )
    
    # Create data loaders with proper train/val/test split
    logger.info("="*50)
    logger.info("Creating datasets with train/val/test split...")
    train_loader, val_loader, test_loader, full_dataset = create_data_loaders(
        data_dir=args.data_dir,
        train_transform=train_transform,
        val_transform=val_transform,
        batch_size=args.batch_size,
        val_split=args.val_split,
        test_split=args.test_split,
        num_workers=args.num_workers,
        use_weighted_sampling=True,
        seed=args.seed,
        pin_memory=device.type == 'cuda',
        check_for_duplicates=True
    )
    logger.info("="*50)
    
    num_classes = len(full_dataset.classes)
    class_names = full_dataset.classes
    logger.info(f"Classes ({num_classes}): {class_names}")
    
    # Create model
    model = create_model(
        model_name=args.model,
        num_classes=num_classes,
        pretrained=args.pretrained,
        freeze_backbone=args.freeze_backbone
    )
    model = model.to(device)
    
    total_params, trainable_params = count_parameters(model)
    logger.info(f"Parameters: {trainable_params:,} trainable / {total_params:,} total")
    
    # Loss function with class weights
    class_weights = full_dataset.get_class_weights().to(device)
    logger.info(f"Class weights: {dict(zip(class_names, class_weights.cpu().numpy().round(3)))}")
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    
    # Optimizer
    optimizer = optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=args.lr,
        weight_decay=args.weight_decay
    )
    
    # Learning rate scheduler
    use_onecycle = args.scheduler == 'onecycle'
    if args.scheduler == 'plateau':
        scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3, min_lr=1e-7)
    elif args.scheduler == 'cosine':
        scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-7)
    elif args.scheduler == 'onecycle':
        steps_per_epoch = len(train_loader) // args.accumulation_steps
        scheduler = OneCycleLR(
            optimizer,
            max_lr=args.lr,
            epochs=args.epochs,
            steps_per_epoch=steps_per_epoch,
            pct_start=0.1,
            anneal_strategy='cos'
        )
    
    # Mixed precision scaler
    scaler = GradScaler(enabled=args.mixed_precision)
    
    # Early stopping and checkpointing
    early_stopping = EarlyStopping(patience=args.patience, mode='min')
    checkpoint = ModelCheckpoint(
        save_dir=args.output_dir,
        filename='best_model.pth',
        monitor='val_loss',
        mode='min'
    )
    
    # Metrics trackers
    train_metrics = MetricsTracker(class_names)
    val_metrics = MetricsTracker(class_names)
    test_metrics = MetricsTracker(class_names)
    
    # Training history
    history = {
        'train_loss': [], 'val_loss': [],
        'train_acc': [], 'val_acc': [],
        'train_f1': [], 'val_f1': [],
        'lr': []
    }
    
    # Training loop
    logger.info("="*50)
    logger.info(f"Starting training: {args.epochs} epochs, batch_size={args.batch_size}, accumulation={args.accumulation_steps}")
    logger.info(f"Effective batch size: {args.batch_size * args.accumulation_steps}")
    logger.info(f"Mixed precision: {args.mixed_precision}, Gradient clipping: {args.grad_clip}")
    logger.info("="*50)
    
    start_time = time.time()
    
    for epoch in range(1, args.epochs + 1):
        epoch_start = time.time()
        
        # Train
        train_results = train_one_epoch(
            model=model,
            train_loader=train_loader,
            criterion=criterion,
            optimizer=optimizer,
            device=device,
            scaler=scaler,
            accumulation_steps=args.accumulation_steps,
            use_amp=args.mixed_precision,
            grad_clip=args.grad_clip,
            metrics_tracker=train_metrics,
            scheduler=scheduler if use_onecycle else None,
            use_onecycle=use_onecycle
        )
        
        # Validate
        val_results = evaluate(
            model=model,
            data_loader=val_loader,
            criterion=criterion,
            device=device,
            metrics_tracker=val_metrics,
            desc='Validation'
        )
        
        # Update scheduler (non-OneCycle)
        if args.scheduler == 'plateau':
            scheduler.step(val_results['loss'])
        elif args.scheduler == 'cosine':
            scheduler.step()
        
        epoch_time = time.time() - epoch_start
        current_lr = get_lr(optimizer)
        
        # Log metrics
        logger.info(f"Epoch {epoch}/{args.epochs} ({epoch_time:.1f}s) | LR: {current_lr:.2e}")
        logger.info(f"  Train: Loss={train_results['loss']:.4f}, Acc={train_results['accuracy']:.4f}, F1={train_results['f1_macro']:.4f}")
        logger.info(f"  Val:   Loss={val_results['loss']:.4f}, Acc={val_results['accuracy']:.4f}, F1={val_results['f1_macro']:.4f}")
        
        # Update history
        history['train_loss'].append(train_results['loss'])
        history['val_loss'].append(val_results['loss'])
        history['train_acc'].append(train_results['accuracy'])
        history['val_acc'].append(val_results['accuracy'])
        history['train_f1'].append(train_results['f1_macro'])
        history['val_f1'].append(val_results['f1_macro'])
        history['lr'].append(current_lr)
        
        # Checkpoint
        metrics_for_checkpoint = {
            'val_loss': val_results['loss'],
            'val_accuracy': val_results['accuracy'],
            'val_f1': val_results['f1_macro'],
            'train_loss': train_results['loss'],
        }
        checkpoint(model, optimizer, epoch, metrics_for_checkpoint, class_names, scheduler)
        
        # Early stopping
        if early_stopping(val_results['loss'], epoch):
            logger.info(f"Early stopping at epoch {epoch} (best: {early_stopping.best_epoch})")
            break
        
        # Clear CUDA cache
        if device.type == 'cuda':
            torch.cuda.empty_cache()
    
    total_time = time.time() - start_time
    logger.info("="*50)
    logger.info(f"Training completed in {total_time/60:.1f} minutes")
    
    # Load best model for final evaluation
    logger.info("Loading best model for final evaluation...")
    # weights_only=False because our checkpoint stores full training state dicts
    best_ckpt = torch.load(output_dir / 'best_model.pth', map_location=device, weights_only=False)
    model.load_state_dict(best_ckpt['model_state_dict'])
    
    # Final validation evaluation
    logger.info("\n" + "="*50)
    logger.info("FINAL VALIDATION RESULTS:")
    logger.info("="*50)
    final_val = evaluate(model, val_loader, criterion, device, val_metrics, 'Final Val')
    logger.info(f"Accuracy: {final_val['accuracy']:.4f}")
    logger.info(f"F1 (macro): {final_val['f1_macro']:.4f}")
    logger.info(f"F1 (weighted): {final_val['f1_weighted']:.4f}")
    logger.info("\nClassification Report:\n" + val_metrics.get_classification_report())
    
    # TEST SET EVALUATION (held-out, never seen during training)
    logger.info("\n" + "="*50)
    logger.info("HELD-OUT TEST SET RESULTS:")
    logger.info("="*50)
    test_results = evaluate(model, test_loader, criterion, device, test_metrics, 'Test')
    logger.info(f"Accuracy: {test_results['accuracy']:.4f}")
    logger.info(f"F1 (macro): {test_results['f1_macro']:.4f}")
    logger.info(f"F1 (weighted): {test_results['f1_weighted']:.4f}")
    logger.info("\nClassification Report:\n" + test_metrics.get_classification_report())
    
    # Save confusion matrices
    val_cm = val_metrics.get_confusion_matrix()
    test_cm = test_metrics.get_confusion_matrix()
    plot_confusion_matrix(val_cm, class_names, save_path=str(output_dir / 'confusion_matrix_val.png'), title='Validation Confusion Matrix')
    plot_confusion_matrix(test_cm, class_names, save_path=str(output_dir / 'confusion_matrix_test.png'), title='Test Confusion Matrix')
    
    # Save training history
    plot_training_history(history, save_path=str(output_dir / 'training_history.png'))
    with open(output_dir / 'training_history.json', 'w') as f:
        json.dump(history, f, indent=2)
    
    # Save final results
    final_results = {
        'validation': {
            'accuracy': final_val['accuracy'],
            'f1_macro': final_val['f1_macro'],
            'f1_weighted': final_val['f1_weighted'],
            'loss': final_val['loss']
        },
        'test': {
            'accuracy': test_results['accuracy'],
            'f1_macro': test_results['f1_macro'],
            'f1_weighted': test_results['f1_weighted'],
            'loss': test_results['loss']
        },
        'training_time_minutes': total_time / 60,
        'best_epoch': early_stopping.best_epoch,
        'total_epochs': epoch
    }
    with open(output_dir / 'final_results.json', 'w') as f:
        json.dump(final_results, f, indent=2)
    
    # Save training config
    config = vars(args)
    config['num_classes'] = num_classes
    config['class_names'] = class_names
    with open(output_dir / 'training_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"\nAll artifacts saved to: {output_dir}")
    logger.info("Training complete!")


if __name__ == '__main__':
    main()
