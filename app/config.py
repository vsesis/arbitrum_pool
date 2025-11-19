"""
Конфигурация приложения
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Arbitrum One Chain ID
ARBITRUM_CHAIN_ID = 42161

# === Uniswap V3 Subgraphs для Arbitrum ===
#
# Uniswap V3 на Arbitrum использует ДВА отдельных subgraph:
# 1. Основной - для пулов, тиков, свопов
# 2. Positions - для NFT позиций LP
#
# Документация: https://docs.uniswap.org/api/subgraph/overview

# 1. Основной Uniswap V3 Arbitrum Subgraph
# Subgraph ID: FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oF1fxPe9aJM
# Содержит: pools, ticks, swaps, mints, burns
UNISWAP_V3_SUBGRAPH_URL = os.getenv("UNISWAP_V3_SUBGRAPH_URL")
if not UNISWAP_V3_SUBGRAPH_URL:
    raise ValueError(
        "❌ UNISWAP_V3_SUBGRAPH_URL не установлен!\n\n"
        "Создайте .env файл и добавьте:\n"
        "UNISWAP_V3_SUBGRAPH_URL=https://gateway.thegraph.com/api/YOUR_API_KEY/subgraphs/id/FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oF1fxPe9aJM\n\n"
        "Получите API ключ на https://thegraph.com/studio/\n"
        "См. .env.example для примера конфигурации"
    )

# 2. Uniswap V3 User Positions Arbitrum Subgraph
# Subgraph ID: EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG
# Содержит: positions (LP NFT позиции)
UNISWAP_V3_POSITIONS_SUBGRAPH_URL = os.getenv("UNISWAP_V3_POSITIONS_SUBGRAPH_URL")
if not UNISWAP_V3_POSITIONS_SUBGRAPH_URL:
    raise ValueError(
        "❌ UNISWAP_V3_POSITIONS_SUBGRAPH_URL не установлен!\n\n"
        "Создайте .env файл и добавьте:\n"
        "UNISWAP_V3_POSITIONS_SUBGRAPH_URL=https://gateway.thegraph.com/api/YOUR_API_KEY/subgraphs/id/EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG\n\n"
        "Получите API ключ на https://thegraph.com/studio/\n"
        "См. .env.example для примера конфигурации"
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
