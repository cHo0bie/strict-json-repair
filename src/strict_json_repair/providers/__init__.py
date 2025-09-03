
import os

def _sec(name: str):
    v = os.environ.get(name)
    if v:
        return v
    try:
        import streamlit as st  # type: ignore
        v = st.secrets.get(name)  # type: ignore[attr-defined]
        if v:
            return str(v)
    except Exception:
        pass
    return None

def _hydrate():
    return None

from .openai_provider import OpenAIChat  # existing
from .gigachat_provider import GigaChat  # new

def get_provider():
    _hydrate()
    use_giga = bool(_sec("GIGACHAT_AUTH_KEY") or _sec("GIGACHAT_AUTH") or _sec("GIGACHAT_CLIENT_ID") or os.getenv("PROVIDER","").lower()=="gigachat")
    if use_giga:
        return GigaChat()
    return OpenAIChat()
