"""SQLAlchemy 数据库引擎与会话工厂。

从 config 的 DATABASE_URL 创建 PostgreSQL 引擎。
提供 SessionLocal 用于请求级会话。
Base 是所有 ORM 模型的声明式基类。
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
