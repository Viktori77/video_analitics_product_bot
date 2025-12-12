from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile, ReplyKeyboardRemove, ContentType, BufferedInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

# Состояния для вопроса от пользователя
class MessageUser(StatesGroup):
    wait_message_user = State()

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

def register_handlers(dp, bot_instance):
    """Регистрация всех обработчиков"""
    
    # Сохраняем bot_instance в данных диспетчера
    dp['bot_instance'] = bot_instance
    
    @router.message()
    async def handle_text_message(message: Message, state: FSMContext):
        """Обработчик текстовых сообщений"""
        try:
            # Получаем bot_instance из данных диспетчера
            bot_instance = dp['bot_instance']
            
            user_query = message.text.strip()
            logger.info(f"Получен запрос: {user_query}")
            
            if not user_query:
                await message.answer("Пожалуйста, задайте вопрос")
                return
            
            # Показываем индикатор "печатает"
            await bot_instance.bot.send_chat_action(
                chat_id=message.chat.id,
                action="typing"
            )
            
            # Парсим запрос в SQL
            sql_query = bot_instance.nlp_parser.parse_query_to_sql(user_query)
            logger.info(f"Сгенерирован SQL: {sql_query}")
            
            # Выполняем запрос
            result = await bot_instance.db_ops.execute_query(sql_query)
            
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
                
                # Форматирование числа
                try:
                    if isinstance(value, (int, float)):
                        response = f"📊 Результат: {value:,}".replace(',', ' ')
                    else:
                        response = f"📊 Результат: {value}"
                except:
                    response = f"📊 Результат: {value}"
            
            await message.answer(response)
            
        except Exception as e:
            logger.error(f"Ошибка обработки запроса: {e}", exc_info=True)
            await message.answer("Произошла ошибка при обработке запроса. Попробуйте переформулировать вопрос.")
    
    # Включаем роутер в диспетчер
    dp.include_router(router)


