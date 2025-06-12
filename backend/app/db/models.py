from .database import Base
from sqlalchemy import Column,Integer,String,Boolean,ForeignKey
from sqlalchemy.sql.expression import null,text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship

class UserAuth(Base):
    __tablename__ = "userauth"
    
    user_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    username = Column(String, nullable=False)
    email = Column(String, primary_key=False, unique=True, nullable=False)
    password = Column(String, nullable=False)
    notionConnected = Column(Boolean, default=False, nullable=False)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    is_logged_in = Column(Boolean,default=False)
    
    notionid = relationship("NotionID", back_populates="user")

class NotionID(Base):
    __tablename__ = "notionid"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("userauth.user_id"), nullable=False)
    token = Column(String, nullable=False)
    user = relationship("UserAuth", back_populates="notionid")
