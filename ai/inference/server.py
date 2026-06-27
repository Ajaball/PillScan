"""
PillScan AI Inference Server
FastAPI microservice for serving pill identification predictions.
Runs independently of the main backend.
"""

import io
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from inference.pipeline import PillScanPipeline

# ── Initialize ───────────────────────────────────────────────────────────

app = FastAPI(
    title="PillScan AI Service",
    version="1.0.0",
    description="AI inference microservice for pill identification",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the inference pipeline
detector_path = "./models/detection/yolov8n_pills.onnx"
classifier_path = "./models/classification/efficientnet_v2s_pills.onnx"
labels_path = "./models/classification/pill_labels.txt"

if os.path.exists(detector_path) and os.path.exists(classifier_path):
    class_names = []
    if os.path.exists(labels_path):
        with open(labels_path, "r", encoding="utf-8") as f:
            class_names = [line.strip() for line in f if line.strip()]
    
    print(f"[AI Server] Loading real models with classes: {class_names}")
    pipeline = PillScanPipeline(
        detector_model_path=detector_path,
        classifier_model_path=classifier_path,
        class_names=class_names
    )
else:
    print("[AI Server] Running in Demo Mode (models not found)")
    pipeline = PillScanPipeline()  # Demo mode


# ── Endpoints ────────────────────────────────────────────────────────────

@app.post("/predict")
async def predict(image: UploadFile = File(...)):
    """
    Run pill identification on an uploaded image.

    Returns top-5 predictions with confidence scores.
    """
    # Validate file type
    if image.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Invalid image format")

    try:
        contents = await image.read()
        pil_image = Image.open(io.BytesIO(contents))

        result = pipeline.identify(pil_image, top_k=5)

        return {
            "success": True,
            "data": result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


@app.get("/health")
async def health():
    """Health check for the AI service."""
    return {
        "status": "healthy",
        "service": "PillScan AI Inference",
        "model_loaded": pipeline.classifier.model is not None,
    }


@app.get("/model-info")
async def model_info():
    """Return information about the loaded models."""
    return {
        "detector": {
            "model_path": pipeline.detector.model_path,
            "loaded": pipeline.detector.model is not None,
            "input_size": pipeline.detector.input_size,
        },
        "classifier": {
            "model_path": pipeline.classifier.model_path,
            "loaded": pipeline.classifier.model is not None,
            "input_size": pipeline.classifier.input_size,
            "num_classes": len(pipeline.classifier.class_names),
        },
    }
