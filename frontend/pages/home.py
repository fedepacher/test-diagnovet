import streamlit as st
from utils import load_css, set_page, fetch_profile, auth_headers, api_request

CREATE_NEW = "➕ Create new institution"


def _fetch_user_institutions() -> list[dict]:
    resp = api_request("get", "/institution/", headers=auth_headers(), show_wakeup=False)
    if resp and resp.status_code == 200:
        return resp.json()
    return []


def _create_institution(name: str) -> dict | None:
    resp = api_request("post", "/institution/", params={"name": name}, headers=auth_headers())
    if resp and resp.status_code == 201:
        return resp.json()
    return None


def show():
    load_css("css/home.css")

    profile_data = fetch_profile()
    user_name = ""
    default_institution_name = None

    if profile_data:
        p = profile_data.get("profile", {})
        user_name = p.get("name", st.session_state.get("user", ""))
        inst = profile_data.get("institutions", {})
        if inst:
            default_institution_name = inst.get("name")

    st.markdown('<div class="brand">✦ diagnoVET</div>', unsafe_allow_html=True)

    if st.session_state.success:
        st.markdown(f'<div class="msg-success">✓ {st.session_state.success}</div>', unsafe_allow_html=True)
        st.session_state.success = ""

    st.markdown(
        f'<p class="home-user">Welcome, <span>{user_name}</span></p>',
        unsafe_allow_html=True,
    )
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── Institution selector ──
    institutions = _fetch_user_institutions()
    inst_map     = {i["name"]: i["id"] for i in institutions}
    inst_options = list(inst_map.keys()) + [CREATE_NEW]

    # Use a separate internal key to avoid widget/state conflict
    if "home_institution_value" not in st.session_state:
        st.session_state.home_institution_value = (
            default_institution_name
            if default_institution_name and default_institution_name in inst_map
            else inst_options[0]
        )

    # Clamp index in case options changed
    default_index = (
        inst_options.index(st.session_state.home_institution_value)
        if st.session_state.home_institution_value in inst_options else 0
    )

    st.markdown('<div class="field-label">Active institution</div>', unsafe_allow_html=True)
    institution_sel = st.selectbox(
        "institution",
        inst_options,
        index=default_index,
        key="home_institution_widget",   # widget key — never set manually
        label_visibility="collapsed",
    )
    # Sync to internal value key
    st.session_state.home_institution_value = institution_sel

    # ── Create new institution inline ──
    if institution_sel == CREATE_NEW:
        st.markdown('<div class="field-label">New institution name *</div>', unsafe_allow_html=True)
        new_inst_name = st.text_input(
            "new_inst_name_home", label_visibility="collapsed",
            placeholder="Enter institution name…"
        )
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        create_clicked = st.button("Create institution", key="btn_create_inst_home", disabled=not new_inst_name)
        st.markdown('</div>', unsafe_allow_html=True)

        if create_clicked and new_inst_name:
            with st.spinner("Creating…"):
                result = _create_institution(new_inst_name)
            if result:
                st.session_state.pop("profile", None)
                # Set internal value — safe because widget key is different
                st.session_state.home_institution_value = new_inst_name
                # Reset widget by removing its key so it re-renders with new options
                st.session_state.pop("home_institution_widget", None)
                st.markdown(f'<div class="msg-success">✓ Institution "{new_inst_name}" created.</div>', unsafe_allow_html=True)
                st.rerun()
            else:
                st.markdown('<div class="msg-error">⚠ Could not create institution.</div>', unsafe_allow_html=True)

        selected_institution_id = None  # can't navigate until created
    else:
        selected_institution_id = inst_map.get(institution_sel)
        st.session_state.active_institution_id = selected_institution_id

    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

    # ── Main action buttons ──
    can_navigate = institution_sel != CREATE_NEW
    col1, col2 = st.columns(2, gap="small")
    with col1:
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        if st.button("📁  Upload Studies", key="btn_upload", disabled=not can_navigate):
            set_page("upload")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        if st.button("🐾  My Patients", key="btn_patients", disabled=not can_navigate):
            set_page("patients")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:32px"></div>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── Sign out ──
    st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
    if st.button("Sign out", key="btn_logout"):
        for k in ["token", "user", "profile", "error", "success",
                  "selected_patient_id", "selected_patient_name", "selected_study_id",
                  "home_institution_sel", "active_institution_id"]:
            st.session_state[k] = None if k == "token" else ""
        set_page("login")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
