from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class LogBase(BaseModel):
    level: str
    service: str
    message: str
    error_code: Optional[str] = None
    stack_trace: Optional[str] = None

class LogCreate(LogBase):
    pass

class Log(LogBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class AlertBase(BaseModel):
    severity: str
    message: str
    log_id: int

class AlertCreate(AlertBase):
    pass

class Alert(AlertBase):
    id: int
    timestamp: datetime
    is_resolved: bool
    resolved_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class AnomalyMetricBase(BaseModel):
    metric_name: str
    value: float
    threshold: float

class AnomalyMetricCreate(AnomalyMetricBase):
    pass

class AnomalyMetric(AnomalyMetricBase):
    id: int
    timestamp: datetime
    is_anomaly: bool

    class Config:
        orm_mode = True

class LogAnalytics(BaseModel):
    total_logs: int
    error_count: int
    warning_count: int
    error_rate: float
    recent_errors: List[Log]

class AlertSummary(BaseModel):
    total_alerts: int
    active_alerts: int
    alerts_by_severity: dict
    recent_alerts: List[Alert]
