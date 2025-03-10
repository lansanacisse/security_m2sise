# TODO
# 3. Visualisation interactive des données (IP source avec le nombre d’occurrences de destination contactées, incluant le nombre de flux rejetés et autorisés).
# 4. Fournir les statistiques relatives au TOP 5 des IP sources les plus émettrices, TOP 10 des ports inférieurs à 1024 avec un accès autorisé, lister les accès des adresses non inclues dans le plan d’adressage de l’Université.

import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import ipaddress


# Définition des plages avec RFC 1918, à vérifier ?
def is_internal_ip(ip: str) -> bool:
    """Vérifie si une IP appartient au réseau interne de l'université"""
    try:
        ip_obj = ipaddress.ip_address(ip)
        internal_networks = [
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16"),
        ]
        return any(ip_obj in network for network in internal_networks)
    except ValueError:
        return False


def analyze_logs():
    # Read the log fileq
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

        # Affichage des données brutes
        st.write("Aperçu des données:")
        st.write(df.head(5))

        # TODO PARTIE 3 ----------------------------
        # Visualisation interactive des données
        # Visualisation interactive des données (IP source avec le nombre d’occurrences de destination contactées, incluant le nombre de flux rejetés et autorisés).

        # ----------------- PARTIE 4 -----------------

        ############################################################################################################
        # TOP 5 des IP sources
        ############################################################################################################

        st.subheader("Top 5 des IP Sources les plus émettrices")
        top_ips = (
            df.select(pl.col("IPsrc"))
            .group_by("IPsrc")
            .count()
            .sort("count", descending=True)
            .limit(5)
        )

        fig_top_ips = px.bar(
            top_ips.to_pandas(), x="IPsrc", y="count", title="Top 5 IP Sources"
        )
        st.plotly_chart(fig_top_ips)

        # Distribution des actions par protocole (Sunburst)
        st.subheader("Distribution des actions par protocole")
        protocol_actions = (
            df.select(["Protocole", "action"])
            .group_by(["Protocole", "action"])
            .count()
            .sort("count", descending=True)
        )

        fig_sunburst = px.sunburst(
            protocol_actions.to_pandas(),
            path=["Protocole", "action"],
            values="count",  # Changed from "counts" to "count"
            title="Actions par Protocole",
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
        # shape
        st.write(df_with_network_info.shape)  # Affiche un tuple
        st.write(df_with_network_info.schema["is_src_internal"])  # Affiche un Boolean

        # Affichage des statistiques
        st.write("Distribution des flux réseau :")

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
