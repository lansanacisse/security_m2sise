import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import ipaddress
from db import LogDatabase

CUSTOM_COLORS = [
    "#E41A1C",  # Rouge
    "#377EB8",  # Bleu
    "#4DAF4A",  # Vert
    "#984EA3",  # Violet
    "#FF7F00",  # Orange
    "#FFFF33",  # Jaune
    "#A65628",  # Marron
    "#F781BF",  # Rose
    "#999999",  # Gris
    "#66C2A5",  # Turquoise
]


@st.cache_data(ttl=3600)  # Cache pendant 1 heure
def load_parquet_data():
    """Charge et met en cache les données du fichier Parquet"""
    try:
        db = LogDatabase()

        df = db.get_logs_sample()

        return df
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier: {e}")
        return None
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier: {str(e)}")
        return None


@st.cache_data(ttl=3600)
def calculate_ip_stats(_df):
    """Calcule et met en cache les statistiques par IP"""
    return (
        _df.group_by("IPsrc")
        .agg(
            [
                pl.n_unique("IPdst").alias("nb_destinations"),
                pl.col("action")
                .filter(pl.col("action") == "PERMIT")
                .count()
                .alias("permit_count"),
                pl.col("action")
                .filter(pl.col("action") == "DENY")
                .count()
                .alias("deny_count"),
                pl.count().alias("total_count"),
            ]
        )
        .sort("total_count", descending=True)
    )


@st.cache_data(ttl=3600)
def calculate_port_stats(_df, port_range):
    """Calcule et met en cache les statistiques par port"""
    # Conversion en entier pour la comparaison numérique
    filtered_data = _df.filter(
        (pl.col("Port_dst").cast(pl.Int32) >= port_range[0])
        & (pl.col("Port_dst").cast(pl.Int32) <= port_range[1])
    )
    return filtered_data


@st.cache_data(ttl=3600)
def calculate_network_info(_df):
    """Calcule et met en cache les informations réseau"""
    return _df.with_columns(
        [
            pl.col("IPsrc").map_elements(is_internal_ip).alias("is_src_internal"),
            pl.col("IPdst").map_elements(is_internal_ip).alias("is_dst_internal"),
        ]
    )


@st.cache_data(ttl=3600)
def calculate_top_ports(_df, max_port=1024, limit=10):
    """Calcule et met en cache les statistiques des ports les plus utilisés"""
    return (
        _df.filter(
            (pl.col("Port_dst").cast(pl.Int32).lt(pl.lit(max_port)))
            & (pl.col("action") == "PERMIT")
        )
        .group_by("Port_dst")
        .agg([pl.count().alias("count"), pl.first("Protocole").alias("protocole")])
        .sort("count", descending=True)
        .limit(limit)
        .with_columns([pl.col("Port_dst").cast(pl.Utf8).alias("Port_dst")])
    )


@st.cache_data(ttl=3600)
def get_ip_details(_df, selected_ip):
    """Récupère et met en cache les détails pour une IP spécifique"""
    return _df.filter(pl.col("IPsrc") == selected_ip)


@st.cache_data(ttl=3600)
def sample_data(_df, n=10000):
    """Échantillonne les données pour les visualisations"""
    if _df.height > n:
        return _df.sample(n=n, seed=42)
    return _df


# Définition des plages avec RFC 1918, à vérifier ?
def is_internal_ip(ip: str) -> bool:
    """Vérifie si une IP appartient au réseau interne de l'université"""
    try:
        ip_obj = ipaddress.ip_address(ip)
        internal_networks = [
            ipaddress.ip_network("10.70.0.0/16"),
            ipaddress.ip_network("159.84.0.0/16"),
            ipaddress.ip_network("192.168.0.0/16"),
        ]
        return any(ip_obj in network for network in internal_networks)
    except ValueError:
        return False


