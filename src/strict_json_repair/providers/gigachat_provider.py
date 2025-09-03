
import os, json

def _sec(name: str, default=None):
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
    return default

class GigaChat:
    def __init__(self, model=None):
        import base64
        self.model = model or _sec("GIGACHAT_MODEL", "GigaChat-Pro")
        self.scope = _sec("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
        self.auth_key = _sec("GIGACHAT_AUTH_KEY") or _sec("GIGACHAT_AUTH")
        if not self.auth_key:
            cid = _sec("GIGACHAT_CLIENT_ID")
            csec = _sec("GIGACHAT_CLIENT_SECRET")
            if cid and csec:
                self.auth_key = base64.b64encode(f"{cid}:{csec}".encode()).decode()
        ver = (_sec("GIGACHAT_VERIFY", "true") or "true").strip().lower()
        self.verify = False if ver in ("0","false","no","off") else True
        if not self.auth_key:
            raise RuntimeError("GIGACHAT_AUTH_KEY (или CLIENT_ID/CLIENT_SECRET) не задан")
        self._token = None

    def _get_token(self) -> str:
        import uuid, requests
        if self._token:
            return self._token
        headers = {
            "Authorization": f"Basic {self.auth_key}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
        }
        data = {"scope": self.scope}
        r = requests.post(
            "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
            headers=headers, data=data, timeout=60, verify=self.verify
        )
        r.raise_for_status()
        self._token = r.json()["access_token"]
        return self._token

    def chat(self, messages_or_prompt, temperature: float=0.0, max_tokens=None, **kwargs) -> str:
        import requests, uuid
        token = self._get_token()
        if isinstance(messages_or_prompt, str):
            messages = [{"role":"user","content":messages_or_prompt}]
        else:
            messages = messages_or_prompt
        payload = {"model": self.model, "messages": messages, "temperature": float(temperature)}
        if max_tokens is not None:
            payload["max_tokens"] = int(max_tokens)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
        }
        r = requests.post(
            "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
            headers=headers, json=payload, timeout=120, verify=self.verify
        )
        if r.status_code == 401:
            self._token = None
            return self.chat(messages_or_prompt, temperature=temperature, max_tokens=max_tokens, **kwargs)
        r.raise_for_status()
        j = r.json()
        try:
            return j["choices"][0]["message"]["content"]
        except Exception:
            return json.dumps(j, ensure_ascii=False)
