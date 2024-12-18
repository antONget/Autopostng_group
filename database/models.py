from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine


engine = create_async_engine(url="sqlite+aiosqlite:///database/db.sqlite3", echo=False)
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(Integer)
    username: Mapped[str] = mapped_column(String(20), default='none')
    role: Mapped[str] = mapped_column(String(20), default='user')


class Group(Base):
    __tablename__ = 'groups'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id_partner = mapped_column(Integer)
    group_id = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(50), default='title')


class Manager(Base):
    __tablename__ = 'managers'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id_manager = mapped_column(Integer)
    group_ids: Mapped[str] = mapped_column(String(), default='0')


class Post(Base):
    __tablename__ = 'posts'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id_manager = mapped_column(Integer)
    posts_text: Mapped[str] = mapped_column(String())
    posts_chat_message: Mapped[str] = mapped_column(String())
    post_date: Mapped[str] = mapped_column(String())


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

