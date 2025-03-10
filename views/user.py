import streamlit as st
from db import Database, LogDatabase
from streamlit_elements import elements, mui, html
from .analysis import analyze_logs  # Import the analysis function


def user_page():
    st.title(f"User Dashboard - Welcome, {st.session_state.username}!")

    # Empty user page as requested
    st.write("properties")

    # db = LogDatabase()

    # logs = db.get_all_logs()
    # st.table(logs)

    # Routeur de l'application

    with st.sidebar:
        st.header("Menu")
        page = st.radio("Go to", ["Analyse", "ML"])

    if page == "Analyse":
        analyze_logs()
