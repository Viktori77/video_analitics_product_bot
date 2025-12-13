from openai import AsyncOpenAI
import logging
from decouple import config
from nlp.prompt_templates import SQL_SCHEMA

logger = logging.getLogger(__name__)

OPENAI_API_KEY=config('OPENAI_API_KEY')

client = AsyncOpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OPENAI_API_KEY,
)

async def parse_with_openai(query: str) -> str:
        """Использование OpenAI для парсинга"""
        try:
            completion = await client.chat.completions.create(
                model="nex-agi/deepseek-v3.1-nex-n1:free",
                messages=
                    [
                            {"role": "system", "content": SQL_SCHEMA},
                            {"role": "user", "content": f"Вход: {query}"}
                        ],
            )
            sql = completion.choices[0].message.content.strip()
            # Убираем возможные кавычки
            sql = sql.replace('```sql', '').replace('```', '').strip()
            logger.info(f'sql: {sql}')
            return sql
        
        except Exception as e:
            logger.error(f"Ошибка OpenAI: {e}")


            
    
    