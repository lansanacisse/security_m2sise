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


## Déploiement

L'application est disponible sur Hugging Face via le lien suivant :  
[Lien vers l'application sur Hugging Face](https://huggingface.co/spaces/jdalfonso/sise-opsie)

Pour déployer l'application localement avec Docker, suivez les étapes suivantes :

```bash
docker build -t security-challenge-app .
docker run -p 7860:7860 security-challenge-app
```
Vous pouvez également exécuter l'application localement en utilisant un environnement Python 3.11 :
```
streamlit run app.py
```

### Exécution locale
1. Clonez le dépôt :

```
git clone https://github.com/lansanacisse/security_m2sise.git
cd sise-opsie
```
2. Installez les dépendances nécessaires et exécutez l'application.


## Deployment
L'application est disponible sur Hugging faces sur le lien 
(https://huggingface.co/spaces/jdalfonso/sise-opsie) 

```bash

docker build -t security-challenge-app .
```

```bash

docker run -p 7860:7860 security-challenge-app

```
---

## Exécution locale

Pour exécuter l'application localement, suivez les étapes ci-dessous :

### 1. Cloner le dépôt
Commencez par cloner le dépôt GitHub sur votre machine locale :
```bash
git clone https://github.com/lansanacisse/security_m2sise.git
cd security_m2sise
```

### 2. Configurer l'environnement Python
Assurez-vous d'avoir Python 3.11 installé, puis créez un environnement virtuel et activez-le :

```bash

python3.11 -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate

```

### 3. Installer les dépendances
Installez les bibliothèques nécessaires à partir du fichier requirements.txt :

```bash
pip install -r requirements.txt
```
### 4. Lancer l'application
Démarrez l'application Streamlit avec la commande suivante :

```bash
streamlit run app.py
```

### 5. Accéder à l'application
Une fois l'application lancée, ouvrez votre navigateur et accédez à l'adresse suivante :
<br> http://localhost:8501


## Collaborateurs

Ce projet a été développé en collaboration par les contributeurs suivants :

- **Lansana Cisse** : [Profil GitHub](https://github.com/lansanacisse)  
- **Quentin Lim** : [Profil GitHub](https://github.com/QL2111)  
- **Juan Alfonso** : [Profil GitHub](https://github.com/jdalfons)  
- **Mariem Amirouch** : [Profil LinkedIn](https://www.linkedin.com/in/mariem-amirouch-b79a64256/)  
- **Riyad ISMAILI** : [Profil GitHub](https://github.com/riyadismaili)  