from fastapi import FastAPI
from app.routes import router as report_router 
from app.database import engine
from app.models import Base

# Creating all tables (only works if tables don’t exist yet)
Base.metadata.create_all(bind=engine)

# Create the FastAPI app
app = FastAPI(
    title="Store Uptime Reporting API",
    description="API to generate and download uptime/downtime reports based on store hours and status.",
    version="1.0.0",
)

# Include the router
app.include_router(report_router)
