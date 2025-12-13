import asyncio
import os
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv
from decouple import config


# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent))

from bot.bot import VideoAnalyticsBot
from database.init_db import main_db
from database.db_handlers import DatabaseOperations

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска"""
    # Загрузка переменных окружения
    load_dotenv()
    
    # Получение конфигурации
    TELEGRAM_TOKEN = config('TELEGRAM_TOKEN')
    OPENAI_API_KEY = config('OPENAI_API_KEY')
    DB = config('DB')
    LOGIN = config('LOGIN')
    PASSWORD = config('PASSWORD')
    HOST = config('HOST')
    
    if not TELEGRAM_TOKEN:
        logger.error("Не задан TELEGRAM_TOKEN в переменных окружения")
        sys.exit(1)
    
    if not OPENAI_API_KEY:
        logger.error("Не задан OPENAI_API_KEY в переменных окружения")
        sys.exit(1)
    
    # Создаем URL базы данных
    DB_URL = f'postgresql+asyncpg://{LOGIN}:{PASSWORD}@{HOST}:5432/{DB}'
    
    
    # Инициализация базы данных
    logger.info("Инициализация базы данных...")
    try:
        await main_db() # потом нужно включить
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        sys.exit(1)
    
    # Создаем экземпляр DatabaseOperations
    db_operations = DatabaseOperations(DB_URL)
    
    # Запуск бота
    logger.info("Запуск Telegram бота...")
    try:
        bot = VideoAnalyticsBot(TELEGRAM_TOKEN, db_operations)
        await bot.run()
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:        
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Бот выключен')