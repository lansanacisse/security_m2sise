# Sise Opsie 👁️  
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)  
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)  
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)  

Application d'analyse des logs de sécurité et de détection d'intrusions à l'aide de techniques de Machine Learning.  
**Déploiement sur Hugging Face :** [Voir l'application](https://huggingface.co/spaces/jdalfonso/sise-opsie)  

---

## Description  
Projet collaboratif entre les étudiants de **OPSIE** et **SISE** pour :  
- Analyser les journaux (logs) d'attaques simulées.  
- Détecter les anomalies avec des algorithmes tels que **Isolation Forest** et **Analyse en Composantes Principales (ACP)**.  
- Classifier les intrusions et identifier les schémas critiques.  
- Permettre le chargement dynamique de nouveaux fichiers au format **Parquet** (jusqu'à 200 Mo).  

---

## Fonctionnalités principales  
✅ **Analyse des logs** avec visualisation interactive.  
✅ **Machine Learning intégré** :  
   - Détection d'anomalies avec *Isolation Forest*.  
   - Réduction de la dimensionalité grâce à l'*ACP*.  
✅ **Chargement dynamique de données** : Importez vos fichiers Parquet pour une analyse instantanée.  
✅ **Déploiement dans le cloud** : Optimisé pour Hugging Face Spaces avec Docker.  

---

## Technologies utilisées  
- **Python** : Pandas, Scikit-learn, Streamlit.  
- **Machine Learning** : Isolation Forest, ACP.  
- **Déploiement** : Docker, Hugging Face Spaces.  
- **Format de données** : Apache Parquet.  

---

## Prérequis  
1. **Docker** installé (pour un déploiement local).  
2. Fichiers au format **Parquet** (structure de colonnes prédéfinie).  
3. Ressources nécessaires :  
   - Mémoire suffisante pour traiter des fichiers allant **jusqu'à 200 Mo**.  

---

## Exécution locale  
1. Clonez le dépôt :  
   ```bash
   git clone https://github.com/lansanacisse/security_m2sise.git
   cd sise-opsie