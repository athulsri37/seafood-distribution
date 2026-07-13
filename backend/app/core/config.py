from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://seafood:seafood_dev_pw@localhost:5432/seafood_distribution"
    jwt_secret_key: str = "change_this_secret_in_production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
