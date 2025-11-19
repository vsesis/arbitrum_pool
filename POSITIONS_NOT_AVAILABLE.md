# LP Positions недоступны для Arbitrum

## Проблема

Официальные Uniswap V3 subgraphs для Arbitrum One в The Graph decentralized network не содержат полных данных по LP позициям:

1. **Основной Uniswap V3 Arbitrum Subgraph** (`FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oF1fxPe9aJM`)
   - ✅ Содержит: pools, ticks, swaps
   - ❌ НЕ содержит: тип Position

2. **Uniswap V3 User Positions Arbitrum** (`EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG`)
   - ✅ Содержит: тип Position
   - ❌ НО схема несовместима (только 3 поля: id, poolProviderKey, user)
   - ❌ НЕ содержит: owner, liquidity, tickLower, tickUpper, depositedToken0/1, etc.

3. **Hosted Service** (deprecated)
   - ❌ Удален ("This endpoint has been removed")

## Что работает

Приложение **полностью функционально** для анализа пулов и распределения ликвидности:

### ✅ Работающие функции:

- **Pool Overview** - информация о пуле, токенах, комиссиях
- **Liquidity Distribution** - график распределения ликвидности по ценовым диапазонам
- **Price ranges** - анализ активной ликвидности
- **API endpoints**:
  - `GET /api/pool/{address}/summary`
  - `GET /api/pool/{address}/liquidity`

### ❌ Недоступные функции:

- **LP Overview** - агрегация данных по провайдерам ликвидности
- **Positions** - детальная информация по позициям
- **CSV экспорт** - экспорт данных по позициям
- **API endpoints**:
  - `GET /api/pool/{address}/lp-summary`
  - `GET /api/pool/{address}/positions`
  - `GET /api/pool/{address}/csv/{type}`

## Настройка без positions

### 1. Создайте .env файл:

```bash
cp .env.example .env
```

### 2. Настройте только основной subgraph:

```env
# Обязательный - для пулов и тиков
UNISWAP_V3_ARBITRUM_SUBGRAPH=https://gateway.thegraph.com/api/YOUR_API_KEY/subgraphs/id/FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oF1fxPe9aJM

# Positions subgraph - закомментируйте или оставьте пустым
# UNISWAP_V3_POSITIONS_ARBITRUM_SUBGRAPH=
```

### 3. Запустите приложение:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Используйте доступные функции:

Откройте http://localhost:8000 и анализируйте:
- Pool information
- Liquidity distribution chart
- Price ranges

## Возможные решения

### Вариант 1: Поиск альтернативного subgraph

Поищите на The Graph Explorer альтернативные subgraphs для Uniswap V3 Arbitrum:

1. Откройте: https://thegraph.com/explorer
2. Найдите: "Uniswap V3 Arbitrum" или "Uniswap Arbitrum Positions"
3. Проверьте Schema - должны быть поля:
   - `positions.owner`
   - `positions.liquidity`
   - `positions.tickLower / positions.tickUpper`
   - `positions.depositedToken0 / depositedToken1`
   - etc.

4. Скопируйте Query URL и обновите `.env`:
   ```env
   UNISWAP_V3_POSITIONS_ARBITRUM_SUBGRAPH=<новый_URL>
   ```

### Вариант 2: Использовать другую сеть

Для других сетей (Ethereum Mainnet, Polygon, Optimism) positions subgraphs могут иметь правильную схему.

### Вариант 3: Читать данные on-chain через web3.py

Можно реализовать чтение позиций напрямую из блокчейна:

```python
from web3 import Web3

# Подключение к Arbitrum RPC
w3 = Web3(Web3.HTTPProvider("https://arb1.arbitrum.io/rpc"))

# NonfungiblePositionManager контракт
NFT_POSITION_MANAGER = "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"

# Читать positions через контракт
# ... (требует дополнительной реализации)
```

**Минусы:**
- Требует много RPC запросов
- Медленнее, чем subgraph
- Нужны ABI контрактов

### Вариант 4: Использовать Dune Analytics API

Альтернатива - получать данные через Dune Analytics:
- https://dune.com/docs/api/

**Минусы:**
- Платный API
- Требует другую архитектуру запросов

## Тестовые скрипты

В проекте есть скрипты для диагностики:

```bash
# Проверить основной subgraph
python test_main_subgraph.py "https://gateway.thegraph.com/api/YOUR_KEY/subgraphs/id/FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oF1fxPe9aJM"

# Проверить positions subgraph
python test_positions_minimal.py "https://gateway.thegraph.com/api/YOUR_KEY/subgraphs/id/EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG"

# Проверить hosted service (не работает)
python test_hosted_service.py
```

## Заключение

**Приложение полностью работоспособно** для анализа пулов и распределения ликвидности на Arbitrum.

LP Positions недоступны из-за отсутствия подходящего subgraph в The Graph decentralized network.

Если найдете работающий positions subgraph с правильной схемой - обновите `.env` файл.

---

**Последнее обновление:** 2025-11-19
**Статус:** Positions недоступны для Arbitrum в The Graph
**Workaround:** Используйте приложение без positions (Pool Overview + Liquidity Distribution работают)
