import streamlit as st
import requests
from utils import load_css, set_page, auth_headers, get_institution_id, back_button, API_BASE

STUDY_ICONS = {
    "analysis": "🧪",
    "eco": "🫀",
    "xray": "🩻",
    "radiography": "🩻",
    "ultrasound": "🔊",
}


def show():
    load_css("css/studies.css")

    patient_name = st.session_state.get("selected_patient_name", "Patient")
    patient_id = st.session_state.get("selected_patient_id")

    back_button("← Patients", "patients")

    st.markdown(f'<div class="brand">Studies — {patient_name}</div>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    if not patient_id:
        st.markdown('<div class="msg-error">⚠ No patient selected.</div>', unsafe_allow_html=True)
        return

    institution_id = get_institution_id()
    if not institution_id:
        st.markdown('<div class="msg-error">⚠ Could not load institution data.</div>', unsafe_allow_html=True)
        return

    try:
        resp = requests.get(
            f"{API_BASE}/study/",
            params={"institution_id": institution_id, "patient_id": patient_id},
            headers=auth_headers(),
            timeout=8,
        )
        if resp.status_code != 200:
            st.markdown(f'<div class="msg-error">⚠ Error loading studies ({resp.status_code}).</div>', unsafe_allow_html=True)
            return

        data = resp.json()
        items = data.get("items", [])

    except requests.exceptions.ConnectionError:
        st.markdown('<div class="msg-error">⚠ Cannot reach the server.</div>', unsafe_allow_html=True)
        return

    if not items:
        st.markdown('<p class="empty-state">No studies found for this patient.</p>', unsafe_allow_html=True)
        return

    st.markdown(f'<p class="studies-count">{len(items)} study(ies) found</p>', unsafe_allow_html=True)

    for study in items:
        study_type = study.get("study_type", "study")
        icon = STUDY_ICONS.get(study_type.lower(), "📋")
        label = f"{icon} **{study_type.capitalize()}** — Study ID: {study['id']}"

        st.markdown('<div class="study-btn">', unsafe_allow_html=True)
        if st.button(label, key=f"study_{study['id']}", use_container_width=True):
            st.session_state.selected_study_id = study["id"]
            set_page("study_result")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)