def render_ip_analysis(df_sample, ip_stats, selected_ip, date_range):
    """Rendu de l'analyse pour une IP spécifique"""
    st.header(f"Analyse de l'IP source: {selected_ip}")

    # Récupération des détails pour l'IP sélectionnée
    ip_details = get_ip_details(df_sample, selected_ip)

    if ip_details.height == 0:
        st.warning(f"Aucune donnée trouvée pour l'IP {selected_ip} dans l'échantillon")
        return

    col1, col2 = st.columns(2)

    with col1:
        # Calcul du nombre de destinations uniques
        n_destinations = ip_details["IPdst"].n_unique()

        # Création d'une métrique avec du contexte
        st.metric(
            "Nombre de destinations uniques contactées",
            value=n_destinations,
            help="Nombre total d'adresses IP uniques contactées par cette source",
        )

        # Ajout d'un détail dans un expander si nécessaire
        with st.expander("Voir les destinations"):
            dest_counts = (
                ip_details.group_by("IPdst")
                .agg(pl.count().alias("count"))
                .sort("count", descending=True)
            )
            st.dataframe(
                dest_counts.to_pandas().style.background_gradient(
                    subset=["count"], cmap="YlOrRd"
                )
            )
    with col2:
        action_counts = (
            ip_details.group_by("action")
            .agg(pl.count().alias("count"))
            .sort("count", descending=True)
        )
        fig_actions = px.pie(
            action_counts.to_pandas(),
            values="count",
            names="action",
            title=f"Distribution des actions pour {selected_ip}",
            color="action",
            color_discrete_map={"PERMIT": "green", "DENY": "red"},
        )
        st.plotly_chart(fig_actions)

    ################################# Détails des connexions
    with st.expander("Détails des connexions"):
        connections_detail = (
            ip_details.select(["IPdst", "Port_dst", "action"])
            .group_by(["IPdst", "Port_dst", "action"])
            .agg(pl.count().alias("occurrences"))
            .sort("occurrences", descending=True)
        )
        st.write("Détail des connexions :")
        st.dataframe(
            connections_detail.to_pandas().style.background_gradient(
                subset=["occurrences"], cmap="YlOrRd"
            )
        )
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nombre total de destinations", ip_details["IPdst"].n_unique())
    with col2:
        st.metric(
            "Connexions autorisées",
            ip_details.filter(pl.col("action") == "PERMIT").height,
        )
    with col3:
        st.metric(
            "Connexions refusées",
            ip_details.filter(pl.col("action") == "DENY").height,
        )

    ################################# Distribution des ports et protocoles pour adresse spécifique
    st.subheader("Distribution des ports et protocoles")
    pie1, pie2 = st.columns(2)

    with pie1:
        # Top 10 Port destinations pie chart
        port_dist = (
            ip_details.group_by("Port_dst")
            .agg(pl.count().alias("count"))
            .sort("count", descending=True)
            .limit(10)  # Limit to top 10 for readability
        )

        if port_dist.height > 0:
            fig_ports = px.pie(
                port_dist.to_pandas(),
                values="count",
                names="Port_dst",
                title=f"Top 10 Ports de destination pour {selected_ip}",
                color_discrete_sequence=CUSTOM_COLORS,
            )
            fig_ports.update_traces(textposition="inside", textinfo="label+percent")
            st.plotly_chart(fig_ports, use_container_width=True)
        else:
            st.info("Aucune donnée de port disponible pour cette IP")

    with pie2:
        # Protocol distribution pie chart
        proto_dist = (
            ip_details.group_by("Protocole")
            .agg(pl.count().alias("count"))
            .sort("count", descending=True)
        )

        if proto_dist.height > 0:
            fig_proto = px.pie(
                proto_dist.to_pandas(),
                values="count",
                names="Protocole",
                title=f"Distribution des protocoles pour {selected_ip}",
                color_discrete_sequence=CUSTOM_COLORS,
            )
            fig_proto.update_traces(textposition="inside", textinfo="label+percent")
            st.plotly_chart(fig_proto, use_container_width=True)
        else:
            st.info("Aucune donnée de protocole disponible pour cette IP")

    ################################# Time Series Analysis
    st.subheader("Analyse temporelle des connexions")

    # Convert to pandas for time series analysis
    ip_details_pd = ip_details.to_pandas()
    ip_details_pd["Date"] = pd.to_datetime(ip_details_pd["Date"])

    # Filtrage par période si date_range est défini
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        mask = (ip_details_pd["Date"].dt.date >= start_date) & (
            ip_details_pd["Date"].dt.date <= end_date
        )
        filtered_data = ip_details_pd[mask]
    else:
        filtered_data = ip_details_pd

    # Vérification si filtered_data contient des données
    if not filtered_data.empty:
        # Daily activity plot
        daily_stats = (
            filtered_data.groupby([filtered_data["Date"].dt.date, "action"])
            .size()
            .unstack(fill_value=0)
        )

        fig_time = go.Figure()

        if "PERMIT" in daily_stats.columns:
            fig_time.add_trace(
                go.Scatter(
                    x=daily_stats.index,
                    y=daily_stats["PERMIT"],
                    name="PERMIT",
                    line=dict(color="green", width=2),
                    fill="tonexty",
                )
            )

        if "DENY" in daily_stats.columns:
            fig_time.add_trace(
                go.Scatter(
                    x=daily_stats.index,
                    y=daily_stats["DENY"],
                    name="DENY",
                    line=dict(color="red", width=2),
                    fill="tonexty",
                )
            )

        fig_time.update_layout(
            title=f"Activité pour {selected_ip}",
            xaxis_title="Date",
            yaxis_title="Nombre de connexions",
            hovermode="x unified",
            showlegend=True,
            height=400,
            xaxis=dict(rangeslider=dict(visible=True), type="date"),
        )

        st.plotly_chart(fig_time, use_container_width=True)

        # Activity statistics
        with st.expander("Statistiques d'activité"):
            stats_col1, stats_col2, stats_col3 = st.columns(3)

            with stats_col1:
                daily_total = daily_stats.sum(axis=1)
                st.metric(
                    "Moyenne journalière",
                    f"{daily_total.mean():.1f}",
                    help="Nombre moyen de connexions par jour",
                )

            with stats_col2:
                st.metric(
                    "Jour le plus actif",
                    daily_total.idxmax().strftime("%Y-%m-%d"),
                    f"{daily_total.max():.0f} connexions",
                )

            with stats_col3:
                active_days = (daily_total > 0).sum()
                st.metric(
                    "Jours d'activité",
                    f"{active_days}",
                    help="Nombre de jours avec au moins une connexion",
                )
    else:
        st.warning("Aucune donnée disponible pour la période sélectionnée")


