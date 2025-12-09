from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from config.db_schema import Base


class VX11Event(Base):
    __tablename__ = "vx11_events"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, server_default=func.now())
    module = Column(String(50), index=True)
    level = Column(String(20), default="info")
    message = Column(Text)
    payload = Column(JSON, default={})


class QueenTask(Base):
    __tablename__ = "queen_tasks"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, index=True)
    task_type = Column(String(50))
    status = Column(String(20), default="pending")
    priority = Column(Integer, default=1)
    payload = Column(JSON, default={})
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Ant(Base):
    __tablename__ = "ants"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer)
    ant_type = Column(String(50))
    status = Column(String(20), default="pending")
    payload = Column(JSON, default={})
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


# Create tables if not exist (safe for tests)
Base.metadata.create_all(bind=engine)
