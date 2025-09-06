import streamlit as st
from config import get_config
from quiz import QuizApp
from dashboard import show_dashboard
from admin import show_admin_panel
from auth import get_authenticator

st.set_page_config(page_title="Quiz Training App",layout="wide")

def inject_custom_css():
    st.markdown("""
        <style>
            html, body, [class*="css"] { font-size: 20px; }
            h1, h2, h3 { font-size: 28px; }
            .stRadio > div, .stCheckbox > div { font-size: 20px !important; }
        </style>
    """, unsafe_allow_html=True)
    st.markdown("""
    <style>
        .reportview-container {
            margin-top: -2em;
        }
        #MainMenu {visibility: hidden;}
        .stAppDeployButton {
                visibility: hidden;
            }
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
    </style>
""", unsafe_allow_html=True)

inject_custom_css()

# 🔐 Authenticate user via email
authenticator = get_authenticator()
name, auth_status, email = authenticator.login("Login", "main")

# 🛡️ Handle login state
if auth_status is False:
    st.error("Invalid credentials")
    st.stop()
elif auth_status is None or not email:
    st.warning("Please enter your credentials")
    st.stop()

# ✅ Fetch user info from MongoDB
user_doc = authenticator.collection.find_one({"email": email})
if not user_doc:
    st.error(f"User '{email}' not found in MongoDB.")
    authenticator.logout("Logout")
    st.stop()

user_role = user_doc.get("role", "user")
st.session_state.email = email
st.session_state.name = name

# 🧭 Sidebar Navigation
st.sidebar.success(f"Welcome {user_doc['name']} ({user_role})")
authenticator.logout("Logout")

st.sidebar.title("📚 Navigation")
page = st.sidebar.radio("Go to", ["Home", "Quiz", "Dashboard", "Admin"])

config = get_config()
app = QuizApp(config)

# 🧩 Page Routing
if page == "Home":
    st.title("🏠 Welcome to the Quiz Platform")
    st.markdown(f"Hello **{user_doc['name']}**, ready to test your knowledge?")
    st.markdown("Use the sidebar to start a quiz, view your performance dashboard, or manage topics in the Admin panel.")

elif page == "Quiz":
    app.run()

elif page == "Dashboard":
    show_dashboard()

elif page == "Admin":
    if user_role != "admin":
        st.warning("Access denied. Admins only.")
        st.stop()
    show_admin_panel()
