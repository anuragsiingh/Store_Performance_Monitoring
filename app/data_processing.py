import os
import uuid
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import pytz

from app import models

# To Ensure if the reports folder exists
os.makedirs("reports", exist_ok=True)


def convert_to_local_time(utc_time: datetime, timezone_str: str) -> datetime:
    """Convert UTC time to local timezone"""
    try:
        local_tz = pytz.timezone(timezone_str)
        return utc_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
    except Exception:
        return utc_time  # fallback to UTC if error


def get_local_business_hours(business_hours_df, timezone_str):
    """Convert business hours to datetime ranges"""
    result = {}
    for day in range(7):  # 0 = Monday, 6 = Sunday
        day_hours = business_hours_df[business_hours_df['day'] == day]
        if day_hours.empty:
            result[day] = []
            continue
        ranges = []
        for _, row in day_hours.iterrows():
            try:
                start = datetime.strptime(str(row['start_time_local']), "%H:%M:%S").time()
                end = datetime.strptime(str(row['end']), "%H:%M:%S").time()
                ranges.append((start, end))
            except Exception:
                pass
        result[day] = ranges
    return result


def is_within_business_hours(local_dt: datetime, business_ranges):
    """Check if a datetime falls within any of the day's business hour ranges"""
    day_of_week = local_dt.weekday()
    time = local_dt.time()
    for start, end in business_ranges.get(day_of_week, []):
        if start <= time <= end:
            return True
    return False


def generate_report(db: Session) -> str:
    """Generate uptime/downtime report and return report_id"""

    # Load all data
    store_status_df = pd.read_sql(db.query(models.StoreStatus).statement, db.bind)
    timezone_df = pd.read_sql(db.query(models.StoreTimeZone).statement, db.bind)
    business_hours_df = pd.read_sql(db.query(models.BusinessHour).statement, db.bind)

    now_utc = datetime.utcnow()

    report_rows = []

    for store_id in store_status_df['store_id'].unique():
        store_data = store_status_df[store_status_df['store_id'] == store_id]
        store_data = store_data.sort_values('timestamp_utc')

        # Getting timezone
        tz_row = timezone_df[timezone_df['store_id'] == str(store_id)]
        timezone_str = tz_row['timezone_str'].iloc[0] if not tz_row.empty else 'America/Chicago'

        # Getting business hours
        bh_df = business_hours_df[business_hours_df['store_id'] == store_id]
        business_ranges = get_local_business_hours(bh_df, timezone_str)

        uptime_1h = 0
        downtime_1h = 0
        uptime_1d = 0
        downtime_1d = 0
        uptime_1w = 0
        downtime_1w = 0

        for _, row in store_data.iterrows():
            local_dt = convert_to_local_time(pd.to_datetime(row['timestamp_utc']), timezone_str)

            if not is_within_business_hours(local_dt, business_ranges):
                continue

            delta = timedelta(minutes=5)
            if row['status'] == 'active':
                if local_dt > now_utc - timedelta(hours=1):
                    uptime_1h += delta.total_seconds() / 60
                if local_dt > now_utc - timedelta(days=1):
                    uptime_1d += delta.total_seconds() / 60
                if local_dt > now_utc - timedelta(weeks=1):
                    uptime_1w += delta.total_seconds() / 60
            else:
                if local_dt > now_utc - timedelta(hours=1):
                    downtime_1h += delta.total_seconds() / 60
                if local_dt > now_utc - timedelta(days=1):
                    downtime_1d += delta.total_seconds() / 60
                if local_dt > now_utc - timedelta(weeks=1):
                    downtime_1w += delta.total_seconds() / 60

        report_rows.append({
            "store_id": store_id,
            "uptime_last_hour(min)": round(uptime_1h, 2),
            "uptime_last_day(min)": round(uptime_1d, 2),
            "uptime_last_week(min)": round(uptime_1w, 2),
            "downtime_last_hour(min)": round(downtime_1h, 2),
            "downtime_last_day(min)": round(downtime_1d, 2),
            "downtime_last_week(min)": round(downtime_1w, 2),
        })

    report_df = pd.DataFrame(report_rows)

    # Saving report
    report_id = str(uuid.uuid4())[:8]
    file_path = f"reports/report_{report_id}.csv"
    report_df.to_csv(file_path, index=False)

    return report_id
