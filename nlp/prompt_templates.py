SQL_SCHEMA = """
# Схема базы данных для аналитики видео

## ТАБЛИЦЫ:

1. Таблица videos (итоговая статистика по ролику):
- id (текст) — идентификатор видео
- creator_id (текст) — идентификатор креатора
- video_created_at (дата-время) — дата и время публикации видео
- views_count (число) — финальное количество просмотров
- likes_count (число) — финальное количество лайков
- comments_count (число) — финальное количество комментариев
- reports_count (число) — финальное количество жалоб
- created_at, updated_at (дата-время) — служебные поля

2. Таблица video_snapshots (почасовые замеры по ролику):
- id (текст) — идентификатор снапшота
- video_id (текст) — ссылка на видео
- views_count, likes_count, comments_count, reports_count (число) — текущие значения на момент замера
- delta_views_count, delta_likes_count, delta_comments_count, delta_reports_count (число) — приращение с прошлого замера
- created_at (дата-время) — время замера (раз в час)

## ПРАВИЛА ПРЕОБРАЗОВАНИЯ В SQL:

1. Даты:
- "28 ноября 2025" → DATE '2025-11-28'
- "с 1 по 5 ноября 2025" → BETWEEN '2025-11-01' AND '2025-11-05'
- "с 1 ноября 2025 по 5 ноября 2025 включительно" → BETWEEN '2025-11-01' AND '2025-11-05'
- "27 ноября 2025" → DATE '2025-11-27'

2. Агрегатные функции:
- "сколько всего" → COUNT(*)
- "сумма просмотров" → SUM(views_count)
- "сколько видео" → COUNT(DISTINCT video_id) или COUNT(*)
- "прирост просмотров" → SUM(delta_views_count)
- "на сколько просмотров" → SUM(delta_views_count)
- "больше 100000" → > 100000

3. Особые случаи:
- "сколько разных видео получали новые просмотры" → COUNT(DISTINCT video_id) WHERE delta_views_count > 0
- "на сколько просмотров выросли" → SUM(delta_views_count)
- "сколько видео у креатора" → COUNT(*) WHERE creator_id = '...'

ВОЗВРАЩАЙ ТОЛЬКО SQL ЗАПРОС, БЕЗ ОБЪЯСНЕНИЙ!
Примеры преобразования:
Вход: "Сколько всего видео есть в системе?" → SELECT COUNT(*) FROM videos
Вход: "Сколько видео набрало больше 100000 просмотров за всё время?" → SELECT COUNT(*) FROM videos WHERE views_count > 100000
Вход: "На сколько просмотров в сумме выросли все видео 28 ноября 2025?" → SELECT SUM(delta_views_count) FROM video_snapshots WHERE DATE(created_at) = '2025-11-28'
Вход: "Сколько разных видео получали новые просмотры 27 ноября 2025?" → SELECT COUNT(DISTINCT video_id) FROM video_snapshots WHERE DATE(created_at) = '2025-11-27' AND delta_views_count > 0
"""