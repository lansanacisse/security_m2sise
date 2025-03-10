import streamlit as st
import polars as pl
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuration de la page
st.title("Analyse descriptive des flux autorisés et rejetés (TCP/UDP)")

# Définition des plages de ports selon la RFC 6056 et options complémentaires
RFC_PORT_RANGES = {
    "Linux 4.x": (32768, 60999),
    "FreeBSD, macOS": (49152, 65535),
    "Windows": (49152, 65535),
    "Autres OS": (1024, 5000),
    "Ports bien connus": (1, 1023),
    "Ports enregistrés": (1024, 49151),
    "Personnalisé": (0, 0)  # Sera remplacé par la sélection utilisateur
}

@st.cache_data
def load_data():
    """
    Charge les données depuis un fichier CSV (ou TXT) et effectue les conversions nécessaires.
    Le fichier doit contenir les colonnes suivantes (sans header) : 
    Date;IPsrc;IPdst;Protocole;Port_src;Port_dst;idRegle;action;interface_entrée;interface_sortie
    """
    try:
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
        # Conversion de la date au format datetime
        df = df.with_columns(pl.col("Date").str.to_datetime("%Y-%m-%d %H:%M:%S"))
        # Conversion des ports en entiers
        df = df.with_columns([
            pl.col("Port_src").cast(pl.Int32),
            pl.col("Port_dst").cast(pl.Int32)
        ])
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier : {e}")
        return None

def apply_filters(df):
    """Applique les filtres via la sidebar."""
    st.sidebar.header("Filtres")
    
    # Filtre par protocole (on se focalise sur TCP et UDP)
    protocoles = ["Tous", "TCP", "UDP"]
    selected_protocol = st.sidebar.selectbox("Protocole", protocoles)
    
    # Filtre par action (autorisé ou rejeté)
    actions = ["Tous", "PERMIT", "DENY"]
    selected_action = st.sidebar.selectbox("Action", actions)
    
    # Filtre par plage de ports selon la RFC 6056
    selected_range = st.sidebar.selectbox("Plage de ports prédéfinie", list(RFC_PORT_RANGES.keys()))
    custom_port_range = RFC_PORT_RANGES[selected_range]
    if selected_range == "Personnalisé":
        min_port, max_port = st.sidebar.slider("Définir une plage de ports", 0, 65535, (1024, 49151))
        custom_port_range = (min_port, max_port)
    
    # Choix du type de port à filtrer
    port_type = st.sidebar.selectbox("Type de port à filtrer", ["Source", "Destination", "Les deux"])
    
    # Filtre par plage de dates
    min_date = df["Date"].min().date()
    max_date = df["Date"].max().date()
    date_range = st.sidebar.date_input("Plage de dates", [min_date, max_date],
                                       min_value=min_date, max_value=max_date)
    
    filtered_df = df.clone()
    
    # Filtre sur le protocole
    if selected_protocol != "Tous":
        filtered_df = filtered_df.filter(pl.col("Protocole") == selected_protocol)
    
    # Filtre sur l'action (autorisé vs rejeté)
    if selected_action != "Tous":
        filtered_df = filtered_df.filter(pl.col("action") == selected_action)
    
    # Filtre sur la plage de ports
    min_port, max_port = custom_port_range
    if port_type in ["Source", "Les deux"]:
        filtered_df = filtered_df.filter((pl.col("Port_src") >= min_port) & (pl.col("Port_src") <= max_port))
    if port_type in ["Destination", "Les deux"]:
        filtered_df = filtered_df.filter((pl.col("Port_dst") >= min_port) & (pl.col("Port_dst") <= max_port))
    
    # Filtre sur la période
    if len(date_range) == 2:
        start_date = datetime.combine(date_range[0], datetime.min.time())
        end_date = datetime.combine(date_range[1], datetime.max.time())
        filtered_df = filtered_df.filter((pl.col("Date") >= start_date) & (pl.col("Date") <= end_date))
    
    return filtered_df

def plot_analysis(filtered_df):
    """Réalise l'analyse descriptive et affiche un graphique en barres et le tableau récapitulatif."""
    st.header("Analyse descriptive des flux")
    
    # Agréger les données par protocole et action
    grouped = filtered_df.group_by(["Protocole", "action"]).agg(pl.count().alias("Nombre"))
    data = grouped.to_pandas()
    
    # Graphique en barres regroupant les flux autorisés et rejetés par protocole
    fig = px.bar(
        data,
        x="Protocole",
        y="Nombre",
        color="action",
        barmode="group",
        title="Flux autorisés et rejetés par protocole",
        labels={"Nombre": "Nombre de flux", "action": "Action"}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Affichage du tableau de synthèse
    st.dataframe(data)
    
    # Affichage des statistiques descriptives
    st.subheader("Statistiques descriptives")
    total_flows = filtered_df.height
    st.write(f"**Nombre total de flux :** {total_flows}")
    
    protocol_counts = filtered_df.group_by("Protocole").agg(pl.count().alias("Nombre")).to_pandas()
    st.write("**Nombre de flux par protocole :**")
    st.dataframe(protocol_counts)
    
def analyze_flows():
    """Charge les données et applique l'analyse descriptive avec filtres."""
    df = load_data()   
    if df is None:
        return
    
    filtered_df = apply_filters(df)
    
    if not filtered_df.is_empty():
        plot_analysis(filtered_df)
