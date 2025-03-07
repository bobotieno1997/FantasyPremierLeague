# Import all relevant libraries
import psycopg2
import os
from dotenv import load_dotenv
from airflow import DAG
from airflow.decorators import task 
from datetime import datetime, timedelta
import logging

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
    "FPL_silver_tables",
    default_args=default_args,
    schedule="10 0 * * *",
    catchup=False,
    tags=["FPL", "Silver"],
) as dag:

    @task(retries=3, retry_delay=timedelta(minutes=1))
    def update_fpl_silver_layer():
        """Update the silver layer by executing stored procedures."""
        
        # Set up database connection parameters
        connection_params = {
            'dbname': os.getenv('dbname'),
            'user': os.getenv('user'),
            'password': os.getenv('password'),
            'host': os.getenv('host'),
            'port': os.getenv('port')
        }

        # Validate environment variables
        if not all(connection_params.values()):
            logging.error("❌ Missing database connection parameters from .env")
            raise ValueError("Missing database connection parameters")

        # Establish database connection
        try:
            connection = psycopg2.connect(**connection_params)
            cur = connection.cursor()
            logging.info("✅ Database connection established successfully")
        except Exception as e:
            logging.error(f"❌ Failed to connect to database: {e}")
            raise

        # SQL command to update silver layer
        update_silver_layer = """ 
            CALL silver.usp_update_team_info();
            CALL silver.usp_update_player_info();
            CALL silver.usp_update_games_info();
            CALL silver.usp_update_future_games_info();
            CALL silver.usp_update_players_stats();
        """

        # Execute stored procedures
        try:
            cur.execute(update_silver_layer)
            connection.commit()
            logging.info("✅ Silver layer updated successfully")
        except Exception as e:
            logging.error(f"❌ Error updating silver layer: {e}")
            connection.rollback()
            raise
        finally:
            # Clean up resources
            try:
                if cur:
                    cur.close()
                if connection:
                    connection.close()
                logging.info("✅ Database connection closed")
            except Exception as e:
                logging.error(f"❌ Error closing database connection: {e}")
                raise

    # Execute the task
    update_fpl_silver_layer()