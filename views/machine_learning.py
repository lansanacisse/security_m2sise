import streamlit as st
import pandas as pd
from db import LogDatabase

@st.cache_data
def get_logs():
    return LogDatabase().get_logs()

def machine_learning_page():
    st.header("Machine Learning Logs Data")
    st.write("This page will contain the machine learning functionality.")
    
    logs = get_logs()
    
    columns = [
        "ID",
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
        "Firewall"]
    
    df = pd.DataFrame(logs, columns=columns)
    st.write(df.head(10))
    
    