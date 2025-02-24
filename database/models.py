from sqlalchemy import String, Integer, BigInteger
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
    data_reg: Mapped[str] = mapped_column(String())
    requisites: Mapped[str] = mapped_column(String(), default='none')


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
    post_location: Mapped[str] = mapped_column(String())
    post_date_create: Mapped[str] = mapped_column(String())
    status: Mapped[str] = mapped_column(String())
    posts_chat_message: Mapped[str] = mapped_column(String(), default='')
    post_date_publish: Mapped[str] = mapped_column(String(), default='')
    post_autopost_1: Mapped[str] = mapped_column(String(), default='')
    post_autopost_2: Mapped[str] = mapped_column(String(), default='')
    post_autopost_3: Mapped[str] = mapped_column(String(), default='')


class Frame(Base):
    __tablename__ = 'frames'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id_creator = mapped_column(Integer)
    title_frame: Mapped[str] = mapped_column(String())
    cost_frame: Mapped[str] = mapped_column(String())
    period_frame: Mapped[str] = mapped_column(String())
    list_id_group: Mapped[str] = mapped_column(String(), default='')


class Subscribe(Base):
    __tablename__ = 'Subscribes'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger)
    frame_id: Mapped[int] = mapped_column(Integer)
    date_start: Mapped[str] = mapped_column(String)
    date_completion: Mapped[str] = mapped_column(String)
    group_id_list: Mapped[str] = mapped_column(String)


class BlackList(Base):
    __tablename__ = 'black_list'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id_partner: Mapped[int] = mapped_column(BigInteger)
    tg_id: Mapped[int] = mapped_column(BigInteger)
    ban_all: Mapped[int] = mapped_column(Integer)


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

