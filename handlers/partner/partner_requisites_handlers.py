from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter, or_f

from utils.error_handling import error_handler
from database import requests as rq
from database.models import User
from keyboards.partner import partner_requisites_keyboards as kb
from filter.admin_filter import IsSuperAdmin
from filter.user_filter import IsRolePartner
from config_data.config import Config, load_config
import logging

config: Config = load_config()
router = Router()
router.message.filter(F.chat.type == "private")


class UserState(StatesGroup):
    requisites = State()


@router.message(F.text == 'Реквизиты', or_f(IsSuperAdmin(), IsRolePartner()))
@error_handler
async def press_button_requisites(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Добавление реквизитов
    :param message:
    :param bot:
    :param state:
    :return:
    """
    logging.info('press_button_frames')
    await state.set_state(state=None)
    info_user: User = await rq.get_user(tg_id=message.from_user.id)
    if info_user.requisites == 'none':
        await message.answer(text='Реквизиты не добавлены',
                             reply_markup=kb.keyboard_requisites_add())
    else:
        await message.answer(text=f'Ваши реквизиты, можете их обновить\n'
                                  f'{info_user.requisites}',
                             reply_markup=kb.keyboard_requisites_update())


@router.callback_query(F.data.startswith('requisites_'))
@error_handler
async def process_frame_create(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Создание нового тарифа
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info('process_frame_create')
    await callback.message.edit_text(text='Пришлите ваши реквизиты',
                                     reply_markup=None)
    await state.set_state(UserState.requisites)
    await callback.answer()


@router.message(F.text, StateFilter(UserState.requisites))
@error_handler
async def process_get_title_frame(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Получение названия тарифа
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_get_group: {message.chat.id}')
    title_requisites = message.text
    if title_requisites in ['Тарифы', 'Мои группы', 'Партнеры', 'Реквизиты']:
        await message.answer(text='Добавление реквизитов отменено')
        await state.set_state(state=None)
        return
    await rq.set_requisites(tg_id=message.from_user.id,
                            requisites=title_requisites)
    await state.set_state(state=None)
    info_user: User = await rq.get_user(tg_id=message.from_user.id)
    await message.answer(text=f'Ваши реквизиты обновлены:\n'
                              f'{info_user.requisites}')

