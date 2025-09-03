import os, requests
class OpenAIChat:
    def __init__(self):
        self.base=os.getenv('OPENAI_BASE_URL','https://api.openai.com/v1')
        self.key=os.getenv('OPENAI_API_KEY','').strip()
        self.model=os.getenv('OPENAI_MODEL','gpt-4o-mini').strip()
        self.org=os.getenv('OPENAI_ORG_ID') or os.getenv('OPENAI_ORGANIZATION')
        assert self.key, 'OPENAI_API_KEY missing'
    def chat(self, messages, temperature=0.2, max_tokens=800):
        url=f"{self.base}/chat/completions"; headers={'Authorization':f'Bearer {self.key}','Content-Type':'application/json'}
        if self.org: headers['OpenAI-Organization']=self.org
        payload={'model':self.model,'messages':messages,'temperature':temperature,'max_tokens':max_tokens}
        r=requests.post(url,headers=headers,json=payload,timeout=60)
        if r.status_code!=200: raise RuntimeError(f'OpenAI error {r.status_code}: {r.text}')
        return r.json()['choices'][0]['message']['content'].strip()
