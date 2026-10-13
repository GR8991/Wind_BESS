"""OIDC authentication and authorization gate for Streamlit Cloud/local deployment."""
from __future__ import annotations
import streamlit as st

def enforce_login() -> None:
    """Require OIDC login and an email allowlist before any engineering UI is rendered.

    Configure [auth] and [access].allowed_emails in .streamlit/secrets.toml
    locally and in Streamlit Community Cloud > App settings > Secrets.
    """
    try:
        auth_configured = "auth" in st.secrets and "access" in st.secrets
    except Exception:
        auth_configured = False

    st.set_page_config(page_title="SunStripe | Wind + BESS Workbench", page_icon="⚡", layout="wide")

    if not auth_configured:
        st.title("SUNSTRIPE")
        st.subheader("Wind + BESS Engineering Workbench")
        st.error("Authentication is not configured. Access is disabled until the app administrator configures OIDC and the approved-email allowlist.")
        st.markdown("See `AUTHENTICATION_SETUP.md`. Do not add credentials or secrets to GitHub.")
        st.stop()

    if not st.user.is_logged_in:
        st.markdown(
            """
            <div style="max-width:620px;margin:8vh auto 0 auto;padding:30px;border:1px solid #d9e0ea;border-radius:16px;text-align:center;">
              <div style="font-size:13px;letter-spacing:4px;color:#64748b;font-weight:700;">SUNSTRIPE</div>
              <h1 style="margin-bottom:8px;color:#17365D;">Wind + BESS Engineering Workbench</h1>
              <p style="color:#64748b;">Sign in with your approved company identity to continue.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        providers = []
        try:
            if "microsoft" in st.secrets["auth"]:
                providers.append(("Sign in with Microsoft", "microsoft"))
            if "google" in st.secrets["auth"]:
                providers.append(("Sign in with Google", "google"))
        except Exception:
            pass
        if not providers:
            providers.append(("Sign in", None))
        _, center, _ = st.columns([1, 2, 1])
        with center:
            for label, provider in providers:
                if provider:
                    st.button(label, use_container_width=True, on_click=st.login, args=(provider,))
                else:
                    st.button(label, use_container_width=True, on_click=st.login)
        st.stop()

    user_email = str(getattr(st.user, "email", "") or "").strip().lower()
    try:
        allowed = {
            str(email).strip().lower()
            for email in st.secrets["access"].get("allowed_emails", [])
            if str(email).strip()
        }
    except Exception:
        allowed = set()

    if not user_email or user_email not in allowed:
        st.title("SUNSTRIPE")
        st.error("Access denied. This account is not on the approved user list.")
        if user_email:
            st.caption(f"Signed-in account: {user_email}")
        st.info("Contact the application administrator if you believe you should have access.")
        st.button("Sign out", on_click=st.logout)
        st.stop()

    with st.sidebar:
        st.caption("SUNSTRIPE • AUTHENTICATED ACCESS")
        st.caption(f"Signed in as: {user_email}")
        st.button("Sign out", on_click=st.logout, use_container_width=True)
