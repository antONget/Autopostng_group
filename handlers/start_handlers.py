import logging

from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

from database import requests as rq
from keyboards import start_keyboards as kb
from config_data.config import Config, load_config
from utils.error_handling import error_handler
from filter.admin_filter import check_super_admin

from datetime import datetime

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
    tg_id = message.from_user.id
    await state.set_state(state=None)
    user = await rq.get_user(tg_id=tg_id)
    if not user:
        if message.from_user.username:
            username = message.from_user.username
        else:
            username = "Ник отсутствует"
        if await check_super_admin(telegram_id=tg_id):
            current_date = datetime.now()
            current_date_str = current_date.strftime('%d-%m-%Y')
            data = {"tg_id": tg_id, "username": username, "role": rq.UserRole.admin, "data_reg": current_date_str}
            await rq.add_user(tg_id=tg_id, data=data)
            await message.answer(text='Добро пожаловать!\n'
                                      'Вы являетесь администратором проекта',
                                 reply_markup=kb.keyboard_main_admin())
        else:
            current_date = datetime.now()
            current_date_str = current_date.strftime('%d-%m-%Y')
            data = {"tg_id": tg_id, "username": username, "role": rq.UserRole.user, "data_reg": current_date_str}
            await rq.add_user(tg_id=tg_id, data=data)
            await message.answer(text='Добро пожаловать!\n',
                                 reply_markup=kb.keyboard_main_manager())
            await message.answer(text='Выберите группу для размещение заявок',
                                 reply_markup=kb.keyboard_main_manager_inline())

    else:
        if user.role == rq.UserRole.admin:
            await message.answer(text='Добро пожаловать!\n'
                                      'Вы являетесь администратором проекта',
                                 reply_markup=kb.keyboard_main_admin())
        elif user.role == rq.UserRole.partner:
            await message.answer(text='Добро пожаловать!\n'
                                      'Вы являетесь партнером проекта',
                                 reply_markup=kb.keyboard_main_partner())

        else:
            await message.answer(text='Добро пожаловать!\n',
                                 reply_markup=kb.keyboard_main_manager())
            await message.answer(text='Выберите группу для размещение заявок',
                                 reply_markup=kb.keyboard_main_manager_inline())
