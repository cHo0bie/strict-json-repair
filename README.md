# strict-json-repair (fixed)

Исправления:
- Локальный repair теперь чинит числа вида `.9` → `0.9` (и в массивах тоже).
- Pydantic: генерация схемы чинится через `model_json_schema()`.
