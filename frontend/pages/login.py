import streamlit as st
import requests
from pathlib import Path

from utils import load_css, set_page, api_request, server_unavailable_msg, API_BASE


def show():
    load_css("css/login.css")

    st.markdown('<div class="brand">✦ diagnoVET</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Sign in to continue</div>', unsafe_allow_html=True)

    if st.session_state.error:
        st.markdown(f'<div class="msg-error">⚠ {st.session_state.error}</div>', unsafe_allow_html=True)

    if st.session_state.success:
        st.markdown(f'<div class="msg-success">✓ {st.session_state.success}</div>', unsafe_allow_html=True)

    st.markdown('<div class="field-label">Email or username</div>', unsafe_allow_html=True)
    identifier = st.text_input("identifier", label_visibility="collapsed", placeholder="you@example.com")

    st.markdown('<div class="field-label">Password</div>', unsafe_allow_html=True)
    password = st.text_input("password", label_visibility="collapsed", type="password", placeholder="••••••••")

    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="small")
    with col1:
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        login_clicked = st.button("Sign in", key="btn_login")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        register_clicked = st.button("Register", key="btn_go_register")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Actions ──
    if login_clicked:
        if not identifier or not password:
            st.session_state.error = "Please fill in all fields."
            st.rerun()

        try:
            resp = api_request("post", "/login", data={"username": identifier, "password": password})
            if resp is None:
                server_unavailable_msg()
                st.stop()
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.token = data.get("access_token")
                st.session_state.user = identifier
                st.session_state.error = ""
                set_page("home")
                st.rerun()
            elif resp.status_code == 401:
                st.session_state.error = "Invalid credentials. Please try again."
                st.rerun()
            else:
                detail = resp.json().get("detail", "Login failed.")
                st.session_state.error = detail
                st.rerun()
        except Exception:
            st.session_state.error = "Unexpected error. Please try again."
            st.rerun()

    if register_clicked:
        set_page("register")
        st.rerun()