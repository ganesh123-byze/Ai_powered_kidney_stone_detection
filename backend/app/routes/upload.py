"""
Kidney Ultrasound Classification - Upload Route
API endpoint for image uploads.
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from loguru import logger

from app.schemas.response import UploadResponse, ErrorResponse


router = APIRouter(prefix="/upload", tags=["Upload"])

# Configure upload directory
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "data/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_file(file: UploadFile) -> tuple[bool, Optional[str]]:
    """
    Validate uploaded file.
    
    Returns:
        (is_valid, error_message)
    """
    # Check filename
    if not file.filename:
        return False, "No filename provided"
    
    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check content type
    if file.content_type and not file.content_type.startswith("image/"):
        return False, f"Invalid content type: {file.content_type}"
    
    return True, None


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename while preserving extension."""
    ext = Path(original_filename).suffix.lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"kidney_{timestamp}_{unique_id}{ext}"


@router.post(
    "",
    response_model=UploadResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    summary="Upload an ultrasound image",
    description="Upload a kidney ultrasound image for later prediction"
)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload"),
    subfolder: Optional[str] = Query(
        None, 
        description="Optional subfolder within upload directory"
    )
):
    """
    Upload an ultrasound image.
    
    - Accepts common image formats (JPEG, PNG, BMP, TIFF)
    - Maximum file size: 10MB
    - Returns the path where file was saved
    """
    # Validate file
    is_valid, error_msg = validate_file(file)
    if not is_valid:
        logger.warning(f"Invalid upload attempt: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    try:
        # Read file content
        content = await file.read()
        
        # Check file size
        file_size = len(content)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Generate unique filename
        unique_filename = generate_unique_filename(file.filename)
        
        # Determine save path
        if subfolder:
            save_dir = UPLOAD_DIR / subfolder
            save_dir.mkdir(parents=True, exist_ok=True)
        else:
            save_dir = UPLOAD_DIR
        
        save_path = save_dir / unique_filename
        
        # Save file
        with open(save_path, "wb") as f:
            f.write(content)
        
        logger.info(f"File uploaded: {save_path} ({file_size} bytes)")
        
        return UploadResponse(
            success=True,
            filename=unique_filename,
            file_path=str(save_path),
            file_size=file_size,
            message="File uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        await file.close()


@router.delete(
    "/{filename}",
    response_model=dict,
    summary="Delete an uploaded file",
    description="Delete a previously uploaded file"
)
async def delete_uploaded_file(filename: str):
    """Delete an uploaded file."""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        os.remove(file_path)
        logger.info(f"File deleted: {filename}")
        return {"success": True, "message": f"File {filename} deleted"}
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.get(
    "/list",
    response_model=dict,
    summary="List uploaded files",
    description="List all files in the upload directory"
)
async def list_uploaded_files(
    limit: int = Query(100, ge=1, le=1000, description="Maximum files to return")
):
    """List uploaded files."""
    try:
        files = []
        for f in UPLOAD_DIR.iterdir():
            if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS:
                files.append({
                    "filename": f.name,
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                })
                if len(files) >= limit:
                    break
        
        return {
            "success": True,
            "count": len(files),
            "files": files
        }
    except Exception as e:
        logger.error(f"List error: {e}")
        raise HTTPException(status_code=500, detail=f"List failed: {str(e)}")
