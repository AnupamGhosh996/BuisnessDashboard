import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False)
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    file_size_bytes = Column(Integer, default=0)
    is_active = Column(Boolean, default=False)
    is_cleaned = Column(Boolean, default=False)
    parent_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    metadata_json = Column(Text, nullable=True)  # stores schema, column types, mappings
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="datasets")
    conversations = relationship("Conversation", back_populates="dataset", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="dataset", cascade="all, delete-orphan")
