# AI-Powered Fabric Structure Analysis, Defect Detection and Quality Inspection System

Final-Year Project: Automated Fabric Quality Inspection and Textile Weave Structural Analysis using Deep Learning (**Faster R-CNN + ResNet-50 FPN**) fused with **OpenCV Structural Algorithms** and an interactive **React + Vite** frontend.

---

## 1. System Overview

The system provides an automated textile inspection workflow:
1. **AI Defect Detection**: Detects, localizes, and classifies surface fabric defects (**hole**, **knot**, **stain**) with high-precision bounding boxes and confidence scores using a trained Faster R-CNN architecture.
2. **OpenCV Weave Structural Analysis**: Analyzes warp (vertical) and weft (horizontal) thread orientation, yarn spacing regularity, and alignment deviation from ideal 90° orthogonality using Canny edge filtering and Probabilistic Hough Line Transform.
3. **Defect & Structure Fusion Scoring**: Combines defect severity/density and structural alignment into a composite quality score (0–100) and assigns an inspection grade (**Grade A, B, C, D**).
4. **Automated PDF Inspection Report**: Generates publication-ready PDF reports via ReportLab with side-by-side original/detection images, defect inventories, and engineering methodology.
5. **Interactive Animated Web Studio**: React + Vite interface featuring an animated textile thread canvas, real-time laser loom scanner animation, interactive defect explorer with loupe zoom, structural polar dials, and historical archives.

---

## 2. Model Location & Architecture

> [!IMPORTANT]
> The trained Faster R-CNN model checkpoint (~473 MB) resides **locally outside Git version control** and is never committed.
> Default Windows local path:
> `E:\Project\models\object detection\best_model.pth`

### Setting the Model Path for Other Machines
To run this application on another machine or environment, set the `FABRIC_MODEL_PATH` environment variable:

```bash
# Windows PowerShell
$env:FABRIC_MODEL_PATH = "C:\path\to\your\best_model.pth"

# Windows Command Prompt
set FABRIC_MODEL_PATH=C:\path\to\your\best_model.pth

# Linux / macOS
export FABRIC_MODEL_PATH="/path/to/your/best_model.pth"
```

The application verifies that the model file exists on startup. If the path is invalid, a descriptive error is displayed.

### Verified Architecture & Classes
- **Base Architecture**: Faster R-CNN with ResNet-50 Feature Pyramid Network (FPN)
- **Number of Classes**: 4 (`0: background`, `1: hole`, `2: knot`, `3: stain`)
- **Note on Line Class**: Legacy 5-class references in older training notebooks are ignored. The active model checkpoint only predicts hole, knot, and stain.
- **Parameters**: 41.4 Million
- **Model Loading**: Pre-loaded **once** in FastAPI lifespan on server boot. Never reloaded per request.

---

## 3. Project Directory Structure

```
fabric-ai-inspection/
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI routes (health, predict, analyze, inspect, report)
│   │   ├── model/               # Model loader, detector, and Stage 1 verification
│   │   ├── analysis/            # Defect analysis, OpenCV structural analyzer, quality scorer
│   │   ├── reports/             # ReportLab automated PDF generator
│   │   ├── database/            # SQLAlchemy models, SQLite / PostgreSQL connection
│   │   ├── config.py            # Centralized application settings
│   │   └── main.py              # FastAPI application entrypoint with lifespan loader
│   ├── tests/                   # Automated unit and integration test suite
│   └── requirements.txt         # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx               # Navigation bar with live backend/model status
│   │   │   ├── WeaveBackground.jsx      # Animated interactive textile weave canvas
│   │   │   ├── DashboardView.jsx        # Master metrics & 1-click benchmark samples
│   │   │   ├── NewInspectionView.jsx    # Drag-and-drop studio with laser loom scanner
│   │   │   ├── DetectionResultView.jsx  # Interactive defect explorer & loupe zoom
│   │   │   ├── StructuralAnalysisView.jsx# OpenCV stages & polar compass orientation dial
│   │   │   ├── QualityScoreView.jsx     # Score gauge, grade badges, confetti & formula
│   │   │   ├── InspectionHistoryView.jsx# Historical records table & PDF downloads
│   │   │   └── ReportModal.jsx          # In-app PDF report preview & printer
│   │   ├── App.jsx                      # Master layout & tab state manager
│   │   └── index.css                    # Luxury dark-theme textile styling
│   ├── package.json
│   └── vite.config.js
│
├── Dataset/                     # Benchmark dataset splits (test, train, valid)
├── .gitignore                   # Excludes *.pth, *.pt, *.onnx, venv, and cache
├── README.md                    # Main project documentation
├── ARCHITECTURE.md              # Detailed technical architecture design
└── API.md                       # Comprehensive REST API specifications
```

---

## 4. Installation & Quick Start

### Prerequisites
- Python 3.10+ (with PyTorch and Torchvision)
- Node.js v18+ and npm
- (Optional) NVIDIA CUDA GPU for ~50ms inference. CPU mode is fully supported.

### A. Backend Setup
1. Activate the Python virtual environment:
   ```powershell
   cd E:\Project
   .\venv\Scripts\Activate.ps1
   ```
2. Ensure backend dependencies are installed:
   ```powershell
   pip install -r backend/requirements.txt
   ```
3. Start the FastAPI server:
   ```powershell
   uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   The model loads into memory upon startup.
   API Documentation is available at `http://127.0.0.1:8000/docs`.

### B. Frontend Setup
1. In a separate terminal, navigate to the frontend directory:
   ```powershell
   cd E:\Project\frontend
   ```
2. Start the Vite development server:
   ```powershell
   npm.cmd run dev
   ```
3. Open your browser at `http://localhost:5173`.

---

## 5. Running Automated Tests

Run the complete 10-point unit and integration test suite:

```powershell
& "E:\Project\venv\Scripts\python.exe" -m unittest backend.tests.test_pipeline
```

All 10 tests verify:
- Model checkpoint existence & integrity
- Architecture and class mapping
- Faster R-CNN defect inference and bounding box accuracy
- Visualization image generation
- Defect statistical analysis
- OpenCV Canny edge and Hough transform analysis
- Quality scoring and grading heuristics
- ReportLab PDF generation
- Database record creation and retrieval
- FastAPI health check

---

## 6. Transparent Quality Scoring Methodology

Quality score calculation:
$$\text{quality\_score} = 0.60 \times \text{defect\_score} + 0.40 \times \text{structure\_score}$$

- **Defect Score (0–100)**: Starts at 100, penalized by defect count (weighted by class severity: Hole > Knot > Stain), defect area percentage, and defect spatial density.
- **Structure Score (0–100)**: Starts at 100, penalized by alignment deviation from 90° orthogonality and thread spacing variation (coefficient of variation).
- **Grading Thresholds**:
  - **Grade A (90–100)**: First Quality / Commercial Standard
  - **Grade B (75–89)**: Second Quality / Usable
  - **Grade C (60–74)**: Third Quality / Noticeable Defects
  - **Grade D (< 60)**: Reject / Failed Quality Inspection

> [!NOTE]
> This scoring formula is an engineering prototype design and is not an officially certified standard (e.g. ASTM D5430 4-Point System or ISO 8498).
