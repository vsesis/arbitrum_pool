# Быстрый старт веб-приложения

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Настройка subgraph (ОБЯЗАТЕЛЬНО!)

**ВАЖНО:** Проект требует API ключ The Graph для работы с официальными subgraphs.

### 1. Получите API ключ:

1. Зарегистрируйтесь на https://thegraph.com/studio/
2. Создайте API ключ в разделе "API Keys"
3. Скопируйте ключ

### 2. Создайте .env файл:

```bash
cp .env.example .env
```

### 3. Отредактируйте .env и замените YOUR_API_KEY:

Откройте `.env` и вставьте ваш API ключ:

```env
UNISWAP_V3_SUBGRAPH_URL=https://gateway.thegraph.com/api/YOUR_API_KEY/subgraphs/id/FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oF1fxPe9aJM
UNISWAP_V3_POSITIONS_SUBGRAPH_URL=https://gateway.thegraph.com/api/YOUR_API_KEY/subgraphs/id/EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG
```

> **Примечание**: Старый Hosted Service больше не работает. Используйте только Gateway URLs.

## Запуск веб-приложения

1. Запустите backend сервер:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

2. Откройте браузер по адресу:

```
http://localhost:8000
```

3. Введите адрес пула для анализа (по умолчанию уже введен дефолтный пул `0xc6962004f452be9203591991d15f6b388e09e8d0`)

4. Нажмите "Analyze Pool" и изучайте данные через вкладки!

## Структура приложения

- **Pool Overview**: Основная информация о пуле (пара, комиссия, цена, ликвидность)
- **Liquidity Distribution**: Интерактивный график распределения ликвидности
- **LP Overview**: Таблица с агрегированными данными по провайдерам ликвидности
- **Positions**: Детальная информация по каждой позиции
- **Downloads**: Экспорт данных в CSV

## API Endpoints

- `GET /` - Главная страница (веб-интерфейс)
- `GET /api/pool/{pool_address}/summary` - Краткая информация о пуле
- `GET /api/pool/{pool_address}/liquidity` - Данные для графика ликвидности
- `GET /api/pool/{pool_address}/lp-summary?page=1&page_size=50&search=` - Данные по LP
- `GET /api/pool/{pool_address}/positions?page=1&page_size=50&lp=` - Данные по позициям
- `GET /api/pool/{pool_address}/csv/{type}` - Скачать CSV (type: "lp-summary" или "positions")
- `GET /docs` - Автоматическая документация API (Swagger UI)

## Пример использования CLI (старый способ)

```bash
# Анализ дефолтного пула
python -m app.main

# Анализ конкретного пула
python -m app.main --pool 0xc6962004f452be9203591991d15f6b388e09e8d0

# С подробными логами
python -m app.main --pool 0xc6962004f452be9203591991d15f6b388e09e8d0 --verbose
```

## Архитектура

```
┌─────────────┐
│   Browser   │
│  (Frontend) │
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────────┐
│  FastAPI        │
│  (backend/)     │
├─────────────────┤
│  • main.py      │  ← Приложение, статика
│  • api.py       │  ← REST endpoints
│  • service.py   │  ← Кеш и бизнес-логика
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│  Core Analytics  │
│  (app/)          │
├──────────────────┤
│  • uniswap_      │  ← GraphQL клиент
│    client.py     │
│  • analytics.py  │  ← Расчеты
│  • models.py     │  ← Модели данных
└────────┬─────────┘
         │ GraphQL
         ▼
┌──────────────────┐
│  Uniswap v3      │
│  Subgraph        │
│  (The Graph)     │
└──────────────────┘
```

## Технологии

- **Backend**: FastAPI, Python 3.8+
- **Frontend**: Vanilla JS, Tailwind CSS, Chart.js
- **Data**: The Graph (Uniswap v3 Subgraph для Arbitrum)
- **Визуализация**: Chart.js для интерактивных графиков

## Особенности дизайна

- Тёмная тема (#0a0a0f фон)
- Минималистичный UI в стиле nof1.ai
- Lazy loading данных (табы загружаются по запросу)
- Responsive дизайн (работает на мобильных)
- Пагинация и поиск для больших таблиц
