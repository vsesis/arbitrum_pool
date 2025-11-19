"""
Минимальный тест для интроспекции схемы Position в positions subgraph
"""
import requests
import json
import sys

# Получаем URL из аргумента командной строки или используем дефолтный
if len(sys.argv) > 1:
    POSITIONS_SUBGRAPH_URL = sys.argv[1]
else:
    # Дефолтный URL - нужно заменить YOUR_API_KEY на реальный ключ
    print("❗ Использование: python test_positions_minimal.py <SUBGRAPH_URL>")
    print("❗ Или создайте .env файл с UNISWAP_V3_POSITIONS_SUBGRAPH_URL")
    print()
    POSITIONS_SUBGRAPH_URL = None

def introspect_position_type():
    """Интроспекция типа Position через GraphQL introspection"""

    introspection_query = """
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
    print("ИНТРОСПЕКЦИЯ ТИПА Position В POSITIONS SUBGRAPH")
    print("=" * 80)
    print(f"URL: {POSITIONS_SUBGRAPH_URL[:60]}...")
    print()

    try:
        response = requests.post(
            POSITIONS_SUBGRAPH_URL,
            json={"query": introspection_query},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            print("❌ Ошибка GraphQL:")
            print(json.dumps(data["errors"], indent=2))
            return

        position_type = data.get("data", {}).get("__type")
        if not position_type:
            print("❌ Тип Position не найден в схеме!")
            return

        print("✅ Найден тип Position с полями:")
        print()

        fields = position_type.get("fields", [])
        for field in sorted(fields, key=lambda f: f["name"]):
            field_name = field["name"]
            field_type = field["type"]

            # Форматируем тип
            type_str = format_type(field_type)

            print(f"  • {field_name:30} : {type_str}")

        print()
        print(f"Всего полей: {len(fields)}")
        print()

    except Exception as e:
        print(f"❌ Ошибка: {e}")


def format_type(field_type):
    """Форматирует тип поля для читаемости"""
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
    else:
        return "Unknown"


def test_simple_query():
    """Тестовый запрос с базовыми полями"""

    # Пробуем получить 1 позицию с минимальным набором полей
    query = """
    query TestPosition {
      positions(first: 1) {
        id
      }
    }
    """

    print("=" * 80)
    print("ТЕСТ ПРОСТОГО ЗАПРОСА")
    print("=" * 80)

    try:
        response = requests.post(
            POSITIONS_SUBGRAPH_URL,
            json={"query": query},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            print("❌ Ошибка GraphQL:")
            print(json.dumps(data["errors"], indent=2))
            return

        positions = data.get("data", {}).get("positions", [])
        print(f"✅ Получено позиций: {len(positions)}")
        if positions:
            print(f"Пример ID: {positions[0]['id']}")
        print()

    except Exception as e:
        print(f"❌ Ошибка: {e}")


def test_position_with_pool():
    """Тестовый запрос с фильтрацией по пулу"""

    pool_address = "0xc6962004f452be9203591991d15f6b388e09e8d0"

    # Пробуем разные варианты полей для фильтрации
    query = """
    query TestPositionPool($poolId: String!) {
      positions(first: 1, where: { pool: $poolId }) {
        id
        pool {
          id
        }
      }
    }
    """

    print("=" * 80)
    print(f"ТЕСТ ЗАПРОСА С ФИЛЬТРАЦИЕЙ ПО ПУЛУ: {pool_address}")
    print("=" * 80)

    try:
        response = requests.post(
            POSITIONS_SUBGRAPH_URL,
            json={"query": query, "variables": {"poolId": pool_address}},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            print("❌ Ошибка GraphQL:")
            print(json.dumps(data["errors"], indent=2))
            return

        positions = data.get("data", {}).get("positions", [])
        print(f"✅ Получено позиций: {len(positions)}")
        if positions:
            print(f"Пример позиции:")
            print(json.dumps(positions[0], indent=2))
        print()

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    if not POSITIONS_SUBGRAPH_URL:
        print("❌ UNISWAP_V3_POSITIONS_SUBGRAPH_URL не настроен в .env файле!")
        exit(1)

    # 1. Интроспекция схемы
    introspect_position_type()

    # 2. Простой запрос
    test_simple_query()

    # 3. Запрос с фильтрацией по пулу
    test_position_with_pool()

    print("=" * 80)
    print("ГОТОВО")
    print("=" * 80)
