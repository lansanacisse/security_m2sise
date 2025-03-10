# TODO
# 3. Visualisation interactive des données (IP source avec le nombre d’occurrences de destination contactées, incluant le nombre de flux rejetés et autorisés).
# 4. Fournir les statistiques relatives au TOP 5 des IP sources les plus émettrices, TOP 10 des ports inférieurs à 1024 avec un accès autorisé, lister les accès des adresses non inclues dans le plan d’adressage de l’Université.

import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go


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

        # TOP 5 des IP sources
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

        # TOP 10 des ports autorisés < 1024
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

        # Analyse des flux (Sankey)
        st.subheader("Analyse des flux réseau")
        flux_data = (
            df.select(["IPsrc", "IPdst", "action"])
            .group_by(["IPsrc", "IPdst", "action"])
            .count()
            .sort("count", descending=True)
            .limit(20)
        )

        # Préparation des données pour Sankey
        nodes = list(
            set(flux_data["IPsrc"].unique())
            | set(flux_data["IPdst"].unique())
            | set(flux_data["action"].unique())
        )

        node_indices = {node: idx for idx, node in enumerate(nodes)}

        fig_sankey = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=nodes,
                    ),
                    link=dict(
                        source=[
                            node_indices[row["IPsrc"]]
                            for row in flux_data.iter_rows(named=True)
                        ],
                        target=[
                            node_indices[row["IPdst"]]
                            for row in flux_data.iter_rows(named=True)
                        ],
                        value=flux_data["count"].to_list(),
                    ),
                )
            ]
        )
        st.plotly_chart(fig_sankey)

    except Exception as e:
        st.error(f"Error reading log file: {str(e)}")


if __name__ == "__main__":
    analyze_logs()
