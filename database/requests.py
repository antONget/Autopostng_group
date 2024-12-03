from database.models import User, Manager, Group, Post
from database.models import async_session
from sqlalchemy import select
from dataclasses import dataclass
import logging
from datetime import datetime

"""USER"""


@dataclass
class UserRole:
    user = "user"
    manager = "manager"
    partner = "partner"
    admin = "admin"


async def get_user(tg_id: int) -> User:
    logging.info(f'get_user')
    async with async_session() as session:
        return await session.scalar(select(User).where(User.tg_id == tg_id))


async def add_user(tg_id: int, data: dict) -> None:
    """
    Добавляем нового пользователя если его еще нет в БД
    :param tg_id:
    :param data:
    :return:
    """
    logging.info(f'add_user')
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        # если пользователя нет в базе
        if not user:
            session.add(User(**data))
            await session.commit()


async def get_all_users() -> list[User]:
    """
    Получаем список всех пользователей зарегистрированных в боте
    :return:
    """
    logging.info(f'get_all_users')
    async with async_session() as session:
        users = await session.scalars(select(User))
        list_users = [user for user in users if user.role != UserRole.admin]
        return list_users


async def get_list_users() -> list:
    """
    ПОЛЬЗОВАТЕЛЬ - список пользователей верифицированных в боте
    :return:
    """
    logging.info(f'get_list_users')
    async with async_session() as session:
        users = await session.scalars(select(User))
        return [[user.tg_id, user.username] for user in users]


async def get_all_partner() -> list[User]:
    """
    Получаем список всех пользователей зарегистрированных в боте
    :return:
    """
    logging.info(f'get_all_partner')
    async with async_session() as session:
        users = await session.scalars(select(User).where(User.role == UserRole.partner))
        list_not_partner = [partner for partner in users if partner.role != UserRole.admin]
        return list_not_partner


async def get_all_not_partner() -> list[User]:
    """
    Получаем список всех пользователей зарегистрированных в боте
    :return:
    """
    logging.info(f'get_all_not_partner')
    async with async_session() as session:
        users = await session.scalars(select(User).where(User.role != UserRole.partner))
        list_not_partner = [partner for partner in users if partner.role != UserRole.admin]
        return list_not_partner


async def set_role_user(id_user: int, role: str) -> None:
    """
    Обновляем роль пользователя
    :return:
    """
    logging.info(f'set_role_user')
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.id == id_user))
        if user:
            user.role = role
            await session.commit()


async def get_user_username(username: str) -> User:
    logging.info(f'get_user_username')
    async with async_session() as session:
        return await session.scalar(select(User).where(User.username == username))


async def get_user_id(id_user: int) -> User:
    logging.info(f'get_user_id')
    async with async_session() as session:
        return await session.scalar(select(User).where(User.id == id_user))


"""MANAGER"""


async def add_manager(tg_id: int, data: dict) -> None:
    """
    Добавляем нового менеджера если его еще нет в БД
    :param tg_id:
    :param data:
    :return:
    """
    logging.info(f'add_manager {tg_id} {data}')
    async with async_session() as session:
        manager = await session.scalar(select(Manager).where(Manager.tg_id_manager == tg_id))
        # если пользователя нет в базе
        if not manager:
            session.add(Manager(**data))
            await session.commit()
        else:
            groups: list = manager.group_ids.split(',')
            if not data['group_ids'] in groups:
                groups.append(data['group_ids'])
            group_ids = ','.join(groups)
            manager.group_ids = group_ids
            await session.commit()


async def add_manager_all_group(tg_id: int, data: dict) -> None:
    """
    Добавляем нового менеджера если его еще нет в БД
    :param tg_id:
    :param data:
    :return:
    """
    logging.info(f'add_manager {tg_id} {data}')
    async with async_session() as session:
        manager = await session.scalar(select(Manager).where(Manager.tg_id_manager == tg_id))
        if not manager:
            data['group_ids'] = ','.join(map(str, data['group_ids']))
            session.add(Manager(**data))
            await session.commit()
        else:
            groups: list = manager.group_ids.split(',')
            for group_id in data['group_ids']:
                if str(group_id) not in groups:
                    groups.append(str(group_id))
            group_ids = ','.join(groups)
            manager.group_ids = group_ids
            await session.commit()


async def get_all_manager() -> list[Manager]:
    """
    Получаем список всех менеджеров
    :return:
    """
    logging.info(f'get_all_manager')
    async with async_session() as session:
        managers = await session.scalars(select(Manager))
        list_manager = [manager for manager in managers]
        return list_manager


async def get_manager(tg_id_manager: int) -> Manager:
    """
    Получаем менеджера по его tg_id
    :return:
    """
    logging.info(f'get_manager')
    async with async_session() as session:
        return await session.scalar(select(Manager).where(Manager.tg_id_manager == tg_id_manager))


async def get_all_manager_partner(tg_id_partner: int) -> list[User]:
    """
    Получаем список пользователей, которые являются менеджерами у партнера
    :param tg_id_partner:
    :return:
    """
    logging.info(f'get_all_manager_partner')
    async with async_session() as session:
        list_group_partner = await get_group_partner(tg_id_partner=tg_id_partner)
        list_all_manager = await get_all_manager()
        list_manager_partner = []
        list_set = []
        for manager in list_all_manager:
            groups_manager: list = manager.group_ids.split(',')
            for group in list_group_partner:
                if str(group.id) in groups_manager:
                    user = await get_user(tg_id=manager.tg_id_manager)
                    if user.tg_id not in list_set:
                        list_set.append(user.tg_id)
                        list_manager_partner.append(user)
        return list_manager_partner


