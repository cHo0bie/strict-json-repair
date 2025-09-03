from __future__ import annotations
import json, pathlib

def _read(name: str) -> str:
    path = pathlib.Path(__file__).with_name(name)
    return path.read_text(encoding='utf-8')

def build_repair_prompt(raw: str, schema=None, pyd_model=None) -> str:
    tmpl = _read('repair_prompt.md')
    schema_text = ''
    if schema: schema_text = json.dumps(schema, ensure_ascii=False, indent=2)
    elif pyd_model is not None: schema_text = pyd_model.model_json_schema_json(indent=2)
    return tmpl.replace('{{schema_text}}', schema_text).replace('{{raw}}', raw)

def build_reask_prompt(schema=None, pyd_model=None) -> str:
    tmpl = _read('reask_prompt.md')
    schema_text = ''
    if schema: schema_text = json.dumps(schema, ensure_ascii=False, indent=2)
    elif pyd_model is not None: schema_text = pyd_model.model_json_schema_json(indent=2)
    return tmpl.replace('{{schema_text}}', schema_text)
