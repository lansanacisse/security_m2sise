import streamlit as st
import pandas as pd
import ipaddress
from db import LogDatabase
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from matplotlib.lines import Line2D
import seaborn as sns


@st.cache_data
def get_logs():
    return LogDatabase().get_logs()

def perform_isolation_forest(pca_df, contamination=0.01):
    print(f"Training Isolation Forest with contamination={contamination}...")
    
    # Initialize and fit the model
    iso_forest = IsolationForest(
        n_estimators=100,
        max_samples='auto',
        contamination=contamination,
        random_state=42
    )
    
    # Fit and predict
    pca_df['anomaly'] = iso_forest.fit_predict(pca_df)
    
    # Convert predictions: -1 for anomalies, 1 for normal points
    # Convert to boolean for easier interpretation
    pca_df['is_anomaly'] = pca_df['anomaly'] == -1
    
    # Count anomalies
    anomaly_count = pca_df['is_anomaly'].sum()
    print(f"Detected {anomaly_count} anomalies out of {len(pca_df)} data points ({anomaly_count/len(pca_df)*100:.2f}%)")
    
    return pca_df, iso_forest

def load_and_preprocess_data():
    db = LogDatabase()
    logs = db.get_logs_sample()
    print(type(logs))
    df = logs.to_pandas()
    
    # Convert date to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Extract time features
    df['hour'] = df['Date'].dt.hour
    df['day_of_week'] = df['Date'].dt.dayofweek
    
    # Convert IP addresses to numerical values
    def ip_to_int(ip):
        try:
            return int(ipaddress.ip_address(ip))
        except:
            return np.nan
    
    print("Converting IP addresses...")
    df['IPsrc_int'] = df['IPsrc'].apply(ip_to_int)
    df['IPdst_int'] = df['IPdst'].apply(ip_to_int)
    
    # One-hot encode categorical features
    print("Encoding categorical features...")
    df = pd.get_dummies(df, columns=['Protocol', 'action'], drop_first=True)
    
    # Handle missing values
    df = df.fillna(0)
    
    return df

def visualize_results(pca_df, original_df=None):
    # Plot PCA with anomalies highlighted
    plt.figure(figsize=(12, 8))
    
    # Create scatter plot
    sns.scatterplot(
        data=pca_df,
        x='PC1',
        y='PC2',
        hue='is_anomaly',
        palette={True: 'red', False: 'blue'},
        alpha=0.5
    )
    
    plt.title('PCA with Anomalies Highlighted')
    plt.xlabel('Principal Component 1')
    plt.ylabel('Principal Component 2')
    plt.legend(title='Anomaly')
    
    plt.tight_layout()
    plt.savefig('pca_anomalies.png')
    print("Plot saved as 'pca_anomalies.png'")
    
    # If original data is provided, analyze anomalies in original context
    if original_df is not None and not pca_df['is_anomaly'].empty:
        # Get anomaly indices
        anomaly_indices = pca_df[pca_df['is_anomaly']].index
        
        # Extract anomaly samples from original data
        anomaly_samples = original_df.iloc[anomaly_indices]
        
        # Display anomalies
        st.write("Detected anomalies:")
        st.write(anomaly_samples)
        
        # Simple analysis of anomalies
        if 'action' in original_df.columns:
            st.write("\nAction distribution in anomalies:")
            st.write(anomaly_samples['action'].value_counts())
        
        if 'Protocol' in original_df.columns:
            st.write("\nProtocol distribution in anomalies:")
            st.write(anomaly_samples['Protocol'].value_counts())

