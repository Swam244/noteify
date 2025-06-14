from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from pydantic.types import conint


class registerRequest(BaseModel):
    username : str
    email: EmailStr
    password: str

class registerResponse(BaseModel):
    info: str
    username : str
    email: EmailStr
    created_at: str


class getLoginInfo(BaseModel):
    username: str
    email : str
    notionConnected: bool
    preference : str

class loginResponse(getLoginInfo):
    pass

class logoutResponse(BaseModel):
    info: str

class loginRequest(BaseModel):
    email : EmailStr
    password : str

class preferenceData(BaseModel):
    preference : str

class Notes(BaseModel):
    text : str

class Category(BaseModel):
    category : str