import requests
import pandas as pd
import logging
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from airflow import DAG
from airflow.decorators import task


# Load environment variables once
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# DAG default arguments
default_args = {
    "owner": "Fantasy Premier League",
    "depends_on_past": False,
    "start_date": datetime(2023, 2, 7),
    "email": ["bobotieno99@gmail.com"],
    "email_on_failure": False,
    "email_on_retry": True,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

# Define Airflow DAG
with DAG(
    "FPL_raw_teams",
    default_args=default_args,
    schedule="@daily",
    catchup=False,
    tags=["FPL", "Raw", "teams"],
) as dag:

    @task(retries=3, retry_delay=timedelta(minutes=1))
    def pull_data_from_api():
        """Fetch data from Fantasy Premier League API."""
        api_url = "https://fantasy.premierleague.com/api/bootstrap-static/"
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            logging.info("✅ Teams data fetched successfully")
            return data
        except requests.RequestException as e:
            logging.error(f"❌ Error fetching data from API: {e}")
            raise

    @task()
    def create_data_frame(data):
        """Convert API response to a Pandas DataFrame."""
        if not data or "teams" not in data:
            raise ValueError("❌ API response is empty or malformed.")

        try:
            df = pd.DataFrame(data["teams"], columns=["id", "code", "name", "short_name"])
            df.rename(columns={"id": "team_id", "code": "team_code","name":"team_name","short_name":"team_short_name"}, inplace=True)
            logging.info(f"✅ DataFrame created with {len(df)} records.")
            return df
        except Exception as e:
            logging.error(f"❌ Error converting data to DataFrame: {e}")
            raise

    @task()
    def upload_to_postgres(df):
        # Database connection parameters
        dbname = os.getenv('dbname')
        user = os.getenv('user')
        password = os.getenv('password')
        host = os.getenv('host')
        port = os.getenv('port')

        # Evaluate if df contains a data
        if df is None or df.empty:
            raise ValueError("❌ DataFrame is empty, cannot upload to S3.")

        # Create SQLAlchemy engine for PostgreSQL connection   
        try:
            engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{dbname}')
            logging.info("✅ Database connection established")
        except Exception as e:
            logging.error(f"❌ Failed to connect to database: {e}")
            raise

        # Load DataFrame into the 'bronze' schema
        try:
            df.to_sql(
                'teams_info',           # Table name
                engine,                 # SQLAlchemy engine
                schema='bronze',        # Target schema
                if_exists='replace',    # 'replace' to overwrite, 'append' to add data
                index=False             # Exclude DataFrame index
            )
            logging.info("✅ Data loaded into 'bronze.teams_info' successfully")
        except Exception as e:
            logging.error(f"❌ Failed to load data into database: {e}")
            raise

    # Task Dependencies
    raw_data = pull_data_from_api()
    df = create_data_frame(raw_data)
    upload_to_postgres(df)

