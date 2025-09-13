from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.file_service import upload_file, retrieve_file
from app.schemas import FileResponse

router = APIRouter()


@router.post("/upload", response_model=FileResponse, summary="Upload a file")
async def upload(file: UploadFile = File(...)) -> FileResponse:
    try:
        return await upload_file(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/retrieve/{file_name}", response_model=FileResponse, summary="Retrieve a file URL")
async def retrieve(file_name: str) -> FileResponse:
    try:
        return await retrieve_file(file_name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File '{file_name}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieve failed: {str(e)}")