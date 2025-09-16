from fastapi import APIRouter, UploadFile, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from schemas import FileUploadResponse, FileDownloadResponse
from services.file_service import upload_file, retrieve_file
from core.database import get_db

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload", response_model=FileUploadResponse)
async def upload(file: UploadFile, db: AsyncSession = Depends(get_db)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    return await upload_file(file, db)


@router.get("/download/{file_name}", response_model=FileDownloadResponse)
async def download(file_name: str, db: AsyncSession = Depends(get_db)):
    try:
        return await retrieve_file(file_name, db)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")