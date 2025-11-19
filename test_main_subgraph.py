"""
Тест основного Uniswap V3 Arbitrum Subgraph на наличие positions
"""
import requests
import json
import sys

# Основной Uniswap V3 Arbitrum Subgraph
if len(sys.argv) > 1:
    MAIN_SUBGRAPH_URL = sys.argv[1]
else:
    print("Usage: python test_main_subgraph.py <MAIN_SUBGRAPH_URL>")
    print()
    print("Example:")
    print('python test_main_subgraph.py "https://gateway.thegraph.com/api/YOUR_KEY/subgraphs/id/FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oF1fxPe9aJM"')
    sys.exit(1)

POOL_ADDRESS = "0xc6962004f452be9203591991d15f6b388e09e8d0"


def introspect_position():
    """Интроспекция типа Position"""

    query = """
    {
      __type(name: "Position") {
        fields {
          name
          type {
            name
            kind
          }
        }
      }
    }
    """

    print("=" * 80)
    print("INTROSPECTION: Position Type в основном subgraph")
    print("=" * 80)
    print(f"URL: {MAIN_SUBGRAPH_URL[:60]}...")
    print()

    try:
        response = requests.post(
            MAIN_SUBGRAPH_URL,
            json={"query": query},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            print("❌ Ошибка:")
            print(json.dumps(data["errors"], indent=2))
            return None

        position_type = data.get("data", {}).get("__type")
        if not position_type:
            print("❌ Тип Position не найден в схеме основного subgraph")
            return None

        fields = position_type.get("fields", [])
        print(f"✅ Найдено полей: {len(fields)}")
        print()
        print("Доступные поля:")
        print("-" * 80)

        for field in sorted(fields, key=lambda f: f["name"]):
            field_name = field["name"]
            field_type = field["type"].get("name") or field["type"].get("kind")
            print(f"  {field_name:30} : {field_type}")

        print("-" * 80)
        print()
        return fields

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None


def test_positions_query():
    """Тест запроса positions"""

    query = f"""
    {{
      positions(
        first: 2
        where: {{ pool: "{POOL_ADDRESS}", liquidity_gt: "0" }}
        orderBy: liquidity
        orderDirection: desc
      ) {{
        id
        owner
        liquidity
        tickLower {{
          tickIdx
        }}
        tickUpper {{
          tickIdx
        }}
        depositedToken0
        depositedToken1
        withdrawnToken0
        withdrawnToken1
        collectedFeesToken0
        collectedFeesToken1
      }}
    }}
    """

    print("=" * 80)
    print("ТЕСТ: Запрос positions с полным набором полей")
    print("=" * 80)
    print(f"Pool: {POOL_ADDRESS}")
    print()

    try:
        response = requests.post(
            MAIN_SUBGRAPH_URL,
            json={"query": query},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            print("❌ Ошибка:")
            for err in data["errors"]:
                print(f"   {err.get('message', err)}")
            print()
            return False

        positions = data.get("data", {}).get("positions", [])
        print(f"✅ Успешно! Найдено позиций: {len(positions)}")
        print()

        if positions:
            print("Пример первой позиции:")
            print(json.dumps(positions[0], indent=2))
            print()

        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    print()
    print("=" * 80)
    print("ТЕСТИРОВАНИЕ ОСНОВНОГО UNISWAP V3 ARBITRUM SUBGRAPH")
    print("=" * 80)
    print()
    print("Проверяем, есть ли positions в основном subgraph...")
    print()

    # 1. Introspection
    fields = introspect_position()

    # 2. Тест запроса
    if fields:
        success = test_positions_query()

        if success:
            print()
            print("=" * 80)
            print("✅ ОТЛИЧНО! Основной subgraph содержит positions")
            print("=" * 80)
            print()
            print("Обновите .env:")
            print(f"  UNISWAP_V3_POSITIONS_ARBITRUM_SUBGRAPH={MAIN_SUBGRAPH_URL}")
            print()
            print("Или используйте тот же URL для обоих переменных:")
            print(f"  UNISWAP_V3_ARBITRUM_SUBGRAPH={MAIN_SUBGRAPH_URL}")
            print(f"  UNISWAP_V3_POSITIONS_ARBITRUM_SUBGRAPH={MAIN_SUBGRAPH_URL}")
            print()
        else:
            print()
            print("=" * 80)
            print("❌ Основной subgraph не содержит positions или схема отличается")
            print("=" * 80)
    else:
        print()
        print("=" * 80)
        print("❌ Тип Position не найден в основном subgraph")
        print("=" * 80)
        print()
        print("Возможно, нужен другой subgraph для positions.")
        print()
