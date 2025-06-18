from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, TIMESTAMP, text, UniqueConstraint,Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.expression import null,text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship
import uuid
import enum

class Preferences(enum.Enum):
    RAW = "RAW"
    CATEGORIZED_AND_ENRICHED = "CATEGORIZED_AND_ENRICHED"
    CATEGORIZED_AND_RAW = "CATEGORIZED_AND_RAW"


class UserAuth(Base):
    __tablename__ = "userauth"
    
    user_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    username = Column(String, nullable=False)
    email = Column(String, primary_key=False, unique=True, nullable=False)
    password = Column(String, nullable=False)
    notionConnected = Column(Boolean, default=False, nullable=False)
    preference = Column(Enum(Preferences), nullable=False, default=Preferences.CATEGORIZED_AND_ENRICHED)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    is_logged_in = Column(Boolean,default=False)
    

    notionid = relationship("NotionID", back_populates="user")
    notion_pages = relationship("NotionPage", back_populates="user", cascade="all, delete")
    notion_blocks = relationship("NotionBlock", back_populates="user", cascade="all, delete")
    user_categories = relationship("UserCategories",back_populates="user",cascade="all, delete")
    images = relationship("UserImages", back_populates="user", cascade="all, delete")


class NotionID(Base):
    __tablename__ = "notionid"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("userauth.user_id"), nullable=False)
    token = Column(String, nullable=False)
    database_id = Column(String,default="DUMMY")

    user = relationship("UserAuth", back_populates="notionid")



class NotionPage(Base):
    __tablename__ = "notion_pages"

    user_id = Column(Integer,ForeignKey("userauth.user_id", ondelete="CASCADE"),primary_key=True,nullable=False)
    title = Column(String,primary_key=True)
    notion_page_id = Column(String, nullable=False, unique=True)
    notion_page_url = Column(Text)
    notion_database_id = Column(String)    
    # notes_block_id= Column(String)   
    # references_block_id= Column(String)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))


    user = relationship("UserAuth", back_populates="notion_pages")
    blocks = relationship("NotionBlock", back_populates="page", cascade="all, delete")



class NotionBlock(Base):
    __tablename__ = "notion_blocks"
    __table_args__ = (UniqueConstraint("notion_block_id"),)

    id = Column(Integer ,primary_key=True,autoincrement=True,nullable=False)
    notion_block_id = Column(String, nullable=False, unique=True)
    notion_page_id = Column(String, ForeignKey("notion_pages.notion_page_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("userauth.user_id", ondelete="CASCADE"), nullable=False)
    block_type = Column(String)
    plain_text_content = Column(Text)
    source_url = Column(Text)
    is_active = Column(Boolean, default=True)
    qdrant_point_id = Column(String, nullable=False, unique=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))


    user = relationship("UserAuth", back_populates="notion_blocks")
    page = relationship("NotionPage", back_populates="blocks", primaryjoin="NotionBlock.notion_page_id == NotionPage.notion_page_id")


class UserCategories(Base):
    __tablename__ = "user_categories"

    id = Column(Integer,primary_key=True,autoincrement=True)
    user_id = Column(Integer,ForeignKey("userauth.user_id", ondelete="CASCADE"),nullable=False)
    category_name = Column(String,nullable=False) # always insert in uppercase letters to avoid same categories.

    user = relationship("UserAuth", back_populates="user_categories")


class UserImages(Base):
    __tablename__ = "user_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("userauth.user_id", ondelete="CASCADE"), nullable=False)
    image_id = Column(String, nullable=False, unique=True)  
    appwrite_link = Column(String,nullable=False)
    uploaded_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    user = relationship("UserAuth", back_populates="images")