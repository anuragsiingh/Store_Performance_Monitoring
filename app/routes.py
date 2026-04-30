from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from uuid import uuid4
import os
from pathlib import Path

from app.database import get_db
from app.models import ReportTracker, ReportStatusEnum
from app.report import generate_and_save_report


router = APIRouter()

REPORTS_DIR = os.path.join(os.getcwd(), "report")
# REPORTS_DIRECT = Path(__file__).resolve().parent.parent / "reports"

# print(REPORTS_DIR,os.getcwd(), REPORTS_DIRECT )   
os.makedirs(REPORTS_DIR, exist_ok=True)    

@router.get("/")
def root():
    return {"message": "Store Monitoring System is running!"}


@router.post("/trigger_report")
def trigger_report(background_tasks: BackgroundTasks, db=Depends(get_db)):
    report_id = str(uuid4())
    tracker = ReportTracker(report_id=report_id, status=ReportStatusEnum.running)
    db.add(tracker)
    db.commit()

    background_tasks.add_task(generate_and_save_report, report_id)
    return {"report_id": report_id}

@router.get("/get_report")
def get_report(report_id: str, db=Depends(get_db)):
    tracker = db.query(ReportTracker).filter(ReportTracker.report_id == report_id).first()
    if not tracker:
        raise HTTPException(404, "Invalid report_id")
    
    return {
        "report_id": tracker.report_id,
        "status": tracker.status.value,
        "file_path": tracker.file_path if tracker.status == ReportStatusEnum.complete else None
    }

@router.get("/download/{report_id}")
def download_report(report_id: str, db=Depends(get_db)):
    tracker = db.query(ReportTracker).filter(ReportTracker.report_id == report_id).first()
    if not tracker:
        raise HTTPException(404, "Report ID not found")
    if tracker.status != ReportStatusEnum.complete:
        raise HTTPException(400, "Report not ready yet")
    if not tracker.file_path or not os.path.exists(tracker.file_path):
        raise HTTPException(404, "Report file not found")
    return FileResponse(path=tracker.file_path, filename=os.path.basename(tracker.file_path), media_type='text/csv')
