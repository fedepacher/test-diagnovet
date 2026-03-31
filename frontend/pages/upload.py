import streamlit as st
import requests
from utils import load_css, back_button, auth_headers, get_institution_id, api_request, server_unavailable_msg, API_BASE


def show():
    load_css("css/upload.css")

    back_button("← Home", "home")

    st.markdown('<div class="brand">📁 Upload Studies</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Upload one or more study files</div>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    institution_id = get_institution_id()
    if not institution_id:
        st.markdown('<div class="msg-error">⚠ Could not load institution data.</div>', unsafe_allow_html=True)
        return

    uploaded_files = st.file_uploader(
        "Choose files",
        accept_multiple_files=True,
        type=None,
        label_visibility="collapsed",
    )

    if uploaded_files:
        st.markdown(
            f'<p class="upload-count">{len(uploaded_files)} file(s) selected</p>',
            unsafe_allow_html=True,
        )
        for f in uploaded_files:
            st.markdown(f'<div class="file-chip">📄 {f.name}</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="small")
    with col1:
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        upload_clicked = st.button("Upload", key="btn_do_upload", disabled=not uploaded_files)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("Cancel", key="btn_upload_cancel"):
            from utils import set_page
            set_page("home")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if upload_clicked and uploaded_files:
        files_payload = [
            ("files", (f.name, f.getvalue(), f.type or "application/octet-stream"))
            for f in uploaded_files
        ]
        with st.spinner("Uploading..."):
            resp = api_request("post", "/patient/upload_patient",
                params={"institution_id": institution_id},
                headers=auth_headers(),
                files=files_payload,
                timeout=120,
            )
        if resp is None:
            server_unavailable_msg()
        elif resp.status_code in (200, 201):
            st.markdown('<div class="msg-success">✓ Files uploaded successfully.</div>', unsafe_allow_html=True)
        else:
            detail = resp.json().get("detail", f"Upload failed ({resp.status_code}).")
            st.markdown(f'<div class="msg-error">⚠ {detail}</div>', unsafe_allow_html=True)