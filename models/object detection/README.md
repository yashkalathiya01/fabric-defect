# Model Checkpoints

The trained Faster R-CNN checkpoint (~473 MB) is excluded from version control.

### Default Local Path
```
models/object detection/best_model.pth
```

### Configuration
Set the model path via environment variable if stored elsewhere:
```bash
# Windows PowerShell
$env:FABRIC_MODEL_PATH = "C:\path\to\your\best_model.pth"

# Linux / macOS
export FABRIC_MODEL_PATH="/path/to/your/best_model.pth"
```

### Architecture Specifications
- **Framework**: PyTorch (`torchvision.models.detection`)
- **Base Architecture**: Faster R-CNN with ResNet-50 Feature Pyramid Network (FPN)
- **Active Classes**: 4 (`0: background`, `1: hole`, `2: knot`, `3: stain`)
