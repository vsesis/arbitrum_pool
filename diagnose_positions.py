"""
Диагностика schema positions subgraph
Использует конфигурацию из app.config
"""
import sys
import os

# Добавляем путь к app модулю
sys.path.insert(0, os.path.dirname(__file__))

try:
    from app.config import UNISWAP_V3_POSITIONS_SUBGRAPH_URL
except Exception as e:
    print(f"❌ Ошибка загрузки конфигурации: {e}")
    print()
    print("Убедитесь что .env файл настроен правильно")
    exit(1)

import requests
import json

URL = UNISWAP_V3_POSITIONS_SUBGRAPH_URL

print("=" * 80)
print("📊 ДИАГНОСТИКА: Positions Subgraph Schema")
print("=" * 80)
print(f"URL: {URL[:70]}...")
print()

# 1. Introspection типа Position
introspection_query = """
query IntrospectPosition {
  __type(name: "Position") {
    name
    fields {
      name
      type {
        name
        kind
        ofType {
          name
          kind
        }
      }
    }
  }
}
"""

print("🔍 Шаг 1: Introspection типа Position...")
try:
    response = requests.post(URL, json={"query": introspection_query}, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "errors" in data:
        print("❌ GraphQL Errors:")
        print(json.dumps(data["errors"], indent=2))
        exit(1)

    position_type = data.get("data", {}).get("__type")
    if not position_type:
        print("❌ Тип Position не найден в схеме!")
        exit(1)

    fields = position_type.get("fields", [])
    print(f"✅ Найдено полей: {len(fields)}")
    print()

    # Выводим все поля
    print("-" * 80)
    print("ДОСТУПНЫЕ ПОЛЯ В POSITION:")
    print("-" * 80)

    field_map = {}
    for field in sorted(fields, key=lambda f: f["name"]):
        name = field["name"]
        type_info = field["type"]

        # Определяем тип
        if type_info.get("kind") == "NON_NULL":
            type_name = type_info["ofType"].get("name", "?") + "!"
        elif type_info.get("kind") == "LIST":
            inner_type = type_info.get("ofType", {})
            if inner_type.get("kind") == "NON_NULL":
                inner_name = inner_type.get("ofType", {}).get("name", "?")
            else:
                inner_name = inner_type.get("name", "?")
            type_name = f"[{inner_name}]"
        else:
            type_name = type_info.get("name", "?")

        print(f"  {name:35} : {type_name}")
        field_map[name] = type_name

    print("-" * 80)
    print()

    # 2. Попробуем запросить первую позицию
    print("🧪 Шаг 2: Тестовый запрос первой позиции...")

    # Берем простые поля (не объекты)
    simple_fields = []
    for field in fields:
        name = field["name"]
        type_info = field["type"]
        type_kind = type_info.get("kind")

        # Пропускаем __typename
        if name.startswith("__"):
            continue

        # Берем скалярные типы
        if type_kind in ["SCALAR", "NON_NULL"]:
            simple_fields.append(name)
        elif type_kind == "LIST":
            # Пропускаем списки пока
            pass

    # Ограничиваем до 15 полей
    test_fields = simple_fields[:15]

    test_query = """
    query TestPosition {
      positions(first: 1, where: { pool: "0xc6962004f452be9203591991d15f6b388e09e8d0" }) {
        """ + "\n        ".join(test_fields) + """
      }
    }
    """

    print(f"Запрашиваем поля: {', '.join(test_fields[:5])}...")

    response = requests.post(URL, json={"query": test_query}, timeout=30)
    data = response.json()

    if "errors" in data:
        print("❌ Ошибка в тестовом запросе:")
        for err in data["errors"]:
            print(f"  - {err.get('message', err)}")
        print()
    else:
        positions = data.get("data", {}).get("positions", [])
        if positions:
            print(f"✅ Получена 1 позиция")
            print()
            print("Пример данных:")
            print(json.dumps(positions[0], indent=2)[:500])
            print()
        else:
            print("⚠️  Позиций не найдено (возможно пул пустой)")
            print()

    # 3. Сравнение с ожидаемыми полями
    print("=" * 80)
    print("📋 СРАВНЕНИЕ С ОЖИДАЕМЫМИ ПОЛЯМИ")
    print("=" * 80)

    expected = {
        "owner": "Владелец позиции",
        "liquidity": "Ликвидность",
        "tickLower": "Нижний тик",
        "tickUpper": "Верхний тик",
        "depositedToken0": "Депонировано token0",
        "depositedToken1": "Депонировано token1",
        "withdrawnToken0": "Выведено token0",
        "withdrawnToken1": "Выведено token1",
        "collectedFeesToken0": "Собранные fees token0",
        "collectedFeesToken1": "Собранные fees token1",
    }

    print()
    print("Ожидаемые поля → Реальные поля (если найдены):")
    print("-" * 80)

    suggestions = {}
    for exp_field, description in expected.items():
        found = exp_field in field_map
        status = "✅" if found else "❌"

        # Пытаемся найти похожие поля
        similar = []
        exp_lower = exp_field.lower()
        for real_field in field_map.keys():
            real_lower = real_field.lower()
            # Ищем совпадения
            if (exp_lower in real_lower or real_lower in exp_lower or
                any(part in real_lower for part in exp_lower.split("_"))):
                similar.append(real_field)

        if found:
            print(f"{status} {exp_field:30} → {exp_field}")
        else:
            if similar:
                suggestions[exp_field] = similar[0]
                print(f"{status} {exp_field:30} → {similar[0]} (возможно)")
            else:
                print(f"{status} {exp_field:30} → НЕ НАЙДЕНО")

    print("-" * 80)
    print()

    if suggestions:
        print("=" * 80)
        print("💡 РЕКОМЕНДАЦИИ ДЛЯ ИСПРАВЛЕНИЯ")
        print("=" * 80)
        print()
        print("Обновите GraphQL запрос в app/uniswap_client.py (строка ~187):")
        print()
        print("Замените поля:")
        for old, new in suggestions.items():
            print(f"  {old:30} → {new}")
        print()

    print("=" * 80)
    print("✅ ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("=" * 80)

except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
