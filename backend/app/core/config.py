from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )
    
    # App Settings
    debug: bool = Field(default=False)
    app_name: str = Field(default="Storage Box")
    
    # Database
    database_url: str = Field(default="", description="PostgreSQL database URL")
    
    # AWS S3
    aws_access_key_id: SecretStr = Field(default=SecretStr(""))
    aws_secret_access_key: SecretStr = Field(default=SecretStr(""))
    aws_region: str = Field(default="us-east-1")
    aws_s3_bucket: str = Field(default="")
    
    # File Settings
    max_file_size: int = Field(default=1024 * 1024 * 1024)  # 1GB
    allowed_extensions: str = Field(default="jpg,jpeg,png,pdf,txt,mp4")
    
    # Helper Methods
    def get_aws_credentials(self) -> dict[str, str]:
        """Get AWS credentials as plain strings."""
        return {
            "aws_access_key_id": self.aws_access_key_id.get_secret_value(),
            "aws_secret_access_key": self.aws_secret_access_key.get_secret_value(),
            "region_name": self.aws_region
        }
    
    def get_allowed_extensions(self) -> list[str]:
        """Get allowed file extensions as list."""
        return [ext.strip().lower() for ext in self.allowed_extensions.split(",")]


# Global settings instance
settings: Settings = Settings()