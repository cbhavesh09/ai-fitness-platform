import os

from dotenv import load_dotenv

load_dotenv()

class Settings:
    mongodb_uri: str = os.getenv(
        "MONGODB_URI",
        "mongodb://localhost:27017",
    )
    mongodb_database: str = os.getenv(
        "MONGODB_DATABASE",
        "ai_fitness",
    )
    jwt_secret: str = os.getenv(
        "JWT_SECRET",
        "",
    )
    model_paths: dict[str,str]= {}

settings = Settings()