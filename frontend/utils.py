import os
import streamlit as st
import requests
from pathlib import Path

API_BASE = os.getenv('API_BASE', "http://localhost:8000")


def load_css(path: str) -> None:
    """Read a CSS file and inject it into the page."""
    css = Path(path).read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def set_page(page: str, **kwargs) -> None:
    """Navigate to a page, clear messages, and optionally set extra state."""
    st.session_state.page = page
    st.session_state.error = ""
    st.session_state.success = ""
    for k, v in kwargs.items():
        st.session_state[k] = v


def auth_headers() -> dict:
    """Return Authorization header using the stored token."""
    return {"Authorization": f"Bearer {st.session_state.get('token', '')}"}


def fetch_options(endpoint: str) -> list[dict]:
    """GET a list of {id, name} from the API. Returns [] on failure."""
    try:
        r = requests.get(f"{API_BASE}{endpoint}", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


def fetch_profile() -> dict | None:
    """Fetch /profile/ and cache result in session_state."""
    if st.session_state.get("profile"):
        return st.session_state["profile"]
    try:
        r = requests.get(f"{API_BASE}/profile/", headers=auth_headers(), timeout=5)
        if r.status_code == 200:
            data = r.json()
            st.session_state["profile"] = data
            return data
    except Exception:
        pass
    return None


def get_institution_id() -> int | None:
    """Return the institution id from the cached profile."""
    profile = fetch_profile()
    if profile and "institutions" in profile:
        return profile["institutions"]["id"]
    return None


def back_button(label: str = "← Back", target_page: str = "home", **kwargs):
    """Render a small back button."""
    st.markdown('<div class="btn-back">', unsafe_allow_html=True)
    if st.button(label, key=f"back__{target_page}__{len(kwargs)}"):
        set_page(target_page, **kwargs)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)