"""
Introspection запрос для Positions Subgraph
Узнаем правильную схему Position
"""
import requests
import json

# ВСТАВЬТЕ ВАШ API КЛЮЧ
API_KEY = "5b92789c9c13bae8a09ff3d3a2ab21f5"

POSITIONS_SUBGRAPH_ID = "EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG"
POSITIONS_SUBGRAPH_URL = f"https://gateway.thegraph.com/api/{API_KEY}/subgraphs/id/{POSITIONS_SUBGRAPH_ID}"

# Introspection запрос для типа Position
query = """
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

print("Запрос схемы Position из subgraph...")
print(f"URL: {POSITIONS_SUBGRAPH_URL}\n")

response = requests.post(
    POSITIONS_SUBGRAPH_URL,
    json={"query": query},
    timeout=30
)

data = response.json()

if "errors" in data:
    print("❌ Ошибка:")
    print(json.dumps(data["errors"], indent=2))
else:
    position_type = data["data"]["__type"]
    print(f"✅ Тип: {position_type['name']}\n")
    print("Доступные поля:")
    print("="*60)

    for field in position_type["fields"]:
        field_name = field["name"]
        field_type = field["type"]

        # Определяем тип поля
        if field_type["kind"] == "NON_NULL":
            type_name = field_type["ofType"]["name"] + "!"
        else:
            type_name = field_type["name"] or field_type["ofType"]["name"]

        print(f"{field_name:30} {type_name}")

    print("="*60)
