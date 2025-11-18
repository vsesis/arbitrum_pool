"""
Модели данных для Uniswap v3
"""
from dataclasses import dataclass, field
from typing import Optional, List
from decimal import Decimal


@dataclass
class Token:
    """Информация о токене"""
    address: str
    symbol: str
    decimals: int
    name: Optional[str] = None

    def normalize_amount(self, amount: int) -> Decimal:
        """Конвертирует сумму из raw в человекочитаемый формат"""
        return Decimal(amount) / Decimal(10 ** self.decimals)


@dataclass
class Pool:
    """Информация о пуле Uniswap v3"""
    address: str
    token0: Token
    token1: Token
    fee_tier: int  # в базисных пунктах (например, 3000 = 0.3%)
    sqrt_price_x96: int
    liquidity: int
    tick: int

    @property
    def current_price(self) -> Decimal:
        """Текущая цена (token1/token0) из sqrtPriceX96"""
        # sqrtPriceX96 = sqrt(price) * 2^96
        # price = (sqrtPriceX96 / 2^96)^2
        sqrt_price = Decimal(self.sqrt_price_x96) / Decimal(2 ** 96)
        price = sqrt_price ** 2
        # Учитываем decimals токенов
        decimals_adjustment = Decimal(10 ** (self.token1.decimals - self.token0.decimals))
        return price / decimals_adjustment

    @property
    def fee_percentage(self) -> Decimal:
        """Комиссия пула в процентах"""
        return Decimal(self.fee_tier) / Decimal(10000)


@dataclass
class Tick:
    """Информация о тике"""
    tick_idx: int
    liquidity_gross: int
    liquidity_net: int

    def to_price(self, token0_decimals: int, token1_decimals: int) -> Decimal:
        """Конвертирует тик в цену"""
        # price = 1.0001^tick
        price = Decimal("1.0001") ** self.tick_idx
        # Учитываем decimals
        decimals_adjustment = Decimal(10 ** (token1_decimals - token0_decimals))
        return price / decimals_adjustment


@dataclass
class Position:
    """NFT позиция в пуле"""
    id: str
    owner: str
    pool_address: str
    liquidity: int
    tick_lower: int
    tick_upper: int
    deposited_token0: Decimal
    deposited_token1: Decimal
    withdrawn_token0: Decimal
    withdrawn_token1: Decimal
    collected_fees_token0: Decimal
    collected_fees_token1: Decimal
    # Текущие несобранные комиссии (если доступны из subgraph)
    uncollected_fees_token0: Optional[Decimal] = None
    uncollected_fees_token1: Optional[Decimal] = None

    @property
    def price_lower(self) -> Decimal:
        """Нижняя граница цены из tickLower"""
        return Decimal("1.0001") ** self.tick_lower

    @property
    def price_upper(self) -> Decimal:
        """Верхняя граница цены из tickUpper"""
        return Decimal("1.0001") ** self.tick_upper

    @property
    def total_fees_token0(self) -> Decimal:
        """Общая прибыль по token0 (собранные + несобранные)"""
        uncollected = self.uncollected_fees_token0 or Decimal(0)
        return self.collected_fees_token0 + uncollected

    @property
    def total_fees_token1(self) -> Decimal:
        """Общая прибыль по token1 (собранные + несобранные)"""
        uncollected = self.uncollected_fees_token1 or Decimal(0)
        return self.collected_fees_token1 + uncollected


@dataclass
class LpOwnerSummary:
    """Агрегированная информация по LP (owner)"""
    owner: str
    positions_count: int
    total_deposited_token0: Decimal
    total_deposited_token1: Decimal
    total_withdrawn_token0: Decimal
    total_withdrawn_token1: Decimal
    total_fees_token0: Decimal
    total_fees_token1: Decimal
    positions: List[Position] = field(default_factory=list)

    @property
    def net_deposited_token0(self) -> Decimal:
        """Чистые депозиты token0 (депозиты - выводы)"""
        return self.total_deposited_token0 - self.total_withdrawn_token0

    @property
    def net_deposited_token1(self) -> Decimal:
        """Чистые депозиты token1 (депозиты - выводы)"""
        return self.total_deposited_token1 - self.total_withdrawn_token1


@dataclass
class LiquidityDistribution:
    """Распределение ликвидности по ценам"""
    prices: List[Decimal]
    liquidity: List[Decimal]
    ticks: List[int]
