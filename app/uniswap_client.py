"""
GraphQL клиент для работы с Uniswap v3 Subgraph на Arbitrum
"""
import requests
from typing import Dict, List, Optional
from decimal import Decimal
import logging

from .config import (
    UNISWAP_V3_SUBGRAPH_URL,
    UNISWAP_V3_POSITIONS_SUBGRAPH_URL,
    MAX_POSITIONS_PER_QUERY,
    MAX_TICKS_PER_QUERY
)
from .models import Pool, Token, Position, Tick

logger = logging.getLogger(__name__)


class UniswapV3Client:
    """
    Клиент для работы с Uniswap v3 subgraph на Arbitrum

    Использует два отдельных subgraph:
    - Основной: pools, ticks, swaps, etc.
    - Positions: LP NFT позиции
    """

    def __init__(
        self,
        subgraph_url: str = UNISWAP_V3_SUBGRAPH_URL,
        positions_subgraph_url: str = UNISWAP_V3_POSITIONS_SUBGRAPH_URL
    ):
        self.subgraph_url = subgraph_url
        self.positions_subgraph_url = positions_subgraph_url

        logger.info(f"Инициализация клиента:")
        logger.info(f"  Основной subgraph: {subgraph_url[:80]}...")
        logger.info(f"  Positions subgraph: {positions_subgraph_url[:80]}...")

    def _query(self, query: str, variables: Optional[Dict] = None, use_positions_subgraph: bool = False) -> Dict:
        """
        Выполняет GraphQL запрос

        Args:
            query: GraphQL запрос
            variables: Переменные для запроса
            use_positions_subgraph: Использовать positions subgraph вместо основного

        Returns:
            Dict с данными ответа
        """
        url = self.positions_subgraph_url if use_positions_subgraph else self.subgraph_url

        try:
            response = requests.post(
                url,
                json={"query": query, "variables": variables or {}},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                raise Exception(f"GraphQL errors: {data['errors']}")

            return data.get("data", {})
        except Exception as e:
            logger.error(f"Ошибка запроса к subgraph ({url[:60]}...): {e}")
            raise

    def get_pool(self, pool_address: str) -> Pool:
        """Получает информацию о пуле"""
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
            }
        }
        """

        pool_id = pool_address.lower()
        data = self._query(query, {"poolId": pool_id})

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

    def get_pool_ticks(self, pool_address: str) -> List[Tick]:
        """Получает все тики пула для построения графика ликвидности"""
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
        skip = 0

        while True:
            data = self._query(query, {"poolId": pool_id, "skip": skip})
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

            skip += 1000
            logger.info(f"Загружено {len(ticks)} тиков...")

        logger.info(f"Всего загружено {len(ticks)} тиков для пула {pool_address}")
        return ticks

    def get_pool_positions(self, pool_address: str) -> List[Position]:
        """
        Получает все позиции в пуле из positions subgraph

        ВАЖНО: Официальные Uniswap V3 subgraphs на Arbitrum не предоставляют
        детальные данные о позициях через The Graph Gateway API.

        Возвращает пустой список если данные недоступны.
        Приложение продолжит работу с ограниченным функционалом:
        - Pool Overview ✅
        - График ликвидности ✅
        - LP данные ❌ (недоступны)
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
            logger.info(f"Получение позиций для пула {pool_address}...")
            skip = 0

            while True:
                # Используем positions subgraph
                data = self._query(query, {"poolId": pool_id, "skip": skip}, use_positions_subgraph=True)
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

                skip += 1000
                logger.info(f"Загружено {len(positions)} позиций...")

            if positions:
                logger.info(f"✅ Успешно загружено {len(positions)} позиций для пула {pool_address}")
            else:
                logger.warning("⚠️  LP данные недоступны")
                logger.info("Причина: Официальные Uniswap V3 subgraphs на Arbitrum не содержат детальных данных о позициях")
                logger.info("Доступный функционал: Pool Overview и график ликвидности")

            return positions

        except Exception as e:
            error_msg = str(e)
            logger.warning(f"⚠️  Не удалось загрузить LP данные: {error_msg[:150]}")

            # Более понятные сообщения для типичных ошибок
            if "has no field" in error_msg:
                logger.info("ℹ️  Subgraph имеет несовместимую схему (отсутствуют необходимые поля)")
            elif "removed" in error_msg.lower():
                logger.info("ℹ️  Используемый API endpoint был удален")

            logger.info("ℹ️  Приложение продолжит работу с ограниченным функционалом")
            logger.info("   ✅ Pool Overview")
            logger.info("   ✅ График ликвидности")
            logger.info("   ❌ LP данные (позиции, владельцы)")

            return []
