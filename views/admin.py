import streamlit as st
from db import Database, UserCreate
import pandas as pd



def admin_page(db: Database):
    st.title(f"Admin Dashboard - Welcome, {st.session_state.username}!")
    st.write("This is the admin page. Only admin users can see this page.")
    
    # Empty admin page as requested
    st.write("admin")
    
    # Add user management functionality for admin
    with st.expander("User Management"):
        st.subheader("Create New User")
        new_username = st.text_input("New Username")
        new_password = st.text_input("Initial Password", type="password")
        is_admin = st.checkbox("Admin Role")
        password_change = st.checkbox("Require Password Change on First Login", value=True)
        
        if st.button("Create User"):
            if new_username and new_password:
                new_user = UserCreate(
                    username=new_username,
                    password=new_password,
                    is_admin=is_admin,
                    password_change_required=password_change
                )
                result = db.create_user(new_user)
                if result:
                    st.success(f"User {new_username} created successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to create user. Username may already exist.")
            else:
                st.warning("Username and password are required")
        
        st.subheader("All Users")
        users = db.get_all_users()
        # Convert the user list to a list of dictionaries for tabular display
        data = [
            {
            "ID": user.id,
            "Username": user.username,
            "Role": "Admin" if user.is_admin else "User",
            "Password Status": "Password change required" if user.password_change_required else "Password set",
            "Created": user.created_at,
            }
            for user in users
        ]
        
        st.table(pd.DataFrame(data))