async def delete_manager(tg_id_manager: int, group_id: str):
    """
    Удаление менеджера по его tg_id
    :param tg_id_manager: id телеграм пользователя
    :param group_id:
    :return:
    """
    logging.info(f'delete_manager')
    async with async_session() as session:
        manager = await session.scalar(select(Manager).where(Manager.tg_id_manager == tg_id_manager))
        if manager:
            groups: list = manager.group_ids.split(',')
            groups.remove(group_id)
            if groups:
                group_ids = ','.join(groups)
            else:
                group_ids = '0'
            manager.group_ids = group_ids
            await session.commit()


async def delete_manager_all_group(tg_id_manager: int, group_ids: list):
    """
    Удаление менеджера по его tg_id
    :param tg_id_manager: id телеграм пользователя
    :param group_ids:
    :return:
    """
    logging.info(f'delete_manager_all_group')
    async with async_session() as session:
        manager = await session.scalar(select(Manager).where(Manager.tg_id_manager == tg_id_manager))
        if manager:
            groups: list = manager.group_ids.split(',')
            for group_id in group_ids:
                if str(group_id) in groups:
                    groups[groups.index(str(group_id))] = '0'
            groups = list(set(groups))
            print(groups)
            if groups:
                group_ids = ','.join(groups)
            else:
                group_ids = '0'
            manager.group_ids = group_ids
            await session.commit()

"""GROUP"""


async def add_group(group_id: int, data: dict) -> None:
    """
    Добавляем новую группу либо обновляем ее название
    :param group_id:
    :param data:
    :return:
    """
    logging.info(f'add_manager')
    async with async_session() as session:
        group = await session.scalar(select(Group).where(Group.group_id == group_id))
        if not group:
            session.add(Group(**data))
            await session.commit()
        else:
            group.title = data['title']
            await session.commit()


async def get_all_group() -> list[Group]:
    """
    Получаем список всех групп добавленных в БД
    :return:
    """
    logging.info(f'get_all_not_partner')
    async with async_session() as session:
        groups = await session.scalars(select(Group))
        list_group = [group for group in groups]
        return list_group


async def get_group_partner(tg_id_partner: int) -> list[Group]:
    """
    Получаем список групп партнера
    :return:
    """
    logging.info(f'get_group_partner')
    async with async_session() as session:
        groups = await session.scalars(select(Group).where(Group.tg_id_partner == tg_id_partner))
        list_groups = [group for group in groups]
        return list_groups


async def get_group_id(id_: int) -> Group:
    """
    Получаем группу
    :return:
    """
    logging.info(f'get_group_id')
    async with async_session() as session:
        return await session.scalar(select(Group).where(Group.id == id_))


async def get_group_manager_partner(tg_id_partner: int, tg_id_manager: int) -> list[Group]:
    """
    Получаем список групп менеджера в которые добавил его партнер
    :param tg_id_partner:
    :param tg_id_manager:
    :return:
    """
    logging.info(f'get_group_manager_partner')
    async with async_session() as session:
        manager = await get_manager(tg_id_manager=tg_id_manager)
        group_id_manager: list = manager.group_ids.split(',')
        groups_partner: list = await get_group_partner(tg_id_partner=tg_id_partner)
        group_manager_partner = []
        for group_id in group_id_manager:
            for group in groups_partner:
                if group_id == str(group.id):
                    group_manager_partner.append(group)
        return group_manager_partner


async def get_group_not_manager(tg_id_manager: int) -> list[Group]:
    """
    Получаем список групп менеджера в которые добавил его партнер
    :param tg_id_manager:
    :return:
    """
    logging.info(f'get_group_manager_partner')
    async with async_session() as session:
        manager = await get_manager(tg_id_manager=tg_id_manager)
        if manager:
            group_ids_manager: list = manager.group_ids.split(',')
            all_groups: list[Group] = await get_all_group()
            group_not_manager = []
            for group in all_groups:
                if str(group.id) not in group_ids_manager:
                    group_not_manager.append(group)
            return group_not_manager
        else:
            group_not_manager = []
            return group_not_manager


async def delete_group(id_: int):
    """
    Удаление группы
    :param id_: id группы
    :return:
    """
    logging.info(f'delete_user')
    async with async_session() as session:
        group = await session.scalar(select(Group).where(Group.id == id_))
        if group:
            await session.delete(group)
            await session.commit()


"""POST"""


async def add_post(data: dict) -> None:
    """
    Добавляем новый пост
    :param data:
    :return:
    """
    logging.info(f'add_post')
    async with async_session() as session:
        session.add(Post(**data))
        await session.commit()


async def get_post_manager(tg_id_manager: int) -> list[Post]:
    """
    Получаем список постов менеджера
    :param tg_id_manager:
    :return:
    """
    logging.info(f'get_post_manager')
    async with async_session() as session:
        posts = await session.scalars(select(Post).where(Post.tg_id_manager == tg_id_manager))
        date_format = '%d-%m-%Y %H:%M'
        current_date = datetime.now().strftime('%d-%m-%Y %H:%M')
        list_posts = []
        for post in posts:
            delta_time = (datetime.strptime(current_date, date_format) - datetime.strptime(post.post_date, date_format))
            if delta_time.seconds < 60*60*47:
                list_posts.append(post)
        return list_posts


async def get_post_id(id_: int) -> Post:
    """
    Получаем пост по id
    :param id_:
    :return:
    """
    logging.info(f'get_post_manager')
    async with async_session() as session:
        return await session.scalar(select(Post).where(Post.id == id_))


async def delete_post(id_: int):
    """
    Удаление поста
    :param id_: id поста
    :return:
    """
    logging.info(f'delete_user')
    async with async_session() as session:
        post = await session.scalar(select(Post).where(Post.id == id_))
        if post:
            await session.delete(post)
            await session.commit()