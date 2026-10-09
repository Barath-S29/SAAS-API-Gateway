from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized app configuration.

    Values are read from environment variables (or a .env file in local dev).
    Never hardcode secrets or connection strings here — this class only
    defines *where* config comes from, not what the values are.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres connection string, e.g.:
    # postgresql+psycopg://user:password@localhost:5432/gateway
    database_url: str


settings = Settings()