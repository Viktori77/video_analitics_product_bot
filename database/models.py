
from sqlalchemy import Column, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from decouple import config
import datetime
import asyncio


LOGIN=config('LOGIN')
PASSWORD=config('PASSWORD')
HOST=config('HOST')
DB=config('DB')

# Создаём асинхронный движок для PostgreSQL
engine = create_async_engine(url=f'postgresql+asyncpg://{LOGIN}:{PASSWORD}@{HOST}:5432/{DB}')

async_session=async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
  pass


class Video(Base):
    __tablename__ = 'videos'
    
    id = Column(String, primary_key=True)
    creator_id = Column(String, nullable=False, index=True)
    video_created_at = Column(DateTime, nullable=False)
    views_count = Column(BigInteger, default=0)
    likes_count = Column(BigInteger, default=0)
    comments_count = Column(BigInteger, default=0)
    reports_count = Column(BigInteger, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    snapshots = relationship("VideoSnapshot", back_populates="video", cascade="all, delete-orphan")

class VideoSnapshot(Base):
    __tablename__ = 'video_snapshots'
    
    id = Column(String, primary_key=True)
    video_id = Column(String, ForeignKey('videos.id'), nullable=False, index=True)
    views_count = Column(BigInteger, default=0)
    likes_count = Column(BigInteger, default=0)
    comments_count = Column(BigInteger, default=0)
    reports_count = Column(BigInteger, default=0)
    delta_views_count = Column(BigInteger, default=0)
    delta_likes_count = Column(BigInteger, default=0)
    delta_reports_count = Column(BigInteger, default=0)
    created_at = Column(DateTime, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    video = relationship("Video", back_populates="snapshots")

async def async_main():
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all) 
  print("Таблицы успешно созданы!")

if __name__ == "__main__":
    asyncio.run(async_main())