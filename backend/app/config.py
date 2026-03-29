from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/referral_engine"
    REWARD_DEPTH: int = 3
    REWARD_PERCENT: float = 10.0
    VELOCITY_LIMIT: int = 5
    VELOCITY_WINDOW_SECONDS: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
