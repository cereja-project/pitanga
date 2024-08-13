import os


class Settings:
    # Database
    AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    ENVIRONMENT = os.getenv("ENVIRONMENT")
    SQS_REGION_NAME = os.getenv("SQS_REGION_NAME")
    SQS_ENDPOINT_URL = os.getenv("SQS_ENDPOINT_URL")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT")
    NUM_WORKERS = int(os.getenv("NUM_WORKERS", 4))
    DB_QUERY_BATCH_SIZE = int(os.getenv("DB_QUERY_BATCH_SIZE", -1))
