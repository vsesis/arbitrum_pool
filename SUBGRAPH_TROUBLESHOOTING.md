# Troubleshooting: Subgraph Schema Issues

## Проблема

Ошибка при запросе позиций:
```
GraphQL errors: [{'message': 'Type `Query` has no field `positions`'}]
```

## Причина

Uniswap v3 Subgraph для Arbitrum на The Graph hosted service имеет ограниченную схему или устаревший endpoint.

## Решения

### Вариант 1: Обновить URL Subgraph

The Graph мигрирует с Hosted Service на Decentralized Network. Попробуйте обновить URL:

1. **Получите API ключ от The Graph:**
   - Зарегистрируйтесь на https://thegraph.com/studio/
   - Создайте API ключ

2. **Найдите правильный subgraph:**
   - Перейдите на https://thegraph.com/explorer
   - Найдите "Uniswap V3" для Arbitrum One
   - Скопируйте Query URL

3. **Обновите `.env`:**
   ```env
   UNISWAP_V3_SUBGRAPH_URL=https://gateway.thegraph.com/api/YOUR-API-KEY/subgraphs/id/...
   ```

### Вариант 2: Использовать альтернативные источники

Если subgraph не поддерживает `positions`, можно:

1. **Использовать только базовую информацию:**
   - Pool Overview (работает ✅)
   - Liquidity Distribution (работает ✅)
   - Без детальных позиций LP

2. **Получать позиции напрямую из блокчейна:**
   - Используйте web3.py + Arbitrum RPC
   - Читайте события `Mint`, `Burn`, `Collect` из смарт-контракта
   - Требует больше времени на загрузку

### Вариант 3: Проверить доступные поля

Запустите тест на **вашей машине** (не в sandbox):

```bash
python test_subgraph_schema.py
```

Это покажет:
- Какие запросы работают
- Какие поля доступны
- Правильную структуру для вашего subgraph

### Вариант 4: Использовать другой Subgraph

Попробуйте альтернативные endpoints:

```env
# Вариант 1: Messari Subgraph (обычно более стабильный)
UNISWAP_V3_SUBGRAPH_URL=https://api.thegraph.com/subgraphs/name/messari/uniswap-v3-arbitrum

# Вариант 2: Официальный Uniswap (если доступен)
UNISWAP_V3_SUBGRAPH_URL=https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3-arbitrum
```

## Текущее состояние приложения

✅ **Работает:**
- Информация о пуле (токены, цена, комиссия)
- График распределения ликвидности
- Веб-интерфейс

⚠️ **Недоступно (из-за ошибки subgraph):**
- LP Overview (список провайдеров ликвидности)
- Positions (детальная информация по позициям)
- CSV экспорт позиций

## Как проверить, что positions работают

После обновления URL subgraph:

1. Перезапустите сервер
2. Откройте веб-интерфейс
3. Нажмите "Analyze Pool"
4. Проверьте логи - должно быть:
   ```
   INFO - Успешно загружено X позиций (метод 1)
   ```

## Дополнительная информация

- Официальная документация Uniswap Subgraph: https://docs.uniswap.org/api/subgraph/overview
- The Graph Explorer: https://thegraph.com/explorer
- Migration Guide: https://thegraph.com/docs/en/sunrise/
