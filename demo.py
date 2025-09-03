import json, streamlit as st
from strict_json_repair.core import ensure_valid
from strict_json_repair.providers import get_provider
from strict_json_repair import pyd_models as M

st.set_page_config(page_title='Strict JSON + Repair', page_icon='🧰', layout='wide')
st.title('Strict JSON + Repair — Demo')

def_schema={'type':'object','required':['answer','confidence'],'properties':{'answer':{'type':'string'},'confidence':{'type':'number','minimum':0,'maximum':1}},'additionalProperties':False}

col1,col2=st.columns(2)
with col1:
    raw=st.text_area('Сырой ответ LLM','```json\n{answer: \'Пример\', confidence: .9,}\n```',height=240)
with col2:
    mode=st.radio('Режим валидации',['JSON Schema','Pydantic'],horizontal=True)
    if mode=='JSON Schema':
        schema_text=st.text_area('JSON Schema',json.dumps(def_schema,ensure_ascii=False,indent=2),height=240); schema=json.loads(schema_text); pyd=None
    else:
        pyd_opt=st.selectbox('Pydantic модель',['FAQAnswer']); schema=None; pyd=getattr(M,pyd_opt)

st.divider()
use_llm=st.checkbox('Включить LLM‑repair (если парсинг не прошёл)')
if use_llm: st.caption('Провайдер берётся из секретов окружения.')

if st.button('Проверить/починить'):
    prov=get_provider() if use_llm else None
    data,err=ensure_valid(raw,schema=schema,pyd_model=pyd,llm_provider=prov,max_rounds=2)
    st.subheader('Результат')
    if err: st.error(err)
    else:
        st.success('Валидно')
        st.code(json.dumps(data,ensure_ascii=False,indent=2),language='json')
