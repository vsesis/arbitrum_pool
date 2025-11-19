"""
GraphQL клиент для работы с Uniswap v3 Subgraph на Arbitrum
"""
import requests
from typing import Dict, List, Optional
from decimal import Decimal
import logging

from .config import (
    UNISWAP_V3_ARBITRUM_SUBGRAPH,
    UNISWAP_V3_POSITIONS_ARBITRUM_SUBGRAPH,
    MAX_POSITIONS_PER_QUERY,
    MAX_TICKS_PER_QUERY
)
from .models import Pool, Token, Position, Tick

logger = logging.getLogger(__name__)


class UniswapV3Client:
    """
    Клиент для работы с Uniswap v3 subgraph на Arbitrum

    Использует два отдельных subgraph:
    - Основной (UNISWAP_V3_ARBITRUM_SUBGRAPH): pools, ticks, swaps, liquidity
    - Positions (UNISWAP_V3_POSITIONS_ARBITRUM_SUBGRAPH): LP NFT позиции
    """

    def __init__(
        self,
        subgraph_url: str = UNISWAP_V3_ARBITRUM_SUBGRAPH,
        positions_subgraph_url: str = UNISWAP_V3_POSITIONS_ARBITRUM_SUBGRAPH
    ):
        self.subgraph_url = subgraph_url
        self.positions_subgraph_url = positions_subgraph_url

        logger.info(f"Инициализация клиента:")
        logger.info(f"  Основной subgraph: {subgraph_url[:80]}...")
        logger.info(f"  Positions subgraph: {positions_subgraph_url[:80]}...")

    def _graphql_query(self, url: str, query: str, variables: Optional[Dict] = None) -> Dict:
        """
        Вспомогательный метод для выполнения GraphQL запросов с обработкой ошибок

        Args:
            url: URL subgraph endpoint
            query: GraphQL запрос
            variables: Переменные для запроса

        Returns:
            Dict с данными ответа

        Raises:
            Exception: При ошибках сети или GraphQL
        """
        try:
            response = requests.post(
                url,
                json={"query": query, "variables": variables or {}},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                error_messages = [err.get("message", str(err)) for err in data["errors"]]
                raise Exception(f"GraphQL errors: {', '.join(error_messages)}")

            return data.get("data", {})

        except requests.exceptions.Timeout:
            logger.error(f"Timeout при запросе к {url[:60]}...")
            raise Exception(f"Timeout при запросе к subgraph")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при запросе к {url[:60]}...: {e}")
            raise Exception(f"Ошибка подключения к subgraph: {str(e)}")
        except Exception as e:
            logger.error(f"Ошибка запроса к {url[:60]}...: {e}")
            raise

    def get_pool_basic(self, pool_address: str) -> Pool:
        """
        Получает базовую информацию о пуле из основного Uniswap V3 Arbitrum subgraph

        Args:
            pool_address: Адрес пула

        Returns:
            Pool объект с данными:
            - id, token0, token1
            - feeTier, sqrtPrice, liquidity, tick
            - totalValueLockedToken0, totalValueLockedToken1

        Raises:
            ValueError: Если пул не найден
            Exception: При ошибках запроса
        """
        query = """
        query GetPool($poolId: ID!) {
            pool(id: $poolId) {
                id
                feeTier
                liquidity
                sqrtPrice
                tick
                token0 {
                    id
                    symbol
                    decimals
                    name
                }
                token1 {
                    id
                    symbol
                    decimals
                    name
                }
                totalValueLockedToken0
                totalValueLockedToken1
            }
        }
        """

        pool_id = pool_address.lower()
        data = self._graphql_query(self.subgraph_url, query, {"poolId": pool_id})

        if not data.get("pool"):
            raise ValueError(f"Пул {pool_address} не найден в subgraph")

        pool_data = data["pool"]

        token0 = Token(
            address=pool_data["token0"]["id"],
            symbol=pool_data["token0"]["symbol"],
            decimals=int(pool_data["token0"]["decimals"]),
            name=pool_data["token0"].get("name")
        )

        token1 = Token(
            address=pool_data["token1"]["id"],
            symbol=pool_data["token1"]["symbol"],
            decimals=int(pool_data["token1"]["decimals"]),
            name=pool_data["token1"].get("name")
        )

        return Pool(
            address=pool_data["id"],
            token0=token0,
            token1=token1,
            fee_tier=int(pool_data["feeTier"]),
            sqrt_price_x96=int(pool_data["sqrtPrice"]),
            liquidity=int(pool_data["liquidity"]),
            tick=int(pool_data["tick"])
        )

    def get_pool_ticks(self, pool_address: str, first: int = 1000, skip: int = 0) -> List[Tick]:
        """
        Получает тики пула из основного Uniswap V3 Arbitrum subgraph

        Используется для построения графика распределения ликвидности

        Args:
            pool_address: Адрес пула
            first: Максимальное количество тиков за один запрос (default: 1000)
            skip: Сколько тиков пропустить (для пагинации)

        Returns:
            Список Tick объектов с tickIdx, liquidityGross, liquidityNet

        Raises:
            Exception: При ошибках запроса
        """
        query = """
        query GetTicks($poolId: String!, $skip: Int!) {
            ticks(
                first: 1000
                skip: $skip
                where: { poolAddress: $poolId }
                orderBy: tickIdx
                orderDirection: asc
            ) {
                tickIdx
                liquidityGross
                liquidityNet
            }
        }
        """

        pool_id = pool_address.lower()
        ticks = []
        current_skip = 0

        while True:
            data = self._graphql_query(self.subgraph_url, query, {"poolId": pool_id, "skip": current_skip})
            ticks_batch = data.get("ticks", [])

            if not ticks_batch:
                break

            for tick_data in ticks_batch:
                tick = Tick(
                    tick_idx=int(tick_data["tickIdx"]),
                    liquidity_gross=int(tick_data["liquidityGross"]),
                    liquidity_net=int(tick_data["liquidityNet"])
                )
                ticks.append(tick)

            if len(ticks_batch) < 1000:
                break

            current_skip += 1000
            logger.info(f"Загружено {len(ticks)} тиков...")

        logger.info(f"Всего загружено {len(ticks)} тиков для пула {pool_address}")
        return ticks

    def get_positions_for_pool(self, pool_address: str, first: int = 1000, skip: int = 0) -> List[Position]:
        """
        Получает LP позиции для пула из Uniswap V3 User Positions Arbitrum subgraph

        ВАЖНО: Использует ОТДЕЛЬНЫЙ subgraph для позиций!
        Subgraph ID: EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG

        Args:
            pool_address: Адрес пула
            first: Максимальное количество позиций за один запрос (default: 1000)
            skip: Сколько позиций пропустить (для пагинации)

        Returns:
            Список Position объектов с полями:
            - id, owner, liquidity
            - tickLower, tickUpper
            - depositedToken0, depositedToken1
            - withdrawnToken0, withdrawnToken1
            - collectedFeesToken0, collectedFeesToken1

        Raises:
            Exception: При ошибках запроса к positions subgraph
        """
        pool_id = pool_address.lower()
        positions = []

        # Запрос к positions subgraph
        query = """
        query GetPositions($poolId: String!, $skip: Int!) {
            positions(
                first: 1000
                skip: $skip
                where: { pool: $poolId, liquidity_gt: "0" }
                orderBy: liquidity
                orderDirection: desc
            ) {
                id
                owner
                liquidity
                tickLower {
                    tickIdx
                }
                tickUpper {
                    tickIdx
                }
                depositedToken0
                depositedToken1
                withdrawnToken0
                withdrawnToken1
                collectedFeesToken0
                collectedFeesToken1
            }
        }
        """

        try:
            logger.info(f"Получение позиций для пула {pool_address} из positions subgraph...")
            current_skip = 0

            while True:
                # Используем positions subgraph
                data = self._graphql_query(
                    self.positions_subgraph_url,
                    query,
                    {"poolId": pool_id, "skip": current_skip}
                )
                positions_batch = data.get("positions", [])

                if not positions_batch:
                    break

                for pos_data in positions_batch:
                    position = Position(
                        id=pos_data["id"],
                        owner=pos_data["owner"],
                        pool_address=pool_id,
                        liquidity=int(pos_data["liquidity"]),
                        tick_lower=int(pos_data["tickLower"]["tickIdx"]),
                        tick_upper=int(pos_data["tickUpper"]["tickIdx"]),
                        deposited_token0=Decimal(pos_data.get("depositedToken0", "0")),
                        deposited_token1=Decimal(pos_data.get("depositedToken1", "0")),
                        withdrawn_token0=Decimal(pos_data.get("withdrawnToken0", "0")),
                        withdrawn_token1=Decimal(pos_data.get("withdrawnToken1", "0")),
                        collected_fees_token0=Decimal(pos_data.get("collectedFeesToken0", "0")),
                        collected_fees_token1=Decimal(pos_data.get("collectedFeesToken1", "0"))
                    )
                    positions.append(position)

                if len(positions_batch) < 1000:
                    break

                current_skip += 1000
                logger.info(f"Загружено {len(positions)} позиций...")

            logger.info(f"✅ Успешно загружено {len(positions)} позиций для пула {pool_address}")
            return positions

        except Exception as e:
            logger.error(f"❌ Ошибка при получении позиций из positions subgraph: {str(e)[:200]}")
            logger.warning("Проверьте настройку UNISWAP_V3_POSITIONS_ARBITRUM_SUBGRAPH в .env файле")
            logger.info("Positions subgraph должен содержать Subgraph ID: EKfnW8Ss1MMNhb8psVRsotcXmeweLgBtKQBG6wayPLBG")
            logger.info("Приложение продолжит работу без данных по позициям (Pool Overview и график доступны)")
            raise

    # Алиасы для обратной совместимости
    def get_pool(self, pool_address: str) -> Pool:
        """Алиас для get_pool_basic() (обратная совместимость)"""
        return self.get_pool_basic(pool_address)

    def get_pool_positions(self, pool_address: str) -> List[Position]:
        """Алиас для get_positions_for_pool() (обратная совместимость)"""
        return self.get_positions_for_pool(pool_address)
