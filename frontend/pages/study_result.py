import streamlit as st
import requests
from utils import load_css, auth_headers, get_institution_id, back_button, API_BASE


def show():
    load_css("css/study_result.css")

    back_button("← Studies", "studies")

    result_id = st.session_state.get("selected_study_id")
    institution_id = get_institution_id()

    if not result_id or not institution_id:
        st.markdown('<div class="msg-error">⚠ Missing study or institution data.</div>', unsafe_allow_html=True)
        return

    try:
        resp = requests.get(
            f"{API_BASE}/study/results/",
            params={"institution_id": institution_id, "result_id": result_id},
            headers=auth_headers(),
            timeout=8,
        )
        if resp.status_code != 200:
            st.markdown(f'<div class="msg-error">⚠ Error loading study ({resp.status_code}).</div>', unsafe_allow_html=True)
            return
        d = resp.json()
    except requests.exceptions.ConnectionError:
        st.markdown('<div class="msg-error">⚠ Cannot reach the server.</div>', unsafe_allow_html=True)
        return

    # ── Header ──
    study_type = d.get("study_type", "Study").capitalize()
    study_date = d.get("study_date", "")[:10] if d.get("study_date") else "—"
    st.markdown(f'<div class="brand">📋 {study_type}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="subtitle">Date: {study_date}</div>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── Patient & Vet info side by side ──
    patient = d.get("patient", {})
    vet = d.get("veterinarian", {})

    col1, col2 = st.columns(2)
    with col1:
        neutered = "Yes" if patient.get("is_neutered") else "No"
        st.markdown(
            f"""<div class="info-card">
                <div class="info-card-title">🐾 Patient</div>
                <div class="info-row"><span>Name</span><strong>{patient.get('name','—')}</strong></div>
                <div class="info-row"><span>Species</span><strong>{patient.get('specie','—')}</strong></div>
                <div class="info-row"><span>Breed</span><strong>{patient.get('breed','—')}</strong></div>
                <div class="info-row"><span>Age</span><strong>{patient.get('age','—')} y/o</strong></div>
                <div class="info-row"><span>Gender</span><strong>{patient.get('gender','—')}</strong></div>
                <div class="info-row"><span>Neutered</span><strong>{neutered}</strong></div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col2:
        license_num = vet.get("license_number") or "—"
        st.markdown(
            f"""<div class="info-card">
                <div class="info-card-title">👨‍⚕️ Veterinarian</div>
                <div class="info-row"><span>Name</span><strong>{vet.get('name','—')} {vet.get('last_name','')}</strong></div>
                <div class="info-row"><span>License</span><strong>{license_num}</strong></div>
            </div>""",
            unsafe_allow_html=True,
        )

    # ── Clinical notes ──
    for field, label, icon in [
        ("observations", "Observations", "🔍"),
        ("diagnosis",    "Diagnosis",    "🩺"),
        ("recommendations", "Recommendations", "💊"),
    ]:
        value = d.get(field, "")
        if value:
            st.markdown(
                f"""<div class="clinical-block">
                    <div class="clinical-title">{icon} {label}</div>
                    <div class="clinical-text">{value}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    # ── Results table ──
    results = d.get("results", [])
    if results:
        st.markdown('<div class="section-title">🧪 Results</div>', unsafe_allow_html=True)
        header_cols = st.columns([3, 2, 2, 3])
        for col, label in zip(header_cols, ["Parameter", "Value", "Unit", "Reference Range"]):
            col.markdown(f'<div class="table-header">{label}</div>', unsafe_allow_html=True)
        st.markdown('<hr class="thin-divider">', unsafe_allow_html=True)

        for i, row in enumerate(results):
            row_cols = st.columns([3, 2, 2, 3])
            bg = "result-row-alt" if i % 2 == 0 else "result-row"
            values = [
                row.get("key", "—"),
                row.get("value", "—"),
                row.get("unit", "—"),
                row.get("reference_range") or "—",
            ]
            for col, val in zip(row_cols, values):
                col.markdown(f'<div class="{bg}">{val}</div>', unsafe_allow_html=True)

    # ── Images ──
    images = d.get("images", [])
    if images:
        st.markdown('<div class="section-title">🖼 Images</div>', unsafe_allow_html=True)
        cols = st.columns(min(len(images), 3))
        for i, img in enumerate(images):
            url = img.get("url", "")
            desc = img.get("description", "")
            with cols[i % 3]:
                # url is stored as "images/page_0_0.png"
                # served by FastAPI static files at /static/
                static_url = f"{API_BASE}/static/{url}"
                try:
                    img_resp = requests.get(static_url, headers=auth_headers(), timeout=10)
                    if img_resp.status_code == 200:
                        st.image(img_resp.content, caption=desc, width='stretch')
                    else:
                        st.markdown(
                            f'<div class="img-placeholder">🖼<br><small>Image not found</small><br><small>{desc}</small></div>',
                            unsafe_allow_html=True,
                        )
                except Exception:
                    st.markdown(
                        f'<div class="img-placeholder">🖼<br><small>Could not load image</small><br><small>{desc}</small></div>',
                        unsafe_allow_html=True,
                    )