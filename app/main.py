"""
CLI для анализа пулов Uniswap v3 на Arbitrum
"""
import argparse
import logging
import sys
from pathlib import Path

from .config import DEFAULT_POOL_ADDRESS, UNISWAP_V3_SUBGRAPH_URL
from .uniswap_client import UniswapV3Client
from .analytics import (
    calculate_liquidity_distribution,
    aggregate_positions_by_owner,
    export_positions_to_csv,
    export_lp_summary_to_csv,
    print_pool_summary,
    print_lp_summary
)
from .plots import build_liquidity_chart, build_liquidity_chart_linear


def setup_logging(verbose: bool = False):
    """Настройка логирования"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def analyze_pool(pool_address: str, verbose: bool = False):
    """
    Основная функция анализа пула

    Args:
        pool_address: адрес пула для анализа
        verbose: включить подробные логи
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    try:
        # Создаём клиент
        logger.info(f"Подключение к subgraph: {UNISWAP_V3_SUBGRAPH_URL}")
        client = UniswapV3Client()

        # 1. Получаем информацию о пуле
        logger.info(f"Получение информации о пуле {pool_address}...")
        pool = client.get_pool(pool_address)
        print_pool_summary(pool)

        # 2. Получаем тики и строим график ликвидности
        logger.info("Получение тиков пула...")
        ticks = client.get_pool_ticks(pool_address)

        if ticks:
            logger.info("Расчёт распределения ликвидности...")
            distribution = calculate_liquidity_distribution(ticks, pool)

            logger.info("Построение графика ликвидности...")
            # Логарифмический график (полный диапазон)
            chart_filename = f"{pool_address}_liquidity_log.png"
            chart_path = build_liquidity_chart(distribution, pool, chart_filename)
            if chart_path:
                print(f"✓ График (логарифмический) сохранён: {chart_path}")

            # Линейный график (фокус на текущей цене)
            chart_filename_linear = f"{pool_address}_liquidity_linear.png"
            chart_path_linear = build_liquidity_chart_linear(
                distribution, pool, chart_filename_linear, price_range_percent=20.0
            )
            if chart_path_linear:
                print(f"✓ График (линейный ±20%) сохранён: {chart_path_linear}")
        else:
            logger.warning("Тики не найдены, график не построен")

        # 3. Получаем позиции
        logger.info("Получение позиций в пуле...")
        positions = client.get_pool_positions(pool_address)

        if not positions:
            logger.warning("Позиции не найдены в пуле")
            print("\n⚠ Активных позиций в пуле не найдено")
            return

        print(f"\n✓ Найдено активных позиций: {len(positions)}")

        # 4. Экспортируем позиции в CSV
        logger.info("Экспорт позиций в CSV...")
        positions_csv = f"{pool_address}_lp_positions.csv"
        positions_path = export_positions_to_csv(positions, pool, positions_csv)
        print(f"✓ Позиции экспортированы: {positions_path}")

        # 5. Агрегируем данные по владельцам
        logger.info("Агрегация данных по LP...")
        lp_summaries = aggregate_positions_by_owner(positions)
        print(f"✓ Уникальных LP: {len(lp_summaries)}")

        # 6. Экспортируем агрегированные данные
        logger.info("Экспорт агрегированных данных по LP...")
        summary_csv = f"{pool_address}_lp_summary_by_owner.csv"
        summary_path = export_lp_summary_to_csv(lp_summaries, pool, summary_csv)
        print(f"✓ Сводка по LP экспортирована: {summary_path}")

        # 7. Выводим топ LP в консоль
        print_lp_summary(lp_summaries, pool, top_n=10)

        # Итоговая информация
        print("\n" + "="*80)
        print("АНАЛИЗ ЗАВЕРШЁН")
        print("="*80)
        print(f"Пул:                {pool.address}")
        print(f"Пара:               {pool.token0.symbol}/{pool.token1.symbol}")
        print(f"Активных позиций:   {len(positions)}")
        print(f"Уникальных LP:      {len(lp_summaries)}")
        print(f"\nВыходные файлы:")
        print(f"  • Графики:        charts/")
        if chart_path:
            print(f"    - {Path(chart_path).name}")
        if chart_path_linear:
            print(f"    - {Path(chart_path_linear).name}")
        print(f"  • Данные:         data/")
        print(f"    - {positions_csv}")
        print(f"    - {summary_csv}")
        print("="*80 + "\n")

    except Exception as e:
        logger.error(f"Ошибка при анализе пула: {e}", exc_info=verbose)
        print(f"\n❌ Ошибка: {e}")
        if not verbose:
            print("Запусти с флагом --verbose для подробной информации")
        sys.exit(1)


def main():
    """Точка входа CLI"""
    parser = argparse.ArgumentParser(
        description='Анализ пулов Uniswap v3 на Arbitrum One',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Примеры использования:

  # Анализ дефолтного пула
  python -m app.main

  # Анализ конкретного пула
  python -m app.main --pool 0xc6962004f452be9203591991d15f6b388e09e8d0

  # С подробными логами
  python -m app.main --pool 0xc6962004f452be9203591991d15f6b388e09e8d0 --verbose

Дефолтный пул для анализа: {DEFAULT_POOL_ADDRESS}

Выходные файлы:
  - charts/<pool_address>_liquidity_log.png     - график ликвидности (лог. шкала)
  - charts/<pool_address>_liquidity_linear.png  - график ликвидности (линейная)
  - data/<pool_address>_lp_positions.csv        - все позиции
  - data/<pool_address>_lp_summary_by_owner.csv - агрегация по LP
        """
    )

    parser.add_argument(
        '--pool',
        type=str,
        default=DEFAULT_POOL_ADDRESS,
        help=f'Адрес пула Uniswap v3 на Arbitrum (default: {DEFAULT_POOL_ADDRESS})'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Включить подробные логи'
    )

    args = parser.parse_args()

    # Нормализуем адрес (lowercase)
    pool_address = args.pool.lower().strip()

    # Валидация адреса
    if not pool_address.startswith('0x') or len(pool_address) != 42:
        print(f"❌ Ошибка: некорректный адрес пула: {pool_address}")
        print("   Адрес должен начинаться с '0x' и содержать 42 символа")
        sys.exit(1)

    # Запуск анализа
    analyze_pool(pool_address, args.verbose)


if __name__ == '__main__':
    main()
