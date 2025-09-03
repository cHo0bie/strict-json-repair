
from __future__ import annotations
import json, re
from typing import Any, Dict, Optional, Tuple
from jsonschema import Draft202012Validator

def _strip_bom(text: str) -> str:
    return text.lstrip('\ufeff')

def _strip_code_fences(text: str) -> str:
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    return m.group(1) if m else text

def _normalize_quotes(text: str) -> str:
    table = str.maketrans({'“':'"', '”':'"', '„':'"', '«':'"', '»':'"','’':"'", '‘':"'" })
    return text.translate(table)

def _quote_unquoted_keys(text: str) -> str:
    def repl(m): return f'{m.group(1)}"{m.group(2)}"{m.group(3)}'
    pattern = r'([\{,]\s*)([A-Za-z_][A-Za-z0-9_\-]*)(\s*:)'
    return re.sub(pattern, repl, text)

def _single_to_double_quotes(text: str) -> str:
    text = re.sub(r"'([A-Za-z_][A-Za-z0-9_\-]*)'\s*:", r'"\1":', text)   # keys
    text = re.sub(r':\s*\'([^\']*)\'', r': "\1"', text)                   # values
    return text

def extract_json(text: str) -> Optional[str]:
    text = _strip_bom(text)
    text = _strip_code_fences(text)
    text = _normalize_quotes(text).strip()
    m = re.search(r'\{[\s\S]*\}', text)
    if not m: return None
    snippet = m.group(0)
    snippet = _quote_unquoted_keys(snippet)
    snippet = _single_to_double_quotes(snippet)
    snippet = re.sub(r',\s*([}\]])', r'\1', snippet)
    return snippet

def coerce_enums(data: Any, schema: Dict[str, Any]) -> Any:
    if isinstance(data, dict) and isinstance(schema, dict):
        props = schema.get("properties", {})
        for k, v in list(data.items()):
            subschema = props.get(k)
            if subschema:
                enum = subschema.get("enum")
                if enum and isinstance(v, str):
                    vv = v.strip()
                    if '|' in vv: vv = vv.split('|', 1)[0].strip()
                    vv_low = vv.lower()
                    if vv in enum or vv_low in enum:
                        data[k] = vv_low if vv_low in enum else vv
                    else:
                        for token in re.split(r'[,/;| ]+', vv_low):
                            if token in enum: data[k] = token; break
                elif enum and isinstance(v, list) and v:
                    first = None
                    for item in v:
                        if isinstance(item, str):
                            token = item.strip().lower()
                            if token in enum: first = token; break
                            if '|' in token:
                                t0 = token.split('|', 1)[0].strip()
                                if t0 in enum: first = t0; break
                    if first: data[k] = first
                else:
                    data[k] = coerce_enums(v, subschema)
            else:
                data[k] = coerce_enums(v, {})
        return data
    elif isinstance(data, list):
        return [coerce_enums(x, schema.get("items", {})) for x in data]
    else:
        return data

def _validate_with_schema(data: dict, schema: dict | None, pyd_model=None) -> None:
    if pyd_model is not None: pyd_model.model_validate(data)
    if schema: Draft202012Validator(schema).validate(data)

def ensure_valid(text: str, schema: dict | None = None, pyd_model=None, llm_provider=None, max_rounds: int = 0) -> Tuple[Optional[dict], Optional[str]]:
    try:
        data = json.loads(text); _validate_with_schema(data, schema, pyd_model); return data, None
    except Exception: pass
    snippet = extract_json(text)
    last_err = "JSON not found"
    if snippet:
        try:
            data = json.loads(snippet); data = coerce_enums(data, schema or {}); _validate_with_schema(data, schema, pyd_model); return data, None
        except Exception as e: last_err = f"JSON parse error: {e}"
    if llm_provider and max_rounds > 0:
        from .prompts import build_repair_prompt, build_reask_prompt
        attempt, raw_input = 0, text
        while attempt < max_rounds:
            prompt = build_repair_prompt(raw_input, schema=schema, pyd_model=pyd_model)
            fixed = llm_provider.chat([{"role":"system","content":"You are a senior JSON engineer."},{"role":"user","content":prompt}], temperature=0.0, max_tokens=1200)
            snippet = extract_json(fixed) or fixed
            try:
                data = json.loads(snippet); data = coerce_enums(data, schema or {}); _validate_with_schema(data, schema, pyd_model); return data, None
            except Exception:
                reask = build_reask_prompt(schema=schema, pyd_model=pyd_model)
                fixed = llm_provider.chat([{"role":"system","content":"You are a senior JSON engineer."},{"role":"user","content":reask}], temperature=0.1, max_tokens=1200)
                raw_input = fixed; attempt += 1
    return None, last_err
