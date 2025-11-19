# Схема Positions Subgraph - Заметки

## Проблема

Positions Subgraph для Arbitrum имеет другую схему, чем ожидалось.

**Ошибки:**
```
Type `Position` has no field `owner`
Type `Position` has no field `liquidity`
Type `Position` has no field `tickLower`
Type `Position` has no field `depositedToken0`
...
```

## Возможные варианты схемы

### Вариант 1: Уменьшенная схема
Position может содержать только:
- `id`
- `pool` (ссылка на Pool)
- `token0`, `token1` (ссылки на Token)
- `transaction` (ссылка на Transaction)

### Вариант 2: Вложенные поля
Данные могут быть в подобъектах:
- `position.account` вместо `owner`
- `position.pool.token0` вместо прямых полей
- События `mints`, `burns`, `collects` вместо агрегированных данных

### Вариант 3: События вместо позиций
Subgraph может предоставлять только события:
- `mints` - создание/добавление ликвидности
- `burns` - удаление ликвидности
- `collects` - сбор комиссий

## Как узнать правильную схему

### Шаг 1: Запустите introspection

```bash
python introspect_positions.py
```

Это покажет все доступные поля Position.

### Шаг 2: Запустите минимальный тест

```bash
python test_positions_minimal.py
```

Это попробует разные варианты запросов.

### Шаг 3: Посмотрите в Graph Explorer

1. Откройте: https://thegraph.com/explorer/subgraphs/EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG
2. Перейдите на вкладку "Playground"
3. Посмотрите примеры запросов
4. Используйте автокомплит (Ctrl+Space) для просмотра полей

## Альтернативное решение: События

Если positions недоступны в нужном формате, можно построить позиции из событий:

### Получить события Mint
```graphql
{
  mints(
    first: 1000
    where: { pool: "0x..." }
    orderBy: timestamp
    orderDirection: desc
  ) {
    id
    transaction {
      id
      from
    }
    pool {
      id
    }
    tickLower
    tickUpper
    amount
    amount0
    amount1
    timestamp
  }
}
```

### Получить события Collect
```graphql
{
  collects(
    first: 1000
    where: { pool: "0x..." }
  ) {
    id
    transaction {
      from
    }
    amount0
    amount1
    tickLower
    tickUpper
  }
}
```

### Построить позиции
Объединить mints, burns, collects по:
- `transaction.from` (owner)
- `tickLower`, `tickUpper` (диапазон)

## Следующие шаги

1. ✅ Запустите `introspect_positions.py` → узнайте поля
2. ✅ Скопируйте вывод и отправьте мне
3. ✅ Я обновлю код с правильной схемой
4. ✅ Перезапустите сервер → всё заработает!

---

**Скопируйте и отправьте мне вывод этих команд:**
```bash
python introspect_positions.py
python test_positions_minimal.py
```

Я сразу исправлю код под правильную схему! 🎯
