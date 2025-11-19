"""
Introspection для определения реальной схемы Position в positions subgraph
"""
import requests
import json
import sys

if len(sys.argv) > 1:
    POSITIONS_SUBGRAPH_URL = sys.argv[1]
else:
    print("❌ Использование: python introspect_positions.py <SUBGRAPH_URL>")
    print()
    print("Пример:")
    print('python introspect_positions.py "https://gateway.thegraph.com/api/YOUR_KEY/subgraphs/id/EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG"')
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
            print()
            print("Попробуйте получить список всех доступных типов:")
            print("python introspect_all_types.py <URL>")
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


def generate_sample_query(fields):
    """Генерирует пример запроса на основе найденных полей"""

    if not fields:
        return None

    print("=" * 80)
    print("📝 ПРИМЕР ЗАПРОСА НА ОСНОВЕ РЕАЛЬНОЙ СХЕМЫ")
    print("=" * 80)
    print()

    # Выбираем простые поля (не вложенные объекты)
    simple_fields = []
    nested_fields = []

    for field in fields:
        field_name = field["name"]
        field_type = format_type(field["type"])

        # Проверяем, является ли поле вложенным объектом
        type_info = field["type"]
        while type_info.get("ofType"):
            type_info = type_info["ofType"]

        type_name = type_info.get("name", "")

        # Скалярные типы
        if type_name in ["String", "Int", "BigInt", "BigDecimal", "Boolean", "Bytes", "ID"]:
            simple_fields.append(field_name)
        else:
            nested_fields.append((field_name, type_name))

    # Генерируем запрос
    query_fields = simple_fields[:10]  # Первые 10 простых полей

    print("query GetPositions {")
    print("  positions(first: 5) {")
    for field in query_fields:
        print(f"    {field}")

    # Добавляем несколько вложенных полей с базовым запросом
    for field_name, type_name in nested_fields[:3]:
        print(f"    {field_name} {{")
        print(f"      id")
        print(f"    }}")

    print("  }")
    print("}")
    print()

    return query_fields, nested_fields


if __name__ == "__main__":
    print()

    # 1. Introspection
    fields = introspect_position()

    if not fields:
        print("❌ Не удалось получить схему Position")
        exit(1)

    # 2. Простой тест
    test_simple_query()

    # 3. Генерация примера запроса
    generate_sample_query(fields)

    print("=" * 80)
    print("✅ ГОТОВО")
    print("=" * 80)
    print()
    print("📌 Следующие шаги:")
    print("1. Сравните найденные поля с текущим запросом в app/uniswap_client.py:187-213")
    print("2. Обновите GraphQL query под реальную схему")
    print("3. См. POSITIONS_SCHEMA_FIX.md для детальных инструкций")
    print()
