import streamlit as st
import pandas as pd
import ipaddress
from db import LogDatabase

@st.cache_data
def get_logs():
    return LogDatabase().get_logs()


def load_and_preprocess_data():
    # # Define column names based on your description
    # column_names = ['Date', 'IPsrc', 'IPdst', 'Protocol', 'Port_src', 'Port_dst', 
    #                'idRegle', 'action', 'interface_entree', 'interface_sortie', 
    #                'firewall', 'Cluster', 'type1', 'type2', 'type3', 'type4', 
    #                'type5', 'type6', 'type7', 'type8', 'type9', 'type10']
    
    # Use existing DataFrame instead of loading from file
    db = LogDatabase()
    
    logs = db.get_logs_sample()
    print(type(logs))
    df = logs.to_pandas()
    
    # Convert date to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Extract time features
    df['hour'] = df['Date'].dt.hour
    df['day_of_week'] = df['Date'].dt.dayofweek
    
    # Convert IP addresses to numerical values
    def ip_to_int(ip):
        try:
            return int(ipaddress.ip_address(ip))
        except:
            return np.nan
    
    print("Converting IP addresses...")
    df['IPsrc_int'] = df['IPsrc'].apply(ip_to_int)
    df['IPdst_int'] = df['IPdst'].apply(ip_to_int)
    
    # One-hot encode categorical features
    print("Encoding categorical features...")
    df = pd.get_dummies(df, columns=['Protocol', 'action'], drop_first=True)
    
    # Handle missing values
    df = df.fillna(0)
    
    return df

def machine_learning_page():
    st.header("Machine Learning Logs Data")
    st.write("This page will contain the machine learning functionality.")
    
    st.write("Loading and preprocessing data...")
    
    # Preprocessing data was created and we have now new rows like hour, day_of_week and IPsrc_int and IPdst_int 
    # to start play with the data if you consider add new features to the model please put into load_and_preprocess_data function
    # and all we will use same data to improve performance of the app using just one dataset
    
    #TODO: Create a navbar inside machine learning page to put each model in a different tab 
    #TODO: Create a model for each tab and show the results of the model in the tab LIKE CLUSTERING, PCA,  ISOLATION_FOREST ETC...
    
    
    try:
        df = load_and_preprocess_data()
        
        st.write("Sample of logs data:")
        st.write(df.head())
    except Exception as e:
        st.write("An error occurred during data preprocessing:")
        st.write(e)
    
    
    