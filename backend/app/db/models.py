from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, TIMESTAMP, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql.expression import null,text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship
import uuid

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

class NotionPage(Base):
    __tablename__ = "notion_pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("userauth.user_id", ondelete="CASCADE"), nullable=False)

    notion_page_id = Column(String, nullable=False, unique=True)
    notion_page_url = Column(Text)

    title = Column(String)
    notion_database_id = Column(String)
    
    last_synced_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))

    user = relationship("UserAuth", back_populates="notion_pages")
    blocks = relationship("NotionBlock", back_populates="page", cascade="all, delete")


class NotionBlock(Base):
    __tablename__ = "notion_blocks"
    __table_args__ = (UniqueConstraint("notion_block_id"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notion_block_id = Column(String, nullable=False, unique=True)
    notion_page_id = Column(String, ForeignKey("notion_pages.notion_page_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("userauth.user_id", ondelete="CASCADE"), nullable=False)

    block_type = Column(String)
    plain_text_content = Column(Text)

    source_url = Column(Text)
    source_title = Column(String)
    
    is_active = Column(Boolean, default=True)
    qdrant_point_id = Column(String, nullable=False, unique=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))

    # Relationships
    user = relationship("UserAuth", back_populates="notion_blocks")
    page = relationship("NotionPage", back_populates="blocks", primaryjoin="NotionBlock.notion_page_id == NotionPage.notion_page_id")