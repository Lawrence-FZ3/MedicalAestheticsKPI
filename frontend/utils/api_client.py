"""
HTTP client for Streamlit → FastAPI communication.
Stores JWT token in st.session_state and attaches it to every request.
"""
import requests
import streamlit as st

API_BASE = st.secrets.get("api_base_url", "http://localhost:8000")


def _headers() -> dict:
    token = st.session_state.get("token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def login(username: str, password: str) -> bool:
    try:
        resp = requests.post(f"{API_BASE}/auth/login", json={"username": username, "password": password}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            st.session_state["token"] = data["access_token"]
            st.session_state["username"] = username
            return True
    except Exception:
        pass
    return False


def get(path: str, params: dict = None):
    resp = requests.get(f"{API_BASE}{path}", headers=_headers(), params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def post(path: str, data: dict = None, files=None):
    if files:
        resp = requests.post(f"{API_BASE}{path}", headers=_headers(), files=files, timeout=30)
    else:
        resp = requests.post(f"{API_BASE}{path}", headers=_headers(), json=data, timeout=15)
    resp.raise_for_status()
    return resp.json()


def patch(path: str, data: dict):
    resp = requests.patch(f"{API_BASE}{path}", headers=_headers(), json=data, timeout=15)
    resp.raise_for_status()
    return resp.json()


def delete(path: str):
    resp = requests.delete(f"{API_BASE}{path}", headers=_headers(), timeout=10)
    resp.raise_for_status()


def is_authenticated() -> bool:
    return bool(st.session_state.get("token"))
