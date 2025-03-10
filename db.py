import psycopg2
import psycopg2.extras
import hashlib
import logging
import polars as pl
import streamlit as st
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Pydantic models for data validation
class User(BaseModel):
    id: Optional[int] = None
    username: str
    password: str
    is_admin: bool = False
    created_at: Optional[datetime] = None
    password_change_required: bool = False

class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    created_at: datetime
    password_change_required: bool

class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = False
    password_change_required: bool = True

class Logs(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    ip_source: str
    ip_destination: str
    protocol: str
    port_destiny: int
    action: str
    id_firewall: int
    interface_in: str
    interface_out: str

# Base Database class with common functionality for PostgreSQL
class Database:
    def __init__(self, db_name="security", user="postgres", password="postgres", host="localhost", port="5432"):
        self.dsn = {
            "dbname": os.getenv("DB_NAME", db_name),
            "user": os.getenv("DB_USER", user),
            "password": os.getenv("DB_PASSWORD", password),
            "host": os.getenv("DB_HOST", host),
            "port": os.getenv("DB_PORT", port)
        }

    def _get_connection(self):
        return psycopg2.connect(**self.dsn)

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

# Subclass handling log-related functionalities with PostgreSQL
class LogDatabase(Database):
    def __init__(self, db_name="security", user="postgres", password="postgres", host="localhost", port="5432"):
        super().__init__(db_name, user, password, host, port)
        self._init_logs_table()

    def _init_logs_table(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                date_log TIMESTAMP NOT NULL,
                ip_source TEXT NOT NULL,
                ip_destination TEXT NOT NULL,
                protocol TEXT NOT NULL,
                port_source INTEGER NOT NULL,
                port_destiny INTEGER NOT NULL,
                id_firewall INTEGER NOT NULL,
                action TEXT NOT NULL,
                interface_in TEXT NOT NULL,
                interface_out TEXT,
                firewall INTEGER NOT NULL
            );
        ''')
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_logs_sample(self, limit=10):
        """
        Retrieve a sample of logs from the database with a limit.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM logs LIMIT %s"
        cursor.execute(query, (limit,))
        # Fetch all rows and extract column names from cursor.description
        rows = cursor.fetchall()
        columns=[
                "ID",
                "Date",
                "IPsrc",
                "IPdst",
                "Protocol",
                "Port_src",
                "Port_dst",
                "idRule",
                "action",
                "interface_entrée",
                "interface_sortie",
                "firewall",
            ]
        # Create Polars DataFrame from the rows
        df = pl.DataFrame(rows, schema=columns)
        cursor.close()
        conn.close()
        return df
    
    def get_logs_count(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM logs")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count
    
    def upload_csv_to_logs(self, df: pl.DataFrame):
        try:
            # Validate columns against the Logs model
            required_columns = [
                "Date", 
                "IP Source", 
                "IP Dest", 
                "Protocole", 
                "Port Source",
                "Port Destination", 
                "Id regles firewall", 
                "Action", 
                "Interface d’entrée", 
                "Interface de sortie",
                "Firewall"
            ]
            
            # Check if all required columns exist
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return False, f"Missing columns: {', '.join(missing_columns)}"
            
            # Convert DataFrame to a list of dictionaries using Polars
            logs_data = df.select(required_columns).to_dicts()
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # First, delete all existing records
            cursor.execute("DELETE FROM logs")
            
            # Insert new records
            for log in logs_data:
                cursor.execute(
                    """INSERT INTO logs 
                       (
                        date_log, ip_source, ip_destination, protocol, port_source, 
                        port_destiny, id_firewall, action, interface_in, 
                        interface_out, firewall
                       ) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        log['Date'],
                        log['IP Source'], 
                        log['IP Dest'], 
                        log['Protocole'], 
                        log['Port Source'],
                        log['Port Destination'],
                        log['Id regles firewall'], 
                        log['Action'],
                        log['Interface d’entrée'],
                        log['Interface de sortie'],
                        log['Firewall']
                    )
                )
            
            conn.commit()
            cursor.close()
            conn.close()
            return True, f"Successfully uploaded {len(logs_data)} records"
            
        except Exception as e:
            return False, f"Error uploading file: {str(e)}"
    
    def get_logs(self) -> List[Logs]:
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM logs")
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        return logs
