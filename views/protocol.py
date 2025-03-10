import streamlit as st
import polars as pl
import pandas as pd
import plotly.express as px
from datetime import datetime


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
    """Réalise l'analyse descriptive et affiche des graphiques avancés."""
    df_pd = filtered_df.to_pandas()
    
    total_flows = len(df_pd)
    
    # 1. Métriques pour les pourcentages par action
    st.subheader("Métriques des Flux")
    
    action_counts = df_pd["action"].value_counts(normalize=True) * 100
    protocol_counts = df_pd["Protocole"].value_counts(normalize=True) * 100
    source_counts = df_pd["IPsrc"].value_counts(normalize=True) * 100
    destination_counts = df_pd["IPdst"].value_counts(normalize=True) * 100
    
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between;">
            <div style="width: 24%; background-color: #4CAF50; padding: 10px; border-radius: 5px; text-align: center;">
                <h5 style="color: white;">PERMIT</h5>
                <h4 style="color: white;">{permit:.2f}%</h4>
            </div>
            <div style="width: 24%; background-color: #F44336; padding: 10px; border-radius: 5px; text-align: center;">
                <h5 style="color: white;">DENY</h5>
                <h4 style="color: white;">{deny:.2f}%</h4>
            </div>
            <div style="width: 24%; background-color: #2196F3; padding: 10px; border-radius: 5px; text-align: center;">
                <h5 style="color: white;">Flux TCP</h5>
                <h4 style="color: white;">{tcp:.2f}%</h4>
            </div>
            <div style="width: 24%; background-color: #FF9800; padding: 10px; border-radius: 5px; text-align: center;">
                <h5 style="color: white;">Flux UDP</h5>
                <h4 style="color: white;">{udp:.2f}%</h4>
            </div>
        </div>
        <br>
        <div style="display: flex; justify-content: space-between;">
            <div style="width: 49%; background-color: #9C27B0; padding: 10px; border-radius: 5px; text-align: center;">
                <h5 style="color: white;">Top 1 Source</h5>
                <h4 style="color: white;">{top_source:.2f}%</h4>
                <p style="color: white;">IP: {top_source_ip}</p>
            </div>
            <div style="width: 49%; background-color: #009688; padding: 10px; border-radius: 5px; text-align: center;">
                <h5 style="color: white;">Top 1 Destination</h5>
                <h4 style="color: white;">{top_dest:.2f}%</h4>
                <p style="color: white;">IP: {top_dest_ip}</p>
            </div>
        </div>
        """.format(
            permit=action_counts.get('PERMIT', 0),
            deny=action_counts.get('DENY', 0),
            tcp=protocol_counts.get('TCP', 0),
            udp=protocol_counts.get('UDP', 0),
            top_source=source_counts.iloc[0],
            top_source_ip=source_counts.index[0],
            top_dest=destination_counts.iloc[0],
            top_dest_ip=destination_counts.index[0]
        ),
        unsafe_allow_html=True
    )
    
    # 2. Sunburst Plot
    st.subheader("Répartition hiérarchique des flux")
    sunburst_data = df_pd.groupby(["Protocole", "action", "IPsrc"]).size().reset_index(name="Nombre")
    fig_sunburst = px.sunburst(
        sunburst_data,
        path=["Protocole", "action", "IPsrc"],
        values="Nombre",
        title="Répartition des flux par protocole, action et source"
    )
    st.plotly_chart(fig_sunburst, use_container_width=True)
    
    # 3. Violin Plot
    st.subheader("Distribution des ports sources et destinations")
    fig_violin = px.violin(
        df_pd,
        y="Port_src",
        x="Protocole",
        color="action",
        box=True,
        points="all",
        title="Distribution des ports sources par protocole et action"
    )
    st.plotly_chart(fig_violin, use_container_width=True)
    
    # 4. Heatmap
    st.subheader("Heatmap : Flux entre IP source et IP destination")
    heatmap_data = df_pd.groupby(["IPsrc", "IPdst"]).size().unstack(fill_value=0)
    fig_heatmap = px.imshow(
        heatmap_data,
        labels=dict(x="IP Destination", y="IP Source", color="Nombre de flux"),
        title="Flux entre IP source et IP destination"
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)


def analyze_flows():
    """Charge les données et applique l'analyse descriptive avec filtres."""
    df = load_data()   
    if df is None:
        return
    
    filtered_df = apply_filters(df)
    
    if not filtered_df.is_empty():
        plot_analysis(filtered_df)