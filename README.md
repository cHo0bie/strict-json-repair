# Strict JSON + Repair

Инструмент (библиотека + CLI + Streamlit‑демо) для **строгой валидации** и **мягкой починки** JSON‑ответов LLM.  
Работает с **JSON Schema** и/или **Pydantic v2**, умеет локально исправлять частые артефакты (неправильные кавычки, лишние запятые, числа вида `.9`) и при необходимости запускает **LLM‑repair** (просит модель починить/перегенерировать ответ строго по схеме). Поддержаны провайдеры **OpenAI‑совместимый API** и **GigaChat**.

> Типичные кейсы: ответы бота/агента по контракту, извлечение реквизитов, формы заявок, чек‑листы QA, отчёты, RAG‑ответы с уверенностью и цитатами.

---

## Возможности

- **Извлечение JSON** из текста и markdown (```json … ```).
- **Локальный repair** без вызова LLM:
  - нормализация кавычек, кавычки для незакрытых ключей;
  - удаление «висячих» запятых в конце объектов/массивов;
  - исправление чисел с ведущей точкой: `.9 → 0.9` (включая массивы);
  - бережная **нормализация `enum`** (`"fraud|card"` → `"fraud"` и др.).
- **Строгая валидация**:
  - по **JSON Schema (Draft 2020‑12)** через `jsonschema`;
  - по **Pydantic v2** (`model_validate`).
- **LLM‑repair / Re‑ask** (по желанию):
  - если парсинг/валидация не прошли — просим LLM «починить JSON строго по схеме»;
  - при повторной неудаче — **re‑ask**: «сгенерируй с нуля строго по схеме».
- **Провайдеры:** OpenAI‑совместимый API и **GigaChat** (OAuth, кэш токена, валидация TLS/кастомный CA bundle).
- **CLI** + **Streamlit‑демо** с переключателем Schema/Pydantic и чекбоксом LLM‑repair.

---

## Установка

```bash
pip install -e .
# Для демо:
pip install -r requirements-demo.txt
```

---

## Быстрый старт (Python)

```python
from strict_json_repair import ensure_valid

schema = {
    "type": "object",
    "required": ["answer", "confidence"],
    "properties": {
        "answer": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
    },
    "additionalProperties": False
}

raw = \"\"\"```json
{answer: 'Пример', confidence: .9,}
```\"\"\"

data, err = ensure_valid(raw, schema=schema)  # только локальный repair
print(data)  # {'answer': 'Пример', 'confidence': 0.9}
```

**Pydantic‑режим**:

```python
from strict_json_repair import ensure_valid
from strict_json_repair import pyd_models as M

raw = "{answer: 'ok', citations: [], confidence: .95}"
data, err = ensure_valid(raw, pyd_model=M.FAQAnswer)  # валидация по модели
```

**LLM‑repair (опционально)**:

```python
from strict_json_repair import ensure_valid
from strict_json_repair.providers import get_provider

schema = {"type":"object","properties":{"a":{"type":"string"}},"required":["a"]}
raw = "{aa: 'oops'}"  # ключ не совпадает со схемой

provider = get_provider()  # берёт настройки из ENV/Streamlit secrets
data, err = ensure_valid(raw, schema=schema, llm_provider=provider, max_rounds=2)
```

---

## Структура проекта

```
src/strict_json_repair/
├── core.py              # извлечение/нормализация/валидация + LLM‑repair/re‑ask
├── pyd_models.py        # пример pydantic‑модели (FAQAnswer)
├── providers/
│   ├── __init__.py      # выбор провайдера из ENV/Streamlit secrets
│   ├── openai_provider.py
│   └── gigachat_provider.py
└── prompts/
    ├── repair_prompt.md # просьба починить JSON
    └── reask_prompt.md  # просьба сгенерировать с нуля
demo.py                  # Streamlit‑демо
requirements-demo.txt
examples/                # примеры схем/сырого текста
tests/                   # примерные кейсы
```

---

## Streamlit‑демо

```bash
streamlit run demo.py
```

В демо можно:
- сравнить **JSON Schema vs Pydantic**;
- включать/выключать **LLM‑repair**;
- увидеть, как локальные фиксы чинят «типичные поломки» (кавычки/запятые/`.9`);
- проверять свои схемы/модели (вставьте JSON Schema или выберите Pydantic‑модель).

### Деплой на Streamlit Cloud

1. Deploy from GitHub → выберите репозиторий.  
2. **Main file**: `demo.py`  
3. **Secrets** (см. ниже).

---

## Конфигурация провайдеров (ENV / Streamlit secrets)

