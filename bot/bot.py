import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers import router

from database.db_handlers import DatabaseOperations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoAnalyticsBot:
    def __init__(self, token: str):
        # Используем MemoryStorage для хранения состояний FSM
        storage = MemoryStorage()
        
        self.bot = Bot(token=token)
        self.dp = Dispatcher(storage=storage)

        self.dp.include_router(router)
        
    
    async def on_startup(self):
        """Действия при запуске бота"""
        logger.info("Бот запущен")
        # await self.db_ops.test_connection()
    
    async def on_shutdown(self):
        """Действия при остановке бота"""
        logger.info("Бот остановлен")
        await self.bot.close()
        # Очищаем хранилище состояний
        await self.dp.storage.close()
    
    async def run(self):
        """Запуск бота"""
        await self.on_startup()
        try:
            await self.dp.start_polling(self.bot)
        finally:
            await self.on_shutdown()