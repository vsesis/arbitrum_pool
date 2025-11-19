"""
Тестирование Messari Uniswap V3 Arbitrum Subgraph
"""
import requests
import json

# Messari Uniswap v3 Arbitrum - обычно более стабильная схема
MESSARI_URL = "https://api.thegraph.com/subgraphs/name/messari/uniswap-v3-arbitrum"
POOL_ADDRESS = "0xc6962004f452be9203591991d15f6b388e09e8d0"

def test_messari_positions():
    """Тестирует запрос к Messari subgraph"""

    print("=" * 80)
    print("ТЕСТ: Messari Uniswap V3 Arbitrum Subgraph")
    print("=" * 80)
    print(f"URL: {MESSARI_URL}")
    print()

    # Простой запрос - получить одну позицию
    query = """
    {
      positions(first: 1) {
        id
      }
    }
    """

    print("1. Тестируем простой запрос (только ID)...")

    try:
        response = requests.post(
            MESSARI_URL,
            json={"query": query},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            print(f"❌ Ошибка: {data['errors']}")
            return False

        positions = data.get("data", {}).get("positions", [])
        print(f"✅ Успешно! Найдено позиций: {len(positions)}")

        if positions:
            print(f"Пример ID: {positions[0]['id']}")

        print()
        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def introspect_messari_position():
    """Интроспекция схемы Position в Messari"""

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

    print("2. Introspection схемы Position...")
    print()

    try:
        response = requests.post(
            MESSARI_URL,
            json={"query": query},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            print(f"❌ Ошибка: {data['errors']}")
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


def test_detailed_query(fields):
    """Тестирует детальный запрос с найденными полями"""

    if not fields:
        return False

    # Выбираем простые поля
    simple_fields = [f["name"] for f in fields if f["name"] in [
        "id", "owner", "account", "liquidity", "liquidityAmount",
        "tickLower", "tickUpper", "lowerTick", "upperTick",
        "depositedToken0", "depositedToken1",
        "withdrawnToken0", "withdrawnToken1",
        "collectedFeesToken0", "collectedFeesToken1"
    ]][:10]

    if not simple_fields:
        print("⚠️  Не найдено знакомых полей")
        return False

    query_fields = "\n        ".join(simple_fields)

    query = f"""
    {{
      positions(first: 1, where: {{ pool: "{POOL_ADDRESS}" }}) {{
        {query_fields}
      }}
    }}
    """

    print("3. Тестируем детальный запрос с фильтром по пулу...")
    print()
    print("Запрашиваемые поля:")
    for field in simple_fields:
        print(f"  - {field}")
    print()

    try:
        response = requests.post(
            MESSARI_URL,
            json={"query": query},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            print(f"❌ Ошибка:")
            for err in data["errors"]:
                print(f"   {err.get('message', err)}")
            return False

        positions = data.get("data", {}).get("positions", [])
        print(f"✅ Успешно! Найдено позиций: {len(positions)}")

        if positions:
            print()
            print("Пример данных:")
            print(json.dumps(positions[0], indent=2))

        print()
        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    print()
    print("=" * 80)
    print("ТЕСТИРОВАНИЕ MESSARI UNISWAP V3 ARBITRUM SUBGRAPH")
    print("=" * 80)
    print()
    print("Messari subgraphs обычно имеют более стабильную схему.")
    print("Документация: https://github.com/messari/subgraphs")
    print()

    # 1. Простой тест
    success = test_messari_positions()
    if not success:
        print("❌ Messari subgraph недоступен или не работает")
        exit(1)

    # 2. Introspection
    fields = introspect_messari_position()

    # 3. Детальный запрос
    if fields:
        test_detailed_query(fields)

    print("=" * 80)
    print("✅ ГОТОВО")
    print("=" * 80)
    print()
    print("Если Messari работает, обновите .env:")
    print(f"  UNISWAP_V3_POSITIONS_ARBITRUM_SUBGRAPH={MESSARI_URL}")
    print()
