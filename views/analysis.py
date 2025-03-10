# TODO
# 3. Visualisation interactive des données (IP source avec le nombre d’occurrences de destination contactées, incluant le nombre de flux rejetés et autorisés).
# 4. Fournir les statistiques relatives au TOP 5 des IP sources les plus émettrices, TOP 10 des ports inférieurs à 1024 avec un accès autorisé, lister les accès des adresses non inclues dans le plan d’adressage de l’Université.

import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import ipaddress
from db import LogDatabase


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


def analyze_logs():
    # Read the log fileq
    try:
        db = LogDatabase()
        
        df = db.get_logs_sample()

        st.write("Aperçu des données:")
        st.write(df.head(5))

        # TODO PARTIE 3 ----------------------------
        # Visualisation interactive des données
        # Visualisation interactive des données (IP source avec le nombre d’occurrences de destination contactées, incluant le nombre de flux rejetés et autorisés).
        st.header("Analyse des connexions par IP source")

        # Calcul des statistiques par IP source
        ip_stats = (
            df.group_by("IPsrc")
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
            .sort("nb_destinations", descending=True)
        )

        # Création d'un sélecteur d'IP interactif
        selected_ip = st.selectbox(
            "Sélectionner une IP source",
            options=ip_stats["IPsrc"].to_list(),
        )

        # Filtrage des données pour l'IP sélectionnée
        ip_details = df.filter(pl.col("IPsrc") == selected_ip)

        # Création de deux colonnes pour l'affichage
        col1, col2 = st.columns(2)

        with col1:
            # Graphique des destinations contactées
            dest_counts = (
                ip_details.group_by("IPdst")
                .agg(pl.count().alias("count"))
                .sort("count", descending=True)
            )

            fig_dest = px.bar(
                dest_counts.to_pandas(),
                x="IPdst",
                y="count",
                title=f"Destinations contactées par {selected_ip}",
                text="count",
            )
            fig_dest.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_dest)

        with col2:
            # Distribution des actions pour cette IP
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

        # Détails supplémentaires dans un expander
        with st.expander("Détails des connexions"):
            # Table des connexions détaillées (en supprimant Protocole, qui n'est pas disponible)
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

        # Métriques globales
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
        # ----------------- PARTIE 4 -----------------

        ############################################################################################################
        # TOP 5 des IP sources
        ############################################################################################################

        st.subheader("Top 5 des IP Sources les plus émetteurs")
        top_ips = (
            df.select(pl.col("IPsrc"))
            .group_by("IPsrc")
            .count()
            .sort("count", descending=True)
            .limit(5)
        )

        fig_top_ips = px.bar(
            top_ips.to_pandas(),
            x="IPsrc",
            y="count",
            title="Top 5 IP Sources",
            text="count",
        )
        st.plotly_chart(fig_top_ips)

        # Distribution des actions par protocol (Sunburst)
        st.subheader("Distribution des actions par protocol")
        protocol_actions = (
            df.select(["Protocol", "action"])
            .group_by(["Protocol", "action"])
            .count()
            .sort("count", descending=True)
        )

        fig_sunburst = px.sunburst(
            protocol_actions.to_pandas(),
            path=["Protocol", "action"],
            values="count",  # Changed from "counts" to "count"
            title="Actions par Protocol",
        )
        st.plotly_chart(fig_sunburst)

        ############################################################################################################
        # TOP 10 des ports autorisés < 1024
        ############################################################################################################

        st.subheader("Top 10 des ports autorisés < 1024")

        # DEBUG : Affichage des données sampled, il n'y a que 443 pour le port dst
        # st.write(
        #     df.filter((pl.col("action") == "PERMIT") & (pl.col("Port_dst") < 1024))
        # )

        allowed_ports = (
            df.filter((pl.col("action") == "PERMIT") & (pl.col("Port_dst") < 1024))
            .select(pl.col("Port_dst"))
            .group_by("Port_dst")
            .count()
            .sort("count", descending=True)
            .limit(10)
        )

        fig_ports = px.bar(
            allowed_ports.to_pandas(),
            x="Port_dst",
            y="count",  # Changed from "counts" to "count"
            title="Top 10 Ports Autorisés < 1024",
            text="count",
        )
        st.plotly_chart(fig_ports)

        ############################################################################################################
        # Analyse des flux réseau
        ############################################################################################################
        st.subheader("Classification des IPs (internes/externes)")

        # Ajout des colonnes pour IP source et destination
        df_with_network_info = df.with_columns(
            [
                pl.col("IPsrc")
                .map_elements(is_internal_ip)
                .alias(
                    "is_src_internal"
                ),  # map_elements est l'équivalent de apply dans pandas
                pl.col("IPdst").map_elements(is_internal_ip).alias("is_dst_internal"),
            ]
        )

        st.write(df_with_network_info)

        # Affichage détaillé des IPs externes
        st.subheader("Détail des IPs externes")
        external_ips = (
            df_with_network_info.filter(pl.col("is_src_internal") == False)
            .group_by(["IPsrc", "action"])
            .agg(pl.count().alias("nombre_tentatives"))
            .sort("nombre_tentatives", descending=True)
        )

        st.write(external_ips)

        # Analyse des flux (Sankey)

        st.subheader("Analyse des flux réseau (interne/externe)")

        # Préparation des données pour Sankey
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

        # Création des nodes uniques
        nodes = list(
            set(flux_data["source"].unique()) | set(flux_data["target"].unique())
        )
        node_indices = {node: idx for idx, node in enumerate(nodes)}

        # Définition des couleurs
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

        # Création du diagramme Sankey
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

        # Mise en page
        fig_sankey.update_layout(
            title="Flux réseau: IP Interne/Externe → Actions", font_size=10, height=600
        )

        # Affichage
        st.plotly_chart(fig_sankey, use_container_width=True)

        # Statistiques complémentaires
        with st.expander("Détails des flux"):
            st.write("Distribution détaillée des flux:")
            st.write(flux_data)

    except Exception as e:
        st.error(f"Error reading log file: {str(e)}")


if __name__ == "__main__":
    analyze_logs()
