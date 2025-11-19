"""
Минимальный тест для определения схемы Position
"""
import requests
import json

API_KEY = "5b92789c9c13bae8a09ff3d3a2ab21f5"
POSITIONS_SUBGRAPH_URL = f"https://gateway.thegraph.com/api/{API_KEY}/subgraphs/id/EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG"
POOL_ADDRESS = "0xc6962004f452be9203591991d15f6b388e09e8d0"

print("="*60)
print("Минимальный тест Position")
print("="*60)

# Тест 1: Только ID
print("\nТест 1: Получаем только ID")
query1 = f"""
{{
  positions(first: 1, where: {{ pool: "{POOL_ADDRESS}" }}) {{
    id
  }}
}}
"""

response = requests.post(POSITIONS_SUBGRAPH_URL, json={"query": query1}, timeout=30)
data = response.json()

if "errors" in data:
    print("❌ Ошибка:", data["errors"])
else:
    print("✅ Работает!")
    print(json.dumps(data, indent=2))

# Тест 2: ID + transaction
print("\n\nТест 2: ID + transaction")
query2 = f"""
{{
  positions(first: 1, where: {{ pool: "{POOL_ADDRESS}" }}) {{
    id
    transaction {{
      id
    }}
  }}
}}
"""

response = requests.post(POSITIONS_SUBGRAPH_URL, json={"query": query2}, timeout=30)
data = response.json()

if "errors" in data:
    print("❌ Ошибка:", data["errors"])
else:
    print("✅ Работает!")
    print(json.dumps(data, indent=2))

# Тест 3: ID + token0 + token1
print("\n\nТест 3: ID + token0 + token1")
query3 = f"""
{{
  positions(first: 1, where: {{ pool: "{POOL_ADDRESS}" }}) {{
    id
    token0 {{
      id
      symbol
    }}
    token1 {{
      id
      symbol
    }}
  }}
}}
"""

response = requests.post(POSITIONS_SUBGRAPH_URL, json={"query": query3}, timeout=30)
data = response.json()

if "errors" in data:
    print("❌ Ошибка:", data["errors"])
else:
    print("✅ Работает!")
    print(json.dumps(data, indent=2))

print("\n" + "="*60)
print("Запустите также: python introspect_positions.py")
print("="*60)
