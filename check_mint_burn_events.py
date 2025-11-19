"""
Проверяем доступность Mint/Burn событий для восстановления позиций
"""
import sys
sys.path.insert(0, '.')

from app.config import UNISWAP_V3_SUBGRAPH_URL
import requests
import json

URL = UNISWAP_V3_SUBGRAPH_URL

print("=" * 80)
print("🔍 ПРОВЕРКА MINT/BURN СОБЫТИЙ В ОСНОВНОМ SUBGRAPH")
print("=" * 80)
print(f"URL: {URL[:70]}...")
print()

# Проверяем наличие типов Mint и Burn
types_to_check = ["Mint", "Burn", "Position", "Tick"]

for type_name in types_to_check:
    introspection = f"""
    query {{
      __type(name: "{type_name}") {{
        name
        fields {{
          name
          type {{
            name
            kind
            ofType {{ name }}
          }}
        }}
      }}
    }}
    """

    response = requests.post(URL, json={"query": introspection}, timeout=30)
    data = response.json()

    if "errors" in data:
        print(f"❌ {type_name}: Ошибка запроса")
        continue

    type_info = data.get("data", {}).get("__type")
    if not type_info:
        print(f"❌ {type_name}: НЕ НАЙДЕН")
        continue

    fields = type_info.get("fields", [])
    print(f"✅ {type_name}: найдено полей - {len(fields)}")

    # Показываем важные поля
    if type_name in ["Mint", "Burn"]:
        print(f"   Поля: ", end="")
        field_names = [f["name"] for f in fields[:10]]
        print(", ".join(field_names))

print()
print("-" * 80)
print()

# Пробуем запросить mint события для пула
print("Тестовый запрос: получаем последние 3 mint события для пула...")
test_query = """
query {
  mints(
    first: 3
    where: { pool: "0xc6962004f452be9203591991d15f6b388e09e8d0" }
    orderBy: timestamp
    orderDirection: desc
  ) {
    id
    owner
    amount
    amount0
    amount1
    tickLower
    tickUpper
    timestamp
  }
}
"""

response = requests.post(URL, json={"query": test_query}, timeout=30)
data = response.json()

if "errors" in data:
    print("❌ Ошибка при запросе mint событий:")
    for err in data["errors"]:
        print(f"  - {err.get('message')}")
else:
    mints = data.get("data", {}).get("mints", [])
    print(f"✅ Получено mint событий: {len(mints)}")

    if mints:
        print()
        print("Пример mint события:")
        print(json.dumps(mints[0], indent=2))

print()
print("=" * 80)
print("РЕКОМЕНДАЦИЯ")
print("=" * 80)
print()
print("Если Mint/Burn события доступны, можно:")
print("1. Агрегировать их для получения активных позиций")
print("2. Отслеживать owner + tickLower + tickUpper как уникальную позицию")
print("3. Суммировать amount0/amount1 по каждой позиции")
print()
print("Альтернативно:")
print("- Упростить функционал: показывать только Pool Overview и график ликвидности")
print("- Использовать другой subgraph (например, Messari)")
print()
