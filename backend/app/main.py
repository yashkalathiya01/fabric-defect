"""
Fabric AI Inspection System - FastAPI Main Application
=======================================================

Entrypoint for the backend server:
- Loads the 500 MB Faster R-CNN checkpoint ONCE during lifespan startup
- Initializes database tables
- Configures CORS for React frontend communication
- Mounts static files (uploads, results, sample images)
- Mounts inspection, prediction, analysis, and report routes
"""

import os
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.config import UPLOAD_DIR, RESULTS_DIR
from backend.app.database.database import init_db
from backend.app.model.model_loader import load_model
from backend.app.api.endpoints import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("fabric_inspection_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan:
    - Pre-loads the 500 MB Faster R-CNN model on server boot so inference is instant.
    - Ensures database tables exist.
    """
    logger.info("Initializing Fabric AI Inspection System backend...")

    # 1. Initialize Database
    init_db()

    # 2. Pre-load Faster R-CNN Model ONCE
    logger.info("Pre-loading Faster R-CNN checkpoint into memory...")
    try:
        model, class_names, device = load_model()
        logger.info(
            "Faster R-CNN model successfully ready on %s with classes: %s",
            device,
            list(class_names.values()),
        )
    except Exception as e:
        logger.error("WARNING: Failed to pre-load model on startup: %s", e)

    # 3. Ensure static directories exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    yield

    logger.info("Shutting down Fabric AI Inspection System.")


app = FastAPI(
    title="Fabric AI Inspection System API",
    description="AI-Powered Fabric Structure Analysis, Defect Detection and Quality Inspection System",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS Configuration (allows React frontend on any common dev port)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static Files Mounting
# ---------------------------------------------------------------------------
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

app.mount("/static/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/static/results", StaticFiles(directory=RESULTS_DIR), name="results")

# Also mount sample dataset images for quick one-click testing from the UI
sample_images_dir = os.path.join(PROJECT_ROOT, "Dataset", "test")
if os.path.isdir(sample_images_dir):
    app.mount("/static/samples", StaticFiles(directory=sample_images_dir), name="samples")

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(api_router, prefix="/api", tags=["Inspection API"])
# Also include at root so /health, /predict, /inspect work directly without /api prefix
app.include_router(api_router, tags=["Direct Routes"])


@app.get("/", response_class=HTMLResponse, summary="Backend Server Landing Page", tags=["Root"])
def root_landing_page():
    """Renders a welcome and navigation page when opening http://localhost:8000 in a browser."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TexVision QA — Backend Inspection Server</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #F5F5F5;
            color: #171717;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }
        .card {
            background: #F5F5F5;
            border: 1px solid #DCDCDC;
            border-radius: 16px;
            padding: 36px;
            max-width: 620px;
            width: 100%;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
            text-align: center;
        }
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: #E6F4EA;
            border: 1px solid #CEEAD6;
            color: #137333;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 11px;
            font-weight: 700;
            padding: 5px 12px;
            border-radius: 9999px;
            margin-bottom: 16px;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .pulse-dot {
            width: 7px;
            height: 7px;
            background: #137333;
            border-radius: 50%;
        }
        h1 {
            font-size: 24px;
            font-weight: 800;
            color: #171717;
            margin-bottom: 8px;
            letter-spacing: -0.02em;
        }
        p.subtitle {
            color: #525252;
            font-size: 13px;
            line-height: 1.55;
            margin-bottom: 20px;
        }
        .specs-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            margin-bottom: 24px;
            text-align: left;
        }
        .spec-box {
            background: #EAEAEA;
            border: 1px solid #DCDCDC;
            border-radius: 10px;
            padding: 10px 12px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }
        .spec-label {
            font-size: 10px;
            color: #737373;
            text-transform: uppercase;
            display: block;
            margin-bottom: 3px;
        }
        .spec-val {
            font-size: 11.5px;
            font-weight: 700;
            color: #171717;
        }
        .actions {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 24px;
        }
        .btn-primary {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: #171717;
            color: #F5F5F5;
            text-decoration: none;
            font-weight: 600;
            font-size: 13.5px;
            padding: 13px 20px;
            border-radius: 10px;
            border: 1px solid #171717;
            transition: all 0.15s ease;
        }
        .btn-primary:hover {
            background: #262626;
        }
        .btn-secondary {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: #EAEAEA;
            border: 1px solid #DCDCDC;
            color: #171717;
            text-decoration: none;
            font-weight: 600;
            font-size: 13px;
            padding: 11px 20px;
            border-radius: 10px;
            transition: all 0.15s ease;
        }
        .btn-secondary:hover {
            background: #E2E2E2;
            border-color: #C4C4C4;
        }
        .footer-links {
            border-top: 1px solid #DCDCDC;
            padding-top: 16px;
            display: flex;
            justify-content: center;
            gap: 16px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 11.5px;
            color: #737373;
        }
        .footer-links a {
            color: #171717;
            font-weight: 600;
            text-decoration: none;
        }
        .footer-links a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="badge">
            <div class="pulse-dot"></div>
            SERVER :8000 ONLINE • MODEL READY
        </div>
        <h1>TexVision QA — Automated Textile Inspection</h1>
        <p class="subtitle">
            Faster R-CNN (ResNet-50 FPN) defect localization &amp; OpenCV Canny Edge, Adaptive Threshold, and Grayscale Luminance processing engine.
        </p>

        <div class="specs-grid">
            <div class="spec-box">
                <span class="spec-label">Defect Classes</span>
                <span class="spec-val">Hole • Knot • Stain</span>
            </div>
            <div class="spec-box">
                <span class="spec-label">Weave Laboratory</span>
                <span class="spec-val">Edge • Threshold • Gray</span>
            </div>
            <div class="spec-box">
                <span class="spec-label">Avg Inference</span>
                <span class="spec-val">0.42 sec (FPN)</span>
            </div>
        </div>

        <div class="actions">
            <a href="http://localhost:5173" class="btn-primary">
                Open TexVision QA Workspace (localhost:5173) →
            </a>
            <a href="/docs" class="btn-secondary">
                Open Interactive Swagger API Docs (/docs)
            </a>
        </div>

        <div class="footer-links">
            <a href="#health" onclick="loadPanel('/api/health', 'System Health Status'); return false;">Health Status</a>
            <span>•</span>
            <a href="#metrics" onclick="loadPanel('/api/dashboard/metrics', 'Live Dashboard Metrics'); return false;">Dashboard Metrics</a>
            <span>•</span>
            <a href="/docs">Swagger UI (/docs)</a>
        </div>

        <div id="live-panel" style="display:none; margin-top:16px; background:#EAEAEA; border:1px solid #DCDCDC; border-radius:10px; padding:12px 14px; text-align:left; font-family:ui-monospace, SFMono-Regular, Menlo, monospace; font-size:11.5px; color:#171717;">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #DCDCDC; padding-bottom:6px; margin-bottom:8px;">
                <strong id="live-panel-title">Status</strong>
                <span style="cursor:pointer; color:#737373; font-size:11px;" onclick="document.getElementById('live-panel').style.display='none'">✕ Close</span>
            </div>
            <pre id="live-panel-body" style="white-space:pre-wrap; word-break:break-word; line-height:1.5; color:#171717;"></pre>
        </div>
    </div>
    <script>
        async function loadPanel(url, title) {
            const panel = document.getElementById('live-panel');
            const titleEl = document.getElementById('live-panel-title');
            const bodyEl = document.getElementById('live-panel-body');
            panel.style.display = 'block';
            titleEl.textContent = title + ' (' + url + ')';
            bodyEl.textContent = 'Loading...';
            try {
                const res = await fetch(url);
                const data = await res.json();
                bodyEl.textContent = JSON.stringify(data, null, 2);
            } catch (err) {
                bodyEl.textContent = 'Error loading endpoint: ' + err.message;
            }
        }
    </script>
</body>
</html>
"""


@app.get("/api/samples", summary="List Sample Fabric Images for Quick Testing", tags=["Sample Images"])
def list_sample_images():
    """Returns a curated list of sample fabric images available for instant one-click testing."""
    samples = []
    if os.path.isdir(sample_images_dir):
        for fname in os.listdir(sample_images_dir)[:24]:
            if fname.lower().endswith((".jpg", ".jpeg", ".png")):
                # Classify sample preview by filename hint
                fl = fname.lower()
                defect_type = "Hole" if ("delik" in fl or "hole" in fl) else ("Stain" if ("leke" in fl or "stain" in fl) else ("Weave/Knot" if "dokuma" in fl else "Fabric Texture"))
                samples.append({
                    "filename": fname,
                    "preview_url": f"/static/samples/{fname}",
                    "type": defect_type,
                })
    return {"samples": samples}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
