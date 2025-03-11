import streamlit as st
from streamlit_option_menu import option_menu
from db import Database, LogDatabase
from views.analysis import analyze_logs  #
from views.data import explore_data  
from views.protocol import analyze_flows 
from views.upload import upload_page 
from views.machine_learning import machine_learning_page

from db import LogDatabase


def user_page():


    # Sidebar navigation with streamlit-option-menu
    with st.sidebar:
        # st.image("img/logo.png", use_container_width=True)
        # st.markdown("<h1 style='text-align: center;'>SecureIA Dashboard</h1>", unsafe_allow_html=True)
        # Navigation menu with icons
        selected_tab = option_menu(
            menu_title=None,  # Added menu_title parameter
            options=["Home", "Upload", "Analysis", "Datasets", "Protocol", "Machine Learning"],
            icons=["house", "arrow-up", "bar-chart", "search", "robot", "cpu"],
            menu_icon="cast",
            default_index=0,
            styles={
            "container": {"padding": "5px", "background-color": "#f0f2f6"},
            "icon": {"color": "orange", "font-size": "18px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "color": "black"},
            "nav-link-selected": {"background-color": "#4CAF50", "color": "white"},
            }
        )
    

    # Content based on selection
    if selected_tab == "Home":
        st.write("Welcome to the Security M2 SISE dashboard!")
        st.markdown("""
            **Overview:**
            - View your security logs
            - Analyze data trends
            - Explore datasets
            - Apply machine learning models
        """)

    elif selected_tab == "Upload":
        upload_page()
    elif selected_tab == "Analysis":
        st.title("Analyse des logs de sécurité")
        analyze_logs()
        
    elif selected_tab == "Datasets":
        st.title("Exploration des données")
        explore_data()
    elif selected_tab == "Protocol":  # Fixed typo in "Protocol"
        st.title("Statistiques des flux réseau par Protocol")
        analyze_flows()

    elif selected_tab == "Machine Learning":
        machine_learning_page()
    
   # Quick links section after filters and content
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📄 About")
        st.write("This dashboard is maintained by the Security M2 SISE team.")
        st.write("For more information, please visit the [GitHub repository](https://github.com/lansanacisse/security_m2sise/tree/develop).")

    with col2:
        st.markdown("###  Collaborators")
        st.write("""
        - [Lansana Cisse](https://github.com/lansanacisse)
        - [Quentin lim](https://github.com/QL2111)
        - [Juan Alfonso](https://github.com/jdalfons)
        - [Mariem Amirouch](https://www.linkedin.com/in/mariem-amirouch-b79a64256/)
        - [Riyad ISMAILI](https://github.com/riyadismaili)
        """)
        
    # st.markdown("### Quick Links")
    # col1, col2, col3 = st.columns(3)
    # with col1:
    #     if st.button("📄 Documentation"):
    #         st.write("Redirecting to documentation...")
    #         # Redirection vers la page de documentation
    #         st.session_state.current_page = "Documentation"
    #         st.experimental_rerun()
    # with col2:
    #     if st.button("🛠️ Settings"):
    #         st.write("Redirecting to settings...")
    # with col3:
    #     if st.button("📤 Logout"):
    #         st.write("Logging out...")
    #         # Add logout logic here
