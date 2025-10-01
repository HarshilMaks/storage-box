from pydantic import Field, SecretStr, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )

    debug: bool = Field(default=False, alias="DEBUG")
    app_name: str = Field(default="Storage Box", alias="APP_NAME")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost/storage_box", 
        alias="DATABASE_URL"
    )

    aws_access_key_id: SecretStr = Field(default=SecretStr(""), alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: SecretStr = Field(default=SecretStr(""), alias="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    aws_s3_bucket: str = Field(default="", alias="AWS_S3_BUCKET")

    @validator('database_url')
    def validate_database_url(cls, v):
        if v and not v.startswith(('postgresql+asyncpg://', 'sqlite+aiosqlite://')):
            if v.startswith('postgresql://'):
                return v.replace('postgresql://', 'postgresql+asyncpg://', 1)
            elif v.startswith('sqlite://'):
                return v.replace('sqlite://', 'sqlite+aiosqlite://', 1)
        return v

    @property
    def aws_s3_public_url(self) -> str:
        if not self.aws_s3_bucket or not self.aws_region:
            return ""
        return f"https://{self.aws_s3_bucket}.s3.{self.aws_region}.amazonaws.com/"

    max_file_size: int = Field(default=1024 * 1024 * 1024, alias="MAX_FILE_SIZE")
    allowed_extensions: str = Field(
        default="jpg,jpeg,png,gif,pdf,txt,doc,docx,mp4,mp3,zip", 
        alias="ALLOWED_EXTENSIONS"
    )

    upload_dir: str = Field(default="uploads", alias="UPLOAD_DIR")
    temp_dir: str = Field(default="temp", alias="TEMP_DIR")

    def get_aws_credentials(self) -> dict[str, str]:
        return {
            "aws_access_key_id": self.aws_access_key_id.get_secret_value(),
            "aws_secret_access_key": self.aws_secret_access_key.get_secret_value(),
            "region_name": self.aws_region,
        }

    def get_allowed_extensions(self) -> list[str]:
        return [ext.strip().lower() for ext in self.allowed_extensions.split(",")]

    def is_file_allowed(self, filename: str) -> bool:
        if not filename or '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in self.get_allowed_extensions()

    def ensure_directories(self) -> None:
        for directory in [self.upload_dir, self.temp_dir]:
            os.makedirs(directory, exist_ok=True)


settings: Settings = Settings()

settings.ensure_directories()