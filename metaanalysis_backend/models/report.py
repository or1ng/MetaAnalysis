from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from models import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    title = Column(String(200), nullable=False)
    template = Column(Enum("business", "academic", "simple"), default="business")
    format = Column(Enum("docx", "pdf", "pptx"), nullable=False)
    content_json = Column(JSON, default=dict)
    file_path = Column(String(500), default="")
    file_size = Column(Integer, default=0)
    status = Column(Enum("generating", "ready", "failed"), default="generating")
    created_at = Column(DateTime, server_default=func.now())
