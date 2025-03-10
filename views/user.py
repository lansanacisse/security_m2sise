import streamlit as st
from db import Database, LogDatabase
from streamlit_elements import elements, mui, html
from .analysis import analyze_logs


def user_page():
    """User Dashboard page."""

    # Title
    st.title(f"User Dashboard - Welcome, {st.session_state.username}!")
    st.write("Properties")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home", "📈 Analysis", "🔍 Datasets", "🤖 Machine Learning"])

    with tab1:
        st.write("Welcome to the Security M2 SISE dashboard!")

    with tab2:
        st.write("This section will contain model analysis.")
        analyze_logs()
        
    with tab3:
        st.write("Here you can explore datasets.")

    with tab4:
        st.write("Using the machine model.")

    # Example of database usage (uncomment if needed)
    # db = LogDatabase()
    # logs = db.get_all_logs()
    # st.table(logs)
