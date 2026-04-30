import os
import csv
from uuid import uuid4
from datetime import datetime, timedelta
import pytz
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import text
from app.database import engine
from app.models import (
    StoreTimeZone, BusinessHour, StoreStatus,
    ReportTracker, ReportStatusEnum, Report
)


# Determine a fixed reports directory relative to project root
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# New session factory for background tasks
db_session_factory = sessionmaker(bind=engine)


def generate_report_for_store(store_id: int, db: Session) -> Report:
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

    # Lookup timezone, default to America/Chicago
    tz_entry = db.query(StoreTimeZone).filter(StoreTimeZone.store_id == store_id).first()
    tz_str = tz_entry.timezone_str if tz_entry else 'America/Chicago'
    store_tz = pytz.timezone(tz_str)

    # Lookup business hours, default to full-day 24x7
    bh_entries = db.query(BusinessHour).filter(BusinessHour.store_id == store_id).all()
    bh_by_day = {}
    if not bh_entries:
        for d in range(7):
            bh_by_day[d] = [(datetime.min.time(), datetime.max.time())]
    else:
        for bh in bh_entries:
            bh_by_day.setdefault(bh.day, []).append((bh.start_time_local, bh.end_time_local))

    # Period definitions: (start_bound, up_field, down_field, unit_sec)
    periods = {
        'hour': (now_utc - timedelta(hours=1), 'uptime_last_hour', 'downtime_last_hour', 60),
        'day':  (now_utc - timedelta(days=1),  'uptime_last_day',  'downtime_last_day',  3600),
        'week': (now_utc - timedelta(weeks=1), 'uptime_last_week', 'downtime_last_week', 3600)
    }

    accum = {k: {'up': 0, 'down': 0} for k in periods}
    last_ts = {k: periods[k][0] for k in periods}
    last_status = {k: None for k in periods}

    # Query all statuses for the last week
    statuses = db.query(StoreStatus) \
        .filter(
            StoreStatus.store_id == store_id,
            StoreStatus.timestamp_utc >= now_utc - timedelta(weeks=1),
            StoreStatus.timestamp_utc <= now_utc
        ) \
        .order_by(StoreStatus.timestamp_utc).all()

    for entry in statuses:
        ts_utc = entry.timestamp_utc.replace(tzinfo=pytz.utc)
        ts_local = ts_utc.astimezone(store_tz)
        weekday = ts_local.weekday()
        for key, (start_bound, up_field, down_field, unit_sec) in periods.items():
            if ts_utc < start_bound:
                continue
            # Only count if within business hours
            if any(r[0] <= ts_local.time() <= r[1] for r in bh_by_day.get(weekday, [])):
                delta = (ts_utc - last_ts[key]).total_seconds()
                if last_status[key] == 'active':
                    accum[key]['up'] += delta
                else:
                    accum[key]['down'] += delta
                last_ts[key] = ts_utc
                last_status[key] = entry.status

    # Final segment until now
    for key, (start_bound, up_field, down_field, unit_sec) in periods.items():
        delta = (now_utc - last_ts[key]).total_seconds()
        if last_status[key] == 'active':
            accum[key]['up'] += delta
        else:
            accum[key]['down'] += delta

    # Create Report with converted units
    return Report(
        store_id=store_id,
        uptime_last_hour=int(accum['hour']['up'] // periods['hour'][3]),
        downtime_last_hour=int(accum['hour']['down'] // periods['hour'][3]),
        uptime_last_day=int(accum['day']['up'] // periods['day'][3]),
        downtime_last_day=int(accum['day']['down'] // periods['day'][3]),
        uptime_last_week=int(accum['week']['up'] // periods['week'][3]),
        downtime_last_week=int(accum['week']['down'] // periods['week'][3]),
        report_generated_at=datetime.utcnow()
    )


def generate_and_save_report(report_id: str):
    db = db_session_factory()
    try:
        tracker = db.query(ReportTracker).filter(ReportTracker.report_id == report_id).first()
        if not tracker:
            return

        store_ids = [r[0] for r in db.execute(text("SELECT DISTINCT store_id FROM store_status")).fetchall()]
        rows = []
        for sid in store_ids:
            rep = generate_report_for_store(sid, db)
            rows.append([
                sid,
                rep.uptime_last_hour,
                rep.downtime_last_hour,
                rep.uptime_last_day,
                rep.downtime_last_day,
                rep.uptime_last_week,
                rep.downtime_last_week,
            ])

        # Write CSV
        fname = f"{report_id}.csv"
        path = REPORTS_DIR / fname
        with path.open('w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["store_id","uptime_last_hour","downtime_last_hour","uptime_last_day","downtime_last_day","uptime_last_week","downtime_last_week"])
            writer.writerows(rows)

        # Update tracker
        tracker.status = ReportStatusEnum.complete
        tracker.file_path = str(path)
        db.commit()
    except Exception:
        db.rollback()
        if tracker:
            tracker.status = ReportStatusEnum.failed
            tracker.file_path = None
            db.commit()
    finally:
        db.close()