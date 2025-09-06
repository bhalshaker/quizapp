import streamlit as st
from quiz import QuizApp
from config import get_config

# ✅ Must be first to apply layout
st.set_page_config(layout="wide")

# ✅ Inject custom font styling
def inject_custom_css():
    st.markdown("""
        <style>
            html, body, [class*="css"] {
                font-size: 18px;
            }
            h1, h2, h3 {
                font-size: 28px;
            }
            .stRadio > div, .stCheckbox > div {
                font-size: 18px !important;
            }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

config = get_config()
app = QuizApp(config)
app.run()
