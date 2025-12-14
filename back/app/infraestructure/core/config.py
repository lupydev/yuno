from typing import Annotated, Any

from pydantic import AnyUrl, BeforeValidator, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    API: str = "/api"
    PROJECT_NAME: str = "Yuknow"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    REFRESH_SECRET_KEY: str = "dev-refresh-secret-key-change-in-production"
    OPENAI_MODEL: str = "gpt-4o-mini"
    AI_TIMEOUT_SECONDS: int = 10
    AI_MAX_RETRIES: int = 2

    # Feature Flags
    ENABLE_AI_NORMALIZATION: bool = True
    ENABLE_RULE_BASED_NORMALIZATION: bool = True

    ALGORITHM: str = "HS256"

    # Environment
    ENVIRONMENT: str = "development"

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        """
        Token expiration time based on environment:
        - development: 8 days (for easier testing)
        - production: 60 minutes (for security)
        """
        if self.ENVIRONMENT == "production":
            return 60  # 60 minutes in production
        return 60 * 24 * 8  # 8 days in development

    @property
    def REFRESH_TOKEN_EXPIRE_DAYS(self) -> int:
        """
        Refresh token expiration time based on environment:
        - development: 30 days
        - production: 7 days
        """
        if self.ENVIRONMENT == "production":
            return 7  # 7 days in production
        return 30  # 30 days in development

    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash-lite"
    AI_TIMEOUT_SECONDS: int = 10
    AI_MAX_RETRIES: int = 2

    # postgres
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    DATA_LAKE_URI: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []

    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS]

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
