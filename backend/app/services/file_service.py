from datetime import datetime, timezone
from fastapi import UploadFile
from app.schemas import FileUploadResponse, FileDownloadResponse


async def upload_file(file: UploadFile) -> FileUploadResponse:
    file_name = file.filename or f"upload-{datetime.now(timezone.utc).timestamp()}"
    size: int | None = None
    try:
        content = await file.read()
        size = len(content)
    except Exception:
        size = None
    return FileUploadResponse(
        id=0,
        filename=file_name,
        size=size or 0,
        content_type=file.content_type or "application/octet-stream",
    )


async def retrieve_file(file_name: str) -> FileDownloadResponse:
    if not file_name:
        raise FileNotFoundError
    url = f"https://example.com/files/{file_name}"
    return FileDownloadResponse(
        filename=file_name,
        download_url=url,
        content_type="application/octet-stream",
        size=0,
    )
