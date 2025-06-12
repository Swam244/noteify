from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    DATABASE_HOST : str
    DATABASE_USER : str
    DATABASE_NAME : str
    DATABASE_PASSWORD : str
    
    SECRET_KEY : str
    ALGORITHM : str
    ACCESS_TOKEN_EXPIRE_MINUTES : int
    
    SQLALCHEMY_DATABASE_URL : str
    SQLALCHEMY_DATABASE_TEST_URL : str
    
    SERVER_KEY : str
    SSL_CERTFILE : str
    
    class Config:
        env_file = ".env"

settings = Settings()