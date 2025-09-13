from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import create_tables, close_db
from app.api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_tables()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="Storage Box API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend
IS_DEBUG = bool(getattr(settings, "DEBUG", False))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if IS_DEBUG else ["http://localhost:3000"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# API routes
app.include_router(router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Storage Box API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=IS_DEBUG
    )