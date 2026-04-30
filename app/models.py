from app.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Time, Enum
import enum

class BusinessHour(Base):
    __tablename__= "menu_hours"
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, index=True)
    day = Column(Integer)
    start_time_local = Column(Time)
    end_time_local = Column(Time)

class StoreStatus(Base):
    __tablename__= "store_status"
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, index=True)
    timestamp_utc = Column(DateTime)
    status = Column(String)

class StoreTimeZone(Base):
    __tablename__ = "store_timezones"
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, unique=True, index=True)
    timezone_str = Column(String)

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, index=True)
    uptime_last_hour = Column(Integer)      # minutes
    uptime_last_day = Column(Integer)       # hours
    uptime_last_week = Column(Integer)      # hours
    downtime_last_hour = Column(Integer)    # minutes
    downtime_last_day = Column(Integer)     # hours
    downtime_last_week = Column(Integer)    # hours
    report_generated_at = Column(DateTime)

class ReportStatusEnum(enum.Enum):
    running = "Running"
    complete = "Complete"
    failed = "Failed"

class ReportTracker(Base):
    __tablename__ = "report_tracker"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String, unique=True, index=True)
    status = Column(Enum(ReportStatusEnum), default=ReportStatusEnum.running)
    file_path = Column(String, nullable=True)