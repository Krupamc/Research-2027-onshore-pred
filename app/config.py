from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
#import env

class Settings(BaseSettings):
    APP_NAME: str = "Buoy API"
    API_KEY: str
    URL_DATABASE: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

       
API_KEY="smth"
URL_DATABASE = "postgresql+psycopg://buoy_user:H!ldeR$m2]@192.168.1.45:5432/buoy_db"

settings = Settings()