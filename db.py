import sqlite3
import hashlib
import os
import logging
import pandas as pd
import streamlit as st
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

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
    ip_source: str
    ip_destination: str
    port: int
    protocol: str
    result: str
    created_at: Optional[datetime] = None

# Base Database class with common functionality
class Database:
    def __init__(self, db_path="security.db"):
        self.db_path = db_path

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

# Subclass handling user-related functionalities
class UserDatabase(Database):
    def __init__(self, db_path="security.db"):
        super().__init__(db_path)
        self._init_users_table()
        self._create_default_users()

    def _init_users_table(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_admin BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                password_change_required BOOLEAN NOT NULL DEFAULT 0
            );
        ''')
        conn.commit()
        conn.close()

    def _create_default_users(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        # Create admin if not exists
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            admin = User(
                username="admin",
                password=self._hash_password("adminpass"),
                is_admin=True,
                password_change_required=True
            )
            cursor.execute(
                "INSERT INTO users (username, password, is_admin, password_change_required) VALUES (?, ?, ?, ?)",
                (admin.username, admin.password, admin.is_admin, admin.password_change_required)
            )

        # Create regular user if not exists
        cursor.execute("SELECT * FROM users WHERE username = 'user'")
        if not cursor.fetchone():
            user = User(
                username="user",
                password=self._hash_password("userpass"),
                is_admin=False,
                password_change_required=True
            )
            cursor.execute(
                "INSERT INTO users (username, password, is_admin, password_change_required) VALUES (?, ?, ?, ?)",
                (user.username, user.password, user.is_admin, user.password_change_required)
            )
        conn.commit()
        conn.close()

    def authenticate_user(self, username: str, password: str) -> Optional[UserResponse]:
        conn = self._get_connection()
        cursor = conn.cursor()
        hashed_password = self._hash_password(password)
        cursor.execute(
            "SELECT id, username, is_admin, created_at, password_change_required FROM users WHERE username = ? AND password = ?",
            (username, hashed_password)
        )
        user_data = cursor.fetchone()
        conn.close()

        if user_data:
            return UserResponse(
                id=user_data[0],
                username=user_data[1],
                is_admin=bool(user_data[2]),
                created_at=datetime.fromisoformat(user_data[3]) if user_data[3] else datetime.now(),
                password_change_required=bool(user_data[4])
            )
        return None

    def get_all_users(self) -> List[UserResponse]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, is_admin, created_at, password_change_required FROM users")
        users_data = cursor.fetchall()
        conn.close()
        return [
            UserResponse(
                id=user[0],
                username=user[1],
                is_admin=bool(user[2]),
                created_at=datetime.fromisoformat(user[3]) if user[3] else datetime.now(),
                password_change_required=bool(user[4])
            )
            for user in users_data
        ]

    def create_user(self, user: UserCreate) -> Optional[UserResponse]:
        conn = self._get_connection()
        cursor = conn.cursor()
        hashed_password = self._hash_password(user.password)
        try:
            cursor.execute(
                "INSERT INTO users (username, password, is_admin, password_change_required) VALUES (?, ?, ?, ?)",
                (user.username, hashed_password, user.is_admin, user.password_change_required)
            )
            user_id = cursor.lastrowid
            conn.commit()
            cursor.execute(
                "SELECT id, username, is_admin, created_at, password_change_required FROM users WHERE id = ?",
                (user_id,)
            )
            new_user = cursor.fetchone()
            conn.close()
            if new_user:
                return UserResponse(
                    id=new_user[0],
                    username=new_user[1],
                    is_admin=bool(new_user[2]),
                    created_at=datetime.fromisoformat(new_user[3]) if new_user[3] else datetime.now(),
                    password_change_required=bool(new_user[4])
                )
        except sqlite3.IntegrityError:
            conn.close()
            return None
        return None

    def change_password(self, user_id: int, new_password: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        hashed_password = self._hash_password(new_password)
        try:
            cursor.execute(
                "UPDATE users SET password = ?, password_change_required = 0 WHERE id = ?",
                (hashed_password, user_id)
            )
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            return success
        except Exception:
            conn.close()
            return False

# Subclass handling log-related functionalities
class LogDatabase(Database):
    def __init__(self, db_path="security.db"):
        super().__init__(db_path)
        self._init_logs_table()
        self._create_default_logs()

    def _init_logs_table(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                ip_source TEXT NOT NULL,
                ip_destination TEXT NOT NULL,
                port INTEGER NOT NULL,
                protocol TEXT NOT NULL,
                result TEXT NOT NULL,
                created_at TIMESTAMP
            );
        ''')
        conn.commit()
        conn.close()

    def _create_default_logs(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        # If no logs exist, assume default logs from a CSV file
        cursor.execute("SELECT * FROM logs")
        if not cursor.fetchone():
            if os.path.exists('data/logs.csv'):
                with open('data/logs.csv', 'r') as csv_file:
                    csv_data = csv_file.readlines()
                    for line in csv_data:
                        data = line.strip().split(',')
                        if len(data) < 6:
                            continue  # skip malformed lines
                        try:
                            log = Logs(
                                ip_source=data[0],
                                ip_destination=data[1],
                                port=int(data[2]),
                                protocol=data[3],
                                result=data[4],
                                created_at=datetime.strptime(data[5], '%Y-%m-%d %H:%M:%S')
                            )
                        except Exception as e:
                            logger.error("Error parsing log: %s", e)
                            continue
                        cursor.execute(
                            "INSERT INTO logs (ip_source, ip_destination, port, protocol, result, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                            (log.ip_source, log.ip_destination, log.port, log.protocol, log.result, log.created_at)
                        )
        conn.commit()
        conn.close()

    @st.cache_data
    def get_all_logs(self) -> list[Logs]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM logs")
        logs_data = cursor.fetchall()
        conn.close()
        # return pd.DataFrame(logs_data)
        # return logs_data
        # return [
        #     Logs(
        #         id=int(log[0]),
        #         ip_source=log[1],
        #         ip_destination=log[2],
        #         port=log[3],
        #         protocol=log[4],
        #         result=log[5],
        #         created_at=datetime.fromisoformat(log[6]) if log[6] else datetime.now()
        #     )
        #     for log in logs_data
        # ]