def machine_learning_page():
    st.header("Machine Learning Logs Data")
    st.write("This page will contain the machine learning functionality.")
    
    import matplotlib.pyplot as plt

    def perform_pca(df, n_components):
        feature_cols = df.select_dtypes(include=[np.number]).columns
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(df[feature_cols])
        
        pca = PCA(n_components=n_components)
        pca_data = pca.fit_transform(scaled_data)
        
        pca_df = pd.DataFrame(data=pca_data, columns=[f'PC{i+1}' for i in range(n_components)])
        
        return pca_df, pca, scaler, feature_cols

    def plot_pca_results(df, n_components=5):
        pca_df, pca, scaler, feature_cols = perform_pca(df, n_components)
        
        significant_pcs = [i for i, var in enumerate(pca.explained_variance_ratio_) if var > 0]
        
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, projection='polar')
        
        values = pca_df.iloc[:, significant_pcs].mean().values
        angles = np.linspace(0, 2*np.pi, len(values), endpoint=False)
        
        values = np.concatenate((values, [values[0]]))
        angles = np.concatenate((angles, [angles[0]]))
        
        ax.plot(angles, values, 'o-', linewidth=2)
        ax.fill(angles, values, alpha=0.25)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([f'PC{i+1}' for i in significant_pcs])
        
        plt.title('PCA Components Spider Plot (Significant Components)')
        plt.tight_layout()
        st.pyplot(fig)
        
        for i in significant_pcs:
            fig = plt.figure(figsize=(10, 10))
            ax = fig.add_subplot(111, projection='polar')
            
            feature_importance = pd.DataFrame(data=pca.components_[i], index=feature_cols, columns=['Importance'])
            values = np.abs(feature_importance['Importance'].values)
            colors = ['b' if v >= 0 else 'r' for v in feature_importance['Importance'].values]
            
            angles = np.linspace(0, 2*np.pi, len(values), endpoint=False)
            
            values = np.concatenate((values, [values[0]]))
            angles = np.concatenate((angles, [angles[0]]))
            feature_names = list(feature_cols) + [feature_cols[0]]
            colors = colors + [colors[0]]
            
            ax.plot(angles, values, 'o-', linewidth=2)
            ax.fill(angles[:-1], values[:-1], alpha=0.25)
            
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(feature_cols)
            
            plt.title(f'PC{i+1} Feature Importance Spider Plot (Variance explained: {pca.explained_variance_ratio_[i]*100:.2f}%)')
            
            legend_elements = [
                Line2D([0], [0], color='b', lw=2, label='Positive weight'),
                Line2D([0], [0], color='r', lw=2, label='Negative weight')
            ]
            ax.legend(handles=legend_elements)
            
            plt.tight_layout()
            st.pyplot(fig)
        
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111)
        
        x = np.arange(len(feature_cols))
        width = 0.15
        offset = 0
        
        for i in significant_pcs:
            feature_importance = pd.DataFrame(data=pca.components_[i], index=feature_cols, columns=['Importance'])
            
            ax.bar(x + offset, feature_importance['Importance'], width, 
                   label=f'PC{i+1} ({pca.explained_variance_ratio_[i]*100:.2f}%)')
            offset += width
        
        ax.set_xlabel('Features')
        ax.set_ylabel('Importance (Weight)')
        ax.set_title('Feature Importance by Principal Component')
        ax.set_xticks(x + width * (len(significant_pcs) - 1) / 2)
        ax.set_xticklabels(feature_cols, rotation=45, ha='right')
        ax.legend()
        
        plt.tight_layout()
        st.pyplot(fig)
        
        return pca_df

    try:
        df = load_and_preprocess_data()
        
        data, pca, other = st.tabs(
        [
            "Check data",
            "Make a PCA",
            "Isolate forest"
        ])
        with data:
            st.write(df.head())
        with pca:
            st.write("PCA")
            pca_df = plot_pca_results(df)
        with other:
            st.write("Isolate forest")
            if 'pca_df' in locals():
                pca_df, iso_forest = perform_isolation_forest(pca_df)
                st.write(pca_df.head())
                visualize_results(pca_df, df)
            else:
                st.write("PCA data is not available.")
    except Exception as e:
        st.write("An error occurred during data preprocessing:")
        st.write(e)