def render_global_analysis(df_sample):
    """Rendu de l'analyse globale pour toutes les IP"""

    # Dashboard global
    st.header("Tableau de bord général")

    # Métriques générales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Nombre total de connexions", df_sample.height)
    with col2:
        st.metric("Nombre d'IP sources uniques", df_sample["IPsrc"].n_unique())
    with col3:
        st.metric("Nombre d'IP destinations uniques", df_sample["IPdst"].n_unique())
    with col4:
        permit_rate = (
            df_sample.filter(pl.col("action") == "PERMIT").height / df_sample.height
        ) * 100
        st.metric("Taux d'autorisation", f"{permit_rate:.1f}%")

    ################################# Top 5 des IP Sources les plus émettrices
    st.subheader("Top 5 des IP Sources les plus émettrices")
    top_ips = (
        df_sample.select(pl.col("IPsrc"))
        .group_by("IPsrc")
        .count()
        .sort("count", descending=True)
        .limit(5)
    )

    if top_ips.height > 0:
        fig_top_ips = px.bar(
            top_ips.to_pandas(),
            x="IPsrc",
            y="count",
            title="Top 5 IP Sources",
            text="count",
            color="IPsrc",
            color_discrete_sequence=CUSTOM_COLORS,
        )
        fig_top_ips.update_traces(textposition="outside")
        st.plotly_chart(fig_top_ips, use_container_width=True)
    else:
        st.info("Aucune donnée disponible pour les IP sources")

    ################################# Top 10 des ports inférieurs à 1024 avec accès autorisé
    st.subheader("Top 10 des ports inférieurs à 1024 avec accès autorisé")
    top_ports = calculate_top_ports(df_sample)

    # st.write(top_ports)

    port_order = top_ports["Port_dst"].to_list()

    fig_top_ports = px.bar(
        top_ports.to_pandas(),
        x="Port_dst",
        y="count",
        title="Top 10 Ports",
        text="count",
        color="Port_dst",
        color_discrete_sequence=CUSTOM_COLORS,
        category_orders={"Port_dst": port_order},  # Ordre personnalisé
    )

    # Personnalisation du graphique
    fig_top_ports.update_xaxes(type="category")

    fig_top_ports.update_traces(
        textposition="outside",
        width=0.8,
    )

    fig_top_ports.update_layout(
        xaxis_title="Port de destination",
        yaxis_title="Nombre de connexions",
        height=500,
        xaxis=dict(tickangle=-45),  # Rotation des étiquettes
        margin=dict(t=50, b=100),  # Ajustement des marges
    )
    st.plotly_chart(fig_top_ports, use_container_width=True)

    ################################ Classification des IPs (internes/externes)
    st.subheader("Analyse des flux réseau (interne/externe)")
    df_with_network_info = calculate_network_info(df_sample)

    # Distribution interne/externe
    int_ext_col1, int_ext_col2 = st.columns(2)

    with int_ext_col1:
        src_type_counts = (
            df_with_network_info.select(
                pl.when(pl.col("is_src_internal"))
                .then(pl.lit("Interne"))
                .otherwise(pl.lit("Externe"))
                .alias("type_source")
            )
            .group_by("type_source")
            .count()
        )

        fig_src_type = px.pie(
            src_type_counts.to_pandas(),
            values="count",
            names="type_source",
            title="Types d'IP sources",
            color_discrete_map={"Interne": "#377EB8", "Externe": "#FF7F00"},
        )
        st.plotly_chart(fig_src_type, use_container_width=True)

    with int_ext_col2:
        dst_type_counts = (
            df_with_network_info.select(
                pl.when(pl.col("is_dst_internal"))
                .then(pl.lit("Interne"))
                .otherwise(pl.lit("Externe"))
                .alias("type_destination")
            )
            .group_by("type_destination")
            .count()
        )

        fig_dst_type = px.pie(
            dst_type_counts.to_pandas(),
            values="count",
            names="type_destination",
            title="Types d'IP destinations",
            color_discrete_map={"Interne": "#377EB8", "Externe": "#FF7F00"},
        )
        st.plotly_chart(fig_dst_type, use_container_width=True)

    # Diagramme Sankey des flux réseau
    flux_data = (
        df_with_network_info.select(
            [
                pl.when(pl.col("is_src_internal"))
                .then(pl.lit("IP Interne"))
                .otherwise(pl.lit("IP Externe"))
                .alias("source"),
                pl.col("action").alias("target"),
            ]
        )
        .group_by(["source", "target"])
        .count()
        .sort("count", descending=True)
    )

    if flux_data.height > 0:
        nodes = list(
            set(flux_data["source"].unique()) | set(flux_data["target"].unique())
        )
        node_indices = {node: idx for idx, node in enumerate(nodes)}
        node_colors = [
            (
                "blue"
                if node == "IP Interne"
                else (
                    "orange"
                    if node == "IP Externe"
                    else "red" if node == "DENY" else "green"
                )
            )
            for node in nodes
        ]
        fig_sankey = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=nodes,
                        color=node_colors,
                    ),
                    link=dict(
                        source=[
                            node_indices[row["source"]]
                            for row in flux_data.iter_rows(named=True)
                        ],
                        target=[
                            node_indices[row["target"]]
                            for row in flux_data.iter_rows(named=True)
                        ],
                        value=flux_data["count"].to_list(),
                        color=[
                            (
                                "rgba(0, 0, 255, 0.4)"
                                if row["source"] == "IP Interne"
                                and row["target"] == "PERMIT"
                                else (
                                    "rgba(0, 0, 255, 0.2)"
                                    if row["source"] == "IP Interne"
                                    and row["target"] == "DENY"
                                    else (
                                        "rgba(255, 165, 0, 0.4)"
                                        if row["source"] == "IP Externe"
                                        and row["target"] == "PERMIT"
                                        else "rgba(255, 165, 0, 0.2)"
                                    )
                                )
                            )
                            for row in flux_data.iter_rows(named=True)
                        ],
                    ),
                )
            ]
        )
        fig_sankey.update_layout(
            title="Flux réseau: IP Interne/Externe → Actions",
            font_size=10,
            height=600,
        )
        st.plotly_chart(fig_sankey, use_container_width=True)
    else:
        st.info("Aucune donnée de flux réseau disponible")

    # Détail des IPs externes
    st.subheader("Détail des IPs externes")
    external_ips = (
        df_with_network_info.filter(pl.col("is_src_internal") == False)
        .group_by(["IPsrc", "action"])
        .agg(pl.count().alias("nombre_tentatives"))
        .sort("nombre_tentatives", descending=True)
    )

    if external_ips.height > 0:
        st.dataframe(external_ips)
    else:
        st.info("Aucune IP externe détectée dans l'échantillon")


