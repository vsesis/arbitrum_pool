# Настройка Positions Subgraph для Arbitrum

## Проблема решена! 🎉

Uniswap V3 на Arbitrum использует **два отдельных subgraph**:

1. **Основной** - для пулов, тиков, свопов (уже работает ✅)
2. **Positions** - для NFT позиций LP (нужно настроить)

## Быстрая настройка (5 минут)

### Шаг 1: Получите API ключ от The Graph

1. Зарегистрируйтесь: https://thegraph.com/studio/
2. Перейдите в раздел "API Keys"
3. Создайте новый ключ или скопируйте существующий

### Шаг 2: Обновите `.env` файл

Откройте `.env` и добавьте/обновите эти строки, заменив `YOUR_API_KEY` на ваш ключ:

```env
# Основной Uniswap V3 Arbitrum Subgraph
UNISWAP_V3_SUBGRAPH_URL=https://gateway.thegraph.com/api/YOUR_API_KEY/subgraphs/id/FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oF1fxPe9aJM

# Positions Subgraph (для LP позиций)
UNISWAP_V3_POSITIONS_SUBGRAPH_URL=https://gateway.thegraph.com/api/YOUR_API_KEY/subgraphs/id/EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG
```

**Пример с ключом:**
```env
UNISWAP_V3_SUBGRAPH_URL=https://gateway.thegraph.com/api/abc123def456ghi789/subgraphs/id/FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oF1fxPe9aJM
UNISWAP_V3_POSITIONS_SUBGRAPH_URL=https://gateway.thegraph.com/api/abc123def456ghi789/subgraphs/id/EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG
```

### Шаг 3: Протестируйте настройку

```bash
# Откройте test_positions_subgraph.py и вставьте ваш API ключ
nano test_positions_subgraph.py

# Найдите строку:
API_KEY = "YOUR_API_KEY"

# Замените на:
API_KEY = "ваш_ключ_сюда"

# Сохраните (Ctrl+O, Enter, Ctrl+X) и запустите:
python test_positions_subgraph.py
```

Если увидите `✅ Успешно! Найдено X позиций` - всё работает!

### Шаг 4: Перезапустите сервер

```bash
# Остановите текущий сервер (Ctrl+C)

# Обновите код
git pull

# Перезапустите
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Шаг 5: Проверьте веб-интерфейс

1. Откройте http://localhost:8000
2. Введите адрес пула: `0xc6962004f452be9203591991d15f6b388e09e8d0`
3. Нажмите "Analyze Pool"
4. Теперь должны работать **все вкладки**:
   - ✅ Pool Overview
   - ✅ Liquidity Distribution
   - ✅ **LP Overview** (теперь с данными!)
   - ✅ **Positions** (теперь с данными!)
   - ✅ **Downloads** (CSV экспорт)

## Что изменилось в коде

### 1. Конфигурация (`app/config.py`)
- Добавлена переменная `UNISWAP_V3_POSITIONS_SUBGRAPH_URL`
- Поддержка двух отдельных subgraph URL

### 2. Клиент (`app/uniswap_client.py`)
- Конструктор принимает два URL: основной и positions
- Метод `_query()` теперь может выбирать между subgraph
- Метод `get_pool_positions()` использует positions subgraph

### 3. `.env.example`
- Обновлены примеры с правильными Subgraph ID
- Добавлены инструкции по получению API ключа

## Subgraph ID для справки

### Основной Uniswap V3 Arbitrum
- **Name**: Uniswap V3 Arbitrum
- **Network**: arbitrum-one
- **Subgraph ID**: `FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oF1fxPe9aJM`
- **Содержит**: pools, ticks, swaps, mints, burns, collects
- **Docs**: https://docs.uniswap.org/api/subgraph/overview

### Positions Uniswap V3 Arbitrum
- **Name**: Uniswap V3 User Positions Arbitrum
- **Network**: arbitrum-one
- **Subgraph ID**: `EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG`
- **Содержит**: positions (NFT позиции LP)
- **Explorer**: https://thegraph.com/explorer/subgraphs/EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG

## Troubleshooting

### Ошибка: "GraphQL errors"
- Проверьте, что API ключ правильный
- Убедитесь, что в URL нет лишних пробелов
- Проверьте, что Subgraph ID скопирован полностью

### Позиции не загружаются
- Запустите `python test_positions_subgraph.py`
- Проверьте логи сервера - должно быть: `✅ Успешно загружено X позиций`
- Убедитесь, что оба URL в `.env` правильные

### HTTP 403 Forbidden
- API ключ недействителен или отозван
- Создайте новый ключ в The Graph Studio
- Обновите `.env` с новым ключом

## Полезные ссылки

- **The Graph Studio**: https://thegraph.com/studio/
- **Uniswap Docs**: https://docs.uniswap.org/api/subgraph/overview
- **Graph Explorer**: https://thegraph.com/explorer
- **Arbitrum Docs**: https://docs.arbitrum.io/

---

**Готово!** После настройки у вас будет полнофункциональное приложение с:
- 📊 Анализом пулов
- 📈 Графиком ликвидности
- 👥 Данными по LP
- 📍 Детальными позициями
- 💾 Экспортом в CSV
