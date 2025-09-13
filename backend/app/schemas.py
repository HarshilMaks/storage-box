from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List


# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


class UserResponse(UserBase):
    id: int
    is_active: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


# File Schemas
class FileResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    created_at: datetime
    user_id: int
    
    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    id: int
    filename: str
    message: str = "File uploaded successfully"
    size: int
    content_type: str


class FileListResponse(BaseModel):
    files: List[FileResponse]
    total: int


class FileDownloadResponse(BaseModel):
    filename: str
    download_url: str
    content_type: str
    size: int
    expires_in: int = 3600  # URL expires in 1 hour


# General Response Schemas
class MessageResponse(BaseModel):
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    success: bool = False