import openai
import re
import logging



logger = logging.getLogger(__name__)

class NaturalLanguageParser:
    def __init__(self, api_key: str, model: str = "nex-agi/deepseek-v3.1-nex-n1:free"):
        openai.api_key = api_key
        self.model = model
        
    def parse_query_to_sql(self, query: str) -> str:
        """Преобразует естественноязыковый запрос в SQL"""
        try:
            # Простые преобразования для демонстрации
            simple_transforms = {
                "сколько всего видео есть в системе": "SELECT COUNT(*) FROM videos",
                "сколько всего видео": "SELECT COUNT(*) FROM videos",
                "общее количество видео": "SELECT COUNT(*) FROM videos",
            }
            
            query_lower = query.lower().strip()
            
            # Проверка простых преобразований
            for pattern, sql in simple_transforms.items():
                if pattern in query_lower:
                    return sql
            
            # Используем OpenAI для сложных запросов
            return self._parse_with_openai(query)
            
        except Exception as e:
            logger.error(f"Ошибка парсинга запроса: {e}")
            # Fallback на простые правила
            return self._parse_with_rules(query)
    
    def _parse_with_openai(self, query: str) -> str:
        """Использование OpenAI для парсинга"""
        try:
            from nlp.prompt_templates import SQL_SCHEMA
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SQL_SCHEMA},
                    {"role": "user", "content": f"Вход: {query}"}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            sql = response.choices[0].message.content.strip()
            # Убираем возможные кавычки
            sql = sql.replace('```sql', '').replace('```', '').strip()
            
            return sql
            
        except Exception as e:
            logger.error(f"Ошибка OpenAI: {e}")
            return self._parse_with_rules(query)
    
    def _parse_with_rules(self, query: str) -> str:
        """Простые правила для парсинга"""
        query_lower = query.lower()
        
        # Извлекаем даты
        date_patterns = [
            (r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(\d{4})', '%d %B %Y'),
            (r'(\d{1,2})\.(\d{1,2})\.(\d{4})', '%d.%m.%Y'),
            (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d')
        ]
        
        date_matches = []
        for pattern, _ in date_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                date_matches.extend(matches)
        
        # Определяем тип запроса
        if "сколько видео у креатора" in query_lower:
            # Извлекаем creator_id
            match = re.search(r'креатора\s+с\s+id\s+(\S+)', query_lower)
            if match:
                creator_id = match.group(1)
                if date_matches:
                    # Есть диапазон дат
                    if len(date_matches) >= 2:
                        start_date = self._parse_date(date_matches[0])
                        end_date = self._parse_date(date_matches[1])
                        return f"SELECT COUNT(*) FROM videos WHERE creator_id = '{creator_id}' AND video_created_at BETWEEN '{start_date}' AND '{end_date}'"
                return f"SELECT COUNT(*) FROM videos WHERE creator_id = '{creator_id}'"
        
        elif "сколько видео набрало больше" in query_lower:
            # Извлекаем число
            match = re.search(r'больше\s+([\d\s]+)\s+просмотров', query_lower)
            if match:
                number = match.group(1).replace(' ', '')
                return f"SELECT COUNT(*) FROM videos WHERE views_count > {number}"
        
        elif "на сколько просмотров в сумме выросли" in query_lower and date_matches:
            date = self._parse_date(date_matches[0])
            return f"SELECT SUM(delta_views_count) FROM video_snapshots WHERE DATE(created_at) = '{date}'"
        
        elif "сколько разных видео получали новые просмотры" in query_lower and date_matches:
            date = self._parse_date(date_matches[0])
            return f"SELECT COUNT(DISTINCT video_id) FROM video_snapshots WHERE DATE(created_at) = '{date}' AND delta_views_count > 0"
        
        # По умолчанию возвращаем простой запрос
        return "SELECT COUNT(*) FROM videos"
    
    def _parse_date(self, date_tuple) -> str:
        """Парсинг даты в формат YYYY-MM-DD"""
        try:
            if isinstance(date_tuple, str):
                return date_tuple
            
            if len(date_tuple) == 3:
                # Формат: (день, месяц, год)
                day, month_str, year = date_tuple
                month_map = {
                    'января': '01', 'февраля': '02', 'марта': '03',
                    'апреля': '04', 'мая': '05', 'июня': '06',
                    'июля': '07', 'августа': '08', 'сентября': '09',
                    'октября': '10', 'ноября': '11', 'декабря': '12'
                }
                
                month = month_map.get(month_str.lower(), '01')
                day = day.zfill(2)
                return f"{year}-{month}-{day}"
            
        except Exception as e:
            logger.error(f"Ошибка парсинга даты: {e}")
        
        return "2025-01-01"