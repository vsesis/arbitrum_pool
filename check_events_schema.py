"""
Introspection событий Mint, Burn, Collect в основном Uniswap v3 Arbitrum subgraph
"""
import requests
import json
import sys

if len(sys.argv) > 1:
    API_KEY = sys.argv[1]
else:
    print("❌ Использование: python check_events_schema.py <API_KEY>")
    exit(1)

MAIN_SUBGRAPH_ID = "FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oF1fxPe9aJM"
SUBGRAPH_URL = f"https://gateway.thegraph.com/api/{API_KEY}/subgraphs/id/{MAIN_SUBGRAPH_ID}"


def format_type(field_type):
    """Форматирует тип поля"""
    if not field_type:
        return "Unknown"

    kind = field_type.get("kind")
    name = field_type.get("name")
    of_type = field_type.get("ofType")

    if kind == "NON_NULL":
        return format_type(of_type) + "!"
    elif kind == "LIST":
        return f"[{format_type(of_type)}]"
    elif name:
        return name
    elif of_type:
        return format_type(of_type)
    return "Unknown"


def introspect_type(type_name):
    """Выполняет introspection типа"""

    query = f"""
    {{
      __type(name: "{type_name}") {{
        name
        kind
        description
        fields {{
          name
          description
          type {{
            name
            kind
            ofType {{
              name
              kind
              ofType {{
                name
                kind
              }}
            }}
          }}
        }}
      }}
    }}
    """

    print("=" * 80)
    print(f"📊 Тип: {type_name}")
    print("=" * 80)

    try:
        response = requests.post(SUBGRAPH_URL, json={"query": query}, timeout=30)
        data = response.json()

        if "errors" in data:
            print(f"❌ Ошибка: {data['errors']}")
            return None

        type_info = data.get("data", {}).get("__type")
        if not type_info:
            print(f"❌ Тип {type_name} не найден")
            return None

        if type_info.get("description"):
            print(f"Описание: {type_info['description']}")
            print()

        fields = type_info.get("fields", [])
        print(f"Полей: {len(fields)}")
        print("-" * 80)

        for field in sorted(fields, key=lambda f: f["name"]):
            field_name = field["name"]
            field_type = format_type(field["type"])
            print(f"  {field_name:30} : {field_type}")

        print("-" * 80)
        print()

        return fields

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None


def test_query_events(pool_address="0xc6962004f452be9203591991d15f6b388e09e8d0"):
    """Тестовый запрос для получения событий пула"""

    query = f"""
    {{
      mints(first: 2, where: {{ pool: "{pool_address}" }}, orderBy: timestamp, orderDirection: desc) {{
        id
        owner
        sender
        origin
        amount
        amount0
        amount1
        amountUSD
        tickLower
        tickUpper
        timestamp
      }}
      burns(first: 2, where: {{ pool: "{pool_address}" }}, orderBy: timestamp, orderDirection: desc) {{
        id
        owner
        origin
        amount
        amount0
        amount1
        amountUSD
        tickLower
        tickUpper
        timestamp
      }}
      collects(first: 2, where: {{ pool: "{pool_address}" }}, orderBy: timestamp, orderDirection: desc) {{
        id
        owner
        amount0
        amount1
        amountUSD
        tickLower
        tickUpper
        timestamp
      }}
    }}
    """

    print("=" * 80)
    print(f"🧪 ТЕСТ: Получение событий для пула {pool_address}")
    print("=" * 80)

    try:
        response = requests.post(SUBGRAPH_URL, json={"query": query}, timeout=30)
        data = response.json()

        if "errors" in data:
            print(f"❌ Ошибка: {json.dumps(data['errors'], indent=2)}")
            return

        result = data.get("data", {})
        mints = result.get("mints", [])
        burns = result.get("burns", [])
        collects = result.get("collects", [])

        print(f"✅ Mint событий: {len(mints)}")
        if mints:
            print("   Пример Mint:")
            print(f"   {json.dumps(mints[0], indent=4)}")
        print()

        print(f"✅ Burn событий: {len(burns)}")
        if burns:
            print("   Пример Burn:")
            print(f"   {json.dumps(burns[0], indent=4)}")
        print()

        print(f"✅ Collect событий: {len(collects)}")
        if collects:
            print("   Пример Collect:")
            print(f"   {json.dumps(collects[0], indent=4)}")
        print()

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    print()
    print("=" * 80)
    print("📋 INTROSPECTION: События Uniswap v3 (Mint, Burn, Collect)")
    print("=" * 80)
    print()

    # Introspection всех трех типов событий
    mint_fields = introspect_type("Mint")
    burn_fields = introspect_type("Burn")
    collect_fields = introspect_type("Collect")

    # Тестовый запрос
    test_query_events()

    print("=" * 80)
    print("✅ ГОТОВО")
    print("=" * 80)
    print()
    print("💡 Вывод:")
    print("   - Position типа НЕТ в основном subgraph")
    print("   - НО можно собрать данные о позициях из событий Mint/Burn/Collect")
    print("   - Каждое событие содержит: owner, tickLower, tickUpper, amount0/1")
    print()
    print("📌 Следующий шаг:")
    print("   - Агрегировать события по (owner, tickLower, tickUpper)")
    print("   - Суммировать Mint/Burn для расчета deposited/withdrawn")
    print("   - Суммировать Collect для расчета collected fees")
    print()
