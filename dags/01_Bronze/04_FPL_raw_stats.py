import requests
import pandas as pd
import logging
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from airflow import DAG
from airflow.decorators import task

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define stats list globally
stats_list = ["goals_scored", "own_goals", "yellow_cards", "red_cards", "assists",
              "penalties_saved", "penalties_missed", "saves", "bonus", "bps"]

# Load environment variables
load_dotenv()  # Added to actually load .env file

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
    "FPL_raw_stats",
    default_args=default_args,
    schedule="@daily",
    catchup=False,
    tags=["FPL", "Raw", "stats"],
) as dag:

    @task
    def pull_data_from_api():
        """Fetch data from Fantasy Premier League API."""
        api_url = "https://fantasy.premierleague.com/api/fixtures/?future=0"
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            logging.info("✅ API data fetched successfully")
            return response.json()
        except requests.RequestException as e:
            logging.error(f"❌ Error fetching data from API: {e}")
            raise

    def extract_stats(data, identifier):
        """Extract relevant match statistics."""
        if not data:
            raise ValueError("❌ API response is empty.")

        extracted_details = []
        for fixture in data:
            stats = fixture.get("stats", [])
            for stat in stats:
                if stat.get("identifier") == identifier:
                    for team_type in ['a', 'h']:
                        for entry in stat.get(team_type, []):
                            extracted_details.append({
                                'game_code': fixture.get('code', None),
                                'finished': fixture.get('finished', None),
                                'game_id': fixture.get('id', None),
                                'stat_value': entry.get('value', None),
                                'player_id': entry.get('element', None),
                                'team_type': team_type
                            })
        return pd.DataFrame(extracted_details)

    @task
    def join_dataframes(data):
        """Process extracted data into relevant statistics."""
        if data is None or len(data) == 0:
            raise ValueError("❌ No data available for processing.")

        df_list = []
        for stat in stats_list:
            df = extract_stats(data, stat)
            if not df.empty:
                df['stat_type'] = stat
                df_list.append(df)

        new_df = pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()
        logging.info("✅ Data processing completed successfully")
        return new_df

    @task
    def upload_to_postgres(df):
        """Upload DataFrame to PostgreSQL."""
        # Database connection parameters
        dbname = os.getenv('dbname')
        user = os.getenv('user')
        password = os.getenv('password')
        host = os.getenv('host')
        port = os.getenv('port')

        # Validate database parameters
        if not all([dbname, user, password, host, port]):
            raise ValueError("❌ Missing database connection parameters")

        if df is None or df.empty:
            logging.warning("⚠️ DataFrame is empty, skipping upload")
            return  # Skip rather than raise error

        try:
            engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{dbname}')
            logging.info("✅ Database connection established")
            
            df.to_sql(
                'player_stats',
                engine,
                schema='bronze',
                if_exists='append',  # Changed to append instead of replace
                index=False,
                method='multi'  # Added for better performance with PostgreSQL
            )
            logging.info("✅ Data loaded into 'bronze.player_stats' successfully")
        except Exception as e:
            logging.error(f"❌ Failed to process database operation: {e}")
            raise
        finally:
            if 'engine' in locals():
                engine.dispose()  # Clean up connection

    # Define task flow
    api_data = pull_data_from_api()
    combined_stats = join_dataframes(api_data)
    upload_to_postgres(combined_stats)


    



