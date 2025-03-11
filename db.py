import hashlib
import logging
import polars as pl
import pandas as pd
import streamlit as st
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Pydantic models for data validation (unchanged)
class Logs(BaseModel):
    Date: Optional[datetime] = None
    IPsrc: str
    IPdst: str
    Protocole: str
    Port_src: int
    Port_dst: int
    idRegle: int
    action: str
    interface_entrée: str
    interface_sortie: Optional[str] = None
    # firewall: int

# Base Database class with common functionality
class Database:
    def __init__(self):
        # Keep the parameters for compatibility, but we won't use them
        self.data_dir = Path("data")
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(exist_ok=True)

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()


class LogDatabase(Database):
    def __init__(self):
        super().__init__()
        self.logs_file = self.data_dir / "logs.parquet"
        # Initialize the parquet file if it doesn't exist
        if not self.logs_file.exists():
            self._init_logs_file()

    def _init_logs_file(self):
        """Initialize an empty logs parquet file with the correct schema"""
        # Create an empty DataFrame with the correct schema
        empty_df = pl.DataFrame(
            schema={
                "Date": pl.Datetime,
                "IPsrc": pl.Utf8,
                "IPdst": pl.Utf8,
                "Protocole": pl.Utf8,
                "Port_src": pl.Int32,
                "Port_dst": pl.Int32,
                "idRegle": pl.Int32,
                "action": pl.Utf8,
                "interface_entrée": pl.Utf8,
                "interface_sortie": pl.Utf8,
                # "firewall": pl.Int32
            }
        )
        # Save the empty DataFrame to parquet
        empty_df.write_parquet(self.logs_file)
    
    @st.cache_data
    def get_logs_sample(_self, limit=10000) -> pl.DataFrame:
        """
        Retrieve a sample of logs from the parquet file with a limit.
        """
        if not _self.logs_file.exists():
            return pl.DataFrame()
        
        try:
            df = pl.read_parquet(_self.logs_file)
            # Return the first 'limit' rows
            return df.head(limit)
        except pl.exceptions.PolarsError as e:
            logger.error("Error reading parquet file: %s", e)
            return pl.DataFrame()
    
    @st.cache_data
    def get_logs_count(self) -> int:
        """
        Get the total number of log entries.
        """
        if not self.logs_file.exists():
            return 0
        
        try:
            df = pl.read_parquet(self.logs_file)
            return len(df)
        except Exception as e:
            logger.error(f"Error reading parquet file: {e}")
            return 0
    
    def upload_csv_to_logs(self, df: pl.DataFrame):
        """
        Upload data from a DataFrame to the logs parquet file.
        """
        try:
            # Check if dataframe is valid
            if df is None or len(df) == 0:
                return False, "Empty DataFrame provided"
            
            # Drop rows with null values except for interface_sortie
            columns_to_check = [col for col in df.columns if col != "interface_sortie"]
            df = df.drop_nulls(columns_to_check)
            
            df = df.to_pandas()
            # Transform the date column to datetime
            df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d %H:%M:%S")
            df = pl.from_pandas(df)
            
            # Convert DataFrame to a list of dictionaries for validation
            records = df.select([
                "Date",
                "IPsrc",
                "IPdst",
                "Protocole",
                "Port_src",
                "Port_dst",
                "idRegle",
                "action",
                "interface_entrée",
                "interface_sortie",
                # "firewall",
            ]).to_dicts()
            
            # Validate each record using the Pydantic Logs model
            logs_data = []
            for record in records:
                try:
                    log_obj = Logs(**record)
                    logs_data.append(log_obj)
                except Exception as e:
                    return False, f"Data validation error: {e}"
            
            # Save the DataFrame to parquet
            df.write_parquet(self.logs_file)
            
            # Clear the cache to refresh the data
            st.cache_data.clear()
            
            return True, f"Successfully uploaded {len(logs_data)} records"
        except Exception as e:
            return False, f"Error uploading file: {e}"
    
    @st.cache_data
    def get_logs(_self) -> pl.DataFrame:
        """
        Retrieve all logs from the parquet file and convert to Logs objects.
        """
        try:
            df = pl.read_parquet(_self.logs_file)
            return df
            
        except Exception as e:
            logger.error(f"Error reading parquet file: {e}")
            return None