from fastapi import UploadFile, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from core.config import settings
from core.database import get_db, FileModel
from core.s3 import upload_to_s3_and_save_db
from schemas import FileUploadResponse, FileDownloadResponse


async def upload_file(file: UploadFile, db: AsyncSession = Depends(get_db)) -> FileUploadResponse:
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        contents = await file.read()
        file_size = len(contents)
        
        if file_size > settings.max_file_size:
            raise HTTPException(status_code=413, detail=f"File too large. Max size: {settings.max_file_size} bytes")
        
        if not settings.is_file_allowed(file.filename):
            raise HTTPException(status_code=400, detail="File type not allowed")
        
        key = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{file.filename}"
        
        result = await upload_to_s3_and_save_db(key, contents, file, db, file_size)
        
        return FileUploadResponse(
            id=result["id"],
            filename=result["filename"],
            size=result["size"],
            content_type=result["content_type"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


async def retrieve_file(file_name: str, db: AsyncSession = Depends(get_db)) -> FileDownloadResponse:
    try:
        stmt = select(FileModel).where(FileModel.filename == file_name)
        result = await db.execute(stmt)
        file_record = result.scalar_one_or_none()
        
        if not file_record:
            raise FileNotFoundError(f"File {file_name} not found")
        
        return FileDownloadResponse(
            filename=file_record.original_filename,
            download_url=file_record.public_url or "File not available in S3",
            content_type=file_record.content_type,
            size=file_record.file_size
        )
        
    except FileNotFoundError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve file: {str(e)}")