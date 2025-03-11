import streamlit as st
from db import LogDatabase
import polars as pl

db = LogDatabase()

def upload_page():
    
    st.header("Upload Logs Data")
    st.write("Upload a CSV or Parquet file to replace the current logs database.")
    
    left, middle, right = st.columns(3, vertical_alignment="bottom")
    
    file_type = left.selectbox("File Type", ["csv", "parquet"])
    if file_type == "csv":
        st.write("type file csv")
        separator = middle.selectbox("Separator", [";", ","], index=0)
    
    uploaded_file = st.file_uploader(f"Choose a {file_type} file.", type=file_type)
    
    if uploaded_file is not None:
        columns = [
            "Date", 
            "IP Source", 
            "IP Dest", 
            "Protocol", 
            "Port Source",
            "Port Destination", 
            "Firewall Rule Id", 
            "Action", 
            "Interface d’entrée", 
            "Interface de sortie",
            "Firewall"]
        
        if file_type == "csv":
            df = pl.read_csv(uploaded_file, separator=separator, has_header=False)
            df.columns = columns
        else:
            df = pl.read_parquet(uploaded_file)
        st.subheader("Preview of uploaded file:")
        st.dataframe(df.head(10).to_pandas())
        
        st.subheader("File Statistics:")
        st.write(f"Total rows: {df.height}")
        st.write(f"Columns: {', '.join(df.columns)}")
        
        if st.button("Replace Database with This File"):
            success, message = db.upload_csv_to_logs(df)
            if success:
                st.success(message)
            else:
                st.error(message)
