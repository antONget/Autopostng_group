import asyncio

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter
from aiogram.enums.chat_member_status import ChatMemberStatus

from utils.error_handling import error_handler
# from utils.scheduler_task import scheduler_task_cron
from filter.user_filter import check_role
from database import requests as rq
from keyboards.user import user_posting_keyboards as kb
from config_data.config import Config, load_config
from database.models import User, Frame, Group, Subscribe, Post
from handlers.user.scheduler_post import publish_post
import validators
import re
import logging
from datetime import datetime


config: Config = load_config()
router = Router()
router.message.filter(F.chat.type != "private")


class ManagerState(StatesGroup):
    text_post = State()
    location = State()
    check_pay = State()
    auto_post_1 = State()
    auto_post_2 = State()
    auto_post_3 = State()


@router.message()
@error_handler
async def action_in_group(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Менеджер выбирает группу
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info('action_in_group')
    subscribes: list[Subscribe] = await rq.get_subscribes_user(tg_id=message.from_user.id)
    active_subscribe = False
    list_active_subscribe = []
    if subscribes:
        for subscribe in subscribes:
            date_format = '%d-%m-%Y %H:%M'
            current_date = datetime.now().strftime('%d-%m-%Y %H:%M')
            delta_time = (datetime.strptime(subscribe.date_completion, date_format) -
                          datetime.strptime(current_date, date_format))
            if delta_time.days >= 0:
                active_subscribe = True
                list_active_subscribe.append(subscribe)

    if not active_subscribe:
        await message.delete()
        msg = await message.answer(text='Публикация поста в группе возможна только после оплаты подписки')
        await asyncio.sleep(5)
        await msg.delete()
    else:
        info_group: Group = await rq.get_group_peer_id(peer_id=message.chat.id)
        check_group_id: int = info_group.id
        group_list = []
        for active in list_active_subscribe:
            group_list.extend(item for item in active.group_id_list.split(',') if item)
        print(f'{check_group_id}/{message.chat.id}, {list(map(int, group_list))}')
        if check_group_id in list(map(int, group_list)):
            await message.answer(text='Ты можешь писать в группе')
        else:
            await message.delete()
            msg = await message.answer(text='Публикация поста в возможна только после оплаты подписки')
            await asyncio.sleep(5)
            await msg.delete()
