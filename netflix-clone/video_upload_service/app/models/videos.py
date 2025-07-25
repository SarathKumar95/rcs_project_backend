import uuid
import enum
from sqlalchemy import (
    Column, String, Text, Enum, TIMESTAMP, JSON, ForeignKey, Integer, ARRAY, Boolean, DateTime
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class UploadStatusEnum(enum.IntEnum):
    pending = 0
    processing = 1
    ready = 2
    failed = 3

class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text)

    original_file_path = Column(Text, nullable=False)
    hls_path = Column(Text, nullable=True)

    upload_status = Column(Enum(UploadStatusEnum), default="pending", nullable=False)
    resolutions = Column(JSON, nullable=True)  # example: {"720p": "path/to.m3u8", ...}

    default_thumbnail = Column(Text, nullable=True)
    custom_thumbnail = Column(Text, nullable=True)

    duration = Column(Integer, nullable=True)  # seconds
    created_by = Column(UUID(as_uuid=True), nullable=False)  # User ID from user service
    cast = Column(ARRAY(Text), nullable=True)  # ["actor1", "actor2"]

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    is_invalid_user = Column(Boolean, default=False, nullable=False)

    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    