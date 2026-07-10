from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str

    tmdb_api_key: str
    tmdb_base_url: str = "https://api.themoviedb.org/3"
    tmdb_image_url: str

    access_token_expire_minutes: int = 30
    secret_key: str
    algorithm: str = "HS256"

    refresh_token_expire_days: int = 30
    refresh_cookie_secure: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