def analyze_logs():

    # Chargement des données
    df = load_parquet_data()
    if df is None:
        st.error("Impossible de charger les données. Vérifiez le fichier logs.parquet.")
        return

    # Configuration de la sidebar
    with st.sidebar:
        st.header("Filtres")

        # Option pour échantillonner les données
        sample_size = st.slider(
            "Nombre d'entrées à analyser (échantillon)",
            min_value=1000,
            max_value=min(100000, df.height),
            value=10000,
            step=1000,
        )

        # Échantillonnage des données
        df_sample = sample_data(df, n=sample_size)

        # Calcul des statistiques IP
        ip_stats = calculate_ip_stats(df_sample)

        # Sélection de l'IP source (pour l'onglet analyse IP)
        selected_ip = st.selectbox(
            "Sélectionner une IP source",
            options=ip_stats["IPsrc"].to_list(),
            format_func=lambda x: f"{x} ({ip_stats.filter(pl.col('IPsrc') == x)['total_count'].item()} connexions)",
            key="ip_selector",
        )

        # Filtre de période pour l'analyse temporelle
        ip_details = get_ip_details(df_sample, selected_ip)
        ip_details_pd = ip_details.to_pandas()
        ip_details_pd["Date"] = pd.to_datetime(ip_details_pd["Date"])

        if not ip_details_pd.empty:
            date_range = st.date_input(
                "Sélectionner la période d'analyse",
                value=(
                    ip_details_pd["Date"].min().date(),
                    ip_details_pd["Date"].max().date(),
                ),
                min_value=ip_details_pd["Date"].min().date(),
                max_value=ip_details_pd["Date"].max().date(),
            )
        else:
            st.warning(f"Aucune donnée trouvée pour l'IP {selected_ip}")
            date_range = None

        st.markdown("---")

    # Création des onglets
    tab1, tab2 = st.tabs(["🔍 Analyse d'une adresse IP", "📊 Vue d'ensemble du réseau"])

    # Contenu de l'onglet 1: Analyse d'une adresse IP spécifique
    with tab1:
        render_ip_analysis(df_sample, ip_stats, selected_ip, date_range)

    # Contenu de l'onglet 2: Analyse de toutes les adresses
    with tab2:
        render_global_analysis(df_sample)


if __name__ == "__main__":
    analyze_logs()
