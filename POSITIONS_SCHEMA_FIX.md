# Исправление схемы Position в positions subgraph

## Проблема

При запросе позиций из positions subgraph возникает ошибка:
```
Type `Position` has no field `owner`
Type `Position` has no field `liquidity`
Type `Position` has no field `tickLower`
...
```

Это означает, что схема Position в используемом subgraph отличается от ожидаемой.

## Диагностика

### Шаг 1: Запустите introspection

На **вашей машине** (не в Docker), где установлены зависимости:

```bash
# Убедитесь, что .env файл существует и содержит правильный URL
python test_positions_minimal.py
```

Или с явным указанием URL:

```bash
python test_positions_minimal.py "https://gateway.thegraph.com/api/YOUR_API_KEY/subgraphs/id/EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG"
```

Этот скрипт покажет:
- ✅ Все доступные поля в типе Position
- ✅ Типы каждого поля
- ✅ Примеры рабочих запросов

### Шаг 2: Найдите правильные названия полей

Сравните вывод introspection с текущим запросом в `app/uniswap_client.py:187-213`.

Возможные варианты названий полей (на основе анализа документации):

| Ожидаемое поле | Возможные альтернативы |
|----------------|------------------------|
| `owner` | `account`, `user`, `address` |
| `liquidity` | `liquidityAmount`, `amount` |
| `tickLower` | `lowerTick`, `minTick` |
| `tickUpper` | `upperTick`, `maxTick` |
| `depositedToken0` | `collectedToken0`, `token0`, `amount0` |
| `depositedToken1` | `collectedToken1`, `token1`, `amount1` |
| `withdrawnToken0` | `removedToken0`, `withdrawn0` |
| `withdrawnToken1` | `removedToken1`, `withdrawn1` |
| `collectedFeesToken0` | `feesToken0`, `fees0` |
| `collectedFeesToken1` | `feesToken1`, `fees1` |

## Возможные решения

### Вариант 1: Использовать другой subgraph (РЕКОМЕНДУЕТСЯ)

Попробуйте альтернативные Uniswap v3 subgraphs для Arbitrum:

#### A. Messari Uniswap v3 Arbitrum (обычно более стабильный)

```env
# Добавьте в .env:
UNISWAP_V3_POSITIONS_SUBGRAPH_URL=https://api.thegraph.com/subgraphs/name/messari/uniswap-v3-arbitrum
```

Схема Messari может отличаться, но обычно более документирована:
- https://github.com/messari/subgraphs

#### B. Официальный Uniswap v3 Arbitrum (может не иметь positions)

```env
UNISWAP_V3_SUBGRAPH_URL=https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3-arbitrum
```

**Проблема:** Официальный subgraph может не иметь отдельного positions endpoint.

#### C. Попробуйте Decentralized Network с другим subgraph ID

Поищите на The Graph Explorer:
- https://thegraph.com/explorer
- Ищите "Uniswap V3" или "Uniswap Positions" для Arbitrum
- Копируйте Query URL

### Вариант 2: Адаптировать код под существующую схему

После запуска introspection обновите файл `app/uniswap_client.py`:

#### Пример исправления (если fields названы по-другому):

```python
# app/uniswap_client.py, строки 187-213

# БЫЛО:
query = """
query GetPositions($poolId: String!, $skip: Int!) {
    positions(...) {
        owner           # ← НЕ СУЩЕСТВУЕТ
        liquidity       # ← НЕ СУЩЕСТВУЕТ
        tickLower {     # ← НЕ СУЩЕСТВУЕТ
            tickIdx
        }
        ...
    }
}
"""

# СТАЛО (пример, зависит от introspection):
query = """
query GetPositions($poolId: String!, $skip: Int!) {
    positions(...) {
        account         # ← если owner называется account
        liquidityAmount # ← если liquidity называется liquidityAmount
        lowerTick       # ← если tickLower - это lowerTick (без вложенности)
        upperTick       # ← если tickUpper - это upperTick (без вложенности)
        ...
    }
}
"""
```

#### Обновите также маппинг в коде:

```python
# app/uniswap_client.py, строки 228-242

# БЫЛО:
position = Position(
    id=pos_data["id"],
    owner=pos_data["owner"],  # ← ИСПРАВИТЬ
    ...
    tick_lower=int(pos_data["tickLower"]["tickIdx"]),  # ← ИСПРАВИТЬ
    ...
)

# СТАЛО (пример):
position = Position(
    id=pos_data["id"],
    owner=pos_data.get("account") or pos_data.get("owner"),  # Попробовать оба варианта
    ...
    tick_lower=int(pos_data.get("lowerTick", pos_data.get("tickLower", {}).get("tickIdx", 0))),
    ...
)
```

### Вариант 3: Использовать основной subgraph вместо positions subgraph

Некоторые Uniswap v3 subgraphs содержат positions в основном endpoint:

```python
# app/uniswap_client.py, строка 221
# use_positions_subgraph=True → use_positions_subgraph=False

data = self._query(query, {"poolId": pool_id, "skip": skip}, use_positions_subgraph=False)
```

Попробуйте запросить positions из основного subgraph URL.

### Вариант 4: Отключить positions (временное решение)

Если нужно, чтобы приложение работало без positions:

```python
# app/uniswap_client.py, строка 259
# return positions  # ← Уже так сделано

# Приложение продолжит работу с:
# - ✅ Pool Overview
# - ✅ Liquidity Distribution
# - ❌ LP Positions (будет пусто)
```

## Тестирование после исправления

### 1. Запустите тест positions:

```bash
# Обновите API_KEY в файле:
# vim test_positions_subgraph.py

python test_positions_subgraph.py
```

### 2. Запустите веб-сервер:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Проверьте логи:

Должно быть:
```
INFO - ✅ Успешно загружено X позиций для пула 0x...
```

Вместо:
```
ERROR - ❌ Ошибка при получении позиций: GraphQL errors: ...
```

## Дополнительные ресурсы

- **Uniswap v3 Subgraph Schema (GitHub):**
  https://github.com/Uniswap/v3-subgraph/blob/main/schema.graphql

- **Messari Subgraphs (альтернативная схема):**
  https://github.com/messari/subgraphs

- **The Graph Explorer (поиск subgraphs):**
  https://thegraph.com/explorer

- **Uniswap Docs:**
  https://docs.uniswap.org/api/subgraph/guides/v3-examples

## Проверьте правильность Subgraph ID

Убедитесь, что используете именно **Arbitrum One** subgraph:

```bash
# В .env должно быть:
UNISWAP_V3_POSITIONS_SUBGRAPH_URL=https://gateway.thegraph.com/api/YOUR_API_KEY/subgraphs/id/EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG

# Subgraph ID: EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG
# Название: Uniswap V3 User Positions Arbitrum
# Сеть: Arbitrum One
```

Не путайте с:
- ❌ Ethereum Mainnet positions (другой ID)
- ❌ Polygon positions (другой ID)
- ❌ Основной Uniswap v3 Arbitrum subgraph (FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oF1fxPe9aJM)

## Если ничего не помогло

Создайте issue с выводом introspection:

1. Запустите: `python test_positions_minimal.py > schema_output.txt`
2. Прикрепите `schema_output.txt`
3. Укажите версию Python, The Graph API key (первые/последние 4 символа)

---

**Следующий шаг:** Запустите `python test_positions_minimal.py` и покажите вывод!
