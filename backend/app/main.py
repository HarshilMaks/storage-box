from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from core.config import settings
from core.database import create_tables, close_db, get_db, FileModel
from core.s3 import upload_to_s3_and_save_db, check_s3_connection
from api import router
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield
    await close_db()


app = FastAPI(
    title="Storage Box API",
    version="1.0.0",
    lifespan=lifespan
)

IS_DEBUG = bool(getattr(settings, "debug", False))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if IS_DEBUG else ["http://localhost:3000"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/")
def root():
    return {"message": "Storage Box API is running"}


@app.get("/test-s3")
async def test_s3():
    is_connected = await check_s3_connection()
    return {
        "s3_connected": is_connected, 
        "bucket": settings.aws_s3_bucket,
        "region": settings.aws_region
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        contents = await file.read()
        file_size = len(contents)
        
        if file_size > settings.max_file_size:
            raise HTTPException(status_code=413, detail="File too large")
        
        if not settings.is_file_allowed(file.filename):
            raise HTTPException(status_code=400, detail="File type not allowed")
        
        key = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{file.filename}"
        
        result = await upload_to_s3_and_save_db(key, contents, file, db, file_size)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/files")
async def get_files(db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(FileModel).order_by(FileModel.created_at.desc())
        result = await db.execute(stmt)
        files = result.scalars().all()
        return {
            "files": [
                {
                    "id": f.id,
                    "filename": f.filename,
                    "original_filename": f.original_filename,
                    "size": f.file_size,
                    "content_type": f.content_type,
                    "public_url": f.public_url,
                    "created_at": f.created_at.isoformat(),
                }
                for f in files
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get files: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=IS_DEBUG
    )