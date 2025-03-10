import streamlit as st
from db import Database, UserCreate


def login_page(db: Database):
    st.title("Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    import time  # ensure time is imported

    if st.button("Login"):
        user = db.authenticate_user(username, password)
        if user:
            # Set session expiration time (10 minutes from now)
            st.session_state.login_expiry = time.time() + 600  # 600 seconds = 10 minutes

            st.session_state.logged_in = True
            st.session_state.username = user.username
            st.session_state.user_id = user.id
            st.session_state.is_admin = user.is_admin
            st.session_state.password_change_required = user.password_change_required
            st.success(f"Welcome {user.username}!")
            st.rerun()
        else:
            st.error("Invalid username or password")
            


def change_password_page(db: Database):
    st.title("Change Password")
    st.write("You need to change your password before continuing.")
    
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    
    if st.button("Change Password"):
        if not new_password:
            st.error("Password cannot be empty")
        elif new_password != confirm_password:
            st.error("Passwords do not match")
        else:
            success = db.change_password(st.session_state.user_id, new_password)
            if success:
                st.session_state.password_change_required = False
                st.success("Password changed successfully!")
                st.rerun()
            else:
                st.error("Failed to change password")