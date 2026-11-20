import json
import shutil
from pathlib import Path
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    File,
    UploadFile,
    Form,
    Depends,
    HTTPException,
    status,
    Request,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.config import (
    ALLOWED_ORIGINS,
    UPLOADS_DIR,
    OUTPUTS_DIR,
    STATIC_DIR,
    TARGET_CLASSES,
    CATEGORY_GROUPS,
    DEFAULT_BOX_THRESHOLD,
    DEFAULT_TEXT_THRESHOLD,
    VIDEO_SAMPLE_FPS,
    DEBUG,
)
from backend.security import (
    verify_api_key,
    sanitize_filename,
    validate_file_extension,
    validate_file_size,
)
from backend.detector import WaterPollutionDetector


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Preload model at server launch
    print("=" * 60)
    print("Initializing Water Pollution Detection Engine...")
    print("Preloading Grounding DINO model weights...")
    try:
        WaterPollutionDetector.get_instance()
        print("Model engine initialized successfully!")
    except Exception as e:
        print(f"Warning: Model preload failed: {e}. Will attempt on first request.")
    print("=" * 60)
    yield


app = FastAPI(
    title="AquaGuard - AI Water Pollution Detection System",
    description="High-precision automated water surface pollution detection using Grounding DINO.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if "*" not in ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static and generated outputs directories
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")


@app.get("/", response_class=FileResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend index.html not found.")
    return FileResponse(index_file)


@app.get("/api/health")
async def health_check():
    detector = WaterPollutionDetector.get_instance()
    return {
        "status": "healthy",
        "device": detector.device,
        "supported_classes_count": len(TARGET_CLASSES),
        "target_classes": TARGET_CLASSES,
    }


@app.get("/api/classes")
async def get_classes():
    """Returns target classes and grouped categories for frontend filters."""
    return {
        "classes": TARGET_CLASSES,
        "groups": CATEGORY_GROUPS,
        "default_thresholds": {
            "box_threshold": DEFAULT_BOX_THRESHOLD,
            "text_threshold": DEFAULT_TEXT_THRESHOLD,
            "video_sample_fps": VIDEO_SAMPLE_FPS,
        },
    }


@app.post("/api/detect/image", dependencies=[Depends(verify_api_key)])
async def detect_image(
    file: UploadFile = File(...),
    threshold: float = Form(DEFAULT_BOX_THRESHOLD),
    text_threshold: float = Form(DEFAULT_TEXT_THRESHOLD),
    classes: Optional[str] = Form(None),  # JSON array string or comma-separated
):
    """
    Accepts PNG or JPG image, runs object detection, and returns annotated results.
    """
    media_type, ext = validate_file_extension(file.filename, expected_type="image")

    # Parse selected classes
    selected_classes = None
    if classes:
        try:
            parsed = json.loads(classes)
            if isinstance(parsed, list) and len(parsed) > 0:
                selected_classes = parsed
        except Exception:
            selected_classes = [c.strip() for c in classes.split(",") if c.strip()]

    # Secure temporary file save
    safe_name = sanitize_filename(file.filename)
    dest_path = UPLOADS_DIR / safe_name

    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Validate file size
        validate_file_size(dest_path.stat().st_size, media_type)

        detector = WaterPollutionDetector.get_instance()
        result = detector.process_image(
            image_path=dest_path,
            selected_classes=selected_classes,
            threshold=threshold,
            text_threshold=text_threshold,
        )
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(e)}",
        )
    finally:
        # Clean up raw upload file to protect privacy and save disk
        if dest_path.exists():
            try:
                dest_path.unlink()
            except Exception:
                pass


@app.post("/api/detect/video", dependencies=[Depends(verify_api_key)])
async def detect_video(
    file: UploadFile = File(...),
    threshold: float = Form(DEFAULT_BOX_THRESHOLD),
    text_threshold: float = Form(DEFAULT_TEXT_THRESHOLD),
    speed_mode: str = Form("turbo"),  # "turbo" (fastest), "balanced", or "detailed"
    interval_sec: Optional[float] = Form(None),
    max_frames: Optional[int] = Form(None),
    classes: Optional[str] = Form(None),
):
    """
    Accepts MP4 or MKV video, applies accelerated direct-seek sampling,
    and returns an interactive timeline summary with annotated video output.
    """
    media_type, ext = validate_file_extension(file.filename, expected_type="video")

    selected_classes = None
    if classes:
        try:
            parsed = json.loads(classes)
            if isinstance(parsed, list) and len(parsed) > 0:
                selected_classes = parsed
        except Exception:
            selected_classes = [c.strip() for c in classes.split(",") if c.strip()]

    safe_name = sanitize_filename(file.filename)
    dest_path = UPLOADS_DIR / safe_name

    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Validate file size
        validate_file_size(dest_path.stat().st_size, media_type)

        detector = WaterPollutionDetector.get_instance()
        result = detector.process_video(
            video_path=dest_path,
            selected_classes=selected_classes,
            threshold=threshold,
            text_threshold=text_threshold,
            speed_mode=speed_mode if speed_mode in ("turbo", "balanced", "detailed") else "turbo",
            custom_interval_sec=interval_sec,
            custom_max_frames=max_frames,
        )
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video analysis error: {str(e)}",
        )
    finally:
        # Clean up raw upload
        if dest_path.exists():
            try:
                dest_path.unlink()
            except Exception:
                pass


# Startup runner helper
if __name__ == "__main__":
    import uvicorn
    from backend.config import PORT, HOST

    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=DEBUG)
