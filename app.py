"""
🚀 APP ENTRYPOINT - Student Financial Advisor

Run with:
    streamlit run app.py

Purpose
-------
Single entrypoint for the full Streamlit application.

This file stays intentionally thin:
- sets Streamlit page config
- imports the dashboard
- launches the app

All business/UI logic lives in ui/dashboard.py
"""

from __future__ import annotations

import streamlit as st

from ui.dashboard import main as dashboard_main


def configure_app():
    """Global Streamlit page configuration."""
    st.set_page_config(
        page_title="Student Financial Advisor",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def main():
    configure_app()
    dashboard_main()


if __name__ == "__main__":
    main()