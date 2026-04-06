import os
import time
import streamlit as st
import requests
from pathlib import Path

API_BASE = os.getenv('API_BASE', "http://localhost:8000")

# Render free tier: service can take up to 50s to wake up
WAKE_UP_RETRIES = int(os.getenv('WAKE_UP_RETRIES', 20))
WAKE_UP_DELAY = int(os.getenv('WAKE_UP_DELAY', 6))   # seconds between retries
WAKE_UP_TIMEOUT = int(os.getenv('WAKE_UP_TIMEOUT', 8))   # seconds per request attempt


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
    Uses st.spinner so Streamlit actually renders the message during the blocking sleep.
    """
    kwargs.setdefault("timeout", WAKE_UP_TIMEOUT)
    url = f"{API_BASE}{endpoint}"
    fn  = getattr(requests, method.lower())

    for attempt in range(1, WAKE_UP_RETRIES + 1):
        try:
            resp = fn(url, **kwargs)
            return resp

        except Exception as exc:
            if not _is_wake_up_error(exc):
                raise  # unexpected error — bubble up normally

            if attempt == WAKE_UP_RETRIES:
                return None  # gave up

            if show_wakeup:
                elapsed_next = attempt * WAKE_UP_DELAY
                with st.spinner(f"⏳ Server is waking up, please wait… ({elapsed_next}s)"):
                    time.sleep(WAKE_UP_DELAY)
            else:
                time.sleep(WAKE_UP_DELAY)

    return None


def _show_wakeup_ui() -> tuple:
    """Render the wake-up waiting UI and return (progress, status_text)."""
    st.markdown(
        """<div style="text-align:center; padding: 32px 0 16px 0;">
            <div style="font-size:2.5rem; margin-bottom:12px;">⏳</div>
            <div style="font-size:1.1rem; color:#c8b89a; font-weight:600; margin-bottom:6px;">
                Server is waking up…
            </div>
            <div style="font-size:0.85rem; color:#555;">
                This may take up to a minute on the free tier. Please wait.
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
    return st.progress(0), st.empty()


def _mark_ready(progress, status_text) -> bool:
    """Show success state, mark backend ready, trigger rerun."""
    progress.progress(100)
    status_text.markdown(
        '<p style="text-align:center; color:#6fcf97; font-size:0.9rem;">✓ Server is ready!</p>',
        unsafe_allow_html=True,
    )
    time.sleep(0.8)
    st.session_state["backend_ready"] = True
    st.rerun()
    return True


def wait_for_backend() -> bool:
    """
    Wake up the Render free tier backend.

    Key insight: Render keeps the TCP connection open while the dyno boots.
    A single request with a long READ timeout (90s) is enough — the server
    will eventually respond without closing the connection.
    Many short-timeout requests just pile up and all fail.
    """
    if st.session_state.get("backend_ready"):
        return True

    # Fast path: backend might already be up (e.g. frontend just woke first)
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=(5, 5))
        if resp.status_code == 200:
            st.session_state["backend_ready"] = True
            return True
    except Exception:
        pass

    # Backend is sleeping — show UI
    progress, status_text = _show_wakeup_ui()

    # ── Round 1: one patient long-timeout request (90s read timeout) ──
    # Render holds the connection while booting, so this usually succeeds.
    status_text.markdown(
        '<p style="text-align:center; color:#555; font-size:0.82rem;">Waiting for server to boot…</p>',
        unsafe_allow_html=True,
    )
    progress.progress(30)
    try:
        resp = requests.get(
            f"{API_BASE}/health",
            timeout=(10, 90),  # connect_timeout=10s, read_timeout=90s
        )
        if resp.status_code == 200:
            return _mark_ready(progress, status_text)
    except Exception:
        pass

    # ── Round 2: a few shorter retries in case the long request timed out ──
    for attempt in range(1, 4):
        progress.progress(30 + attempt * 20)
        status_text.markdown(
            f'<p style="text-align:center; color:#555; font-size:0.82rem;">Retrying… ({attempt}/3)</p>',
            unsafe_allow_html=True,
        )
        time.sleep(15)
        try:
            resp = requests.get(f"{API_BASE}/health", timeout=(10, 30))
            if resp.status_code == 200:
                return _mark_ready(progress, status_text)
        except Exception:
            pass

    # ── Gave up ──
    progress.empty()
    status_text.empty()
    st.markdown(
        """<div class="wakeup-banner wakeup-error">
            ❌ The server took too long to respond. Please refresh the page and try again.
        </div>""",
        unsafe_allow_html=True,
    )
    return False


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
    """
    Return the active institution id.
    Prefers the one selected in home (active_institution_id),
    falls back to the default from profile.
    """
    if st.session_state.get("active_institution_id"):
        return st.session_state["active_institution_id"]
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