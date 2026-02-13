"""
BigQuery I/O operations for the reformas-momento-ideal project.
Handles reading events and writing scores to BigQuery.
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path

try:
    from google.cloud import bigquery
    from google.oauth2 import service_account
    BIGQUERY_AVAILABLE = True
except ImportError:
    BIGQUERY_AVAILABLE = False

from .config import (
    BQ_PROJECT_ID, 
    BQ_DATASET, 
    BQ_EVENTS_TABLE, 
    BQ_SCORES_TABLE,
    get_bq_credentials_path
)
from .event_schema import Score


class BigQueryIO:
    """Handle BigQuery I/O operations."""
    
    def __init__(self):
        """Initialize BigQuery client."""
        if not BIGQUERY_AVAILABLE:
            raise ImportError(
                "google-cloud-bigquery is not installed. "
                "Install it with: pip install google-cloud-bigquery"
            )
        
        self.project_id = BQ_PROJECT_ID
        self.dataset = BQ_DATASET
        
        # Initialize client
        credentials_path = get_bq_credentials_path()
        
        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                str(credentials_path)
            )
            self.client = bigquery.Client(
                project=self.project_id,
                credentials=credentials
            )
        else:
            # Use default credentials
            self.client = bigquery.Client(project=self.project_id)
    
    def read_events(
        self, 
        start_date: datetime, 
        end_date: Optional[datetime] = None,
        anon_ids: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Read events from BigQuery.
        
        Args:
            start_date: Start date for events
            end_date: End date for events (default: now)
            anon_ids: Optional list of anon_ids to filter
            
        Returns:
            DataFrame with events
        """
        if end_date is None:
            end_date = datetime.now()
        
        table_ref = f"{self.project_id}.{self.dataset}.{BQ_EVENTS_TABLE}"
        
        # Build query
        query = f"""
        SELECT 
            event_time,
            channel,
            anon_id,
            event_name,
            event_props,
            ingestion_time
        FROM `{table_ref}`
        WHERE DATE(event_time) >= @start_date
          AND DATE(event_time) <= @end_date
        """
        
        if anon_ids:
            anon_ids_str = "', '".join(anon_ids)
            query += f" AND anon_id IN ('{anon_ids_str}')"
        
        query += " ORDER BY event_time DESC"
        
        # Set up query parameters
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date.date()),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date.date()),
            ]
        )
        
        # Execute query
        df = self.client.query(query, job_config=job_config).to_dataframe()
        
        return df
    
    def write_scores(self, scores: List[Score]) -> None:
        """
        Write scores to BigQuery.
        
        Args:
            scores: List of Score objects to write
        """
        if not scores:
            print("No scores to write")
            return
        
        table_ref = f"{self.project_id}.{self.dataset}.{BQ_SCORES_TABLE}"
        
        # Convert scores to DataFrame
        scores_data = [s.to_dict() for s in scores]
        df = pd.DataFrame(scores_data)
        
        # Write to BigQuery
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            schema=[
                bigquery.SchemaField("anon_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("score", "FLOAT64", mode="REQUIRED"),
                bigquery.SchemaField("class_label", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("score_date", "DATE", mode="REQUIRED"),
                bigquery.SchemaField("top_drivers", "STRING", mode="NULLABLE"),
            ]
        )
        
        job = self.client.load_table_from_dataframe(
            df, table_ref, job_config=job_config
        )
        
        job.result()  # Wait for the job to complete
        
        print(f"Successfully wrote {len(scores)} scores to {table_ref}")
    
    def get_latest_scores(
        self, 
        limit: int = 50,
        class_filter: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get latest scores from BigQuery.
        
        Args:
            limit: Maximum number of scores to return
            class_filter: Optional filter by class_label
            
        Returns:
            DataFrame with latest scores
        """
        table_ref = f"{self.project_id}.{self.dataset}.{BQ_SCORES_TABLE}"
        
        query = f"""
        SELECT 
            anon_id,
            score,
            class_label,
            score_date,
            top_drivers,
            created_at
        FROM `{table_ref}`
        WHERE score_date = (SELECT MAX(score_date) FROM `{table_ref}`)
        """
        
        if class_filter:
            query += f" AND class_label = '{class_filter}'"
        
        query += f" ORDER BY score DESC LIMIT {limit}"
        
        df = self.client.query(query).to_dataframe()
        
        return df
    
    def test_connection(self) -> bool:
        """
        Test BigQuery connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try a simple query
            query = "SELECT 1 as test"
            self.client.query(query).result()
            print(f"✓ BigQuery connection successful to project: {self.project_id}")
            return True
        except Exception as e:
            print(f"✗ BigQuery connection failed: {e}")
            return False


def load_events_from_csv(csv_path: Path) -> pd.DataFrame:
    """
    Load events from a CSV file (for local testing).
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        DataFrame with events
    """
    df = pd.read_csv(csv_path)
    
    # Parse datetime columns
    if 'event_time' in df.columns:
        df['event_time'] = pd.to_datetime(df['event_time'])
    
    if 'ingestion_time' in df.columns:
        df['ingestion_time'] = pd.to_datetime(df['ingestion_time'])
    
    return df


def save_scores_to_csv(scores: List[Score], csv_path: Path) -> None:
    """
    Save scores to a CSV file (for local testing).
    
    Args:
        scores: List of Score objects
        csv_path: Path to save CSV file
    """
    scores_data = [s.to_dict() for s in scores]
    df = pd.DataFrame(scores_data)
    df.to_csv(csv_path, index=False)
    print(f"Saved {len(scores)} scores to {csv_path}")
