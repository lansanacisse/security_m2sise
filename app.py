import streamlit as st
from views.user import user_page


# Initialize session state
def init_session_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.is_admin = False
        st.session_state.username = None
        st.session_state.user_id = None
        st.session_state.password_change_required = False


# Main app
def main():
    # Initialize database

    # Initialize session state
    init_session_state()
    
    # Initialize page
    user_page()


if __name__ == "__main__":
    main()
