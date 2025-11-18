"""
Конфигурация приложения
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Arbitrum One Chain ID
ARBITRUM_CHAIN_ID = 42161

# URL сабграфа Uniswap v3 для Arbitrum
# Получить актуальный URL можно из документации Uniswap:
# https://docs.uniswap.org/api/subgraph/overview
# Или The Graph: https://thegraph.com/hosted-service/subgraph/ianlapham/uniswap-arbitrum-one
UNISWAP_V3_SUBGRAPH_URL = os.getenv(
    "UNISWAP_V3_SUBGRAPH_URL",
    # Дефолтный URL - нужно заменить на актуальный из документации
    "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-arbitrum-one"
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
