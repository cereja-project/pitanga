import os

class Settings:
    # Database
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT")
    NUM_WORKERS = int(os.getenv("NUM_WORKERS", 4))
    DB_QUERY_BATCH_SIZE = int(os.getenv("DB_QUERY_BATCH_SIZE", -1))
