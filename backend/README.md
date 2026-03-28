# Kidney Ultrasound Classification Backend

A production-grade deep learning backend for classifying kidney conditions from ultrasound images using PyTorch and FastAPI.

## Features

- **Deep Learning Models**: ResNet50 (default) and DenseNet121 with transfer learning
- **CUDA Optimized**: Mixed precision training (FP16) for efficient GPU usage
- **Low VRAM Support**: Optimized for GTX 1650 (4GB VRAM) with gradient accumulation
- **REST API**: FastAPI backend with async endpoints
- **Grad-CAM**: Model interpretability visualization
- **Class Imbalance Handling**: Weighted loss and oversampling support

## System Requirements

- Python 3.11.9
- NVIDIA GPU with CUDA support (GTX 1650 or better recommended)
- 8GB RAM minimum
- CUDA 11.8 compatible drivers

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── routes/
│   │   ├── predict.py       # Prediction endpoints
│   │   └── upload.py        # File upload endpoints
│   ├── services/
│   │   ├── inference.py     # Inference service
│   │   └── preprocessing.py # Image preprocessing
│   ├── models/
│   │   └── model_loader.py  # Model loading singleton
│   └── schemas/
│       ├── request.py       # Request validation
│       └── response.py      # Response schemas
├── training/
│   ├── train.py             # Training script
│   ├── dataset.py           # PyTorch dataset
│   ├── transforms.py        # Data augmentation
│   └── utils.py             # Training utilities
├── data/
│   ├── raw/                 # Raw dataset (class folders)
│   └── processed/           # Processed data
├── saved_models/            # Trained model checkpoints
├── requirements.txt         # Python dependencies
├── config.yaml              # Configuration file
└── README.md
```

## Installation

### 1. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3.11 -m venv venv
source venv/bin/activate
```

### 2. Install PyTorch with CUDA

**Important**: Install PyTorch separately BEFORE other dependencies.

```bash
# For CUDA 11.8 (recommended for GTX 1650)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Verify CUDA installation
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}')"
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Dataset Preparation

Organize your dataset in the following structure:

```
data/raw/
├── Normal/
│   ├── image001.jpg
│   ├── image002.jpg
│   └── ...
├── CKD_Stage_1/
│   ├── image001.jpg
│   └── ...
├── CKD_Stage_2/
│   └── ...
├── CKD_Stage_3/
│   └── ...
└── CKD_Stage_4/
    └── ...
```

- Each folder name becomes a class label
- Supports: JPG, JPEG, PNG, BMP, TIFF formats
- Class imbalance is handled automatically

## Training

### Basic Training

```bash
python training/train.py --data_dir ./data/raw
```

### Full Training Options

```bash
python training/train.py \
    --data_dir ./data/raw \
    --output_dir ./saved_models \
    --model resnet50 \
    --epochs 50 \
    --batch_size 8 \
    --accumulation_steps 4 \
    --lr 1e-4 \
    --patience 10 \
    --mixed_precision \
    --augmentation medium
```

### Training Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--data_dir` | Required | Path to dataset directory |
| `--output_dir` | `saved_models` | Output directory for checkpoints |
| `--model` | `resnet50` | Model architecture (`resnet50`, `densenet121`) |
| `--epochs` | `50` | Number of training epochs |
| `--batch_size` | `8` | Batch size (keep ≤8 for 4GB VRAM) |
| `--accumulation_steps` | `4` | Gradient accumulation steps |
| `--lr` | `1e-4` | Initial learning rate |
| `--patience` | `10` | Early stopping patience |
| `--mixed_precision` | `True` | Use FP16 training |
| `--augmentation` | `medium` | Augmentation strength (`light`, `medium`, `heavy`) |

### Training Output

After training, you'll find in `saved_models/`:
- `best_model.pth` - Best model checkpoint
- `class_names.json` - Class label mapping
- `training_config.json` - Training configuration
- `training_history.json` - Loss/accuracy history
- `confusion_matrix.png` - Confusion matrix visualization
- `training_history.png` - Training curves

## Running the API Server

### Start the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

### Environment Variables

```bash
# Optional: Auto-load model on startup
export MODEL_PATH=saved_models/best_model.pth
export MODEL_NAME=resnet50

# Server configuration
export HOST=0.0.0.0
export PORT=8000
export DEBUG=false
export CORS_ORIGINS=*
```

## API Usage

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Load Model
```bash
curl -X POST http://localhost:8000/api/v1/predict/model/load \
    -H "Content-Type: application/json" \
    -d '{"model_path": "saved_models/best_model.pth", "model_name": "resnet50"}'
```

#### Upload Image
```bash
curl -X POST http://localhost:8000/api/v1/upload \
    -F "file=@kidney_scan.jpg"
```

#### Predict from File Upload
```bash
curl -X POST http://localhost:8000/api/v1/predict \
    -F "file=@kidney_scan.jpg"
```

#### Predict with All Probabilities
```bash
curl -X POST "http://localhost:8000/api/v1/predict?return_all_probs=true" \
    -F "file=@kidney_scan.jpg"
```

### Example Response

```json
{
    "success": true,
    "class": "CKD Stage 3",
    "confidence": 0.92,
    "severity": "Moderate",
    "class_index": 2
}
```

### Python Client Example

```python
import requests

# Load model
requests.post(
    "http://localhost:8000/api/v1/predict/model/load",
    json={"model_path": "saved_models/best_model.pth"}
)

# Predict
with open("kidney_scan.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/predict",
        files={"file": f}
    )

print(response.json())
```

## Deployment

### Docker (Recommended)

Create a `Dockerfile`:

```dockerfile
FROM pytorch/pytorch:2.0.1-cuda11.8-cudnn8-runtime

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t kidney-classification .
docker run -p 8000:8000 --gpus all kidney-classification
```

### Production Considerations

1. **Single Worker**: Use 1 worker for model serving to avoid loading multiple model copies
2. **Model Caching**: Model is loaded once and cached (singleton pattern)
3. **Memory Management**: CUDA cache is cleared periodically
4. **Logging**: Logs are rotated and retained for 7 days

## VRAM Optimization Tips

For GTX 1650 (4GB VRAM):

1. **Batch Size**: Keep ≤8 (default: 8)
2. **Gradient Accumulation**: Use 4+ steps for effective larger batches
3. **Mixed Precision**: Always enable (default: True)
4. **Workers**: Use 2 data loading workers
5. **Clear Cache**: Training script clears CUDA cache periodically

If you still encounter OOM errors:
```bash
python training/train.py --data_dir ./data/raw --batch_size 4 --accumulation_steps 8
```

## Troubleshooting

### CUDA Out of Memory
- Reduce batch size
- Increase gradient accumulation steps
- Ensure no other GPU processes running

### Model Not Loading
- Verify checkpoint path exists
- Check model architecture matches checkpoint
- Ensure CUDA drivers are compatible

### Slow Training
- Enable mixed precision (`--mixed_precision`)
- Reduce augmentation strength
- Check data loading bottlenecks

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
