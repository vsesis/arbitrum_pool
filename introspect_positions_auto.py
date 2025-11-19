"""
Автоматический introspection для positions subgraph
Читает URL из переменных окружения
"""
import os
import requests
import json
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

POSITIONS_SUBGRAPH_URL = os.getenv("UNISWAP_V3_POSITIONS_SUBGRAPH_URL")

if not POSITIONS_SUBGRAPH_URL:
    print("❌ UNISWAP_V3_POSITIONS_SUBGRAPH_URL не установлен в .env файле!")
    exit(1)

def format_type(field_type):
    """Форматирует тип поля для читаемости"""
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
    else:
        return "Unknown"


def introspect_position():
    """Выполняет introspection типа Position"""

    introspection_query = """
    query IntrospectPosition {
      __type(name: "Position") {
        name
        kind
        description
        fields {
          name
          description
          type {
            name
            kind
            ofType {
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
    }
    """

    print("=" * 80)
    print("📊 INTROSPECTION: Position Type")
    print("=" * 80)
    print(f"URL: {POSITIONS_SUBGRAPH_URL[:70]}...")
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
            print("❌ GraphQL Errors:")
            print(json.dumps(data["errors"], indent=2))
            return None

        position_type = data.get("data", {}).get("__type")
        if not position_type:
            print("❌ Тип Position не найден в схеме!")
            return None

        print(f"✅ Найден тип: {position_type['name']} ({position_type.get('kind', 'OBJECT')})")
        if position_type.get('description'):
            print(f"Описание: {position_type['description']}")
        print()

        fields = position_type.get("fields", [])
        if not fields:
            print("⚠️  У типа Position нет полей!")
            return None

        print(f"📋 Всего полей: {len(fields)}")
        print()
        print("-" * 80)

        for field in sorted(fields, key=lambda f: f["name"]):
            field_name = field["name"]
            field_type = format_type(field["type"])
            field_desc = field.get("description", "")

            print(f"  {field_name:30} : {field_type}")
            if field_desc:
                print(f"    {'':30}   └─ {field_desc}")

        print("-" * 80)
        print()

        return fields

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
        return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_simple_query():
    """Тестовый запрос - получить первую позицию с ID"""

    query = """
    query TestSimple {
      positions(first: 1) {
        id
      }
    }
    """

    print("=" * 80)
    print("🧪 ТЕСТ: Простой запрос (только ID)")
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
            print("❌ Ошибка:")
            print(json.dumps(data["errors"], indent=2))
            return False

        positions = data.get("data", {}).get("positions", [])
        print(f"✅ Получено позиций: {len(positions)}")

        if positions:
            print(f"Пример ID: {positions[0].get('id')}")
            print()
            print("Полный объект:")
            print(json.dumps(positions[0], indent=2))

        print()
        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    print()

    # 1. Introspection
    fields = introspect_position()

    if not fields:
        print("❌ Не удалось получить схему Position")
        exit(1)

    # 2. Простой тест
    test_simple_query()

    print("=" * 80)
    print("✅ ГОТОВО")
    print("=" * 80)
    print()
    print("📌 Следующие шаги:")
    print("1. Сравните найденные поля с текущим запросом в app/uniswap_client.py:187-213")
    print("2. Обновите GraphQL query под реальную схему")
    print()
