import streamlit as st
from utils import load_css, wait_for_backend
from pages import login, register, home, patients, studies, study_result, upload

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="diagnoVET",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ───────────────────────────────────────────────────────────────
load_css("css/global.css")

# ── Session state init ───────────────────────────────────────────────────────
for key, default in {
    "page": "login",
    "token": None,
    "user": None,
    "profile": None,
    "backend_ready": False,
    "error": "",
    "success": "",
    "selected_patient_id": None,
    "selected_patient_name": None,
    "selected_study_id": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Logo (shown on every page) ───────────────────────────────────────────────
st.markdown('<div style="text-align:center; margin-top:20px; margin-bottom:8px;">', unsafe_allow_html=True)
st.image("resources/logo.png", width=200)
st.markdown('</div>', unsafe_allow_html=True)

# ── Wait for backend before rendering anything ───────────────────────────────
if not wait_for_backend():
    st.stop()

# ── Router ───────────────────────────────────────────────────────────────────
page = st.session_state.page

if page == "login":
    login.show()
elif page == "register":
    register.show()
elif page == "home":
    home.show()
elif page == "patients":
    patients.show()
elif page == "studies":
    studies.show()
elif page == "study_result":
    study_result.show()
elif page == "upload":
    upload.show()