from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from models import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    task_type = Column(Enum("ai_chat", "statistic", "chart", "clean", "auto_explore"), nullable=False)
    config_json = Column(JSON, default=dict)
    status = Column(Enum("pending", "running", "completed", "failed"), default="pending")
    result_json = Column(JSON, default=dict)
    error_msg = Column(Text, default="")
    duration_sec = Column(Float, default=0)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
