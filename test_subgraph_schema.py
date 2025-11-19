"""
Тестовый скрипт для проверки доступных полей в Uniswap v3 subgraph
"""
import requests
import json

SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-arbitrum-one"
POOL_ADDRESS = "0xc6962004f452be9203591991d15f6b388e09e8d0"

def test_query(name, query):
    """Тестирует GraphQL запрос"""
    print(f"\n{'='*60}")
    print(f"Тест: {name}")
    print(f"{'='*60}")

    try:
        response = requests.post(
            SUBGRAPH_URL,
            json={"query": query},
            timeout=30
        )
        data = response.json()

        if "errors" in data:
            print(f"❌ Ошибка: {data['errors']}")
            return False

        print(f"✅ Успешно!")
        print(f"Ответ: {data}")
        return True

    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False


# Тест 1: Получить информацию о пуле (базовый тест)
test_query(
    "1. Базовая информация о пуле",
    f"""
    {{
      pool(id: "{POOL_ADDRESS}") {{
        id
        token0 {{ symbol }}
        token1 {{ symbol }}
        feeTier
      }}
    }}
    """
)

# Тест 2: Проверить поле positions через pool
test_query(
    "2. Позиции через pool.positions",
    f"""
    {{
      pool(id: "{POOL_ADDRESS}") {{
        id
        positions(first: 1) {{
          id
          owner
        }}
      }}
    }}
    """
)

# Тест 3: Прямой запрос к positions
test_query(
    "3. Прямой запрос к positions",
    f"""
    {{
      positions(first: 1, where: {{ pool: "{POOL_ADDRESS}" }}) {{
        id
        owner
      }}
    }}
    """
)

# Тест 4: Прямой запрос к positions с pool_
test_query(
    "4. Прямой запрос с pool_ фильтром",
    f"""
    {{
      positions(first: 1, where: {{ pool_: {{ id: "{POOL_ADDRESS}" }} }}) {{
        id
        owner
      }}
    }}
    """
)

# Тест 5: Интроспекция - какие типы доступны
test_query(
    "5. Introspection - доступные типы",
    """
    {
      __schema {
        queryType {
          fields {
            name
            description
          }
        }
      }
    }
    """
)

print(f"\n{'='*60}")
print("Тестирование завершено!")
print(f"{'='*60}\n")
