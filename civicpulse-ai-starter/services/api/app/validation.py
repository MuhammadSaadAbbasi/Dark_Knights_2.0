from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError


ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


async def read_valid_image(photo: UploadFile, max_upload_mb: int) -> tuple[bytes, str]:
    if photo.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Upload a JPG, PNG, or WebP image.")

    contents = await photo.read()
    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    if len(contents) > max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"Image must be smaller than {max_upload_mb} MB.",
        )

    try:
        with Image.open(BytesIO(contents)) as image:
            actual_format = image.format
            image.verify()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid image.")

    expected_formats = {
        "image/jpeg": "JPEG",
        "image/png": "PNG",
        "image/webp": "WEBP",
    }
    if actual_format != expected_formats[photo.content_type]:
        raise HTTPException(status_code=415, detail="The image content does not match its type.")

    return contents, ALLOWED_TYPES[photo.content_type]


def safe_image_path(upload_dir: Path, report_id: str, extension: str) -> Path:
    upload_dir.mkdir(parents=True, exist_ok=True)
    path = (upload_dir / f"{report_id}{extension}").resolve()
    if path.parent != upload_dir.resolve():
        raise HTTPException(status_code=500, detail="Could not create a safe image path.")
    return path
