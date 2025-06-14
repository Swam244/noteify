# app/routers/auth.py
from fastapi import APIRouter,Depends,Response
from fastapi import status, HTTPException
from app.db.models import UserAuth
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.utils import Autherize,generate_jwt_token
from app.db.schemas import *
from app.config import settings
from app.password_utils import verify_hash,generate_hash
import logging
from sqlalchemy.exc import DataError

router = APIRouter(prefix="/users",tags=['Users'])
logger = logging.getLogger(__name__)


@router.post("/register",status_code=status.HTTP_201_CREATED,response_model=registerResponse)
def register(data : registerRequest ,db : Session=Depends(get_db)):
    logger.info(f"Register attempt for email: {data.email}")
    if db.query(UserAuth).filter(UserAuth.email == data.email).first():
        logger.warning(f"Registration failed: Email already exists: {data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )

    hash_pass = generate_hash(data.password)

    new_user = UserAuth(
        username=data.username,
        email=data.email,
        password=hash_pass
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"User registered: {new_user.email}")
    return registerResponse(
        info="Registered successfully.",
        username=new_user.username,
        email=new_user.email,
        created_at=str(new_user.created_at)
    )


@router.get("/login",response_model=getLoginInfo,status_code=status.HTTP_200_OK)
def getUserInfo(db : Session=Depends(get_db), user : UserAuth = Depends(Autherize)):
    return user



@router.post("/login", status_code=status.HTTP_200_OK, response_model=loginResponse)
def login(data: loginRequest,response: Response,db: Session = Depends(get_db)):
    logger.info(f"Login attempt for email: {data.email}")
    user = db.query(UserAuth).filter(UserAuth.email == data.email).first()
    
    if not user:
        logger.warning(f"Login failed: Invalid email {data.email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not verify_hash(data.password,user.password):
        logger.warning(f"Login failed: Invalid password for {data.email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    access_token = generate_jwt_token(user, is_refresh=False)
    refresh_token = generate_jwt_token(user, is_refresh=True)

    user.is_logged_in = True
    db.commit()

    response.set_cookie(
        key="jwt",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=60 * int(settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=60 * int(settings.REFRESH_TOKEN_EXPIRY)
    )
    logger.info(f"User logged in: {user.email}")
    return loginResponse(
        username=user.username,
        email=user.email,
        notionConnected=user.notionConnected,
        preference=user.preference
    )

@router.post("/logout",status_code=status.HTTP_200_OK,response_model=logoutResponse)
def logout(response : Response, user: UserAuth = Depends(Autherize),db: Session = Depends(get_db)):
    logger.info(f"Logout for user: {user.email}")
    user.is_logged_in = False
    db.commit()
    response.delete_cookie(key="jwt")
    response.delete_cookie(key="refresh_token")
    return logoutResponse(info="Logged out Successfully")


@router.patch("/preference",status_code=status.HTTP_200_OK,response_model=preferenceData)
def preference(data : preferenceData, user : UserAuth = Depends(Autherize), db : Session = Depends(get_db)):
    logger.info(f"Changing preference for {user.user_id} from {user.preference} to {data.preference}")
    try:
        user.preference = data.preference
        db.commit()
    except DataError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Valid choices are 1.RAW 2.CATEGORIZED_AND_ENRICHED 3.CATEGORIZED_AND_RAW")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"{e}") 
    
    return preferenceData(preference=str(user.preference.value))
