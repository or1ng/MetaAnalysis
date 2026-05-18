from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from models import Base


class CleanLog(Base):
    __tablename__ = "clean_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)
    params_json = Column(JSON, default=dict)
    affected_rows = Column(Integer, default=0)
    result_summary = Column(Text, default="")
    snapshot_path = Column(String(500), default="")
    created_at = Column(DateTime, server_default=func.now())
