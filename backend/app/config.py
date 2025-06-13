from pydantic_settings import BaseSettings

class Settings(BaseSettings):

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
    
    SERVER_KEY : str
    SSL_CERTFILE : str
    
    NOTION_CLIENT_ID: str
    NOTION_CLIENT_SECRET: str
    NOTION_REDIRECT_URI: str
    
    class Config:
        env_file = ".env"

settings = Settings()