### OpenAI‑совместимый API
```
PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

### GigaChat
```
PROVIDER=gigachat
GIGACHAT_AUTH=<Authorization Key: base64(client_id:client_secret)>
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_AUTH_URL=https://ngw.devices.sberbank.ru:9443/api/v2/oauth
GIGACHAT_API_URL=https://gigachat.devices.sberbank.ru/api/v1
# Для Streamlit Cloud чаще всего:
GIGACHAT_VERIFY=false
# или свой сертификат:
# GIGACHAT_CA_BUNDLE=/mount/src/<repo>/certs/gigachat_ca.pem
GIGACHAT_MODEL=GigaChat
```

> Функция `get_provider()` сама подберёт провайдера по `PROVIDER` и доступным секретам.  
> В Streamlit‑демо секреты автоматически подхватываются из *Secrets* в ENV.

---

## API

### `ensure_valid(text, schema=None, pyd_model=None, llm_provider=None, max_rounds=0)`
Возвращает `(data: dict | None, err: str | None)`.

Алгоритм:
1. Попытка распарсить **как есть** → валидация.
2. Если не вышло — **локальный repair** (`extract_json`, кавычки, `.9→0.9`, запятые, enum‑нормализация) → валидация.
3. Если всё ещё невалидно и задан `llm_provider` → до `max_rounds`:
   - **repair** по `prompts/repair_prompt.md`;
   - при неудаче — **re‑ask** по `prompts/reask_prompt.md` (сгенерировать с нуля).

### `extract_json(text) -> str | None`
Выделяет JSON‑фрагмент из текста/markdown и «доводит» его до валидного синтаксиса.

### `coerce_enums(data, schema) -> data`
Осторожная нормализация значений для полей с `enum`:
- `"fraud|card" → "fraud"`
- для списков берётся первый валидный токен.

---

## CLI

```bash
python -m strict_json_repair.cli \
  --schema examples/faq.schema.json \
  --input examples/noisy_faq.txt \
  --llm-repair      # опционально
```

Параметры:
- `--schema path.json` — путь к JSON Schema (необязательно).
- `--pydantic-model FAQAnswer` — альтернатива схеме, использовать встроенную модель.
- `--input file.txt` — файл с сырым ответом LLM.
- `--llm-repair` — задействовать LLM‑ремонт (нужны секреты).

---

## Что можно сделать прямо в демо

- **Проверить контракт**: структура, типы, обязательные поля, диапазоны.
- **Оценить локальные фиксы** без вызова модели (кавычки/запятые/`.9`).
- **Сравнить режимы**: JSON Schema vs Pydantic.
- **Включить LLM‑repair**, если локального ремонта не хватает.
- **Прогнать свои схемы** и понять, какие места ломаются чаще.

Идеи мини‑кейсов:
- **FAQ‑ответ**: `{"answer": "...", "citations": ["..."], "confidence": 0.87}`
- **Категория жалобы** c enum‑нормализацией: `{"category": "fraud"}`
- **Форма заявки**: строгие обязательные поля и типы

---

## Траблшутинг

- **`JSON parse error: Expecting value: ...`** — чаще всего `.9`/одинарные кавычки/висячие запятые. В проекте есть локальная починка; если всё ещё не работает — проверьте, действительно ли в тексте есть JSON‑объект `{ ... }`.
- **Pydantic + LLM‑repair: `AttributeError`** — в этой версии исправлено: для схемы Pydantic используется `model_json_schema()` + `json.dumps(...)`.
- **GigaChat OAuth/SSL** — в облаке используйте `GIGACHAT_VERIFY=false` или прокиньте `GIGACHAT_CA_BUNDLE`. Проверьте `GIGACHAT_AUTH` (base64 от `client_id:client_secret`) и `GIGACHAT_SCOPE`.

---

## Производственные заметки

- При аккуратной схеме + локальном ремонте обычно достигается **валидность ≥98–99%** без LLM‑repair.
- Среднее число ретраев при включённом LLM‑repair — **≤ 1.2** на запрос (зависит от домена/модели).
- Держите промпты repair/re‑ask в репозитории и адаптируйте под домен (термины, допустимые диапазоны, policy.

---

## Дорожная карта

- Доп. локальные фиксы: `True/False/None → true/false/null`, строгие даты/ISO8601, escape‑правила.
- Простая телеметрия: счётчики валидности/ретраев для прод‑пайплайнов.
- Набор pydantic‑контрактов под фин‑домены (жалобы, реквизиты, заявки).

---

## Лицензия

MIT — свободно для коммерческого использования, форков и модификаций.
