import streamlit as st
from utils import load_css, set_page, auth_headers, get_institution_id, back_button, api_request, server_unavailable_msg


def show():
    load_css("css/patients.css")

    back_button("← Home", "home")

    st.markdown('<div class="brand">🐾 My Patients</div>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    institution_id = get_institution_id()
    if not institution_id:
        st.markdown('<div class="msg-error">⚠ Could not load institution data.</div>', unsafe_allow_html=True)
        return

    # ── Session state defaults ──
    for key, default in {
        "patient_search": "",
        "patients_page": 1,
        "patient_order_by": "",
        "patient_order_dir": "asc",
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    # ── Search bar ──
    search_input = st.text_input(
        "Search patients",
        value=st.session_state.patient_search,
        placeholder="🔍 Search by name...",
        key="patient_search_input",
        label_visibility="collapsed",
    )

    if search_input != st.session_state.patient_search:
        st.session_state.patient_search = search_input
        st.session_state.patients_page = 1
        st.rerun()

    # ── New Patient button ──
    st.markdown('<div class="btn-new-patient">', unsafe_allow_html=True)
    if st.button("➕ New Patient", key="btn_new_patient"):
        set_page("new_patient")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Sort controls ──
    st.markdown('<div class="sort-row">', unsafe_allow_html=True)
    col_name, col_date, col_spacer = st.columns([2, 2, 1])

    with col_name:
        active = st.session_state.patient_order_by == "name"
        if active:
            label = "🔤 A→Z" if st.session_state.patient_order_dir == "asc" else "🔤 Z→A"
        else:
            label = "🔤 A-Z"
        st.markdown(f'<div class="{"btn-sort-active" if active else "btn-sort"}">', unsafe_allow_html=True)
        if st.button(label, key="sort_name"):
            if active:
                st.session_state.patient_order_dir = "desc" if st.session_state.patient_order_dir == "asc" else "asc"
            else:
                st.session_state.patient_order_by  = "name"
                st.session_state.patient_order_dir = "asc"
            st.session_state.patients_page = 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_date:
        active = st.session_state.patient_order_by == "created_at"
        if active:
            label = "🕒 Newest" if st.session_state.patient_order_dir == "desc" else "🕒 Oldest"
        else:
            label = "🕒 Recent"
        st.markdown(f'<div class="{"btn-sort-active" if active else "btn-sort"}">', unsafe_allow_html=True)
        if st.button(label, key="sort_date"):
            if active:
                st.session_state.patient_order_dir = "desc" if st.session_state.patient_order_dir == "asc" else "asc"
            else:
                st.session_state.patient_order_by  = "created_at"
                st.session_state.patient_order_dir = "desc"  # default: newest first
            st.session_state.patients_page = 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # close sort-row

    # ── API request ──
    limit    = 10
    page_num = st.session_state.patients_page

    params = {"page": page_num, "limit": limit, "institution_id": institution_id}
    if st.session_state.patient_search:
        params["name"] = st.session_state.patient_search
    if st.session_state.patient_order_by:
        params["order_by"]  = st.session_state.patient_order_by
        params["order_dir"] = st.session_state.patient_order_dir

    resp = api_request("get", "/patient/", params=params, headers=auth_headers())
    if resp is None:
        server_unavailable_msg()
        return
    if resp.status_code != 200:
        st.markdown(f'<div class="msg-error">⚠ Error loading patients ({resp.status_code}).</div>', unsafe_allow_html=True)
        return

    data        = resp.json()
    items       = data.get("items", [])
    pagination  = data.get("pagination", {})
    total_pages = pagination.get("totalPages", 1)
    total       = pagination.get("total", 0)

    # ── Results header ──
    if st.session_state.patient_search:
        st.markdown(
            f'<p class="patients-count">Found {total} result(s) for "<strong>{st.session_state.patient_search}</strong>"</p>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f'<p class="patients-count">{total} patient(s)</p>', unsafe_allow_html=True)

    if not items:
        st.markdown('<p class="empty-state">No patients found.</p>', unsafe_allow_html=True)
        return

    # ── Patient list ──
    for patient in items:
        neutered = "✓ Neutered" if patient.get("is_neutered") else "✗ Not neutered"
        label = (
            f"**{patient['name']}**  \n"
            f"{patient.get('specie','')} · {patient.get('breed','')} · "
            f"{patient.get('age','')} y/o · {patient.get('gender','')} · {neutered}"
        )
        st.markdown('<div class="patient-btn">', unsafe_allow_html=True)
        if st.button(label, key=f"patient_{patient['id']}", use_container_width=True):
            st.session_state.selected_patient_id   = patient["id"]
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