# Uniswap v3 Pool Analyzer для Arbitrum

Инструмент для глубокого анализа пулов Uniswap v3 в сети Arbitrum One. Позволяет анализировать распределение ликвидности, позиции провайдеров ликвидности (LP) и их доходность.

## 🎯 Возможности

- **Информация о пуле**: Получение детальной информации о токенах, комиссиях, текущей цене
- **График ликвидности**: Визуализация распределения ликвидности по ценовым диапазонам
- **Анализ позиций**: Детальная информация по всем активным позициям в пуле
- **Аналитика LP**: Агрегация данных по провайдерам ликвидности:
  - Внесённые суммы (deposited)
  - Выведенные суммы (withdrawn)
  - Заработанные комиссии (collected + uncollected fees)
  - Ценовые диапазоны позиций
- **Экспорт данных**: CSV файлы для дальнейшего анализа

## 📋 Требования

- Python 3.8+
- Доступ к Uniswap v3 Subgraph для Arbitrum (The Graph)

## 🚀 Установка

### 1. Клонируй репозиторий

```bash
git clone <your-repo>
cd arbitrum_pool
```

### 2. Создай виртуальное окружение (рекомендуется)

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Установи зависимости

```bash
pip install -r requirements.txt
```

### 4. Настрой конфигурацию

Скопируй файл `.env.example` в `.env`:

```bash
cp .env.example .env
```

Отредактируй `.env` и укажи актуальный URL сабграфа:

```env
UNISWAP_V3_SUBGRAPH_URL=https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-arbitrum-one
```

**Где взять актуальный URL сабграфа:**

- Uniswap Docs: https://docs.uniswap.org/api/subgraph/overview
- The Graph Explorer: https://thegraph.com/explorer
- Для Arbitrum ищи: "uniswap-v3-arbitrum" или "uniswap-arbitrum-one"

> **Примечание**: Hosted Service может быть deprecated. Рекомендуется использовать децентрализованную сеть The Graph с API ключом.

## 📁 Структура проекта

```
arbitrum_pool/
├── app/
│   ├── __init__.py          # Инициализация модуля
│   ├── config.py            # Конфигурация (endpoint subgraph, константы)
│   ├── models.py            # Модели данных (Pool, Position, Token, etc.)
│   ├── uniswap_client.py    # GraphQL клиент для subgraph
│   ├── analytics.py         # Расчёты, агрегации, экспорт в CSV
│   ├── plots.py             # Построение графиков
│   └── main.py              # CLI точка входа
├── data/                    # Выходные CSV файлы
├── charts/                  # Выходные графики (PNG)
├── requirements.txt         # Зависимости Python
├── .env.example             # Пример конфигурации
└── README.md                # Документация (этот файл)
```

### Описание модулей

- **`config.py`**: Настройки приложения (URL subgraph, дефолтный пул, директории)
- **`models.py`**: Dataclass модели для Pool, Token, Position, LpOwnerSummary
- **`uniswap_client.py`**: Клиент для выполнения GraphQL запросов к Uniswap v3 subgraph
- **`analytics.py`**: Функции для расчёта распределения ликвидности, агрегации по LP, экспорта в CSV
- **`plots.py`**: Построение графиков с помощью matplotlib
- **`main.py`**: CLI интерфейс для запуска анализа

## 💻 Использование

### Базовый запуск (дефолтный пул)

Дефолтный пул: `0xc6962004f452be9203591991d15f6b388e09e8d0`

```bash
python -m app.main
```

### Анализ конкретного пула

```bash
python -m app.main --pool 0xc6962004f452be9203591991d15f6b388e09e8d0
```

### С подробными логами

```bash
python -m app.main --pool 0xc6962004f452be9203591991d15f6b388e09e8d0 --verbose
```

### Справка

```bash
python -m app.main --help
```

## 📊 Выходные данные

После выполнения анализа создаются следующие файлы:

### Графики (charts/)

- **`<pool_address>_liquidity_log.png`**: График распределения ликвидности (логарифмическая шкала, полный диапазон)
- **`<pool_address>_liquidity_linear.png`**: График ликвидности (линейная шкала, ±20% от текущей цены)

### CSV файлы (data/)

- **`<pool_address>_lp_positions.csv`**: Детальная информация по каждой позиции
  - Position ID, Owner, Liquidity
  - Tick Lower/Upper, Price Lower/Upper
  - Deposited/Withdrawn Token0/Token1
  - Collected Fees, Total Fees

- **`<pool_address>_lp_summary_by_owner.csv`**: Агрегированные данные по каждому LP
  - Owner address
  - Количество позиций
  - Суммарные депозиты/выводы
  - Общая прибыль по комиссиям

## 📝 Пример вывода

