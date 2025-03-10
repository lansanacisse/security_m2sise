# TODO
# 3. Visualisation interactive des données (IP source avec le nombre d’occurrences de destinationcontactées, incluant le nombre de flux rejetés et autorisés).
# 4. Fournir les statistiques relatives au TOP 5 des IP sources les plus émettrices, TOP 10 des ports inférieurs à 1024 avec un accès autorisé, lister les accès des adresses non inclues dans le plan d’adressage de l’Université.

import streamlit as st
import polars as pl
import plotly.express as px


def analyze_logs():
    # Read the log file
    try:
        df = pl.read_csv(
            "data/sample.txt",
            separator=";",
            has_header=False,
            new_columns=[
                "timestamp",
                "action",
                "protocol",
                "src_ip",
                "src_port",
                "dst_ip",
                "dst_port",
            ],
        )

        st.header("Log Analysis Dashboard")

        # TOP 5 Source IPs
        st.subheader("Top 5 des IP Sources les plus émettrices")

        # TOP 10 Allowed Ports < 1024
        st.subheader("Top 10 Ports Autorisés (< 1024)")

    except Exception as e:
        st.error(f"Error reading log file: {str(e)}")


if __name__ == "__main__":
    analyze_logs()
