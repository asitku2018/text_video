import os
import uuid
import shutil
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from worker import process_video_task, celery_app
from core.config import settings

app = FastAPI(title="Video Generation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend domain
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/videos/generate")
async def generate_video(
    image: UploadFile = File(...),
    text: str = Form(..., min_length=1, max_length=1000),
    language: str = Form(...)
):
    if image.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, and WebP are allowed.")
    
    # Path traversal prevention: Generate a random UUID for the file name
    file_ext = image.filename.split(".")[-1]
    safe_filename = f"{uuid.uuid4().hex}.{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # Dispatch to background worker
    task = process_video_task.delay(safe_filename, text, language)
    
    return {"task_id": task.id, "status": "QUEUED"}

@app.get("/api/v1/videos/status/{task_id}")
async def get_status(task_id: str):
    task = celery_app.AsyncResult(task_id)
    if task.state == 'PENDING':
        return {"status": "QUEUED"}
    elif task.state == 'SUCCESS':
        return task.result
    elif task.state == 'FAILED':
        return {"status": "FAILED", "error": "An error occurred during rendering."}
    else:
        return {"status": task.state, "meta": task.info}

@app.get("/api/v1/videos/download/{filename}")
async def download_video(filename: str):
    # Strict validation to prevent directory traversal
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
        
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video not found or expired")
        
    return FileResponse(path=file_path, media_type='video/mp4', filename="generated_video.mp4")