```
================================================================================
ИНФОРМАЦИЯ О ПУЛЕ: 0xc6962004f452be9203591991d15f6b388e09e8d0
================================================================================
Пара:           WETH / USDC
Token0:         WETH (0x82af49447d8a07e3bd95bd0d56f35241523fbab1)
  - Decimals:   18
Token1:         USDC (0xff970a61a04b1ca14834a43f5de4533ebddb5cc8)
  - Decimals:   6
Комиссия:       0.05%
Текущая цена:   3250.45678912 USDC/WETH
Текущий тик:    201234
Общая ликв.:    1234567890123456
================================================================================

✓ Найдено активных позиций: 156
✓ Уникальных LP: 89

================================================================================
ТОП 10 ПРОВАЙДЕРОВ ЛИКВИДНОСТИ
================================================================================

1. 0x1234567890abcdef...
   Позиций:             5
   Депозиты:            12.5000 WETH, 40500.0000 USDC
   Выводы:              2.1000 WETH, 6800.0000 USDC
   Чистые депозиты:     10.4000 WETH, 33700.0000 USDC
   Заработано комиссий: 0.123456 WETH, 400.123456 USDC
...
```

## 🔧 Технические детали

### Расчёт цен из тиков

Формула конвертации тика в цену:

```python
price = 1.0001^tick / (10^(decimals1 - decimals0))
```

Где:
- `tick`: индекс тика
- `decimals0/decimals1`: количество decimals у токенов

### Расчёт прибыли LP

Прибыль от комиссий рассчитывается как:

```
Total Fees = Collected Fees + Uncollected Fees
```

Где:
- **Collected Fees**: Комиссии, уже собранные LP (из событий `Collect`)
- **Uncollected Fees**: Накопленные, но ещё не собранные комиссии

### Источник данных

Все данные получаются из Uniswap v3 Subgraph через GraphQL запросы:

- **Pool**: `pool(id: $poolId)`
- **Ticks**: `ticks(where: {poolAddress: $poolId})`
- **Positions**: `positions(where: {pool: $poolId})`

## ⚠️ Допущения и ограничения

1. **Комиссии**: Данные по `uncollectedFees` могут быть недоступны в некоторых версиях subgraph. В этом случае учитываются только `collectedFees`.

2. **Deposited/Withdrawn суммы**: Берутся из subgraph. Для более точных данных можно читать события `Mint`/`Burn`/`Collect` напрямую из блокчейна через RPC.

3. **Закрытые позиции**: Позиции с `liquidity = 0` исключаются из анализа.

4. **Текущая стоимость**: Инструмент НЕ рассчитывает текущую стоимость позиций в USD/ETH. Для этого нужно дополнительно вычислять количество token0/token1 в позиции на основе текущей цены и диапазона.

## 🚀 Возможные улучшения

1. **Чтение событий из блокчейна**: Использовать web3.py для чтения событий `Mint`, `Burn`, `Collect` напрямую из Arbitrum RPC
   - Более точные данные по комиссиям
   - Информация о времени создания/закрытия позиций

2. **Расчёт текущей стоимости позиций**: На основе формул Uniswap v3:
   ```python
   amount0 = liquidity * (sqrt(P) - sqrt(Pa)) / (sqrt(P) * sqrt(Pa))
   amount1 = liquidity * (sqrt(Pb) - sqrt(P))
   ```

3. **Исторический анализ**: Отслеживание изменения ликвидности во времени

4. **Оценка APR/APY**: Расчёт доходности на основе комиссий и времени нахождения в пуле

5. **Impermanent Loss**: Расчёт IL для каждой позиции

6. **Сравнение пулов**: Анализ нескольких пулов одновременно

7. **Web интерфейс**: Добавить простой веб-интерфейс (Flask/FastAPI + React)

## 🐛 Решение проблем

### Ошибка: "GraphQL errors" или "pool not found"

- Проверь, что адрес пула корректный и существует на Arbitrum
- Убедись, что URL subgraph актуальный (Hosted Service может быть deprecated)
- Попробуй использовать The Graph decentralized network с API ключом

### Ошибка: "Connection timeout"

- Проблемы с подключением к subgraph endpoint
- Попробуй другой endpoint или RPC

### Пустые данные по позициям

- Возможно, в пуле действительно нет активных позиций
- Проверь пул в интерфейсе Uniswap: https://app.uniswap.org/

## 📚 Полезные ссылки

- [Uniswap v3 Docs](https://docs.uniswap.org/protocol/concepts/V3-overview/concentrated-liquidity)
- [Uniswap v3 Subgraph Schema](https://docs.uniswap.org/api/subgraph/overview)
- [The Graph Explorer](https://thegraph.com/explorer)
- [Arbitrum One Chain Info](https://arbiscan.io/)

## 📄 Лицензия

MIT

## 👨‍💻 Автор

Разработано для анализа пулов Uniswap v3 на Arbitrum One.

---

**Тестовый пул**: `0xc6962004f452be9203591991d15f6b388e09e8d0`

Все примеры и дефолтные настройки используют этот пул.
