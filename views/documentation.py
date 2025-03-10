# pages/documentation.py
import streamlit as st

st.set_page_config(page_title="Documentation", page_icon="📄")

st.title("📄 Documentation")
st.markdown("""
### Bienvenue dans la documentation de l'application Security M2 SISE !

Cette documentation vous guide à travers les fonctionnalités de l'application.

#### Sections disponibles :
1. **Accueil** : Vue d'ensemble du tableau de bord.
2. **Analyse** : Analyse des logs de sécurité.
3. **Datasets** : Exploration des jeux de données.
4. **Protocole** : Analyse des flux réseau.
5. **Machine Learning** : Modèles d'apprentissage automatique.

#### Comment utiliser l'application :
- Utilisez la sidebar pour naviguer entre les différentes sections.
- Appliquez des filtres pour explorer les données.
- Consultez les statistiques et visualisations pour mieux comprendre les tendances.

#### Support :
Pour toute question ou assistance, contactez l'équipe de support à [support@securitym2sise.com](mailto:support@securitym2sise.com).
""")