from app.config import settings
import hashlib
import datetime
import jwt
from fastapi import Request, HTTPException, Response, Cookie, Depends
from app.db.models import UserAuth
from sqlalchemy.orm import Session
from app.db.models import UserAuth, NotionID
from app.db.database import get_db
import logging
import inflect

logger = logging.getLogger(__name__)

p = inflect.engine()

def normalizeCategoryName(name: str) -> str:
    name = name.strip().lower()
    name = p.singular_noun(name) or name 
    return name.upper()  


def md5_hash(data):
    md5_hash = hashlib.md5(data.encode())
    return md5_hash.hexdigest()


def generate_jwt_token(user, is_refresh=False):
    expiry_minutes = settings.REFRESH_TOKEN_EXPIRY if is_refresh else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expiry = datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=int(expiry_minutes))
    payload = {
        "user_id": user.user_id,
        "email": user.email,
        "exp": expiry,
        "is_refresh": is_refresh
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def validate_token(token):
    """Validate JWT token and return payload if valid."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        logger.info("Token validated successfully")
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        return None


async def Autherize(request: Request, response: Response, jwt: str = Cookie(None), refresh_token: str = Cookie(None), db: Session = Depends(get_db)) -> UserAuth:
    if not jwt:
        logger.warning("No JWT provided in request")
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = validate_token(jwt)
    if payload:
        user_id = payload["user_id"]
        user = db.query(UserAuth).filter(UserAuth.user_id == user_id).first()
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        logger.info(f"User authorized: {user.email}")
        return user

    if not refresh_token:
        logger.warning("No refresh token provided")
        raise HTTPException(status_code=401, detail="Session expired")

    refresh_payload = validate_token(refresh_token)
    if not refresh_payload:
        logger.warning("Invalid refresh token")
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = refresh_payload["user_id"]
    user = db.query(UserAuth).filter(UserAuth.user_id == user_id).first()
    if not user:
        logger.warning(f"User not found with refresh token: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    new_token = generate_jwt_token(user)
    response.set_cookie(
        key="jwt",
        value=new_token,
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=3600
    )
    logger.info(f"User re-authorized with refresh token: {user.email}")
    return user