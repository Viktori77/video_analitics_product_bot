import asyncio
import json
import os
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
import logging
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import async_session, Video, VideoSnapshot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_datetime(dt_str: str):
    """Парсит строку datetime с учетом часовых поясов"""
    try:
        # Убираем Z и добавляем timezone если нужно
        if dt_str.endswith('Z'):
            dt_str = dt_str.replace('Z', '+00:00')
        
        # Парсим datetime
        dt = datetime.fromisoformat(dt_str)
        
        # Если datetime без timezone, делаем его UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        # Преобразуем в naive datetime (без timezone) для PostgreSQL
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
        
    except Exception as e:
        logger.error(f"Ошибка парсинга datetime '{dt_str}': {e}")
        raise


async def load_json_data(file_path: str):
    """Загружает данные из JSON файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Проверяем структуру данных
        if isinstance(data, dict):
            if 'videos' in data:
                data = data['videos']
            elif 'data' in data:
                data = data['data']
            else:
                data = [data]
        
        if not isinstance(data, list):
            logger.error(f"Ожидался список, получен {type(data)}")
            return []
            
        return data
        
    except FileNotFoundError:
        logger.error(f"Файл {file_path} не найден!")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON: {e}")
        return []


async def seed_videos(session, videos_data):
    """Заполняет таблицу videos"""
    inserted_count = 0
    updated_count = 0
    error_count = 0
    
    for idx, video_data in enumerate(videos_data):
        try:
            # Проверяем, что video_data - словарь
            if not isinstance(video_data, dict):
                logger.error(f"Элемент {idx} не является словарем: {type(video_data)}")
                error_count += 1
                continue
            
            video_id = video_data.get('id', f'unknown_{idx}')
            logger.info(f"Обработка видео {idx + 1}/{len(videos_data)}: {video_id}")
            
            # Проверяем обязательные поля
            required_fields = ['id', 'creator_id', 'video_created_at', 'created_at', 'updated_at']
            for field in required_fields:
                if field not in video_data:
                    logger.error(f"Видео {video_id} пропущено: отсутствует поле {field}")
                    error_count += 1
                    continue
            
            # Преобразуем строки дат с учетом часовых поясов
            try:
                video_created_at = parse_datetime(video_data['video_created_at'])
                created_at = parse_datetime(video_data['created_at'])
                updated_at = parse_datetime(video_data['updated_at'])
            except Exception as e:
                logger.error(f"Ошибка парсинга дат для видео {video_id}: {e}")
                error_count += 1
                continue
            
            # Получаем числовые значения с проверкой
            views_count = video_data.get('views_count', 0) or 0
            likes_count = video_data.get('likes_count', 0) or 0
            comments_count = video_data.get('comments_count', 0) or 0
            reports_count = video_data.get('reports_count', 0) or 0
            
            # Создаем запись видео
            video = Video(
                id=video_id,
                creator_id=video_data['creator_id'],
                video_created_at=video_created_at,
                views_count=views_count,
                likes_count=likes_count,
                comments_count=comments_count,
                reports_count=reports_count,
                created_at=created_at,
                updated_at=updated_at
            )
            
            session.add(video)
            await session.flush()
            inserted_count += 1
            
            # Создаем снимки для этого видео
            snapshots = video_data.get('snapshots', [])
            if snapshots:
                snapshots_added = await seed_snapshots_for_video(session, video, snapshots)
                if snapshots_added > 0:
                    logger.debug(f"Добавлено {snapshots_added} снимков для видео {video_id}")
            
            # Коммитим каждые 100 записей для экономии памяти
            if inserted_count % 100 == 0:
                await session.commit()
                logger.info(f"Промежуточный коммит: обработано {inserted_count} видео")
            
        except IntegrityError:
            await session.rollback()
            # Если видео уже существует, обновляем его
            try:
                await update_existing_video(session, video_data)
                updated_count += 1
            except Exception as e:
                logger.error(f"Ошибка при обновлении видео {video_id}: {e}")
                error_count += 1
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка при добавлении видео {video_id}: {e}")
            error_count += 1
    
    # Финальный коммит
    await session.commit()
    
    logger.info(f"Импорт видео завершен:")
    logger.info(f"  Добавлено: {inserted_count}")
    logger.info(f"  Обновлено: {updated_count}")
    logger.info(f"  Ошибок: {error_count}")
    
    return inserted_count, updated_count, error_count


async def update_existing_video(session, video_data):
    """Обновляет существующее видео"""
    video_id = video_data.get('id')
    
    try:
        # Преобразуем даты
        video_created_at = parse_datetime(video_data['video_created_at'])
        updated_at = parse_datetime(video_data['updated_at'])
        created_at = parse_datetime(video_data['created_at'])
        
        # Используем upsert операцию
        stmt = insert(Video).values(
            id=video_id,
            creator_id=video_data['creator_id'],
            video_created_at=video_created_at,
            views_count=video_data.get('views_count', 0) or 0,
            likes_count=video_data.get('likes_count', 0) or 0,
            comments_count=video_data.get('comments_count', 0) or 0,
            reports_count=video_data.get('reports_count', 0) or 0,
            created_at=created_at,
            updated_at=updated_at
        ).on_conflict_do_update(
            index_elements=['id'],
            set_={
                'views_count': video_data.get('views_count', 0) or 0,
                'likes_count': video_data.get('likes_count', 0) or 0,
                'comments_count': video_data.get('comments_count', 0) or 0,
                'reports_count': video_data.get('reports_count', 0) or 0,
                'updated_at': updated_at
            }
        )
        
        await session.execute(stmt)
        await session.commit()
        
        # Добавляем снимки
        video = await session.get(Video, video_id)
        snapshots = video_data.get('snapshots', [])
        if snapshots:
            await seed_snapshots_for_video(session, video, snapshots)
        
    except Exception as e:
        await session.rollback()
        raise e


async def seed_snapshots_for_video(session, video, snapshots_data):
    """Заполняет снимки для конкретного видео"""
    added_count = 0
    
    for idx, snapshot_data in enumerate(snapshots_data):
        try:
            # Проверяем обязательные поля
            required_fields = ['created_at', 'updated_at']
            for field in required_fields:
                if field not in snapshot_data:
                    logger.warning(f"Снимок {idx} для видео {video.id} пропущен: отсутствует поле {field}")
                    continue
            
            # Преобразуем даты
            created_at = parse_datetime(snapshot_data['created_at'])
            updated_at = parse_datetime(snapshot_data['updated_at'])
            
            # Получаем числовые значения
            views_count = snapshot_data.get('views_count', 0) or 0
            likes_count = snapshot_data.get('likes_count', 0) or 0
            comments_count = snapshot_data.get('comments_count', 0) or 0
            reports_count = snapshot_data.get('reports_count', 0) or 0
            delta_views_count = snapshot_data.get('delta_views_count', 0) or 0
            delta_likes_count = snapshot_data.get('delta_likes_count', 0) or 0
            delta_reports_count = snapshot_data.get('delta_reports_count', 0) or 0
            
            snapshot = VideoSnapshot(
                id=str(uuid4()),
                video_id=video.id,
                views_count=views_count,
                likes_count=likes_count,
                comments_count=comments_count,
                reports_count=reports_count,
                delta_views_count=delta_views_count,
                delta_likes_count=delta_likes_count,
                delta_reports_count=delta_reports_count,
                created_at=created_at,
                updated_at=updated_at
            )
            
            session.add(snapshot)
            added_count += 1
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении снимка {idx} для видео {video.id}: {e}")
            continue
    
    await session.flush()
    return added_count


async def clear_database(session):
    """Очищает базу данных"""
    try:
        await session.execute(VideoSnapshot.__table__.delete())
        await session.execute(Video.__table__.delete())
        await session.commit()
        logger.info("База данных очищена")
    except Exception as e:
        await session.rollback()
        logger.error(f"Ошибка при очистке базы данных: {e}")


async def count_records(session):
    """Подсчитывает количество записей в таблицах"""
    try:
        videos_count = await session.scalar(select(func.count()).select_from(Video))
        snapshots_count = await session.scalar(select(func.count()).select_from(VideoSnapshot))
        
        logger.info(f"Всего видео: {videos_count}")
        logger.info(f"Всего снимков: {snapshots_count}")
        
        return videos_count, snapshots_count
    except Exception as e:
        logger.error(f"Ошибка при подсчете записей: {e}")
        return 0, 0


async def main_db():
    """Основная функция для заполнения базы данных"""
    from decouple import config
    
    # Получаем путь из конфига или используем по умолчанию
    file_path = config('JSON_FILE_PATH', default='data/videos.json')
    
    logger.info(f"Ищем файл по пути: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"Файл {file_path} не найден!")
        
            
    logger.info(f"Загрузка данных из {file_path}...")

    videos_data = await load_json_data(file_path)
    
    if not videos_data:
        logger.info("Нет данных для импорта!")
        return
    
    logger.info(f"Найдено {len(videos_data)} элементов для импорта...")
    
    async with async_session() as session:
        # Опционально: очистить базу перед заполнением
        # await clear_database(session)
        
        # Заполняем базу данных
        inserted, updated, errors = await seed_videos(session, videos_data)
        
        # Подсчитываем общее количество записей
        videos_count, snapshots_count = await count_records(session)
        
        logger.info(f"\n=== ИТОГИ ИМПОРТА ===")
        logger.info(f"Обработано видео: {len(videos_data)}")
        logger.info(f"Успешно добавлено: {inserted}")
        logger.info(f"Обновлено: {updated}")
        logger.info(f"Ошибок: {errors}")
        logger.info(f"Итоговое количество видео в БД: {videos_count}")
        logger.info(f"Итоговое количество снимков в БД: {snapshots_count}")

if __name__ == "__main__":
    asyncio.run(main_db())