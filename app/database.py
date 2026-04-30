from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os


load_dotenv()

USER = os.getenv("DB_USER", "your_db_user")
PASSWORD = os.getenv("DB_PASSWORD", "your_db_password")
HOST = os.getenv("DB_HOST", "localhost")
PORT = 5433  
NAME = os.getenv("DB_NAME", "your_db_name")

# SQLAlchemy database URL
DB_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}"

# Create SQLAlchemy engine
engine = create_engine(
    DB_URL,
    pool_recycle=3600,
    echo=True 
)

# Creating a configured session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()

# Dependency for getting DB session (used in FastAPI routes)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()