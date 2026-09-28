"""
SQLite models for sites, visits, and findings history.

Phase 1: SQLite via SQLAlchemy. Designed to migrate to PostgreSQL later
without changing calling code.
"""
import os
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/audit.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True)
    site_code = Column(String, unique=True, nullable=False)
    region = Column(String)


class Visit(Base):
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, nullable=False)
    visit_date = Column(DateTime, default=datetime.utcnow)


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True)
    visit_id = Column(Integer, nullable=False)
    asset_category = Column(String)
    finding_text = Column(String)
    priority = Column(String)
    status = Column(String, default="open")  # open | closed
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
