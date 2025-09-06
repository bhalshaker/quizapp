import streamlit as st
import pandas as pd
import json
from mongo_storage import (
    get_users, delete_user,
    save_topic, get_all_topics, delete_topic, validate_questions,
    create_user, update_user
)
import streamlit_authenticator_mongo as stauth

def show_admin_panel():
    st.title("🛠️ Admin Panel")

    tab1, tab2, tab3, tab4 = st.tabs(["Users", "Topics", "Analytics", "Manage Users"])

    # 👥 User Management
    with tab1:
        st.subheader("👥 View & Delete Users")
        users = get_users()
        if users:
            st.dataframe(pd.DataFrame(users), width='stretch')
        else:
            st.info("No users found.")

        col1, col2 = st.columns(2)
        with col1:
            delete_u = st.text_input("Delete user by email")
        with col2:
            if st.button("Delete User"):
                if delete_user(delete_u):
                    st.success(f"User '{delete_u}' deleted.")
                else:
                    st.warning("User not found.")

    # 📤 Topic Upload
    with tab2:
        st.subheader("📤 Upload Question Set (Topic)")
        uploaded_file = st.file_uploader("Upload JSON file of questions", type="json")
        topic_name = st.text_input("Topic unique name (e.g., Physics 101 - Midterm)")

        if uploaded_file and topic_name and st.button("Save Topic"):
            try:
                questions = json.load(uploaded_file)
                issues = validate_questions(questions)
                if issues:
                    st.error("Validation failed:")
                    for issue in issues:
                        st.markdown(f"- {issue}")
                else:
                    for q in questions:
                        q.setdefault("category", "Uncategorized")
                        q.setdefault("difficulty", "Unknown")
                    topic_id = save_topic(topic_name, questions)
                    st.success(f"✅ Topic '{topic_name}' saved with ID: {topic_id}")
            except Exception as e:
                st.exception(e)

        st.subheader("📚 Existing Topics")
        topics = get_all_topics()
        if not topics:
            st.info("No topics found.")
        else:
            for t in topics:
                with st.expander(f"{t['topic_name']} — {t['topic_id']}"):
                    if st.button("Delete", key=f"del_{t['topic_id']}"):
                        if delete_topic(t["topic_id"]):
                            st.success("Deleted")
                        else:
                            st.error("Delete failed")

    # 📊 Topic Analytics
    with tab3:
        st.subheader("📊 Topic Overview")
        topics = get_all_topics()
        df = pd.DataFrame(topics)
        if df.empty:
            st.info("No topics to show.")
        else:
            st.dataframe(df, width='stretch')

    # 🧑‍💼 Manage Users
    with tab4:
        st.subheader("🧑‍💼 Create New User")
        new_email = st.text_input("Email")
        new_name = st.text_input("Full Name")
        new_password = st.text_input("Password", type="password")
        new_role = st.selectbox("Role", ["admin", "user", "teacher"])

        if st.button("Create User"):
            if not all([new_email, new_name, new_password]):
                st.warning("Please fill in all fields.")
            else:
                hashed_pw = stauth.Hasher([new_password]).generate()[0]
                success = create_user(new_email, new_name, hashed_pw, new_role)
                if success:
                    st.success(f"User '{new_email}' created.")
                else:
                    st.error("User already exists or creation failed.")

        st.subheader("✏️ Update Existing User")
        update_email = st.text_input("User Email to Update")
        update_name = st.text_input("New Name (optional)")
        update_role = st.selectbox("New Role", ["admin", "user", "teacher"])
        update_password = st.text_input("New Password (optional)", type="password")

        if st.button("Update User"):
            updates = {}
            if update_name:
                updates["name"] = update_name
            if update_role:
                updates["role"] = update_role
            if update_password:
                updates["password"] = stauth.Hasher([update_password]).generate()[0]

            success = update_user(update_email, updates)
            if success:
                st.success(f"User '{update_email}' updated.")
            else:
                st.error("User not found or update failed.")
