import streamlit as st
import requests
from datetime import date

from utils import load_css, set_page, fetch_options, API_BASE


def show():
    load_css("css/register.css")

    countries = fetch_options("/country/")
    genders   = fetch_options("/gender/")
    roles     = fetch_options("/role/")

    country_map = {c["name"]: c["id"] for c in countries}
    gender_map  = {g["name"]: g["id"] for g in genders}
    role_map    = {r["name"]: r["id"] for r in roles}

    # Ensure selects always start at index 0 when entering the register page
    for key, options in [
        ("reg_gender",  ["— select —"] + list(gender_map.keys())),
        ("reg_country", ["— select —"] + list(country_map.keys())),
        ("reg_role",    ["— select —"] + list(role_map.keys())),
    ]:
        if key not in st.session_state:
            st.session_state[key] = "— select —"

    st.markdown('<div class="brand">✦ Create account</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Fill in your details below</div>', unsafe_allow_html=True)

    if st.session_state.error:
        st.markdown(f'<div class="msg-error">⚠ {st.session_state.error}</div>', unsafe_allow_html=True)

    # ── Account credentials ──
    st.markdown('<div class="section-title">Account</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="field-label">Email *</div>', unsafe_allow_html=True)
        email = st.text_input("email", label_visibility="collapsed", placeholder="you@example.com")
    with col2:
        st.markdown('<div class="field-label">Username *</div>', unsafe_allow_html=True)
        username = st.text_input("username", label_visibility="collapsed", placeholder="johndoe")

    st.markdown('<div class="field-label">Password *</div>', unsafe_allow_html=True)
    password = st.text_input("reg_password", label_visibility="collapsed", type="password", placeholder="••••••••")

    # ── Personal info ──
    st.markdown('<div class="section-title">Personal info</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="field-label">Name *</div>', unsafe_allow_html=True)
        name = st.text_input("name", label_visibility="collapsed", placeholder="John")
    with col2:
        st.markdown('<div class="field-label">Last name *</div>', unsafe_allow_html=True)
        last_name = st.text_input("last_name", label_visibility="collapsed", placeholder="Doe")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="field-label">Birthdate *</div>', unsafe_allow_html=True)
        birthdate = st.date_input(
            "birthdate",
            label_visibility="collapsed",
            value=date(2000, 1, 1),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
        )
    with col2:
        st.markdown('<div class="field-label">Gender</div>', unsafe_allow_html=True)
        gender_options = ["— select —"] + list(gender_map.keys())
        gender_sel = st.selectbox("gender", gender_options, index=0, key="reg_gender", label_visibility="collapsed")

    # ── Location & contact ──
    st.markdown('<div class="section-title">Location & contact</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="field-label">Country *</div>', unsafe_allow_html=True)
        country_options = ["— select —"] + list(country_map.keys())
        country_sel = st.selectbox("country", country_options, index=0, key="reg_country", label_visibility="collapsed")
    with col2:
        st.markdown('<div class="field-label">Contact number</div>', unsafe_allow_html=True)
        contact_number = st.text_input("contact_number", label_visibility="collapsed", placeholder="+54 9 11 …")

    st.markdown('<div class="field-label">Document number *</div>', unsafe_allow_html=True)
    document_number = st.text_input("document_number", label_visibility="collapsed", placeholder="DNI / Passport")

    # ── Role & institution ──
    st.markdown('<div class="section-title">Role & institution</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="field-label">Role</div>', unsafe_allow_html=True)
        role_options = ["— select —"] + list(role_map.keys())
        role_sel = st.selectbox("role", role_options, index=0, key="reg_role", label_visibility="collapsed")
    with col2:
        st.markdown('<div class="field-label">Institution *</div>', unsafe_allow_html=True)
        institution = st.text_input("institution", label_visibility="collapsed", placeholder="Institution")

    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="small")
    with col1:
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        register_clicked = st.button("Create account", key="btn_register")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        cancel_clicked = st.button("Cancel", key="btn_cancel")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Actions ──
    if cancel_clicked:
        for k in ["reg_gender", "reg_country", "reg_role"]:
            st.session_state.pop(k, None)
        set_page("login")
        st.rerun()

    if register_clicked:
        missing = []
        if not email:            missing.append("email")
        if not username:         missing.append("username")
        if not password:         missing.append("password")
        if not name:             missing.append("name")
        if not last_name:        missing.append("last name")
        if not document_number:  missing.append("document number")
        if not institution:      missing.append("institution")
        if country_sel == "— select —":
            missing.append("country")

        if missing:
            st.session_state.error = f"Required fields missing: {', '.join(missing)}."
            st.rerun()

        payload = {
            "email": email,
            "username": username,
            "password": password,
            "name": name,
            "last_name": last_name,
            "birthdate": birthdate.isoformat(),
            "country_id": country_map[country_sel],
            "document_number": document_number,
            "institution": institution,
            "gender_id": gender_map.get(gender_sel) if gender_sel != "— select —" else None,
            "role_id": role_map.get(role_sel) if role_sel != "— select —" else None,
            "contact_number": contact_number or None,
        }

        try:
            resp = requests.post(f"{API_BASE}/user/", data=payload, timeout=8)

            if resp.status_code == 201:
                for k in ["reg_gender", "reg_country", "reg_role"]:
                    st.session_state.pop(k, None)
                st.session_state.error = ""
                st.session_state.success = f"Account created successfully. Please sign in, {name}!"
                set_page("login")
                st.rerun()

            elif resp.status_code == 400:
                detail = resp.json().get("detail", "Registration error.")
                st.session_state.error = detail
                st.rerun()

            else:
                detail = resp.json().get("detail", "Unexpected error. Please try again.")
                st.session_state.error = detail
                st.rerun()

        except requests.exceptions.ConnectionError:
            st.session_state.error = "Cannot reach the server. Is the API running?"
            st.rerun()