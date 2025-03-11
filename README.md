# Sise Opsie 👁️  
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)  
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)  
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)  

Aplicación de análisis de logs de seguridad y detección de intrusiones mediante técnicas de Machine Learning.  
**Deploy en Hugging Face:** [Ver aplicación](https://huggingface.co/spaces/tu-usuario/sise-opsie)  

---

## Descripción  
Proyecto colaborativo entre estudiantes de **OPSIE** y **SISE** para:  
- Analizar registros de ataques simulados.  
- Detectar anomalías con algoritmos como **Isolation Forest** y **Análisis de Componentes Principales (ACP)**.  
- Clasificar intrusiones y determinar patrones críticos.  
- Permitir carga de nuevos datos en formato **Parquet** (hasta 200 MB).  

---

## Características Principales  
✅ **Análisis de logs** con visualización interactiva.  
✅ **Machine Learning integrado**:  
   - Detección de outliers con *Isolation Forest*.  
   - Reducción de dimensionalidad mediante *ACP*.  
✅ **Carga dinámica de datos**: Sube tus archivos Parquet para análisis instantáneo.  
✅ **Despliegue en la nube**: Optimizado para Hugging Face Spaces con Docker.  

---

## Tecnologías Utilizadas  
- **Python**: Pandas, Scikit-learn, Streamlit.  
- **Machine Learning**: Isolation Forest, PCA.  
- **Despliegue**: Docker, Hugging Face Spaces.  
- **Formato de datos**: Apache Parquet.  

---

## Requisitos  
1. **Docker** instalado (para despliegue local).  
2. Archivos en formato **Parquet** (estructura de columnas predefinida).  
3. Recursos:  
   - Memoria suficiente para procesar archivos de **hasta 200 MB**.  

---

## Ejecución Local  
1. Clona el repositorio:  
   ```bash
   git clone https://github.com/tu-repositorio/sise-opsie.git
   cd sise-opsie