"""
Конфигурация приложения
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Arbitrum One Chain ID
ARBITRUM_CHAIN_ID = 42161

# === Uniswap V3 Subgraph для Arbitrum ===
#
# Используем ТОЛЬКО основной Uniswap V3 Arbitrum subgraph для всего:
# - Пулы, тики, токены
# - События: Mint, Burn, Collect
# - Позиции строятся из событий (positions subgraph не содержит нужных данных)
#
# Документация: https://docs.uniswap.org/api/subgraph/overview

# Основной Uniswap V3 Arbitrum Subgraph
# Subgraph ID: FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oF1fxPe9aJM
# Содержит: Pool, Tick, Token, Mint, Burn, Collect, Swap
UNISWAP_V3_SUBGRAPH_URL = os.getenv(
    "UNISWAP_V3_SUBGRAPH_URL",
    # Fallback на hosted service (deprecated, может не работать)
    "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-arbitrum-one"
)

# DEPRECATED: Positions subgraph больше не используется
# Позиции теперь строятся из событий Mint/Burn/Collect основного subgraph
# Старый Subgraph ID: EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG (не содержит нужных полей)
UNISWAP_V3_POSITIONS_SUBGRAPH_URL = os.getenv(
    "UNISWAP_V3_POSITIONS_SUBGRAPH_URL",
    UNISWAP_V3_SUBGRAPH_URL  # Используем основной для обратной совместимости
)

# Arbitrum RPC endpoint (опционально для будущих улучшений)
ARBITRUM_RPC_URL = os.getenv(
    "ARBITRUM_RPC_URL",
    "https://arb1.arbitrum.io/rpc"
)

# Дефолтный пул для анализа
DEFAULT_POOL_ADDRESS = "0xc6962004f452be9203591991d15f6b388e09e8d0"

# Директории для выходных файлов
DATA_DIR = "data"
CHARTS_DIR = "charts"

# Настройки графиков
CHART_WIDTH = 1200
CHART_HEIGHT = 600
CHART_DPI = 100

# Лимиты для запросов к subgraph
MAX_POSITIONS_PER_QUERY = 1000
MAX_TICKS_PER_QUERY = 1000
