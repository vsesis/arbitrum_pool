"""
Аналитика и расчёты для пулов и позиций Uniswap v3
"""
import csv
import os
from typing import List, Dict
from decimal import Decimal
from collections import defaultdict
import logging

from .models import Pool, Position, LpOwnerSummary, Tick, LiquidityDistribution
from .config import DATA_DIR

logger = logging.getLogger(__name__)


def tick_to_price(tick: int, decimals0: int = 0, decimals1: int = 0) -> Decimal:
    """
    Конвертирует тик в цену (token1/token0)

    Args:
        tick: индекс тика
        decimals0: количество decimals у token0
        decimals1: количество decimals у token1

    Returns:
        Цена в формате token1/token0
    """
    # Базовая формула: price = 1.0001^tick
    price = Decimal("1.0001") ** tick

    # Корректировка на decimals
    if decimals0 != decimals1:
        decimals_adjustment = Decimal(10 ** (decimals1 - decimals0))
        price = price / decimals_adjustment

    return price


def calculate_liquidity_distribution(
    ticks: List[Tick],
    pool: Pool
) -> LiquidityDistribution:
    """
    Рассчитывает распределение ликвидности по ценам на основе тиков

    Args:
        ticks: список тиков пула
        pool: информация о пуле

    Returns:
        LiquidityDistribution с ценами и соответствующей ликвидностью
    """
    if not ticks:
        logger.warning("Нет тиков для расчёта распределения ликвидности")
        return LiquidityDistribution(prices=[], liquidity=[], ticks=[])

    # Сортируем тики по индексу
    sorted_ticks = sorted(ticks, key=lambda t: t.tick_idx)

    prices = []
    liquidity_values = []
    tick_indices = []
    current_liquidity = Decimal(0)

    for tick in sorted_ticks:
        # Пропускаем тики с нулевой ликвидностью
        if tick.liquidity_gross == 0:
            continue

        price = tick_to_price(
            tick.tick_idx,
            pool.token0.decimals,
            pool.token1.decimals
        )

        # Обновляем текущую ликвидность
        current_liquidity += Decimal(tick.liquidity_net)

        prices.append(price)
        liquidity_values.append(abs(current_liquidity))  # Берём модуль для отображения
        tick_indices.append(tick.tick_idx)

    logger.info(f"Рассчитано распределение для {len(prices)} точек")

    return LiquidityDistribution(
        prices=prices,
        liquidity=liquidity_values,
        ticks=tick_indices
    )


def aggregate_positions_by_owner(positions: List[Position]) -> Dict[str, LpOwnerSummary]:
    """
    Агрегирует позиции по владельцам (LP)

    Args:
        positions: список всех позиций

    Returns:
        Словарь {owner_address: LpOwnerSummary}
    """
    owners_data = defaultdict(lambda: {
        'positions': [],
        'deposited_token0': Decimal(0),
        'deposited_token1': Decimal(0),
        'withdrawn_token0': Decimal(0),
        'withdrawn_token1': Decimal(0),
        'fees_token0': Decimal(0),
        'fees_token1': Decimal(0),
    })

    for position in positions:
        owner = position.owner
        owners_data[owner]['positions'].append(position)
        owners_data[owner]['deposited_token0'] += position.deposited_token0
        owners_data[owner]['deposited_token1'] += position.deposited_token1
        owners_data[owner]['withdrawn_token0'] += position.withdrawn_token0
        owners_data[owner]['withdrawn_token1'] += position.withdrawn_token1
        owners_data[owner]['fees_token0'] += position.total_fees_token0
        owners_data[owner]['fees_token1'] += position.total_fees_token1

    # Создаём объекты LpOwnerSummary
    summaries = {}
    for owner, data in owners_data.items():
        summaries[owner] = LpOwnerSummary(
            owner=owner,
            positions_count=len(data['positions']),
            total_deposited_token0=data['deposited_token0'],
            total_deposited_token1=data['deposited_token1'],
            total_withdrawn_token0=data['withdrawn_token0'],
            total_withdrawn_token1=data['withdrawn_token1'],
            total_fees_token0=data['fees_token0'],
            total_fees_token1=data['fees_token1'],
            positions=data['positions']
        )

    logger.info(f"Агрегировано данные по {len(summaries)} LP")
    return summaries


