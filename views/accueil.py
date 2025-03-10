# Import packages
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Security M2 SISE",
    page_icon="🔒",
    layout="centered",
)

# Tabs configuration
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home", "📈 Analysis", "🔍 Datasets", "🤖 Machine Learning"])

# Home Page
with tab1:
    st.write("Welcome to the Security M2 SISE dashboard!")

# Training Models Page
with tab2:
    st.write("This section will contain model analysis.")

# Predict Page
with tab3:
    st.write("Here you can explore datasets.")

# Metrics Page
with tab4:
    st.write("Using the machine Model .")
