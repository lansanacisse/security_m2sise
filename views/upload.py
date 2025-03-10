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
    # right.text_input("Write something")

    uploaded_file = st.file_uploader(f"Choose a {file_type} file.", type=file_type)

    if uploaded_file is not None:
        # Display first 10 rows of the file
        parquet_columns = [
            "Date",
            "IPsrc",
            "IPdst",
            "Protocole",
            "Port_src",
            "Port_dst",
            "idRegle",
            "action",
            "interface_entrée",
            "interface_sortie",
        ]

        columns = [
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
            "Firewall",
        ]
        if file_type == "csv":
            df = pd.read_csv(uploaded_file, sep=separator, names=columns, header=None)
        elif file_type == "parquet":
            df = pd.read_parquet(uploaded_file)
            # Renommage des colonnes pour l'affichage
            column_mapping = dict(zip(parquet_columns, columns))
            df = df.rename(columns=column_mapping)
        st.subheader("Preview of uploaded file:")
        st.dataframe(df.head(10))

        # Show basic file stats
        st.subheader("File Statistics:")
        st.write(f"Total rows: {len(df)}")
        st.write(f"Columns: {', '.join(df.columns.tolist())}")

        # Upload button
        if st.button("Replace Database with This File"):
            success, message = db.upload_csv_to_logs(df)
            if success:
                st.success(message)
            else:
                st.error(message)
