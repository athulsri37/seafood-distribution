from typing import Optional

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Secrets that were once published in this repository. A server must never sign tokens
# with them, because anyone could forge a login.
KNOWN_PUBLIC_SECRETS = {"change_this_secret_in_production"}
GENERATE_SECRET = 'python -c "import secrets; print(secrets.token_urlsafe(48))"'


class Settings(BaseSettings):
    """Read from environment variables, or from a `.env` file in the working directory.

    There are no defaults for credentials: the app refuses to start without them rather
    than fall back to a value that's public on GitHub.
    """

    model_config = SettingsConfigDict(env_file=".env")

    database_url: str
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    @field_validator("jwt_secret_key")
    @classmethod
    def _not_a_published_secret(cls, value: str) -> str:
        if value in KNOWN_PUBLIC_SECRETS:
            raise ValueError("is the old example value published on GitHub; generate a new one")
        return value


def load_settings(env_file: Optional[str] = ".env") -> Settings:
    try:
        return Settings(_env_file=env_file)
    except ValidationError as exc:
        problems = "\n".join(
            f"  - {str(error['loc'][0]).upper()}: "
            f"{'not set' if error['type'] == 'missing' else error['msg'].removeprefix('Value error, ')}"
            for error in exc.errors()
        )
        raise RuntimeError(
            "The backend can't start because its settings are incomplete:\n"
            f"{problems}\n"
            "Set them as environment variables or in backend/.env (copy backend/.env.example).\n"
            f"Generate a JWT secret with: {GENERATE_SECRET}"
        ) from None


settings = load_settings()
