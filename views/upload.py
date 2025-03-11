import streamlit as st
from db import LogDatabase
import pandas as pd
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
        # Display first 10 rows of the file
        parquet_columns = [
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
        ]

        columns = [
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
            # "Firewall",
        ]
        if file_type == "csv":
            df = pl.read_csv(uploaded_file, separator=separator, has_header=False)
            df.columns = columns
        elif file_type == "parquet":
            df = pl.read_parquet(uploaded_file)
            # Renommage des colonnes pour l'affichage
            column_mapping = dict(zip(parquet_columns, columns))
            df = df.rename(column_mapping)
        st.subheader("Preview of uploaded file:")
        st.dataframe(df.head(10).to_pandas())
        
        # Select only the columns specified in 'columns'
        df = df.select(columns)
        
        # Show basic file stats
        st.subheader("File Statistics:")
        st.write(f"Total rows: {df.shape[0]}")
        st.write(f"Columns: {', '.join(df.columns)}")
        
        # Convert to polars DataFrame
        # df_pl = pl.from_pandas(df)

        # Upload button
        if st.button("Replace Database with This File"):
            success, message = db.upload_csv_to_logs(df)
            if success:
                st.success(message)
            else:
                st.error(message)
