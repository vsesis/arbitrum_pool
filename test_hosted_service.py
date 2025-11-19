"""
Тест Hosted Service Uniswap V3 Arbitrum на наличие positions
"""
import requests
import json

# Hosted Service (deprecated, но может работать)
HOSTED_SERVICE_URL = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-arbitrum-one"
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
    print("INTROSPECTION: Position Type в Hosted Service")
    print("=" * 80)
    print(f"URL: {HOSTED_SERVICE_URL}")
    print()

    try:
        response = requests.post(
            HOSTED_SERVICE_URL,
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
            print("❌ Тип Position не найден")
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
    print("ТЕСТ: Запрос positions")
    print("=" * 80)
    print(f"Pool: {POOL_ADDRESS}")
    print()

    try:
        response = requests.post(
            HOSTED_SERVICE_URL,
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
    print("ТЕСТИРОВАНИЕ HOSTED SERVICE UNISWAP V3 ARBITRUM")
    print("=" * 80)
    print()
    print("Hosted Service устарел, но может содержать positions...")
    print()

    # 1. Introspection
    fields = introspect_position()

    # 2. Тест запроса
    if fields:
        success = test_positions_query()

        if success:
            print()
            print("=" * 80)
            print("✅ ОТЛИЧНО! Hosted Service содержит positions")
            print("=" * 80)
            print()
            print("Создайте .env файл:")
            print()
            print(f"UNISWAP_V3_ARBITRUM_SUBGRAPH={HOSTED_SERVICE_URL}")
            print(f"UNISWAP_V3_POSITIONS_ARBITRUM_SUBGRAPH={HOSTED_SERVICE_URL}")
            print()
            print("Или используйте ваш Gateway URL для основного subgraph + Hosted Service для positions:")
            print()
            print("UNISWAP_V3_ARBITRUM_SUBGRAPH=https://gateway.thegraph.com/api/YOUR_KEY/subgraphs/id/FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oF1fxPe9aJM")
            print(f"UNISWAP_V3_POSITIONS_ARBITRUM_SUBGRAPH={HOSTED_SERVICE_URL}")
            print()
        else:
            print()
            print("=" * 80)
            print("❌ Hosted Service не содержит positions или схема отличается")
            print("=" * 80)
    else:
        print()
        print("=" * 80)
        print("❌ Тип Position не найден в Hosted Service")
        print("=" * 80)
        print()
