"""
Построение графиков для визуализации данных пулов
"""
import os
import logging
from typing import List
import matplotlib
matplotlib.use('Agg')  # Используем non-GUI backend для серверной среды
import matplotlib.pyplot as plt
from decimal import Decimal

from .models import Pool, LiquidityDistribution
from .config import CHARTS_DIR, CHART_WIDTH, CHART_HEIGHT, CHART_DPI

logger = logging.getLogger(__name__)


def build_liquidity_chart(
    distribution: LiquidityDistribution,
    pool: Pool,
    filename: str
) -> str:
    """
    Строит график распределения ликвидности по ценам

    Args:
        distribution: данные распределения ликвидности
        pool: информация о пуле
        filename: имя файла для сохранения (без пути)

    Returns:
        Полный путь к сохранённому графику
    """
    if not distribution.prices or not distribution.liquidity:
        logger.warning("Нет данных для построения графика")
        return ""

    os.makedirs(CHARTS_DIR, exist_ok=True)
    filepath = os.path.join(CHARTS_DIR, filename)

    # Конвертируем Decimal в float для matplotlib
    prices = [float(p) for p in distribution.prices]
    liquidity = [float(liq) for liq in distribution.liquidity]

    # Создаём график
    fig, ax = plt.subplots(figsize=(CHART_WIDTH/100, CHART_HEIGHT/100), dpi=CHART_DPI)

    # График ликвидности
    ax.fill_between(prices, liquidity, alpha=0.5, color='blue', label='Liquidity')
    ax.plot(prices, liquidity, color='darkblue', linewidth=1)

    # Добавляем текущую цену
    current_price = float(pool.current_price)
    ax.axvline(x=current_price, color='red', linestyle='--', linewidth=2,
               label=f'Текущая цена: {current_price:.6f}')

    # Настройки осей и подписей
    ax.set_xlabel(f'Цена ({pool.token1.symbol}/{pool.token0.symbol})', fontsize=12)
    ax.set_ylabel('Ликвидность', fontsize=12)
    ax.set_title(
        f'Распределение ликвидности: {pool.token0.symbol}/{pool.token1.symbol}\n'
        f'Пул: {pool.address}\nКомиссия: {pool.fee_percentage}%',
        fontsize=14,
        pad=20
    )

    # Логарифмическая шкала по X для лучшей читаемости
    ax.set_xscale('log')
    ax.set_yscale('log')

    # Сетка
    ax.grid(True, alpha=0.3, linestyle='--')

    # Легенда
    ax.legend(fontsize=10)

    # Улучшаем отображение
    plt.tight_layout()

    # Сохраняем
    plt.savefig(filepath, dpi=CHART_DPI, bbox_inches='tight')
    plt.close(fig)

    logger.info(f"График сохранён в {filepath}")
    return filepath


def build_liquidity_chart_linear(
    distribution: LiquidityDistribution,
    pool: Pool,
    filename: str,
    price_range_percent: float = 20.0
) -> str:
    """
    Строит график распределения ликвидности в линейной шкале
    с фокусом на диапазоне вокруг текущей цены

    Args:
        distribution: данные распределения ликвидности
        pool: информация о пуле
        filename: имя файла для сохранения (без пути)
        price_range_percent: процент от текущей цены для определения диапазона

    Returns:
        Полный путь к сохранённому графику
    """
    if not distribution.prices or not distribution.liquidity:
        logger.warning("Нет данных для построения графика")
        return ""

    os.makedirs(CHARTS_DIR, exist_ok=True)
    filepath = os.path.join(CHARTS_DIR, filename)

    current_price = float(pool.current_price)
    price_min = current_price * (1 - price_range_percent / 100)
    price_max = current_price * (1 + price_range_percent / 100)

    # Фильтруем данные по диапазону
    filtered_data = [
        (float(p), float(liq))
        for p, liq in zip(distribution.prices, distribution.liquidity)
        if price_min <= float(p) <= price_max
    ]

    if not filtered_data:
        logger.warning(f"Нет данных в диапазоне ±{price_range_percent}% от текущей цены")
        # Используем все данные
        prices = [float(p) for p in distribution.prices]
        liquidity = [float(liq) for liq in distribution.liquidity]
    else:
        prices, liquidity = zip(*filtered_data)

    # Создаём график
    fig, ax = plt.subplots(figsize=(CHART_WIDTH/100, CHART_HEIGHT/100), dpi=CHART_DPI)

    # График ликвидности
    ax.fill_between(prices, liquidity, alpha=0.5, color='green', label='Liquidity')
    ax.plot(prices, liquidity, color='darkgreen', linewidth=1.5)

    # Добавляем текущую цену
    ax.axvline(x=current_price, color='red', linestyle='--', linewidth=2,
               label=f'Текущая цена: {current_price:.6f}')

    # Настройки осей и подписей
    ax.set_xlabel(f'Цена ({pool.token1.symbol}/{pool.token0.symbol})', fontsize=12)
    ax.set_ylabel('Ликвидность', fontsize=12)
    ax.set_title(
        f'Распределение ликвидности (±{price_range_percent}% от текущей цены)\n'
        f'{pool.token0.symbol}/{pool.token1.symbol} | Комиссия: {pool.fee_percentage}%',
        fontsize=14,
        pad=20
    )

    # Сетка
    ax.grid(True, alpha=0.3, linestyle='--')

    # Легенда
    ax.legend(fontsize=10)

    # Улучшаем отображение
    plt.tight_layout()

    # Сохраняем
    plt.savefig(filepath, dpi=CHART_DPI, bbox_inches='tight')
    plt.close(fig)

    logger.info(f"График (линейный) сохранён в {filepath}")
    return filepath
