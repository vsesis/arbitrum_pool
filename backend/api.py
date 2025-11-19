"""
API routes для веб-приложения
"""
import io
import csv
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Response
from .service import PoolAnalysisService

router = APIRouter(prefix="/api")
service = PoolAnalysisService()


@router.get("/pool/{pool_address}/summary")
async def get_pool_summary(pool_address: str):
    """
    Получает краткую информацию о пуле

    Returns:
        JSON с основными данными: токены, цена, TVL, количество LP и позиций
    """
    try:
        return service.get_pool_summary(pool_address)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")


@router.get("/pool/{pool_address}/liquidity")
async def get_pool_liquidity(pool_address: str):
    """
    Получает данные для графика распределения ликвидности

    Returns:
        JSON с массивом точек {price, liquidity} и текущей ценой
    """
    try:
        return service.get_liquidity_data(pool_address)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")


@router.get("/pool/{pool_address}/lp-summary")
async def get_lp_summary(
    pool_address: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    search: Optional[str] = Query("", description="Поиск по адресу LP")
):
    """
    Получает агрегированные данные по LP с пагинацией

    Query параметры:
        - page: номер страницы (начиная с 1)
        - page_size: размер страницы
        - search: фильтр по адресу LP

    Returns:
        JSON с данными по LP и метаинформацией для пагинации
    """
    try:
        return service.get_lp_summary(pool_address, page, page_size, search)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")


@router.get("/pool/{pool_address}/positions")
async def get_positions(
    pool_address: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    lp: Optional[str] = Query("", description="Фильтр по адресу LP")
):
    """
    Получает данные по позициям с пагинацией

    Query параметры:
        - page: номер страницы
        - page_size: размер страницы
        - lp: фильтр по конкретному адресу LP

    Returns:
        JSON с данными по позициям и метаинформацией
    """
    try:
        return service.get_positions(pool_address, page, page_size, lp)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")


@router.get("/pool/{pool_address}/csv/{csv_type}")
async def download_csv(pool_address: str, csv_type: str):
    """
    Скачивает CSV файл с данными

    Path параметры:
        - csv_type: "lp-summary" или "positions"

    Returns:
        CSV файл
    """
    try:
        filename, rows = service.get_csv_data(pool_address, csv_type)

        if not rows:
            raise HTTPException(status_code=404, detail="No data available")

        # Создаем CSV в памяти
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        csv_content = output.getvalue()
        output.close()

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации CSV: {str(e)}")
