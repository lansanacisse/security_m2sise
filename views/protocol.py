import streamlit as st
import polars as pl
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.title("Analyse descriptive des flux par protocoles")

# Définition des plages de ports éphémères selon RFC 6056
RFC_PORT_RANGES = {
    "Linux 4.x": (32768, 60999),
    "FreeBSD, macOS": (49152, 65535),
    "Windows": (49152, 65535),
    "Autres OS": (1024, 5000),
    "Ports bien connus": (1, 1023),
    "Ports enregistrés": (1024, 49151),
    "Personnalisé": (0, 0)  # Sera remplacé par la sélection de l'utilisateur
}

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
        
        # Convertir les ports en entiers si ce n'est pas déjà fait
        if "Port_src" in df.columns:
            df = df.with_columns(pl.col("Port_src").cast(pl.Int32))
        if "Port_dst" in df.columns:
            df = df.with_columns(pl.col("Port_dst").cast(pl.Int32))
        
        return df
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier: {e}")
        return None

def analyze_protocols():
    """Fonction pour analyser les flux par protocoles et plages de ports."""
    try:
        # Charger les données
        df = load_data()
        
        if df is None:
            return
        
        # Section de filtres
        st.header("Filtres")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtre par protocole
            protocols = ["Tous"] + df["Protocole"].unique().to_list()
            selected_protocol = st.selectbox("Protocole", protocols)
            
            # Filtre par action
            actions = ["Tous"] + df["action"].unique().to_list()
            selected_action = st.selectbox("Action", actions)
        
        with col2:
            # Filtre par plage de ports prédéfinie
            port_range_names = list(RFC_PORT_RANGES.keys())
            selected_range = st.selectbox("Plage de ports prédéfinie", port_range_names)
            
            # Si "Personnalisé" est sélectionné, afficher des sliders
            custom_port_range = RFC_PORT_RANGES[selected_range]
            if selected_range == "Personnalisé":
                min_port, max_port = st.slider(
                    "Plage de ports personnalisée", 
                    0, 65535, (1024, 49151)
                )
                custom_port_range = (min_port, max_port)
                
        with col3:
            # Filtre par type de port (source/destination)
            port_type = st.selectbox("Type de port à filtrer", ["Source", "Destination", "Les deux"])
            
            # Filtre par plage de dates
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
        
        # Filtre par protocole
        if selected_protocol != "Tous":
            filtered_df = filtered_df.filter(pl.col("Protocole") == selected_protocol)
        
        # Filtre par action
        if selected_action != "Tous":
            filtered_df = filtered_df.filter(pl.col("action") == selected_action)
        
        # Filtre par plage de ports
        min_port, max_port = custom_port_range
        if port_type == "Source" or port_type == "Les deux":
            filtered_df = filtered_df.filter(
                (pl.col("Port_src") >= min_port) & (pl.col("Port_src") <= max_port)
            )
        if port_type == "Destination" or port_type == "Les deux":
            filtered_df = filtered_df.filter(
                (pl.col("Port_dst") >= min_port) & (pl.col("Port_dst") <= max_port)
            )
        
        # Filtre par plage de dates
        if len(date_range) == 2:
            start_date = date_range[0]
            end_date = date_range[1]
            
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            filtered_df = filtered_df.filter(
                (pl.col("Date") >= start_datetime) & 
                (pl.col("Date") <= end_datetime)
            )
        
        # Afficher le nombre d'enregistrements après filtrage
        st.metric("Nombre d'enregistrements filtrés", filtered_df.height)
        
        # Analyse des données filtrées
        st.header("Analyse des flux")
        
        # Création de l'onglet pour les différentes vues
        tab1, tab2, tab3 = st.tabs(["Analyse par protocole", "Analyse par action", "Distribution des ports"])
        
        with tab1:
            # Analyse par protocole
            st.subheader("Répartition des flux par protocole")
            
            # Compter par protocole
            protocol_counts = filtered_df.group_by("Protocole").agg(
                pl.count().alias("Nombre"),
                (pl.col("action") == "PERMIT").sum().alias("Autorisés"),
                (pl.col("action") == "DENY").sum().alias("Rejetés")
            ).sort("Nombre", descending=True)
            
            # Convertir pour Plotly
            protocol_data = protocol_counts.to_pandas()
            
            # Créer un graphique
            col1, col2 = st.columns(2)
            
            with col1:
                # Graphique en barres
                fig_protocol = px.bar(
                    protocol_data,
                    x="Protocole",
                    y=["Autorisés", "Rejetés"],
                    title="Nombre de flux par protocole et action",
                    barmode="group"
                )
                st.plotly_chart(fig_protocol, use_container_width=True)
            
            with col2:
                # Tableau des statistiques
                st.dataframe(protocol_data, use_container_width=True)
        
        with tab2:
            # Analyse par action
            st.subheader("Répartition des actions par protocole")
            
            # Compter par action et protocole
            action_protocol = filtered_df.group_by(["action", "Protocole"]).agg(
                pl.count().alias("Nombre")
            ).sort("Nombre", descending=True)
            
            # Convertir pour la visualisation
            action_data = action_protocol.to_pandas()
            
            # Créer un graphique
            fig_action = px.pie(
                action_data,
                names="action",
                values="Nombre",
                color="Protocole",
                title="Répartition des actions par protocole",
                hole=0.4
            )
            st.plotly_chart(fig_action, use_container_width=True)
            
            # Tableau récapitulatif
            action_summary = filtered_df.group_by("action").agg(
                pl.count().alias("Nombre"),
                pl.col("Protocole").value_counts().alias("Distribution protocoles")
            )
            st.dataframe(action_summary.to_pandas(), use_container_width=True)
        
        with tab3:
            # Distribution des ports
            st.subheader("Distribution des ports")
            
            # Options de visualisation
            port_view = st.radio(
                "Type de ports à visualiser",
                ["Ports source", "Ports destination", "Les deux"]
            )
            
            # Préparation des données
            if port_view == "Ports source" or port_view == "Les deux":
                src_ports = filtered_df.group_by("Port_src").agg(
                    pl.count().alias("Nombre"),
                    (pl.col("action") == "PERMIT").sum().alias("Autorisés"),
                    (pl.col("action") == "DENY").sum().alias("Rejetés")
                ).sort("Nombre", descending=True).head(20)
                
                fig_src = px.scatter(
                    src_ports.to_pandas(), 
                    x="Port_src", 
                    y="Nombre", 
                    size="Nombre",
                    color=["Autorisés" if r > d else "Rejetés" for r, d in zip(src_ports["Autorisés"], src_ports["Rejetés"])],
                    title="Distribution des ports source les plus fréquents",
                    labels={"Port_src": "Port source", "Nombre": "Nombre de connexions"}
                )
                st.plotly_chart(fig_src, use_container_width=True)
            
            if port_view == "Ports destination" or port_view == "Les deux":
                dst_ports = filtered_df.group_by("Port_dst").agg(
                    pl.count().alias("Nombre"),
                    (pl.col("action") == "PERMIT").sum().alias("Autorisés"),
                    (pl.col("action") == "DENY").sum().alias("Rejetés")
                ).sort("Nombre", descending=True).head(20)
                
                fig_dst = px.scatter(
                    dst_ports.to_pandas(), 
                    x="Port_dst", 
                    y="Nombre", 
                    size="Nombre",
                    color=["Autorisés" if r > d else "Rejetés" for r, d in zip(dst_ports["Autorisés"], dst_ports["Rejetés"])],
                    title="Distribution des ports destination les plus fréquents",
                    labels={"Port_dst": "Port destination", "Nombre": "Nombre de connexions"}
                )
                st.plotly_chart(fig_dst, use_container_width=True)
            
            # Histogramme de la distribution des ports pour visualiser les plages
            st.subheader("Distribution par plages de ports")
            
            # Choix du type de port pour l'histogramme
            hist_port_type = st.selectbox(
                "Visualiser la distribution pour", 
                ["Ports source", "Ports destination"]
            )
            
            port_col = "Port_src" if hist_port_type == "Ports source" else "Port_dst"
            
            # Créer l'histogramme
            fig_hist = px.histogram(
                filtered_df.to_pandas(),
                x=port_col,
                color="action",
                nbins=50,
                title=f"Distribution des {hist_port_type.lower()} par plage",
                barmode="stack"
            )
            
            # Ajouter des lignes verticales pour les plages RFC 6056
            for name, (start, end) in RFC_PORT_RANGES.items():
                if name != "Personnalisé":
                    fig_hist.add_vline(x=start, line_dash="dash", line_color="gray")
                    fig_hist.add_vline(x=end, line_dash="dash", line_color="gray")
                    
                    # Ajouter une annotation pour la plage
                    fig_hist.add_annotation(
                        x=(start + end) / 2,
                        y=fig_hist.data[0]["y"].max() if len(fig_hist.data) > 0 and len(fig_hist.data[0]["y"]) > 0 else 10,
                        text=name,
                        showarrow=False,
                        yshift=10
                    )
            
            st.plotly_chart(fig_hist, use_container_width=True)
        
        # Tableau de données filtrées
        st.header("Données filtrées")
        st.dataframe(filtered_df.to_pandas(), use_container_width=True)
    
    except Exception as e:
        st.error(f"Erreur lors de l'analyse des données: {e}")
        st.exception(e)
