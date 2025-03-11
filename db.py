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
from sqlalchemy import create_engine

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Pydantic models for data validation
class Logs(BaseModel):
    Date: Optional[datetime] = None
    IPsrc: str
    IPdst: str
    Protocol: str
    Port_src: int
    Port_dst: int
    idRegle: int
    action: str
    interface_entrée: str
    interface_sortie: Optional[str] = None
    firewall: int

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


class LogDatabase(Database):
    def __init__(self, db_name="security", user="postgres", password="postgres", host="localhost", port="5432"):
        super().__init__(db_name, user, password, host, port)
        self._init_logs_table()

    def _init_logs_table(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
            "Date" TIMESTAMP NOT NULL,
            "IPsrc" TEXT NOT NULL,
            "IPdst" TEXT NOT NULL,
            "Protocol" TEXT NOT NULL,
            "Port_src" INTEGER NOT NULL,
            "Port_dst" INTEGER NOT NULL,
            "idRegle" INTEGER NOT NULL,
            "action" TEXT NOT NULL,
            "interface_entrée" TEXT NOT NULL,
            "interface_sortie" TEXT,
            "firewall" INTEGER NOT NULL
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
        rows = cursor.fetchall()
        columns=[
            # "ID",
            "Date",
            "IPsrc",
            "IPdst",
            "Protocol",
            "Port_src",
            "Port_dst",
            "idRegle",
            "action",
            "interface_entrée",
            "interface_sortie",
            "firewall",
        ]
        df = pl.DataFrame(rows, schema=columns)
        # Convert the "Date" column to datetime format
        df = df.with_columns([pl.col("Date").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S")])
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
            # Drop rows with null values except for interface_sortie
            columns_to_check = [col for col in df.columns if col != "interface_sortie"]
            df = df.drop_nulls(subset=columns_to_check)
            # Convert DataFrame to a list of dictionaries using the selected schema fields
            records = df.select([
                "Date",
                "IPsrc",
                "IPdst",
                "Protocol",
                "Port_src",
                "Port_dst",
                "idRegle",
                "action",
                "interface_entrée",
                "interface_sortie",
                "firewall",
            ]).to_dicts()

            # Validate each record using the Pydantic Logs model
            logs_data = []
            for record in records:
                try:
                    log_obj = Logs(**record)
                    logs_data.append(log_obj)
                except Exception as e:
                    return False, f"Data validation error: {e}"

            conn = self._get_connection()
            cursor = conn.cursor()
            # Delete all existing records before inserting new ones
            cursor.execute("DELETE FROM logs")
            # for log in logs_data:
            #     cursor.execute(
            #         """INSERT INTO logs 
            #            ("Date", "IPsrc", "IPdst", "Protocol", "Port_src", 
            #             "Port_dst", "idRegle", "action", "interface_entrée", 
            #             "interface_sortie", "firewall")
            #            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            #         """,
            #         (
            #             log.Date,
            #             log.IPsrc,
            #             log.IPdst,
            #             log.Protocol,
            #             log.Port_src,
            #             log.Port_dst,
            #             log.idRegle,
            #             log.action,
            #             log.interface_entrée,
            #             log.interface_sortie if log.interface_sortie is not None else '',
            #             log.firewall
            #         )
            #     )
            conn.commit()
            cursor.close()
            conn.close()
            
            load_dotenv()

            # Create database connection URL
            DB_USER = os.getenv("DB_NAME", "postgres")
            DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
            DB_HOST = os.getenv("DB_HOST", "localhost")
            DB_PORT = os.getenv("DB_PORT", "5432")
            DB_NAME = os.getenv("DB_NAME", "security")
            
            engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

            # Insertar datos en la tabla (ajustar el nombre de la tabla)
            df.to_sql("logs", engine, if_exists="replace", index=False)
            
            return True, f"Successfully uploaded {len(logs_data)} records"
        except Exception as e:
            return False, f"Error uploading file: {e}"
    
    def get_logs(self) -> List[Logs]:
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM logs")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        # Validate each row using the Logs model and return a list of Logs objects
        logs = []
        for row in rows:
            row_dict = dict(row)
            try:
                log = Logs(**row_dict)
                logs.append(log)
            except Exception as e:
                logging.error(f"Data validation error: {e}")
        return logs
