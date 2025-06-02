from typing import AsyncGenerator

import aiosqlite

from ..config import settings


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """获取数据库连接的上下文管理器"""
    # 为每个请求创建新的连接
    db = await aiosqlite.connect(settings.DATABASE_URL.replace("sqlite:///", ""))
    try:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()


async def get_standalone_db() -> aiosqlite.Connection:
    """获取一个独立（非生成器）的数据库连接，需手动关闭"""
    db = await aiosqlite.connect(settings.DATABASE_URL.replace("sqlite:///", ""))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    return db


# 初始化数据库 schema 的函数
async def init_db():
    """初始化数据库"""
    async with aiosqlite.connect(settings.DATABASE_URL.replace("sqlite:///", "")) as db:
        with open("schema.sql", encoding="utf-8") as f:
            await db.executescript(f.read())
        await db.execute("PRAGMA foreign_keys = ON")
        await db.commit()
