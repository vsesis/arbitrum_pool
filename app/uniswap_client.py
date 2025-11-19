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
        Получает все позиции в пуле из событий Mint, Burn, Collect

        ВАЖНО: Positions subgraph на Arbitrum не содержит детальных данных о позициях.
        Вместо этого мы агрегируем события из основного Uniswap V3 subgraph:
        - Mint: добавление ликвидности (depositedToken0/1)
        - Burn: удаление ликвидности (withdrawnToken0/1)
        - Collect: сбор комиссий (collectedFeesToken0/1)

        Позиции идентифицируются по (owner, tickLower, tickUpper).
        """
        pool_id = pool_address.lower()

        try:
            logger.info(f"Получение позиций для пула {pool_address} из событий Mint/Burn/Collect...")

            # Загружаем все события
            mints = self._get_pool_mints(pool_id)
            burns = self._get_pool_burns(pool_id)
            collects = self._get_pool_collects(pool_id)

            logger.info(f"Загружено событий: Mint={len(mints)}, Burn={len(burns)}, Collect={len(collects)}")

            # Агрегируем события в позиции
            positions = self._aggregate_events_to_positions(pool_id, mints, burns, collects)

            logger.info(f"✅ Успешно построено {len(positions)} позиций для пула {pool_address}")
            return positions

        except Exception as e:
            logger.error(f"❌ Ошибка при получении позиций из событий: {str(e)[:200]}")
            logger.info("Приложение продолжит работу без данных по позициям (Pool Overview и график доступны)")
            import traceback
            logger.debug(traceback.format_exc())

            return []

    def _get_pool_mints(self, pool_id: str) -> list:
        """Получает все события Mint для пула"""
        query = """
        query GetMints($poolId: String!, $skip: Int!) {
            mints(
                first: 1000
                skip: $skip
                where: { pool: $poolId }
                orderBy: timestamp
                orderDirection: desc
            ) {
                id
                owner
                tickLower
                tickUpper
                amount0
                amount1
                timestamp
            }
        }
        """

        events = []
        skip = 0

        while True:
            data = self._query(query, {"poolId": pool_id, "skip": skip})
            batch = data.get("mints", [])

            if not batch:
                break

            events.extend(batch)

            if len(batch) < 1000:
                break

            skip += 1000

        return events

    def _get_pool_burns(self, pool_id: str) -> list:
        """Получает все события Burn для пула"""
        query = """
        query GetBurns($poolId: String!, $skip: Int!) {
            burns(
                first: 1000
                skip: $skip
                where: { pool: $poolId }
                orderBy: timestamp
                orderDirection: desc
            ) {
                id
                owner
                tickLower
                tickUpper
                amount0
                amount1
                timestamp
            }
        }
        """

        events = []
        skip = 0

        while True:
            data = self._query(query, {"poolId": pool_id, "skip": skip})
            batch = data.get("burns", [])

            if not batch:
                break

            events.extend(batch)

            if len(batch) < 1000:
                break

            skip += 1000

        return events

    def _get_pool_collects(self, pool_id: str) -> list:
        """Получает все события Collect для пула"""
        query = """
        query GetCollects($poolId: String!, $skip: Int!) {
            collects(
                first: 1000
                skip: $skip
                where: { pool: $poolId }
                orderBy: timestamp
                orderDirection: desc
            ) {
                id
                owner
                tickLower
                tickUpper
                amount0
                amount1
                timestamp
            }
        }
        """

        events = []
        skip = 0

        while True:
            data = self._query(query, {"poolId": pool_id, "skip": skip})
            batch = data.get("collects", [])

            if not batch:
                break

            events.extend(batch)

            if len(batch) < 1000:
                break

            skip += 1000

        return events

    def _aggregate_events_to_positions(
        self,
        pool_id: str,
        mints: list,
        burns: list,
        collects: list
    ) -> List[Position]:
        """
        Агрегирует события Mint/Burn/Collect в позиции LP

        Группирует события по (owner, tickLower, tickUpper) и суммирует:
        - Mint → depositedToken0/1
        - Burn → withdrawnToken0/1
        - Collect → collectedFeesToken0/1
        """
        from collections import defaultdict

        # Структура: {(owner, tickLower, tickUpper): {...}}
        positions_dict = defaultdict(lambda: {
            "deposited_token0": Decimal(0),
            "deposited_token1": Decimal(0),
            "withdrawn_token0": Decimal(0),
            "withdrawn_token1": Decimal(0),
            "collected_fees_token0": Decimal(0),
            "collected_fees_token1": Decimal(0),
        })

        # Агрегируем Mint события (deposited)
        for mint in mints:
            owner = mint.get("owner", "").lower()
            tick_lower = int(mint.get("tickLower", 0))
            tick_upper = int(mint.get("tickUpper", 0))
            key = (owner, tick_lower, tick_upper)

            positions_dict[key]["deposited_token0"] += Decimal(str(mint.get("amount0", "0")))
            positions_dict[key]["deposited_token1"] += Decimal(str(mint.get("amount1", "0")))

        # Агрегируем Burn события (withdrawn)
        for burn in burns:
            owner = burn.get("owner", "").lower()
            tick_lower = int(burn.get("tickLower", 0))
            tick_upper = int(burn.get("tickUpper", 0))
            key = (owner, tick_lower, tick_upper)

            positions_dict[key]["withdrawn_token0"] += Decimal(str(burn.get("amount0", "0")))
            positions_dict[key]["withdrawn_token1"] += Decimal(str(burn.get("amount1", "0")))

        # Агрегируем Collect события (fees)
        for collect in collects:
            owner = collect.get("owner", "").lower()
            tick_lower = int(collect.get("tickLower", 0))
            tick_upper = int(collect.get("tickUpper", 0))
            key = (owner, tick_lower, tick_upper)

            positions_dict[key]["collected_fees_token0"] += Decimal(str(collect.get("amount0", "0")))
            positions_dict[key]["collected_fees_token1"] += Decimal(str(collect.get("amount1", "0")))

        # Конвертируем в объекты Position
        positions = []
        for (owner, tick_lower, tick_upper), data in positions_dict.items():
            # Фильтруем позиции без активности
            if (data["deposited_token0"] == 0 and data["deposited_token1"] == 0 and
                data["withdrawn_token0"] == 0 and data["withdrawn_token1"] == 0):
                continue

            # Вычисляем текущую ликвидность (deposited - withdrawn)
            net_token0 = data["deposited_token0"] - data["withdrawn_token0"]
            net_token1 = data["deposited_token1"] - data["withdrawn_token1"]

            # Упрощенный расчет ликвидности (можно улучшить)
            # Для точного расчета нужна формула Uniswap v3
            liquidity = 0
            if net_token0 > 0 or net_token1 > 0:
                # Примерная ликвидность (среднее геометрическое)
                liquidity = int(float(net_token0 * net_token1) ** 0.5 * 1e18) if net_token0 > 0 and net_token1 > 0 else int(max(float(net_token0), float(net_token1)) * 1e18)

            position = Position(
                id=f"{owner}#{tick_lower}#{tick_upper}",
                owner=owner,
                pool_address=pool_id,
                liquidity=liquidity,
                tick_lower=tick_lower,
                tick_upper=tick_upper,
                deposited_token0=data["deposited_token0"],
                deposited_token1=data["deposited_token1"],
                withdrawn_token0=data["withdrawn_token0"],
                withdrawn_token1=data["withdrawn_token1"],
                collected_fees_token0=data["collected_fees_token0"],
                collected_fees_token1=data["collected_fees_token1"]
            )
            positions.append(position)

        # Сортируем по ликвидности (от большей к меньшей)
        positions.sort(key=lambda p: p.liquidity, reverse=True)

        return positions
