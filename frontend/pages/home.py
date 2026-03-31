import streamlit as st
from utils import load_css, set_page, fetch_profile


def show():
    load_css("css/home.css")

    profile_data = fetch_profile()
    user_name = ""
    if profile_data:
        p = profile_data.get("profile", {})
        user_name = p.get("name", st.session_state.get("user", ""))

    st.markdown('<div class="brand">✦ diagnoVET</div>', unsafe_allow_html=True)

    if st.session_state.success:
        st.markdown(f'<div class="msg-success">✓ {st.session_state.success}</div>', unsafe_allow_html=True)
        st.session_state.success = ""

    st.markdown(
        f'<p class="home-user">Welcome, <span>{user_name}</span></p>',
        unsafe_allow_html=True,
    )
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── Main action buttons ──
    col1, col2 = st.columns(2, gap="small")
    with col1:
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        if st.button("📁  Upload Studies", key="btn_upload"):
            set_page("upload")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        if st.button("🐾  My Patients", key="btn_patients"):
            set_page("patients")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:32px"></div>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── Sign out ──
    st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
    if st.button("Sign out", key="btn_logout"):
        for k in ["token", "user", "profile", "error", "success",
                  "selected_patient_id", "selected_patient_name", "selected_study_id"]:
            st.session_state[k] = None if k == "token" else ""
        set_page("login")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)