def export_positions_to_csv(
    positions: List[Position],
    pool: Pool,
    filename: str
) -> str:
    """
    Экспортирует позиции в CSV файл

    Args:
        positions: список позиций
        pool: информация о пуле
        filename: имя файла (без пути)

    Returns:
        Полный путь к созданному файлу
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, filename)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Заголовки
        writer.writerow([
            'Position ID',
            'Owner',
            'Liquidity',
            'Tick Lower',
            'Tick Upper',
            'Price Lower',
            'Price Upper',
            f'Deposited {pool.token0.symbol}',
            f'Deposited {pool.token1.symbol}',
            f'Withdrawn {pool.token0.symbol}',
            f'Withdrawn {pool.token1.symbol}',
            f'Collected Fees {pool.token0.symbol}',
            f'Collected Fees {pool.token1.symbol}',
            f'Total Fees {pool.token0.symbol}',
            f'Total Fees {pool.token1.symbol}'
        ])

        # Данные
        for pos in positions:
            price_lower = tick_to_price(
                pos.tick_lower,
                pool.token0.decimals,
                pool.token1.decimals
            )
            price_upper = tick_to_price(
                pos.tick_upper,
                pool.token0.decimals,
                pool.token1.decimals
            )

            writer.writerow([
                pos.id,
                pos.owner,
                pos.liquidity,
                pos.tick_lower,
                pos.tick_upper,
                f"{price_lower:.8f}",
                f"{price_upper:.8f}",
                f"{pos.deposited_token0:.8f}",
                f"{pos.deposited_token1:.8f}",
                f"{pos.withdrawn_token0:.8f}",
                f"{pos.withdrawn_token1:.8f}",
                f"{pos.collected_fees_token0:.8f}",
                f"{pos.collected_fees_token1:.8f}",
                f"{pos.total_fees_token0:.8f}",
                f"{pos.total_fees_token1:.8f}"
            ])

    logger.info(f"Позиции экспортированы в {filepath}")
    return filepath


def export_lp_summary_to_csv(
    summaries: Dict[str, LpOwnerSummary],
    pool: Pool,
    filename: str
) -> str:
    """
    Экспортирует агрегированные данные по LP в CSV

    Args:
        summaries: словарь с агрегированными данными
        pool: информация о пуле
        filename: имя файла (без пути)

    Returns:
        Полный путь к созданному файлу
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, filename)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Заголовки
        writer.writerow([
            'Owner',
            'Positions Count',
            f'Total Deposited {pool.token0.symbol}',
            f'Total Deposited {pool.token1.symbol}',
            f'Total Withdrawn {pool.token0.symbol}',
            f'Total Withdrawn {pool.token1.symbol}',
            f'Net Deposited {pool.token0.symbol}',
            f'Net Deposited {pool.token1.symbol}',
            f'Total Fees {pool.token0.symbol}',
            f'Total Fees {pool.token1.symbol}'
        ])

        # Данные, сортируем по общей стоимости комиссий (примерная оценка)
        sorted_summaries = sorted(
            summaries.values(),
            key=lambda s: float(s.total_fees_token0 + s.total_fees_token1),
            reverse=True
        )

        for summary in sorted_summaries:
            writer.writerow([
                summary.owner,
                summary.positions_count,
                f"{summary.total_deposited_token0:.8f}",
                f"{summary.total_deposited_token1:.8f}",
                f"{summary.total_withdrawn_token0:.8f}",
                f"{summary.total_withdrawn_token1:.8f}",
                f"{summary.net_deposited_token0:.8f}",
                f"{summary.net_deposited_token1:.8f}",
                f"{summary.total_fees_token0:.8f}",
                f"{summary.total_fees_token1:.8f}"
            ])

    logger.info(f"Агрегированные данные LP экспортированы в {filepath}")
    return filepath


def print_pool_summary(pool: Pool):
    """Выводит краткую информацию о пуле в консоль"""
    print("\n" + "="*80)
    print(f"ИНФОРМАЦИЯ О ПУЛЕ: {pool.address}")
    print("="*80)
    print(f"Пара:           {pool.token0.symbol} / {pool.token1.symbol}")
    print(f"Token0:         {pool.token0.symbol} ({pool.token0.address})")
    print(f"  - Decimals:   {pool.token0.decimals}")
    print(f"Token1:         {pool.token1.symbol} ({pool.token1.address})")
    print(f"  - Decimals:   {pool.token1.decimals}")
    print(f"Комиссия:       {pool.fee_percentage}%")
    print(f"Текущая цена:   {pool.current_price:.8f} {pool.token1.symbol}/{pool.token0.symbol}")
    print(f"Текущий тик:    {pool.tick}")
    print(f"Общая ликв.:    {pool.liquidity}")
    print("="*80 + "\n")


def print_lp_summary(summaries: Dict[str, LpOwnerSummary], pool: Pool, top_n: int = 10):
    """Выводит топ LP в консоль"""
    print("\n" + "="*80)
    print(f"ТОП {top_n} ПРОВАЙДЕРОВ ЛИКВИДНОСТИ")
    print("="*80)

    # Сортируем по общим комиссиям
    sorted_summaries = sorted(
        summaries.values(),
        key=lambda s: float(s.total_fees_token0 + s.total_fees_token1),
        reverse=True
    )[:top_n]

    for i, summary in enumerate(sorted_summaries, 1):
        print(f"\n{i}. {summary.owner}")
        print(f"   Позиций:             {summary.positions_count}")
        print(f"   Депозиты:            {summary.total_deposited_token0:.4f} {pool.token0.symbol}, "
              f"{summary.total_deposited_token1:.4f} {pool.token1.symbol}")
        print(f"   Выводы:              {summary.total_withdrawn_token0:.4f} {pool.token0.symbol}, "
              f"{summary.total_withdrawn_token1:.4f} {pool.token1.symbol}")
        print(f"   Чистые депозиты:     {summary.net_deposited_token0:.4f} {pool.token0.symbol}, "
              f"{summary.net_deposited_token1:.4f} {pool.token1.symbol}")
        print(f"   Заработано комиссий: {summary.total_fees_token0:.6f} {pool.token0.symbol}, "
              f"{summary.total_fees_token1:.6f} {pool.token1.symbol}")

    print("\n" + "="*80 + "\n")
