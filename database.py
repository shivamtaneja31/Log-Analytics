from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Create SQLite database engine
SQLALCHEMY_DATABASE_URL = "sqlite:///./logs.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# Create declarative base
Base = declarative_base()

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String)  # INFO, WARNING, ERROR, CRITICAL
    service = Column(String)  # Service/component that generated the log
    message = Column(String)
    error_code = Column(String, nullable=True)
    stack_trace = Column(String, nullable=True)

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    severity = Column(String)  # HIGH, MEDIUM, LOW
    message = Column(String)
    log_id = Column(Integer)  # Reference to the log that triggered the alert
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

class AnomalyMetrics(Base):
    __tablename__ = "anomaly_metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metric_name = Column(String)  # e.g., "error_rate", "response_time"
    value = Column(Float)
    threshold = Column(Float)
    is_anomaly = Column(Boolean, default=False)

# Create database tables
Base.metadata.create_all(bind=engine)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
