"""
Проверяем основной subgraph на наличие positions
"""
import sys
sys.path.insert(0, '.')

from app.config import UNISWAP_V3_SUBGRAPH_URL
import requests
import json

URL = UNISWAP_V3_SUBGRAPH_URL

print("=" * 80)
print("🔍 ПРОВЕРКА ОСНОВНОГО SUBGRAPH НА НАЛИЧИЕ POSITIONS")
print("=" * 80)
print(f"URL: {URL[:70]}...")
print()

# 1. Проверяем есть ли тип Position
introspection = """
query {
  __type(name: "Position") {
    name
    fields {
      name
      type {
        name
        kind
        ofType { name kind }
      }
    }
  }
}
"""

print("Шаг 1: Проверяем наличие типа Position...")
response = requests.post(URL, json={"query": introspection}, timeout=30)
data = response.json()

if "errors" in data:
    print("❌ Ошибка:")
    print(json.dumps(data["errors"], indent=2))
    exit(1)

position_type = data.get("data", {}).get("__type")
if not position_type:
    print("❌ Тип Position НЕ НАЙДЕН в основном subgraph")
    print()
    print("Это означает что позиции нужно получать из другого источника.")
    exit(1)

print(f"✅ Тип Position НАЙДЕН!")
print()

fields = position_type.get("fields", [])
print(f"Найдено полей: {len(fields)}")
print()
print("-" * 80)

for field in sorted(fields, key=lambda f: f["name"]):
    name = field["name"]
    type_info = field["type"]

    if type_info.get("kind") == "NON_NULL":
        type_name = type_info["ofType"].get("name", "?") + "!"
    elif type_info.get("kind") == "LIST":
        type_name = f"[{type_info.get('ofType', {}).get('name', '?')}]"
    else:
        type_name = type_info.get("name", "?")

    print(f"  {name:35} : {type_name}")

print("-" * 80)
print()

# 2. Пробуем запросить позиции
print("Шаг 2: Пробуем запросить позиции из пула...")

test_query = """
query {
  positions(first: 1, where: { pool: "0xc6962004f452be9203591991d15f6b388e09e8d0" }) {
    id
    owner
    liquidity
    pool {
      id
    }
  }
}
"""

response = requests.post(URL, json={"query": test_query}, timeout=30)
data = response.json()

if "errors" in data:
    print("❌ Ошибка при запросе позиций:")
    for err in data["errors"]:
        print(f"  - {err.get('message')}")
    print()
else:
    positions = data.get("data", {}).get("positions", [])
    print(f"✅ Получено позиций: {len(positions)}")

    if positions:
        print()
        print("Пример позиции:")
        print(json.dumps(positions[0], indent=2))
        print()
        print("=" * 80)
        print("✅ ОТЛИЧНО! Позиции ДОСТУПНЫ в основном subgraph!")
        print("=" * 80)
        print()
        print("Решение: Использовать UNISWAP_V3_SUBGRAPH_URL для получения позиций")
    else:
        print("⚠️  Позиций не найдено (возможно пул пустой)")

print()
print("=" * 80)
print("ДИАГНОСТИКА ЗАВЕРШЕНА")
print("=" * 80)
