import os, time, uuid, base64, requests
AUTH_URL=os.getenv('GIGACHAT_AUTH_URL','https://ngw.devices.sberbank.ru:9443/api/v2/oauth')
API_BASE=os.getenv('GIGACHAT_API_URL','https://gigachat.devices.sberbank.ru/api/v1')
SCOPE=os.getenv('GIGACHAT_SCOPE','GIGACHAT_API_PERS')
AUTH_B64=os.getenv('GIGACHAT_AUTH'); CLIENT_ID=os.getenv('GIGACHAT_CLIENT_ID'); CLIENT_SECRET=os.getenv('GIGACHAT_CLIENT_SECRET')
CA_BUNDLE=os.getenv('GIGACHAT_CA_BUNDLE')
if CA_BUNDLE and os.path.exists(CA_BUNDLE): VERIFY=CA_BUNDLE
else: VERIFY=os.getenv('GIGACHAT_VERIFY','true').lower() not in {'0','false','no'}
class _TokenCache: token=None; exp=0.0

def _auth_header():
    if AUTH_B64: return f'Basic {AUTH_B64.strip()}'
    if CLIENT_ID and CLIENT_SECRET:
        import base64
        raw=f"{CLIENT_ID}:{CLIENT_SECRET}".encode('utf-8'); return 'Basic '+base64.b64encode(raw).decode('utf-8')
    raise AssertionError('Provide GIGACHAT_AUTH or GIGACHAT_CLIENT_ID/SECRET')

def _get_token():
    now=time.time()
    if _TokenCache.token and (_TokenCache.exp-now)>60: return _TokenCache.token
    headers={'Authorization':_auth_header(),'Content-Type':'application/x-www-form-urlencoded','RqUID':str(uuid.uuid4())}
    data={'scope':SCOPE}
    resp=requests.post(AUTH_URL,headers=headers,data=data,timeout=40,verify=VERIFY)
    if resp.status_code!=200: raise RuntimeError(f'GigaChat OAuth error {resp.status_code}: {resp.text}')
    payload=resp.json(); token=payload.get('access_token') or payload.get('accessToken')
    if not token: raise RuntimeError(f'GigaChat OAuth: token missing: {payload}')
    _TokenCache.token=token; _TokenCache.exp=time.time()+25*60; return token

class GigaChat:
    def __init__(self): self.model=os.getenv('GIGACHAT_MODEL','GigaChat')
    def chat(self, messages, temperature=0.2, max_tokens=800):
        token=_get_token(); url=f"{API_BASE}/chat/completions"; headers={'Authorization':f'Bearer {token}','Content-Type':'application/json; charset=utf-8'}
        body={'model':self.model,'messages':messages,'temperature':temperature,'max_tokens':max_tokens}
        r=requests.post(url,headers=headers,json=body,timeout=60,verify=VERIFY)
        if r.status_code!=200: raise RuntimeError(f'GigaChat error {r.status_code}: {r.text}')
        return r.json().get('choices',[{}])[0].get('message',{}).get('content','').strip()
