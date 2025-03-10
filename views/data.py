import streamlit as st
import polars as pl
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Analyse des logs de firewall", layout="wide")

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
        
        # Convertir la colonne "Date" en datetime
        if "Date" in df.columns:
            df = df.with_columns(pl.col("Date").str.to_datetime("%Y-%m-%d %H:%M:%S"))
        
        return df
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier: {e}")
        return None

def render_data_explorer(df):
    """Fonction pour explorer les données avec des filtres."""
    
    # Section des filtres dans la sidebar
    st.sidebar.subheader("Filtres")
    
    # Filtre par action (PERMIT/DENY)
    selected_action = "Tous"
    if "action" in df.columns:
        actions = ["Tous"] + df["action"].unique().to_list()
        selected_action = st.sidebar.selectbox("Action", actions)
    
    # Filtre par protocole
    selected_protocol = "Tous"
    if "Protocole" in df.columns:
        protocols = ["Tous"] + df["Protocole"].unique().to_list()
        selected_protocol = st.sidebar.selectbox("Protocole", protocols)
    
    # Filtre par port de destination
    selected_dst_port = "Tous"
    if "Port_dst" in df.columns:
        dst_ports = ["Tous"] + df["Port_dst"].unique().to_list()
        selected_dst_port = st.sidebar.selectbox("Port de destination", dst_ports)
    
    # Filtre par plage de temps
    date_range = [df["Date"].min().date(), df["Date"].max().date()]
    if "Date" in df.columns:
        min_date = df["Date"].min().date()
        max_date = df["Date"].max().date()
        
        date_range = st.sidebar.date_input(
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
    
    # Afficher les données filtrées avec un titre clair
    st.subheader("Données filtrées")
    st.dataframe(filtered_df.to_pandas(), use_container_width=True)
    
    # Compte des lignes filtrées
    st.info(f"Nombre d'enregistrements affichés: {filtered_df.height}")
    
    # Section des statistiques
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
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
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
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

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

