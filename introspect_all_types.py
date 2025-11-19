"""
Получить список ВСЕХ доступных типов в subgraph
"""
import requests
import json
import sys

if len(sys.argv) > 1:
    SUBGRAPH_URL = sys.argv[1]
else:
    print("❌ Использование: python introspect_all_types.py <SUBGRAPH_URL>")
    exit(1)

query = """
{
  __schema {
    types {
      name
      kind
      description
    }
  }
}
"""

print("=" * 80)
print("📊 INTROSPECTION: Все доступные типы в subgraph")
print("=" * 80)
print(f"URL: {SUBGRAPH_URL[:70]}...")
print()

try:
    response = requests.post(SUBGRAPH_URL, json={"query": query}, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "errors" in data:
        print("❌ Ошибка:")
        print(json.dumps(data["errors"], indent=2))
        exit(1)

    types = data.get("data", {}).get("__schema", {}).get("types", [])

    # Фильтруем системные типы (начинаются с __)
    user_types = [t for t in types if not t["name"].startswith("__")]

    print(f"✅ Найдено типов: {len(user_types)}")
    print()

    # Группируем по kind
    by_kind = {}
    for t in user_types:
        kind = t.get("kind", "UNKNOWN")
        if kind not in by_kind:
            by_kind[kind] = []
        by_kind[kind].append(t)

    for kind, types_list in sorted(by_kind.items()):
        print(f"\n{kind} ({len(types_list)}):")
        print("-" * 80)
        for t in sorted(types_list, key=lambda x: x["name"]):
            desc = t.get("description", "")
            if desc:
                print(f"  • {t['name']:30} - {desc[:50]}")
            else:
                print(f"  • {t['name']}")

    print()
    print("=" * 80)
    print()
    print("💡 Для introspection конкретного типа:")
    print('   python introspect_positions.py "<URL>"')
    print()

except Exception as e:
    print(f"❌ Ошибка: {e}")
    exit(1)
