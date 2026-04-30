# making engine to connect sqlalchemy with postgre and upload all three csv files to the database by making tables

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from pathlib import Path
load_dotenv()


# setting up my PostgreSQL database connection.
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = 5433
db_name = os.getenv("DB_NAME")


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR,'data')

STORE_STATUS_CSV = os.path.join(DATA_DIR, 'store_status.csv')
TIMEZONES_CSV = os.path.join(DATA_DIR, 'timezones.csv')
MENU_HOURS_CSV = os.path.join(DATA_DIR, 'menu_hours.csv')


engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}", pool_recycle=3600,
        echo=True,)

# loading csv files to database.
def load_csv_to_db():
    print("loading all csv files to PostgreSQL database ....waiting for a while......")

    df_status = pd.read_csv(STORE_STATUS_CSV)
    df_status.to_sql("store_status", con=engine, if_exists="replace", index=False)
    print("store_status csv file loaded successfully!")

    df_tz=  pd.read_csv(TIMEZONES_CSV)
    df_tz.to_sql("store_timezones", con= engine, if_exists= "replace", index= False)
    print("store_timezones csv file loaded successfully!") 

    df_menu=  pd.read_csv(MENU_HOURS_CSV)
    df_menu.to_sql("menu_hours", con= engine, if_exists= "replace", index= False)
    print("menu_hours csv file loaded successfully!")



if __name__ == "__main__":
    load_csv_to_db()