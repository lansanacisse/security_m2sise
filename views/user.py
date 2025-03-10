import streamlit as st
from db import Database, LogDatabase
from streamlit_elements import elements, mui, html


def user_page():
    st.title(f"User Dashboard - Welcome, {st.session_state.username}!")
    
    # Empty user page as requested
    st.write("properties")
    
    # db = LogDatabase()
    
    # logs = db.get_all_logs()
    # st.table(logs)
    
    