import streamlit as st
from db import Database, LogDatabase
from views.upload import upload_page
from views.analysis import analysis_page
from views.machine_learning import machine_learning_page
from streamlit_option_menu import option_menu


def user_page():
    st.title(f"Bienvenu à Firewall Logs Manager")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    # "with" notation
    with st.sidebar:
        st.image("img/logo.png")
        st.markdown("<h1 style='text-align: center;'>TechnoLog dashboard</h1>", unsafe_allow_html=True)
                
        selected = option_menu(
            "", 
            ["Upload", "Analyse", "Machine Learning"],
            # icons=["Arrow-up", "graph-up", "bar-chart-steps", "bar-chart-steps", "bar-chart-steps", "bar-chart-steps"],
            menu_icon="none",
        )

    if selected == "Upload":
        upload_page()
    elif selected == "Analyse":
        analysis_page()
    elif selected == "Machine Learning":
        machine_learning_page()

    # if page == "Upload Data":
    #     upload_page()
        