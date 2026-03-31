import streamlit as st
import requests
from utils import load_css, set_page, auth_headers, get_institution_id, back_button, API_BASE


def show():
    load_css("css/patients.css")

    back_button("← Home", "home")

    st.markdown('<div class="brand">🐾 My Patients</div>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    institution_id = get_institution_id()
    if not institution_id:
        st.markdown('<div class="msg-error">⚠ Could not load institution data.</div>', unsafe_allow_html=True)
        return

    if "patients_page" not in st.session_state:
        st.session_state.patients_page = 1

    limit = 10
    page_num = st.session_state.patients_page

    try:
        resp = requests.get(
            f"{API_BASE}/patient/",
            params={"page": page_num, "limit": limit, "institution_id": institution_id},
            headers=auth_headers(),
            timeout=8,
        )
        if resp.status_code != 200:
            st.markdown(f'<div class="msg-error">⚠ Error loading patients ({resp.status_code}).</div>', unsafe_allow_html=True)
            return

        data = resp.json()
        items = data.get("items", [])
        pagination = data.get("pagination", {})
        total_pages = pagination.get("totalPages", 1)
        total = pagination.get("total", 0)

    except requests.exceptions.ConnectionError:
        st.markdown('<div class="msg-error">⚠ Cannot reach the server.</div>', unsafe_allow_html=True)
        return

    if not items:
        st.markdown('<p class="empty-state">No patients found for your institution.</p>', unsafe_allow_html=True)
        return

    st.markdown(f'<p class="patients-count">{total} patient(s) found</p>', unsafe_allow_html=True)

    for patient in items:
        neutered = "✓ Neutered" if patient.get("is_neutered") else "✗ Not neutered"
        label = (
            f"**{patient['name']}**  \n"
            f"{patient.get('specie','')} · {patient.get('breed','')} · "
            f"{patient.get('age','')} y/o · {patient.get('gender','')} · {neutered}"
        )
        st.markdown('<div class="patient-btn">', unsafe_allow_html=True)
        if st.button(label, key=f"patient_{patient['id']}", use_container_width=True):
            st.session_state.selected_patient_id = patient["id"]
            st.session_state.selected_patient_name = patient["name"]
            set_page("studies")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Pagination ──
    if total_pages > 1:
        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        with col_prev:
            st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
            if st.button("← Prev", key="prev_page", disabled=page_num <= 1):
                st.session_state.patients_page -= 1
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_info:
            st.markdown(
                f'<p style="text-align:center; color:#666; font-size:0.85rem; padding-top:14px;">Page {page_num} of {total_pages}</p>',
                unsafe_allow_html=True,
            )
        with col_next:
            st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
            if st.button("Next →", key="next_page", disabled=page_num >= total_pages):
                st.session_state.patients_page += 1
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)