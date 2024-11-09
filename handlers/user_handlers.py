import logging

from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

from database import requests as rq
from keyboards import user_keyboards as kb
from config_data.config import Config, load_config
from utils.error_handling import error_handler
from filter.admin_filter import check_super_admin

config: Config = load_config()
router = Router()
router.message.filter(F.chat.type == "private")


@router.message(CommandStart())
@error_handler
async def start(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Запуск бота
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info('start')
    tg_id = message.chat.id
    await state.set_state(state=None)
    user = await rq.get_user(tg_id=tg_id)
    if not user:
        if message.from_user.username:
            username = message.from_user.username
        else:
            username = "Ник отсутствует"
        if await check_super_admin(telegram_id=tg_id):
            data = {"tg_id": tg_id, "username": username, "role": rq.UserRole.admin}
            await rq.add_user(tg_id=tg_id, data=data)
            await message.answer(text='Добро пожаловать!\n'
                                      'Вы являетесь администратором проекта',
                                 reply_markup=kb.keyboard_main_admin())
        else:
            data = {"tg_id": tg_id, "username": username, "role": rq.UserRole.user}
            await rq.add_user(tg_id=tg_id, data=data)
            await message.answer(text='Добро пожаловать!\n'
                                      'Для получения доступа к функционалу бота обратитесь к администратору'
                                      ' проекта @Aleksandr9828')
    else:
        if user.role == rq.UserRole.admin:
            await message.answer(text='Добро пожаловать!\n'
                                      'Вы являетесь администратором проекта',
                                 reply_markup=kb.keyboard_main_admin())
        elif user.role == rq.UserRole.partner:
            await message.answer(text='Добро пожаловать!\n'
                                      'Вы являетесь партнером проекта',
                                 reply_markup=kb.keyboard_main_partner())
        elif user.role == rq.UserRole.manager:
            await message.answer(text='Добро пожаловать!\n'
                                      'Вы являетесь менеджером проекта',
                                 reply_markup=kb.keyboard_main_manager())
            await message.answer(text='Выберите группу для размещение заявок',
                                 reply_markup=kb.keyboard_main_manager_inline())
        else:
            await message.answer(text='Добро пожаловать!\n'
                                      'Для получения доступа к функционалу бота обратитесь к администратору'
                                      ' проекта @Aleksandr9828')