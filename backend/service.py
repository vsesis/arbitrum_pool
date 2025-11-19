"""
Сервисный слой для кеширования и управления данными пулов
"""
import logging
from typing import Dict, Optional, Tuple
from app.uniswap_client import UniswapV3Client
from app.analytics import (
    calculate_liquidity_distribution,
    aggregate_positions_by_owner,
    get_pool_summary_data,
    get_lp_summary_data,
    get_positions_data,
    get_liquidity_chart_data
)
from app.models import Pool, Position, LpOwnerSummary, LiquidityDistribution

logger = logging.getLogger(__name__)


class PoolDataCache:
    """Кеш для данных пулов"""

    def __init__(self):
        self._pools: Dict[str, Pool] = {}
        self._positions: Dict[str, list[Position]] = {}
        self._lp_summaries: Dict[str, Dict[str, LpOwnerSummary]] = {}
        self._distributions: Dict[str, LiquidityDistribution] = {}

    def get_pool(self, pool_address: str) -> Optional[Pool]:
        return self._pools.get(pool_address.lower())

    def set_pool(self, pool_address: str, pool: Pool):
        self._pools[pool_address.lower()] = pool

    def get_positions(self, pool_address: str) -> Optional[list[Position]]:
        return self._positions.get(pool_address.lower())

    def set_positions(self, pool_address: str, positions: list[Position]):
        self._positions[pool_address.lower()] = positions

    def get_lp_summaries(self, pool_address: str) -> Optional[Dict[str, LpOwnerSummary]]:
        return self._lp_summaries.get(pool_address.lower())

    def set_lp_summaries(self, pool_address: str, summaries: Dict[str, LpOwnerSummary]):
        self._lp_summaries[pool_address.lower()] = summaries

    def get_distribution(self, pool_address: str) -> Optional[LiquidityDistribution]:
        return self._distributions.get(pool_address.lower())

    def set_distribution(self, pool_address: str, distribution: LiquidityDistribution):
        self._distributions[pool_address.lower()] = distribution


class PoolAnalysisService:
    """Сервис для анализа пулов"""

    def __init__(self):
        self.client = UniswapV3Client()
        self.cache = PoolDataCache()

    def _load_pool_data(self, pool_address: str) -> Tuple[Pool, list[Position], Dict[str, LpOwnerSummary], LiquidityDistribution]:
        """
        Загружает все данные пула из subgraph

        Returns:
            (pool, positions, lp_summaries, distribution)
        """
        pool_address = pool_address.lower()
        logger.info(f"Загрузка данных пула {pool_address}")

        # Получаем пул
        pool = self.client.get_pool(pool_address)
        self.cache.set_pool(pool_address, pool)

        # Получаем позиции
        positions = self.client.get_pool_positions(pool_address)
        self.cache.set_positions(pool_address, positions)

        # Агрегируем по владельцам
        lp_summaries = aggregate_positions_by_owner(positions)
        self.cache.set_lp_summaries(pool_address, lp_summaries)

        # Получаем тики и строим распределение
        ticks = self.client.get_pool_ticks(pool_address)
        distribution = calculate_liquidity_distribution(ticks, pool)
        self.cache.set_distribution(pool_address, distribution)

        logger.info(f"Данные пула {pool_address} загружены: {len(positions)} позиций, {len(lp_summaries)} LP")

        return pool, positions, lp_summaries, distribution

    def get_pool_summary(self, pool_address: str) -> Dict:
        """Получает краткую информацию о пуле"""
        pool_address = pool_address.lower()

        # Проверяем кеш
        pool = self.cache.get_pool(pool_address)
        if not pool:
            pool, positions, lp_summaries, _ = self._load_pool_data(pool_address)
        else:
            positions = self.cache.get_positions(pool_address) or []
            lp_summaries = self.cache.get_lp_summaries(pool_address) or {}

        summary = get_pool_summary_data(pool)
        summary["total_positions"] = len(positions)
        summary["total_lps"] = len(lp_summaries)

        return summary

    def get_liquidity_data(self, pool_address: str) -> Dict:
        """Получает данные для графика ликвидности"""
        pool_address = pool_address.lower()

        # Проверяем кеш
        pool = self.cache.get_pool(pool_address)
        distribution = self.cache.get_distribution(pool_address)

        if not pool or not distribution:
            pool, _, _, distribution = self._load_pool_data(pool_address)

        return get_liquidity_chart_data(distribution, pool)

    def get_lp_summary(
        self,
        pool_address: str,
        page: int = 1,
        page_size: int = 50,
        search: str = ""
    ) -> Dict:
        """Получает агрегированные данные по LP"""
        pool_address = pool_address.lower()

        # Проверяем кеш
        pool = self.cache.get_pool(pool_address)
        lp_summaries = self.cache.get_lp_summaries(pool_address)

        if not pool or not lp_summaries:
            pool, _, lp_summaries, _ = self._load_pool_data(pool_address)

        return get_lp_summary_data(lp_summaries, pool, page, page_size, search)

    def get_positions(
        self,
        pool_address: str,
        page: int = 1,
        page_size: int = 50,
        lp: str = ""
    ) -> Dict:
        """Получает данные по позициям"""
        pool_address = pool_address.lower()

        # Проверяем кеш
        pool = self.cache.get_pool(pool_address)
        positions = self.cache.get_positions(pool_address)

        if not pool or not positions:
            pool, positions, _, _ = self._load_pool_data(pool_address)

        return get_positions_data(positions, pool, page, page_size, lp)

    def get_csv_data(self, pool_address: str, csv_type: str) -> Tuple[str, list]:
        """
        Получает данные для CSV экспорта

        Returns:
            (filename, rows) где rows - список словарей для CSV
        """
        pool_address = pool_address.lower()

        # Проверяем кеш
        pool = self.cache.get_pool(pool_address)
        positions = self.cache.get_positions(pool_address)
        lp_summaries = self.cache.get_lp_summaries(pool_address)

        if not pool:
            pool, positions, lp_summaries, _ = self._load_pool_data(pool_address)

        if csv_type == "lp-summary":
            # Получаем все данные LP
            lp_data = get_lp_summary_data(lp_summaries, pool, page=1, page_size=100000)
            filename = f"{pool_address}_lp_summary.csv"
            rows = lp_data["data"]
        elif csv_type == "positions":
            # Получаем все позиции
            positions_data = get_positions_data(positions, pool, page=1, page_size=100000)
            filename = f"{pool_address}_positions.csv"
            rows = positions_data["data"]
        else:
            raise ValueError(f"Unknown CSV type: {csv_type}")

        return filename, rows
