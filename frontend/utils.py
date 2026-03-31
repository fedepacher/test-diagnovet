import os
import time
import streamlit as st
import requests
from pathlib import Path

API_BASE = os.getenv('API_BASE', "http://localhost:8000")

# Render free tier: service can take up to 50s to wake up
WAKE_UP_RETRIES = os.getenv('WAKE_UP_RETRIES', 10)
WAKE_UP_DELAY = os.getenv('WAKE_UP_DELAY', 6)   # seconds between retries
WAKE_UP_TIMEOUT = os.getenv('WAKE_UP_TIMEOUT', 8)   # seconds per request attempt


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


def _is_wake_up_error(exc: Exception) -> bool:
    """Return True if the error looks like the backend is still sleeping."""
    return isinstance(exc, (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
    ))


def api_request(method: str, endpoint: str, show_wakeup: bool = True, **kwargs) -> requests.Response | None:
    """
    Make an HTTP request to the API with automatic retry while the backend wakes up.

    Args:
        method:      "get", "post", etc.
        endpoint:    e.g. "/login"
        show_wakeup: show a spinner with wake-up message on retries
        **kwargs:    passed directly to requests (data, params, headers, files, timeout…)

    Returns:
        requests.Response on success, None if backend never woke up.
    """
    kwargs.setdefault("timeout", WAKE_UP_TIMEOUT)
    url = f"{API_BASE}{endpoint}"
    fn  = getattr(requests, method.lower())

    placeholder = st.empty()

    for attempt in range(1, WAKE_UP_RETRIES + 1):
        try:
            resp = fn(url, **kwargs)
            placeholder.empty()   # clear any wake-up message
            return resp

        except Exception as exc:
            if not _is_wake_up_error(exc):
                placeholder.empty()
                raise  # unexpected error — bubble up normally

            if attempt == WAKE_UP_RETRIES:
                placeholder.empty()
                return None  # gave up

            if show_wakeup:
                elapsed = attempt * WAKE_UP_DELAY
                placeholder.markdown(
                    f"""<div class="wakeup-banner">
                        ⏳ The server is waking up — please wait…
                        <span class="wakeup-counter">{elapsed}s</span>
                    </div>""",
                    unsafe_allow_html=True,
                )

            time.sleep(WAKE_UP_DELAY)

    return None


def fetch_options(endpoint: str) -> list[dict]:
    """GET a list of {{id, name}} from the API. Returns [] on failure."""
    try:
        resp = api_request("get", endpoint, show_wakeup=False)
        if resp is not None and resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []


def fetch_profile() -> dict | None:
    """Fetch /profile/ and cache result in session_state."""
    if st.session_state.get("profile"):
        return st.session_state["profile"]
    try:
        resp = api_request("get", "/profile/", headers=auth_headers())
        if resp is not None and resp.status_code == 200:
            data = resp.json()
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


def server_unavailable_msg():
    """Show a friendly message when the backend never woke up."""
    st.markdown(
        """<div class="wakeup-banner wakeup-error">
            ❌ The server is taking too long to respond. Please refresh the page and try again.
        </div>""",
        unsafe_allow_html=True,
    )