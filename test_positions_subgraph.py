"""
Тестовый скрипт для проверки Positions Subgraph
"""
import requests
import json

# === ВАЖНО: Замените YOUR_API_KEY на ваш ключ от The Graph Studio ===
# Получить ключ: https://thegraph.com/studio/

API_KEY = "YOUR_API_KEY"  # <-- ВСТАВЬТЕ ВАШ КЛЮЧ СЮДА

# Uniswap V3 User Positions Arbitrum Subgraph
POSITIONS_SUBGRAPH_ID = "EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG"
POSITIONS_SUBGRAPH_URL = f"https://gateway.thegraph.com/api/{API_KEY}/subgraphs/id/{POSITIONS_SUBGRAPH_ID}"

POOL_ADDRESS = "0xc6962004f452be9203591991d15f6b388e09e8d0"

def test_positions():
    """Тестирует запрос к positions subgraph"""
    print(f"\n{'='*60}")
    print(f"Тестирование Positions Subgraph")
    print(f"{'='*60}")
    print(f"URL: {POSITIONS_SUBGRAPH_URL}")
    print(f"Pool: {POOL_ADDRESS}")
    print(f"{'='*60}\n")

    # Запрос позиций
    query = f"""
    {{
      positions(
        first: 5
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

    try:
        response = requests.post(
            POSITIONS_SUBGRAPH_URL,
            json={"query": query},
            timeout=30
        )

        print(f"HTTP Status: {response.status_code}")

        data = response.json()

        if "errors" in data:
            print(f"❌ GraphQL Errors:")
            for error in data['errors']:
                print(f"   {error}")
            return False

        positions = data.get('data', {}).get('positions', [])

        if not positions:
            print(f"⚠️  Позиции не найдены (может быть пул пустой)")
            print(f"Ответ: {json.dumps(data, indent=2)}")
            return True

        print(f"✅ Успешно! Найдено {len(positions)} позиций\n")

        for i, pos in enumerate(positions, 1):
            print(f"Позиция {i}:")
            print(f"  ID: {pos['id']}")
            print(f"  Owner: {pos['owner']}")
            print(f"  Liquidity: {pos['liquidity']}")
            print(f"  Tick Range: [{pos['tickLower']['tickIdx']}, {pos['tickUpper']['tickIdx']}]")
            print(f"  Deposited: {pos['depositedToken0']} / {pos['depositedToken1']}")
            print(f"  Fees: {pos['collectedFeesToken0']} / {pos['collectedFeesToken1']}")
            print()

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Тест Uniswap V3 Positions Subgraph для Arbitrum")
    print("="*60)

    if API_KEY == "YOUR_API_KEY":
        print("\n❌ ОШИБКА: Необходимо указать API ключ!")
        print("\n📝 Инструкция:")
        print("1. Зарегистрируйтесь: https://thegraph.com/studio/")
        print("2. Создайте API ключ")
        print("3. Откройте этот файл и замените YOUR_API_KEY на ваш ключ")
        print("4. Запустите скрипт снова\n")
        exit(1)

    success = test_positions()

    print("\n" + "="*60)
    if success:
        print("✅ Тест пройден! Positions subgraph работает")
        print("\nТеперь обновите ваш .env файл:")
        print(f"UNISWAP_V3_POSITIONS_SUBGRAPH_URL={POSITIONS_SUBGRAPH_URL}")
    else:
        print("❌ Тест не пройден")
        print("\nПроверьте:")
        print("- API ключ правильный")
        print("- Интернет соединение")
        print("- URL subgraph")
    print("="*60 + "\n")
