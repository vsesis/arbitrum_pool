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

    def _load_pool_basic_data(self, pool_address: str) -> Tuple[Pool, LiquidityDistribution]:
        """
        Загружает базовые данные пула (без позиций) из основного subgraph

        Используется для summary и liquidity endpoints, которые должны работать
        даже если positions subgraph недоступен

        Returns:
            (pool, distribution)

        Raises:
            Exception: При ошибках запроса к основному subgraph
        """
        pool_address = pool_address.lower()
        logger.info(f"Загрузка базовых данных пула {pool_address}")

        # Получаем пул из основного subgraph
        pool = self.client.get_pool_basic(pool_address)
        self.cache.set_pool(pool_address, pool)

        # Получаем тики и строим распределение
        ticks = self.client.get_pool_ticks(pool_address)
        distribution = calculate_liquidity_distribution(ticks, pool)
        self.cache.set_distribution(pool_address, distribution)

        logger.info(f"Базовые данные пула {pool_address} загружены")
        return pool, distribution

    def _load_pool_positions_data(self, pool_address: str) -> Tuple[list[Position], Dict[str, LpOwnerSummary]]:
        """
        Загружает данные по позициям из positions subgraph

        Returns:
            (positions, lp_summaries)

        Raises:
            Exception: При ошибках запроса к positions subgraph
        """
        pool_address = pool_address.lower()
        logger.info(f"Загрузка позиций для пула {pool_address}")

        # Получаем позиции из positions subgraph
        positions = self.client.get_positions_for_pool(pool_address)
        self.cache.set_positions(pool_address, positions)

        # Агрегируем по владельцам
        lp_summaries = aggregate_positions_by_owner(positions)
        self.cache.set_lp_summaries(pool_address, lp_summaries)

        logger.info(f"Загружено {len(positions)} позиций, {len(lp_summaries)} LP")
        return positions, lp_summaries

    def get_pool_summary(self, pool_address: str) -> Dict:
        """
        Получает краткую информацию о пуле

        Работает только с основным subgraph (pools, ticks).
        Если позиции уже загружены, добавляет их статистику.
        """
        pool_address = pool_address.lower()

        # Проверяем кеш
        pool = self.cache.get_pool(pool_address)
        if not pool:
            # Загружаем только базовые данные (без позиций)
            pool, _ = self._load_pool_basic_data(pool_address)

        # Получаем базовый summary
        summary = get_pool_summary_data(pool)

        # Пытаемся добавить статистику по позициям, если они уже загружены
        positions = self.cache.get_positions(pool_address)
        lp_summaries = self.cache.get_lp_summaries(pool_address)

        if positions is not None and lp_summaries is not None:
            summary["total_positions"] = len(positions)
            summary["total_lps"] = len(lp_summaries)
        else:
            # Позиции не загружены - указываем null
            summary["total_positions"] = None
            summary["total_lps"] = None
            logger.info(f"Summary для пула {pool_address} возвращен без данных по позициям")

        return summary

    def get_liquidity_data(self, pool_address: str) -> Dict:
        """
        Получает данные для графика ликвидности

        Работает только с основным subgraph (pools, ticks).
        """
        pool_address = pool_address.lower()

        # Проверяем кеш
        pool = self.cache.get_pool(pool_address)
        distribution = self.cache.get_distribution(pool_address)

        if not pool or not distribution:
            # Загружаем только базовые данные
            pool, distribution = self._load_pool_basic_data(pool_address)

        return get_liquidity_chart_data(distribution, pool)

    def get_lp_summary(
        self,
        pool_address: str,
        page: int = 1,
        page_size: int = 50,
        search: str = ""
    ) -> Dict:
        """
        Получает агрегированные данные по LP

        Требует positions subgraph.
        """
        pool_address = pool_address.lower()

        # Проверяем кеш пула
        pool = self.cache.get_pool(pool_address)
        if not pool:
            # Загружаем базовые данные пула
            try:
                pool, _ = self._load_pool_basic_data(pool_address)
            except Exception as e:
                logger.error(f"Ошибка загрузки пула: {e}")
                raise

        # Проверяем кеш позиций
        lp_summaries = self.cache.get_lp_summaries(pool_address)
        if not lp_summaries:
            # Загружаем позиции из positions subgraph
            try:
                _, lp_summaries = self._load_pool_positions_data(pool_address)
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки позиций для LP summary: {e}")
                logger.warning("Убедитесь, что UNISWAP_V3_POSITIONS_ARBITRUM_SUBGRAPH настроен правильно")
                raise Exception(
                    "Positions subgraph error. "
                    "Проверьте настройку UNISWAP_V3_POSITIONS_ARBITRUM_SUBGRAPH в .env"
                )

        return get_lp_summary_data(lp_summaries, pool, page, page_size, search)

    def get_positions(
        self,
        pool_address: str,
        page: int = 1,
        page_size: int = 50,
        lp: str = ""
    ) -> Dict:
        """
        Получает данные по позициям

        Требует positions subgraph.
        """
        pool_address = pool_address.lower()

        # Проверяем кеш пула
        pool = self.cache.get_pool(pool_address)
        if not pool:
            # Загружаем базовые данные пула
            try:
                pool, _ = self._load_pool_basic_data(pool_address)
            except Exception as e:
                logger.error(f"Ошибка загрузки пула: {e}")
                raise

        # Проверяем кеш позиций
        positions = self.cache.get_positions(pool_address)
        if not positions:
            # Загружаем позиции из positions subgraph
            try:
                positions, _ = self._load_pool_positions_data(pool_address)
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки позиций: {e}")
                logger.warning("Убедитесь, что UNISWAP_V3_POSITIONS_ARBITRUM_SUBGRAPH настроен правильно")
                raise Exception(
                    "Positions subgraph error. "
                    "Проверьте настройку UNISWAP_V3_POSITIONS_ARBITRUM_SUBGRAPH в .env"
                )

        return get_positions_data(positions, pool, page, page_size, lp)

    def get_csv_data(self, pool_address: str, csv_type: str) -> Tuple[str, list]:
        """
        Получает данные для CSV экспорта

        Требует positions subgraph.

        Returns:
            (filename, rows) где rows - список словарей для CSV
        """
        pool_address = pool_address.lower()

        # Проверяем кеш пула
        pool = self.cache.get_pool(pool_address)
        if not pool:
            try:
                pool, _ = self._load_pool_basic_data(pool_address)
            except Exception as e:
                logger.error(f"Ошибка загрузки пула: {e}")
                raise

        # Проверяем кеш позиций
        positions = self.cache.get_positions(pool_address)
        lp_summaries = self.cache.get_lp_summaries(pool_address)

        if not positions or not lp_summaries:
            try:
                positions, lp_summaries = self._load_pool_positions_data(pool_address)
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки позиций для CSV: {e}")
                raise Exception(
                    "Positions subgraph error. "
                    "Проверьте настройку UNISWAP_V3_POSITIONS_ARBITRUM_SUBGRAPH в .env"
                )

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
