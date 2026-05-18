from sqlalchemy import Column, Integer, BigInteger, String, Enum, DateTime
from sqlalchemy.sql import func
from models import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, default="")
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("free", "pro", "admin"), default="free")
    avatar_url = Column(String(500), default="")
    storage_used = Column(Integer, default=0)
    storage_limit = Column(Integer, default=536_870_912)  # 512MB
    status = Column(Enum("active", "disabled"), default="active")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
