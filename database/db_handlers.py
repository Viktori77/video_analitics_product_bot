from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
import logging
from typing import Any, Optional


logger = logging.getLogger(__name__)

class DatabaseOperations:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url)
        self.Session = async_sessionmaker(bind=self.engine)
    
            
    async def execute_query(self, sql_query: str) -> Optional[Any]:
        """Выполнение SQL запроса и возврат результата"""
        try:
            async with self.engine.connect() as conn:
                # Убираем возможные символы конца запроса
                sql_query = sql_query.strip().rstrip(';')
                
                logger.info(f"Выполняем запрос: {sql_query}")
                result = await conn.execute(text(sql_query))
                
                # Получаем результаты
                rows = result.fetchall()
                
                if rows:
                    # Если одна строка и один столбец
                    if len(rows) == 1 and len(rows[0]) == 1:
                        
                        return rows[0][0]
                    return rows
                else:
                    # Для агрегатных функций возвращаем 0 если нет данных
                    if any(keyword in sql_query.upper() for keyword in ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN']):
                        return 0
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка выполнения SQL запроса: {e}")
            logger.error(f"Запрос: {sql_query}")
            return None