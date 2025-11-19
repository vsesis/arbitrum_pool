# Настройка Gateway URLs для The Graph

## Проблема

Старый Hosted Service The Graph (`api.thegraph.com/subgraphs/name/...`) больше не работает.

**Ошибки:**
- `GraphQL error: Type Query has no field positions`
- `GraphQL error: This endpoint has been removed`

## Решение: Миграция на Gateway API

### Шаг 1: Получите API ключ

1. Зарегистрируйтесь на https://thegraph.com/studio/
2. Перейдите в раздел **API Keys**
3. Создайте новый API ключ
4. Скопируйте ключ

### Шаг 2: Обновите .env файл

Если `.env` не существует, создайте его:

```bash
cp .env.example .env
```

Откройте `.env` и **замените `YOUR_API_KEY` на ваш ключ**:

```env
# Основной Uniswap V3 Arbitrum Subgraph (pools, ticks, liquidity)
UNISWAP_V3_SUBGRAPH_URL=https://gateway.thegraph.com/api/ВАШ_КЛЮЧ_ЗДЕСЬ/subgraphs/id/FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oF1fxPe9aJM

# Positions Subgraph (LP NFT positions)
UNISWAP_V3_POSITIONS_SUBGRAPH_URL=https://gateway.thegraph.com/api/ВАШ_КЛЮЧ_ЗДЕСЬ/subgraphs/id/EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG
```

### Шаг 3: Перезапустите приложение

```bash
# Остановите текущий процесс (Ctrl+C)

# Запустите заново
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## Официальные Subgraph IDs

Проект использует два официальных subgraph от Uniswap для Arbitrum One:

### 1. Основной Subgraph
- **Subgraph ID**: `FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oF1fxPe9aJM`
- **Network**: arbitrum-one
- **Содержит**: pools, ticks, swaps, mints, burns, liquidity

### 2. Positions Subgraph
- **Subgraph ID**: `EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG`
- **Network**: arbitrum-one
- **Содержит**: positions (LP NFT позиции)

## Проверка

После настройки все endpoints должны работать:

```bash
# Pool summary
curl http://localhost:8000/api/pool/0xc6962004f452be9203591991d15f6b388e09e8d0/summary

# Liquidity chart data
curl http://localhost:8000/api/pool/0xc6962004f452be9203591991d15f6b388e09e8d0/liquidity

# LP data (должен вернуть 200 вместо 500!)
curl http://localhost:8000/api/pool/0xc6962004f452be9203591991d15f6b388e09e8d0/lp-summary
```

## Что изменилось

- ✅ Убраны все fallback на deprecated Hosted Service
- ✅ Обязательная настройка обоих subgraph URLs
- ✅ Использование официальных Gateway URLs
- ✅ Обновлена документация (README, QUICKSTART)

## Troubleshooting

### Ошибка: "UNISWAP_V3_SUBGRAPH_URL не установлен"

**Причина**: Не создан .env файл или в нём отсутствуют переменные.

**Решение**:
1. Создайте `.env` файл: `cp .env.example .env`
2. Добавьте ваш API ключ в обе переменные
3. Перезапустите приложение

### Ошибка: "Unauthorized" или "403"

**Причина**: Неправильный или невалидный API ключ.

**Решение**:
1. Проверьте, что API ключ скопирован полностью
2. Убедитесь, что ключ активен в The Graph Studio
3. Проверьте, что в `.env` нет пробелов или кавычек вокруг URL

### LP данные всё ещё падают (500 error)

**Возможные причины**:
1. Схема positions subgraph отличается от ожидаемой
2. Нужно использовать introspection для проверки

**Диагностика**:
```bash
# Запустите introspection для positions subgraph
python introspect_positions.py "https://gateway.thegraph.com/api/ВАШ_КЛЮЧ/subgraphs/id/EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG"
```

См. `POSITIONS_SCHEMA_FIX.md` для дополнительных инструкций.

## Ссылки

- The Graph Studio: https://thegraph.com/studio/
- Uniswap Subgraph Docs: https://docs.uniswap.org/api/subgraph/overview
- The Graph Explorer: https://thegraph.com/explorer
