import asyncio
import os
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent))

from bot.bot import VideoAnalyticsBot
from database.init_db import main_db

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
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    DB = os.getenv('DB')
    LOGIN = os.getenv('LOGIN')
    PASSWORD = os.getenv('PASSWORD')
    HOST = os.getenv('HOST')
    
    
    if not TELEGRAM_TOKEN:
        logger.error("Не задан TELEGRAM_TOKEN в переменных окружения")
        sys.exit(1)
    
    if not OPENAI_API_KEY:
        logger.error("Не задан OPENAI_API_KEY в переменных окружения")
        sys.exit(1)
        
    # Инициализация базы данных
    logger.info("Инициализация базы данных...")
    try:
        # await main_db() # потом нужно включить
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        sys.exit(1)
    
    # Запуск бота
    logger.info("Запуск Telegram бота...")
    try:
        bot = VideoAnalyticsBot(TELEGRAM_TOKEN)
        await bot.run()
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:        
        asyncio.run(main())
    except KeyboardInterrupt:
      print('Бот выключен') 