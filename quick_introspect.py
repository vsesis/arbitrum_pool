"""
Быстрый introspection для positions subgraph
"""
import sys
import requests
import json

# Проверяем аргументы
if len(sys.argv) < 2:
    print("❌ Использование: python quick_introspect.py <POSITIONS_SUBGRAPH_URL>")
    print()
    print("Или запустите приложение и скопируйте URL из логов")
    exit(1)

URL = sys.argv[1]

# Introspection query
query = """
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

print("=" * 80)
print("📊 INTROSPECTION: Position Type")
print("=" * 80)
print(f"URL: {URL[:70]}...")
print()

try:
    response = requests.post(URL, json={"query": query}, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "errors" in data:
        print("❌ GraphQL Errors:")
        print(json.dumps(data["errors"], indent=2))
        exit(1)

    position_type = data.get("data", {}).get("__type")
    if not position_type:
        print("❌ Тип Position не найден!")
        exit(1)

    fields = position_type.get("fields", [])
    print(f"✅ Найдено полей: {len(fields)}")
    print()
    print("-" * 80)

    for field in sorted(fields, key=lambda f: f["name"]):
        name = field["name"]
        type_info = field["type"]

        # Определяем тип
        if type_info.get("kind") == "NON_NULL":
            type_name = type_info["ofType"].get("name", "?") + "!"
        elif type_info.get("kind") == "LIST":
            type_name = f"[{type_info['ofType'].get('name', '?')}]"
        else:
            type_name = type_info.get("name", "?")

        print(f"  {name:35} : {type_name}")

    print("-" * 80)
    print()

    # Тестовый запрос с первыми 10 полями
    print("🧪 Попробуем запросить первую позицию с этими полями...")
    simple_fields = [f["name"] for f in fields[:10] if f["name"] != "__typename"]

    test_query = "query { positions(first: 1) { " + " ".join(simple_fields) + " } }"

    response = requests.post(URL, json={"query": test_query}, timeout=30)
    data = response.json()

    if "errors" in data:
        print("❌ Ошибка в тестовом запросе:")
        print(json.dumps(data["errors"], indent=2))
    else:
        positions = data.get("data", {}).get("positions", [])
        if positions:
            print(f"✅ Получено {len(positions)} позиций")
            print()
            print("Пример данных:")
            print(json.dumps(positions[0], indent=2))

except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
