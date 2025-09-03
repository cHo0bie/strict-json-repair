import os
from .openai_provider import OpenAIChat
from .gigachat_provider import GigaChat
def _hydrate():
    try:
        import streamlit as st
        for k,v in st.secrets.items():
            if isinstance(v,str) and k not in os.environ: os.environ[k]=v
    except Exception: pass
def get_provider():
    _hydrate(); return GigaChat() if os.getenv('PROVIDER','openai').lower()=='gigachat' else OpenAIChat()
