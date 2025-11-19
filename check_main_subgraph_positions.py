"""
Проверка positions в ОСНОВНОМ Uniswap v3 Arbitrum subgraph
"""
import requests
import json
import sys

# Основной Uniswap v3 Arbitrum Subgraph
MAIN_SUBGRAPH_ID = "FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oF1fxPe9aJM"

if len(sys.argv) > 1:
    API_KEY = sys.argv[1]
else:
    print("❌ Использование: python check_main_subgraph_positions.py <API_KEY>")
    print()
    print("Пример:")
    print("   python check_main_subgraph_positions.py 5b92789c9c13bae8a09ff3d3a2ab21f5")
    exit(1)

MAIN_SUBGRAPH_URL = f"https://gateway.thegraph.com/api/{API_KEY}/subgraphs/id/{MAIN_SUBGRAPH_ID}"

print("=" * 80)
print("🔍 ПРОВЕРКА: Positions в основном Uniswap v3 Arbitrum subgraph")
print("=" * 80)
print(f"Subgraph ID: {MAIN_SUBGRAPH_ID}")
print(f"URL: {MAIN_SUBGRAPH_URL[:70]}...")
print()

# 1. Проверяем, есть ли тип Position
introspection_query = """
{
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

print("Шаг 1: Проверяем наличие типа Position...")
try:
    response = requests.post(MAIN_SUBGRAPH_URL, json={"query": introspection_query}, timeout=30)
    data = response.json()

    if "errors" in data:
        print("❌ Ошибка:")
        print(json.dumps(data["errors"], indent=2))
    else:
        position_type = data.get("data", {}).get("__type")
        if position_type:
            print(f"✅ Тип Position найден!")
            print(f"   Полей: {len(position_type.get('fields', []))}")
            print()

            print("Поля Position:")
            print("-" * 80)
            for field in sorted(position_type.get("fields", []), key=lambda f: f["name"]):
                field_name = field["name"]
                field_type = field["type"]

                # Простое форматирование типа
                type_str = field_type.get("name") or field_type.get("ofType", {}).get("name", "Complex")
                print(f"  • {field_name:30} : {type_str}")
            print("-" * 80)
            print()

            # Пробуем простой запрос
            print("Шаг 2: Тестовый запрос...")
            test_query = """
            {
              positions(first: 1) {
                id
              }
            }
            """

            response2 = requests.post(MAIN_SUBGRAPH_URL, json={"query": test_query}, timeout=30)
            data2 = response2.json()

            if "errors" in data2:
                print("❌ Ошибка при запросе:")
                print(json.dumps(data2["errors"], indent=2))
            else:
                positions = data2.get("data", {}).get("positions", [])
                print(f"✅ Получено позиций: {len(positions)}")
                if positions:
                    print(f"   Пример ID: {positions[0].get('id')}")

        else:
            print("❌ Тип Position НЕ найден в основном subgraph")
            print()
            print("Попробуем найти альтернативные типы...")

            # Получаем все типы
            all_types_query = """
            {
              __schema {
                types {
                  name
                  kind
                }
              }
            }
            """

            response3 = requests.post(MAIN_SUBGRAPH_URL, json={"query": all_types_query}, timeout=30)
            data3 = response3.json()

            if "errors" not in data3:
                all_types = data3.get("data", {}).get("__schema", {}).get("types", [])
                user_types = [t for t in all_types if not t["name"].startswith("__") and t["kind"] == "OBJECT"]

                print("Доступные OBJECT типы:")
                for t in sorted(user_types, key=lambda x: x["name"]):
                    print(f"  • {t['name']}")

except Exception as e:
    print(f"❌ Ошибка: {e}")

print()
print("=" * 80)
print("✅ ГОТОВО")
print("=" * 80)
