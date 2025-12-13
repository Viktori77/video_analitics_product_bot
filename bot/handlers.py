from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import logging
from nlp.query_parser import parse_with_openai
from database.db_handlers import DatabaseOperations
from decouple import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

# Глобальная переменная для DatabaseOperations
db_operations = None

# Состояния для вопроса от пользователя
class Gen(StatesGroup):
    wait = State()

# Функция для установки DatabaseOperations
def set_db_operations(db_ops):
    global db_operations
    db_operations = db_ops
    logger.info("DatabaseOperations установлен в handlers")

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    welcome_text = """
        Привет! Я бот для аналитики видео.

        Я могу отвечать на вопросы на естественном языке, например:
        • Сколько всего видео есть в системе?
        • Сколько видео у креатора с id X вышло с 1 по 5 ноября 2025?
        • Сколько видео набрало больше 100000 просмотров?
        • На сколько просмотров выросли все видео 28 ноября 2025?
        • Сколько разных видео получали новые просмотры 27 ноября 2025?

        Просто задайте вопрос в чат!
        """
    

    await message.answer(welcome_text)

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = """
        Примеры вопросов:
        1. "Сколько всего видео есть в системе?"
        2. "Сколько видео у креатора с id 123 вышло с 1 ноября 2025 по 5 ноября 2025?"
        3. "Сколько видео набрало больше 100000 просмотров за всё время?"
        4. "На сколько просмотров в сумме выросли все видео 28 ноября 2025?"
        5. "Сколько разных видео получали новые просмотры 27 ноября 2025?"

        Формат дат: "28 ноября 2025", "с 1 по 5 ноября 2025"
        """
    await message.answer(help_text)

@router.message(Gen.wait)
async def stop_flood(message: Message):
    await message.answer('Подождите, ваш запрос генерируется.')

@router.message()
async def generating(message: Message, state: FSMContext):
    if db_operations is None:
        await message.answer("База данных не инициализирована. Проверьте настройки подключения.")
        return

    # Сразу отправляем сообщение о том, что запрос обрабатывается
    wait_msg = await message.answer('Подождите, ваш запрос генерируется...')

    await state.set_state(Gen.wait)
    
    if not message.text:
        await message.answer("Пожалуйста, задайте вопрос")
        await state.clear()
        return
        
    try:
        sql_query = await parse_with_openai(message.text)
        logger.info(f"Сгенерирован SQL: {sql_query}")

        if not sql_query:
            await message.answer("Не удалось сгенерировать SQL запрос")
            await state.clear()
            return

        # Выполняем запрос через экземпляр класса
        result = await db_operations.execute_query(sql_query)

        # Форматируем ответ
        if result is None:
            response = "Не удалось получить данные"
        else:
            # Извлекаем числовое значение
            if isinstance(result, (list, tuple)) and len(result) > 0:
                if isinstance(result[0], (list, tuple)) and len(result[0]) > 0:
                    value = result[0][0]
                else:
                    value = result[0]
            else:
                value = result
            
            # Преобразуем Decimal в строку
            from decimal import Decimal
            if isinstance(value, Decimal):
                # Преобразуем Decimal в int или float для форматирования
                if value % 1 == 0:
                    value = int(value)
                else:
                    value = float(value)
            
            # Форматирование числа
            try:
                if isinstance(value, (int, float)):
                    # Форматируем с разделителями тысяч
                    formatted = f"{value:,}".replace(',', ' ')
                    response = formatted
                else:
                    # Просто преобразуем в строку
                    response = str(value)
            except Exception as e:
                logger.error(f"Ошибка форматирования: {e}")
                response = str(value)
        
        # Убедимся, что response - строка
        if not isinstance(response, str):
            response = str(response)
                
        await message.answer(response)

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.answer(f"Произошла ошибка: {str(e)}")
    
    finally:
        await wait_msg.delete()
        await state.clear()



