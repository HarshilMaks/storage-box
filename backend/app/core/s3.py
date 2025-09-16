from typing import Any, Dict
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import aioboto3  # type: ignore[reportMissingTypeStubs]
from botocore.exceptions import ClientError, BotoCoreError
from core.database import FileModel
from core.config import settings


async def get_s3_client():
    """Create and return async S3 client with configured credentials."""
    try:
        credentials = settings.get_aws_credentials()
        session = aioboto3.Session()
        return session.client('s3', **credentials)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create S3 client: {str(e)}")


async def upload_to_s3_and_save_db(
    key: str,
    contents: bytes,
    file: UploadFile,
    db: AsyncSession,
    file_size: int,
) -> Dict[str, Any]:
    """Upload file to S3 and save metadata to database."""
    
    async with await get_s3_client() as s3_client:
        try:
            content_type = file.content_type or "application/octet-stream"
            
            # Upload to S3
            await s3_client.put_object(
                Bucket=settings.aws_s3_bucket,
                Key=key,
                Body=contents,
                ContentType=content_type,
                ServerSideEncryption='AES256'
            )

            public_url = f"{settings.aws_s3_public_url}{key}"

            # Save DB entry
            db_file = FileModel(
                filename=key,
                original_filename=file.filename,
                file_size=file_size,
                content_type=content_type,
                public_url=public_url,
            )
            
            db.add(db_file)
            await db.commit()
            await db.refresh(db_file)

            return {
                "id": db_file.id,
                "filename": db_file.filename,
                "original_filename": db_file.original_filename,
                "size": db_file.file_size,
                "content_type": db_file.content_type,
                "public_url": db_file.public_url,
                "message": "File uploaded successfully",
            }
            
        except ClientError as e:
            await db.rollback()
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                raise HTTPException(status_code=500, detail="S3 bucket does not exist")
            elif error_code == 'AccessDenied':
                raise HTTPException(status_code=500, detail="Access denied to S3 bucket")
            else:
                raise HTTPException(status_code=500, detail=f"S3 error: {str(e)}")
                
        except BotoCoreError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"AWS connection error: {str(e)}")
            
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


async def delete_from_s3_and_db(file_id: int, db: AsyncSession) -> Dict[str, str]:
    """Delete file from S3 and remove from database."""
    
    try:
        # Get file record from database
        db_file = await db.get(FileModel, file_id)
        if not db_file:
            raise HTTPException(status_code=404, detail="File not found")
        
        async with await get_s3_client() as s3_client:
            # Delete from S3
            await s3_client.delete_object(
                Bucket=settings.aws_s3_bucket,
                Key=db_file.filename
            )
        
        # Delete from database
        await db.delete(db_file)
        await db.commit()
        
        return {"message": f"File {db_file.original_filename} deleted successfully"}
        
    except ClientError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"S3 deletion error: {str(e)}")
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


async def check_s3_connection() -> bool:
    """Check if S3 connection is working."""
    try:
        async with await get_s3_client() as s3_client:
            await s3_client.head_bucket(Bucket=settings.aws_s3_bucket)
            return True
    except Exception:
        return False