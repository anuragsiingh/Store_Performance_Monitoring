#  create all tables using our models and centralized engine from database.py


from app.database import Base, engine
from app import models

def create_all_tables():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully.")

if __name__ == "__main__":
    create_all_tables()
