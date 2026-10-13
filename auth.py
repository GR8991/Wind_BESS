"""Simple approved-email gate for the Wind + BESS Streamlit workbench.

Note: email allowlist matching alone does not prove ownership of an email address.
Use an identity provider or email OTP for production-grade authentication.
"""
from __future__ import annotations
import re
import streamlit as st

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

def enforce_login() -> None:
    """Ask for an email and compare it with the admin-managed allowlist in Secrets."""
    st.set_page_config(page_title="SunStripe | Wind + BESS Workbench", page_icon="⚡", layout="wide")

    try:
        allowed = {
            str(email).strip().lower()
            for email in st.secrets["access"].get("allowed_emails", [])
            if str(email).strip()
        }
    except Exception:
        allowed = set()

    if not allowed:
        st.markdown(
            """<div style="max-width:760px;margin:7vh auto 0 auto;text-align:center;">
            <div style="font-size:42px;font-weight:800;letter-spacing:2px;">SUNSTRIPE</div>
            <h2>Wind + BESS Engineering Workbench</h2></div>""",
            unsafe_allow_html=True,
        )
        st.error("Login is not configured. The administrator must add approved email addresses to Streamlit Secrets.")
        st.caption("Do not add real credentials or secrets to GitHub.")
        st.stop()

    if not st.session_state.get("email_access_granted", False):
        st.markdown(
            """<div style="max-width:680px;margin:7vh auto 1rem auto;text-align:center;">
            <div style="font-size:42px;font-weight:800;letter-spacing:2px;">SUNSTRIPE</div>
            <h2 style="margin-bottom:6px;">Wind + BESS Engineering Workbench</h2>
            <p style="color:#9ca3af;">Enter your approved company email address to continue.</p>
            </div>""",
            unsafe_allow_html=True,
        )
        _, center, _ = st.columns([1, 1.3, 1])
        with center:
            with st.form("email_login_form", clear_on_submit=False):
                email = st.text_input("Company email address", placeholder="name@company.com", key="login_email")
                submitted = st.form_submit_button("Continue", use_container_width=True, type="primary")
            if submitted:
                normalized = email.strip().lower()
                if not _EMAIL_RE.match(normalized):
                    st.error("Enter a valid email address.")
                elif normalized not in allowed:
                    st.error("This email address is not on the approved access list. Contact the administrator.")
                else:
                    st.session_state["email_access_granted"] = True
                    st.session_state["authenticated_email"] = normalized
                    st.rerun()
        st.caption("Access is checked against the administrator-managed approved email list.")
        st.warning("Security note: matching an email address alone does not verify that you own it. Use company SSO or email verification for sensitive deployments.")
        st.stop()

    email = str(st.session_state.get("authenticated_email", "")).strip().lower()
    # Recheck authorization each rerun so removed addresses lose access.
    if not email or email not in allowed:
        st.session_state.pop("email_access_granted", None)
        st.session_state.pop("authenticated_email", None)
        st.rerun()

    with st.sidebar:
        st.caption("SUNSTRIPE • EMAIL ALLOWLIST")
        st.caption(f"Access email: {email}")
        if st.button("Log out", use_container_width=True):
            st.session_state.pop("email_access_granted", None)
            st.session_state.pop("authenticated_email", None)
            st.session_state.pop("login_email", None)
            st.rerun()
