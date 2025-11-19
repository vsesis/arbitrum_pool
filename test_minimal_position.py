"""
Минимальный тест для positions subgraph
Пробует получить позицию с базовыми полями
"""
import requests
import json
import sys

# URL из аргументов или используем заглушку
if len(sys.argv) > 1:
    URL = sys.argv[1]
else:
    print("Использование: python test_minimal_position.py <POSITIONS_SUBGRAPH_URL>")
    print()
    print("Вы можете скопировать URL из логов приложения (он показывается как:")
    print("  https://gateway.thegraph.com/api/YOUR_KEY/subgraphs/id/EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG")
    print()
    sys.exit(1)

print(f"Testing URL: {URL[:70]}...")
print()

# Тест 1: Минимальный запрос
print("=" * 80)
print("ТЕСТ 1: Получение позиций с минимальными полями (id, pool)")
print("=" * 80)

query1 = """
{
  positions(first: 5, where: { pool: "0xc6962004f452be9203591991d15f6b388e09e8d0" }) {
    id
  }
}
"""

try:
    response = requests.post(URL, json={"query": query1}, timeout=30)
    data = response.json()

    if "errors" in data:
        print("❌ Ошибка:")
        print(json.dumps(data["errors"], indent=2))
    else:
        positions = data.get("data", {}).get("positions", [])
        print(f"✅ Получено позиций: {len(positions)}")
        if positions:
            print(f"   Пример ID: {positions[0].get('id')}")

except Exception as e:
    print(f"❌ Ошибка: {e}")

print()

# Тест 2: Попробуем добавить поле pool
print("=" * 80)
print("ТЕСТ 2: Добавляем поле pool")
print("=" * 80)

query2 = """
{
  positions(first: 1, where: { pool: "0xc6962004f452be9203591991d15f6b388e09e8d0" }) {
    id
    pool {
      id
    }
  }
}
"""

try:
    response = requests.post(URL, json={"query": query2}, timeout=30)
    data = response.json()

    if "errors" in data:
        print("❌ Ошибка:")
        for err in data["errors"]:
            print(f"  - {err.get('message')}")
    else:
        positions = data.get("data", {}).get("positions", [])
        print(f"✅ Получено позиций: {len(positions)}")
        if positions:
            print("Пример данных:")
            print(json.dumps(positions[0], indent=2))

except Exception as e:
    print(f"❌ Ошибка: {e}")

print()

# Тест 3: Попробуем альтернативные имена полей
print("=" * 80)
print("ТЕСТ 3: Пробуем альтернативные имена для owner/liquidity")
print("=" * 80)

# Список возможных вариантов полей
field_variants = [
    ("account", "владелец (account)"),
    ("recipient", "получатель (recipient)"),  ("depositToken0", "депозит токен0"),
    ("collectedToken0", "собранный токен0"),
]

for field, description in field_variants:
    query = f"""
    {{
      positions(first: 1, where: {{ pool: "0xc6962004f452be9203591991d15f6b388e09e8d0" }}) {{
        id
        {field}
      }}
    }}
    """

    try:
        response = requests.post(URL, json={"query": query}, timeout=10)
        data = response.json()

        if "errors" in data:
            print(f"❌ {field:25} - НЕТ")
        else:
            positions = data.get("data", {}).get("positions", [])
            if positions and field in positions[0]:
                value = positions[0].get(field)
                print(f"✅ {field:25} - ЕСТЬ (значение: {str(value)[:40]})")
            else:
                print(f"⚠️  {field:25} - пусто")

    except Exception as e:
        print(f"❌ {field:25} - ошибка: {e}")

print()
print("=" * 80)
print("ГОТОВО")
print("=" * 80)
print()
print("Для полного introspection запустите:")
print(f"python quick_introspect.py \"{URL}\"")
