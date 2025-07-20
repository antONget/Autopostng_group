from aiogram.filters import BaseFilter
from aiogram.types import Message
from database.requests import get_list_users
from database import requests as rq
import logging


async def check_user(telegram_id: int) -> bool:
    logging.info('check_user')
    list_user = await get_list_users()
    for info_user in list_user:
        if info_user[0] == telegram_id:
            return True
    return False


async def check_role(tg_id: int, role: str) -> bool:
    """
    Проверка на роль пользователя
    :param tg_id: id пользователя телеграм
    :param role: str
    :return: true если пользователь администратор, false в противном случае
    """
    logging.info(f'check_role {tg_id} {role}')
    user = await rq.get_user(tg_id=tg_id)
    return user.role == role


class IsRoleAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return await check_role(tg_id=message.from_user.id, role=rq.UserRole.admin)


class IsRolePartner(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return await check_role(tg_id=message.from_user.id, role=rq.UserRole.partner)


class IsRoleManager(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return await check_role(tg_id=message.from_user.id, role=rq.UserRole.manager)
