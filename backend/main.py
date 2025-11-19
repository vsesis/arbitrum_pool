"""
FastAPI приложение для анализа пулов Uniswap v3
"""
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from .api import router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Создаем приложение
app = FastAPI(
    title="Uniswap v3 Pool Analytics",
    description="API для анализа пулов Uniswap v3 на Arbitrum",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем API роуты
app.include_router(router)

# Статические файлы
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Главная страница - отдаем HTML"""
    return FileResponse(str(static_dir / "index.html"))


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "uniswap-v3-pool-analytics"}
