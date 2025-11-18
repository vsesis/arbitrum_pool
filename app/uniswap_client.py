"""
GraphQL клиент для работы с Uniswap v3 Subgraph на Arbitrum
"""
import requests
from typing import Dict, List, Optional
from decimal import Decimal
import logging

from .config import UNISWAP_V3_SUBGRAPH_URL, MAX_POSITIONS_PER_QUERY, MAX_TICKS_PER_QUERY
from .models import Pool, Token, Position, Tick

logger = logging.getLogger(__name__)


class UniswapV3Client:
    """Клиент для работы с Uniswap v3 subgraph"""

    def __init__(self, subgraph_url: str = UNISWAP_V3_SUBGRAPH_URL):
        self.subgraph_url = subgraph_url

    def _query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Выполняет GraphQL запрос"""
        try:
            response = requests.post(
                self.subgraph_url,
                json={"query": query, "variables": variables or {}},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                raise Exception(f"GraphQL errors: {data['errors']}")

            return data.get("data", {})
        except Exception as e:
            logger.error(f"Ошибка запроса к subgraph: {e}")
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
        """Получает все позиции в пуле"""
        query = """
        query GetPositions($poolId: String!, $skip: Int!) {
            positions(
                first: 1000
                skip: $skip
                where: { pool: $poolId }
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

        pool_id = pool_address.lower()
        positions = []
        skip = 0

        while True:
            data = self._query(query, {"poolId": pool_id, "skip": skip})
            positions_batch = data.get("positions", [])

            if not positions_batch:
                break

            for pos_data in positions_batch:
                # Пропускаем закрытые позиции (liquidity = 0)
                if int(pos_data["liquidity"]) == 0:
                    continue

                position = Position(
                    id=pos_data["id"],
                    owner=pos_data["owner"],
                    pool_address=pool_id,
                    liquidity=int(pos_data["liquidity"]),
                    tick_lower=int(pos_data["tickLower"]["tickIdx"]),
                    tick_upper=int(pos_data["tickUpper"]["tickIdx"]),
                    deposited_token0=Decimal(pos_data["depositedToken0"]),
                    deposited_token1=Decimal(pos_data["depositedToken1"]),
                    withdrawn_token0=Decimal(pos_data["withdrawnToken0"]),
                    withdrawn_token1=Decimal(pos_data["withdrawnToken1"]),
                    collected_fees_token0=Decimal(pos_data["collectedFeesToken0"]),
                    collected_fees_token1=Decimal(pos_data["collectedFeesToken1"])
                )
                positions.append(position)

            if len(positions_batch) < 1000:
                break

            skip += 1000
            logger.info(f"Загружено {len(positions)} активных позиций...")

        logger.info(f"Всего загружено {len(positions)} активных позиций для пула {pool_address}")
        return positions
