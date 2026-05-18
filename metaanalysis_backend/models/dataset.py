from sqlalchemy import Column, Integer, String, BigInteger, Enum, DateTime, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from models import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    file_type = Column(Enum("xlsx", "csv", "pdf", "txt"), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    row_count = Column(Integer, default=0)
    col_count = Column(Integer, default=0)
    columns_json = Column(JSON, default=list)
    is_cleaned = Column(Integer, default=0)
    cleaned_path = Column(String(500), default="")
    version = Column(Integer, default=1)
    status = Column(Enum("processing", "ready", "error"), default="processing")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
