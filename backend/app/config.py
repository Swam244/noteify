from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    BASE_URL : str

    DATABASE_HOST : str
    DATABASE_USER : str
    DATABASE_NAME : str
    DATABASE_PASSWORD : str
    DATABASE_PORT : int
    
    SECRET_KEY : str
    ALGORITHM : str
    ACCESS_TOKEN_EXPIRE_MINUTES : int
    REFRESH_TOKEN_EXPIRY : int
    
    SQLALCHEMY_DATABASE_URL : str
    SQLALCHEMY_DATABASE_TEST_URL : str
    
    TOKEN_KEY : str
    
    NOTION_CLIENT_ID: str
    NOTION_CLIENT_SECRET: str
    NOTION_REDIRECT_URI: str
    
    QDRANT_URL: str
    QDRANT_API_KEY : str
    VECTOR_DB_NAME : str
    VECTOR_DB_NAME_TEST : str

    GROQ_API_KEY : str
    GROQ_MODEL : str

    COHERE_API_KEY : str
    
    APPWRITE_SECRET : str
    BUCKET_ID : str
    PROJECT_ID : str
    ENDPOINT : str

    class Config:
        env_file = ".env"

settings = Settings()