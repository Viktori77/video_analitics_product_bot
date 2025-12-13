import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers import router
from database.db_handlers import DatabaseOperations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoAnalyticsBot:
    def __init__(self, token: str, db_operations: DatabaseOperations):
        # Используем MemoryStorage для хранения состояний FSM
        storage = MemoryStorage()
        
        self.bot = Bot(token=token)
        self.dp = Dispatcher(storage=storage)
        self.db_operations = db_operations

        self.dp.include_router(router)

        # Передаем db_operations в handlers
        from bot.handlers import set_db_operations

        set_db_operations(db_operations)
            
    async def on_startup(self):
        """Действия при запуске бота"""
        logger.info("Бот запущен")
        
    
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