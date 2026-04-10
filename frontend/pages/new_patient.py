import streamlit as st
from utils import load_css, set_page, auth_headers, get_institution_id, back_button, api_request, fetch_options, server_unavailable_msg


def show():
    load_css("css/new_patient.css")

    back_button("← Patients", "patients")

    st.markdown('<div class="brand">🐾 New Patient</div>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    if st.session_state.error:
        st.markdown(f'<div class="msg-error">⚠ {st.session_state.error}</div>', unsafe_allow_html=True)
        st.session_state.error = ""

    institution_id = get_institution_id()
    if not institution_id:
        st.markdown('<div class="msg-error">⚠ Could not load institution data.</div>', unsafe_allow_html=True)
        return

    # ── Fetch dropdowns ──
    species = fetch_options("/specie/")
    breeds  = fetch_options("/breed/")
    genders = fetch_options("/gender/")

    specie_map = {s["name"]: s["id"] for s in species}
    breed_map  = {b["name"]: b["id"] for b in breeds}
    gender_map = {g["name"]: g["id"] for g in genders}

    # ── Owner info ──
    st.markdown('<div class="section-title">👤 Owner</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="field-label">Name *</div>', unsafe_allow_html=True)
        owner_name = st.text_input("owner_name", label_visibility="collapsed", placeholder="John")
    with col2:
        st.markdown('<div class="field-label">Last name *</div>', unsafe_allow_html=True)
        owner_last_name = st.text_input("owner_last_name", label_visibility="collapsed", placeholder="Doe")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="field-label">Email</div>', unsafe_allow_html=True)
        owner_email = st.text_input("owner_email", label_visibility="collapsed", placeholder="owner@example.com")
    with col2:
        st.markdown('<div class="field-label">Document number</div>', unsafe_allow_html=True)
        owner_doc = st.text_input("owner_doc", label_visibility="collapsed", placeholder="DNI / Passport")

    st.markdown('<div class="field-label">Contact number</div>', unsafe_allow_html=True)
    owner_phone = st.text_input("owner_phone", label_visibility="collapsed", placeholder="+54 9 11 …")

    # ── Patient info ──
    st.markdown('<div class="section-title">🐾 Patient</div>', unsafe_allow_html=True)

    st.markdown('<div class="field-label">Name *</div>', unsafe_allow_html=True)
    patient_name = st.text_input("patient_name", label_visibility="collapsed", placeholder="Rex")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="field-label">Species *</div>', unsafe_allow_html=True)
        specie_options = ["— select —"] + list(specie_map.keys())
        specie_sel = st.selectbox("specie", specie_options, index=0, label_visibility="collapsed")
    with col2:
        st.markdown('<div class="field-label">Breed *</div>', unsafe_allow_html=True)
        breed_options = ["— select —"] + list(breed_map.keys())
        breed_sel = st.selectbox("breed", breed_options, index=0, label_visibility="collapsed")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="field-label">Age</div>', unsafe_allow_html=True)
        patient_age = st.text_input("patient_age", label_visibility="collapsed", placeholder="e.g. 3")
    with col2:
        st.markdown('<div class="field-label">Gender *</div>', unsafe_allow_html=True)
        gender_options = ["— select —"] + list(gender_map.keys())
        gender_sel = st.selectbox("gender", gender_options, index=0, label_visibility="collapsed")
    with col3:
        st.markdown('<div class="field-label">Neutered</div>', unsafe_allow_html=True)
        is_neutered = st.checkbox("Yes", key="is_neutered")

    # ── Professional info ──
    st.markdown('<div class="section-title">👨‍⚕️ Referring professional</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="field-label">Name</div>', unsafe_allow_html=True)
        prof_name = st.text_input("prof_name", label_visibility="collapsed", placeholder="Carlos")
    with col2:
        st.markdown('<div class="field-label">Last name</div>', unsafe_allow_html=True)
        prof_last_name = st.text_input("prof_last_name", label_visibility="collapsed", placeholder="Gomez")

    st.markdown('<div class="field-label">License number</div>', unsafe_allow_html=True)
    prof_license = st.text_input("prof_license", label_visibility="collapsed", placeholder="ABC123")

    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

    # ── Buttons ──
    col1, col2 = st.columns(2, gap="small")
    with col1:
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        save_clicked = st.button("Create patient", key="btn_save_patient")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("Cancel", key="btn_cancel_patient"):
            set_page("patients")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Submit ──
    if save_clicked:
        missing = []
        if not owner_name:      missing.append("owner name")
        if not owner_last_name: missing.append("owner last name")
        if not patient_name:    missing.append("patient name")
        if specie_sel == "— select —": missing.append("species")
        if breed_sel  == "— select —": missing.append("breed")
        if gender_sel == "— select —": missing.append("gender")

        if missing:
            st.session_state.error = f"Required fields missing: {', '.join(missing)}."
            st.rerun()

        payload = {
            "owner": {
                "contact_email":   owner_email or None,
                "name":            owner_name,
                "last_name":       owner_last_name,
                "document_number": owner_doc or None,
                "contact_number":  owner_phone or None,
            },
            "patient": {
                "name":       patient_name,
                "specie_id":  specie_map[specie_sel],
                "breed_id":   breed_map[breed_sel],
                "age":        patient_age or None,
                "gender_id":  gender_map[gender_sel],
                "is_neutered": is_neutered,
            },
            "professional": {
                "name":           prof_name or None,
                "last_name":      prof_last_name or None,
                "license_number": prof_license or None,
            },
        }

        resp = api_request(
            "post", "/patient/",
            params={"institution_id": institution_id},
            headers={**auth_headers(), "Content-Type": "application/json"},
            json=payload,
        )

        if resp is None:
            server_unavailable_msg()
        elif resp.status_code == 201:
            st.session_state.success = f"Patient '{patient_name}' created successfully."
            set_page("patients")
            st.rerun()
        else:
            detail = resp.json().get("detail", f"Error ({resp.status_code}).")
            st.session_state.error = detail
            st.rerun()
