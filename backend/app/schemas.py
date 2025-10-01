from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    id: int
    filename: str
    size: int
    content_type: str


class FileDownloadResponse(BaseModel):
    filename: str
    download_url: str
    content_type: str
    size: int
