import streamlit as st
import polars as pl
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Analyse des logs de firewall", layout="wide")
st.title("Analyse des logs de firewall")

def load_data():
    """Fonction pour charger et préparer les données."""
    try:
        # Charger les données à partir du fichier
        df = pl.read_csv(
            "data/sample.txt",
            separator=";",
            has_header=False,
            new_columns=[
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
            ],
        )
        
        # Reconnaître et convertir les valeurs pour timestamp
        if "Date" in df.columns:
            df = df.with_columns(pl.col("Date").str.to_datetime("%Y-%m-%d %H:%M:%S"))
        
        return df
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier: {e}")
        return None

def render_data_explorer(df):
    """Fonction pour explorer les données avec des filtres."""
    st.header("Explorer les données")
    
    # Créer des colonnes pour les filtres
    col1, col2, col3 = st.columns(3)
    
    # Filtres
    with col1:
        # Filtre par action (PERMIT/DENY)
        if "action" in df.columns:
            actions = ["Tous"] + df["action"].unique().to_list()
            selected_action = st.selectbox("Action", actions)
        
        # Filtre par IP source
        if "IPsrc" in df.columns:
            src_ips = ["Tous"] + df["IPsrc"].unique().to_list()
            selected_src_ip = st.selectbox("IP Source", src_ips)
    
    with col2:
        # Filtre par protocole
        if "Protocole" in df.columns:
            protocols = ["Tous"] + df["Protocole"].unique().to_list()
            selected_protocol = st.selectbox("Protocole", protocols)
        
        # Filtre par port de destination
        if "Port_dst" in df.columns:
            dst_ports = ["Tous"] + df["Port_dst"].unique().to_list()
            selected_dst_port = st.selectbox("Port de destination", dst_ports)
    
    with col3:
        # Filtre par plage de temps
        if "Date" in df.columns:
            min_date = df["Date"].min().date()
            max_date = df["Date"].max().date()
            
            date_range = st.date_input(
                "Plage de dates",
                [min_date, max_date],
                min_value=min_date,
                max_value=max_date
            )
    
    # Appliquer les filtres
    filtered_df = df.clone()
    
    # Filtre par action
    if "action" in df.columns and selected_action != "Tous":
        filtered_df = filtered_df.filter(pl.col("action") == selected_action)
    
    # Filtre par IP source
    if "IPsrc" in df.columns and selected_src_ip != "Tous":
        filtered_df = filtered_df.filter(pl.col("IPsrc") == selected_src_ip)
    
    # Filtre par protocole
    if "Protocole" in df.columns and selected_protocol != "Tous":
        filtered_df = filtered_df.filter(pl.col("Protocole") == selected_protocol)
    
    # Filtre par port de destination
    if "Port_dst" in df.columns and selected_dst_port != "Tous":
        filtered_df = filtered_df.filter(pl.col("Port_dst") == selected_dst_port)
    
    # Filtre par plage de temps
    if "Date" in df.columns and len(date_range) == 2:
        start_date = date_range[0]
        end_date = date_range[1]
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        filtered_df = filtered_df.filter(
            (pl.col("Date") >= start_datetime) & 
            (pl.col("Date") <= end_datetime)
        )
    
    # Afficher les données filtrées
    st.subheader("Données filtrées")
    st.dataframe(filtered_df.to_pandas())
    
    # Afficher des statistiques
    st.subheader("Statistiques")
    col1, col2 = st.columns(2)
    
    with col1:
        if "action" in df.columns:
            action_counts = filtered_df.group_by("action").agg(pl.count()).sort("count", descending=True)
            st.write("Répartition des actions:")
            
            # Créer un graphique avec Plotly
            fig = px.pie(
                action_counts.to_pandas(), 
                names="action", 
                values="count", 
                title="Répartition des actions"
            )
            st.plotly_chart(fig)
    
    with col2:
        if "IPsrc" in df.columns:
            ip_counts = filtered_df.group_by("IPsrc").agg(pl.count()).sort("count", descending=True).head(10)
            st.write("Top 10 des IPs sources:")
            
            fig = px.bar(
                ip_counts.to_pandas(), 
                x="IPsrc", 
                y="count", 
                title="Top 10 des IPs sources"
            )
            st.plotly_chart(fig)

def explore_data():
    """Fonction principale pour afficher les données sous forme de tableau et analyses."""
    try:
        # Lire les données à partir du fichier
        df = load_data()
        
        if df is not None:
            # Afficher uniquement l'explorateur de données
            render_data_explorer(df)
    except Exception as e:
        st.error(f"Erreur lors de l'analyse des données: {e}")


