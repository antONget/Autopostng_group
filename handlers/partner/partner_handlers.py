from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter, or_f

from utils.error_handling import error_handler
from database import requests as rq
from database.models import User
from keyboards.partner import partner_keyboards as kb
from filter.admin_filter import IsSuperAdmin
from filter.user_filter import IsRolePartner, check_role
from config_data.config import Config, load_config
import logging

config: Config = load_config()
router = Router()
router.message.filter(F.chat.type == "private")


class Partner(StatesGroup):
    manager = State()


@router.message(F.text == 'Черный список',
                or_f(IsSuperAdmin(), IsRolePartner()))
@error_handler
async def press_button_black_list(message: Message, bot: Bot, state: FSMContext) -> None:
    """
    Меню правки черного списка
    :param message:
    :param bot:
    :param state:
    :return:
    """
    logging.info('press_button_black_list')
    await state.set_state(state=None)
    if await check_role(tg_id=message.from_user.id,
                        role=rq.UserRole.partner):
        await message.answer(text='Выберите действие для черного списка',
                             reply_markup=kb.keyboard_select_action_black_list())
    else:
        await message.answer(text='Выберите действие для черного списка',
                             reply_markup=kb.keyboard_select_action_black_list_admin())


@router.callback_query(F.data.startswith('BL_'))
@error_handler
async def select_action_black_list_admin(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Действие для черного списка
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info('select_action_black_list_admin')
    BL = int(callback.data.split('_')[-1])
    await state.update_data(BL=BL)
    await callback.message.edit_text(text='Выберите действие для черного списка',
                                     reply_markup=kb.keyboard_select_action_black_list())


@router.callback_query(F.data.startswith('selectactionblacklist_'))
@error_handler
async def select_action_black_list(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Действие для черного списка
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info('select_action_black_list')
    select = callback.data.split('_')[-1]
    await state.update_data(action_black_list=select)
    # Добавление пользователя в ЧС
    if select == 'add':
        list_users: list = await rq.get_list_user_role()
        await state.update_data(change_manager='add')
        if list_users:
            await callback.message.edit_text(text='Выберите пользователя для добавления его в <b>черный список</b>'
                                                  ' или пришлите его username (например, @manager)',
                                             reply_markup=await kb.keyboards_black_list(black_list=list_users,
                                                                                        block=0))
        else:
            await callback.answer(text='Нет пользователей в БД для добавления в черный список', show_alert=True)
    # Удаление пользователя из ЧС
    elif select == 'del':
        await state.update_data(change_manager='del')
        blacklist_partner: list = await rq.get_blacklist_partner(tg_id=callback.from_user.id)
        if blacklist_partner:
            await callback.message.edit_text(text='Выберите пользователя для удаления его из <b>черного списка</b>'
                                                  ' (например, @manager)',
                                             reply_markup=await kb.keyboards_black_list(black_list=blacklist_partner,
                                                                                        block=0))
        else:
            await callback.answer(text='Нет пользователей добавленных в черный список', show_alert=True)
    await callback.answer()
    await state.set_state(Partner.manager)


# Вперед
@router.callback_query(F.data.startswith('blacklistforward_'))
@error_handler
async def process_black_list_forward(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Пагинация вперед
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_black_list_forward: {callback.from_user.id}')
    data = await state.get_data()
    action_black_list = data['action_black_list']
    if action_black_list == 'add':
        list_managers = await rq.get_list_user_role()
    else:
        list_managers = await rq.get_blacklist_partner(tg_id=callback.from_user.id)
    count_block = len(list_managers) // 6 + 1
    num_block = int(callback.data.split('_')[-1]) + 1
    if num_block == count_block:
        num_block = 0
    keyboard = await kb.keyboards_black_list(black_list=list_managers,
                                             block=num_block)
    try:
        await callback.message.edit_text(text='Выберите пользователя для удаления его из <b>черного списка</b>'
                                              ' (например, @manager)',
                                         reply_markup=keyboard)
    except:
        await callback.message.edit_text(text='Выберитe пользователя для удаления его из <b>черного списка</b>'
                                              ' (например, @manager)',
                                         reply_markup=keyboard)
    await callback.answer()


# Назад
@router.callback_query(F.data.startswith('blacklistback_'))
@error_handler
async def process_black_list_back(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Пагинация назад
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_black_list_back: {callback.message.chat.id}')
    data = await state.get_data()
    action_black_list = data['action_black_list']
    if action_black_list == 'add':
        list_managers = await rq.get_list_user_role()
    else:
        list_managers = await rq.get_blacklist_partner(tg_id=callback.from_user.id)
    count_block = len(list_managers) // 6 + 1
    num_block = int(callback.data.split('_')[-1]) - 1
    if num_block < 0:
        num_block = count_block - 1
    keyboard = await kb.keyboards_black_list(black_list=list_managers,
                                             block=num_block)
    try:
        await callback.message.edit_text(text='Выберите пользователя для удаления его из <b>черного списка</b>'
                                              ' (например, @manager)',
                                         reply_markup=keyboard)
    except:
        await callback.message.edit_text(text='Выберитe пользователя для удаления его из <b>черного списка</b>'
                                              ' (например, @manager)',
                                         reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith('blacklistselect_'))
@error_handler
async def process_black_list_select(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Выбор пользователя
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_black_list_select: {callback.message.chat.id}')
    await state.set_state(state=None)
    id_user = int(callback.data.split('_')[-1])
    user: User = await rq.get_user_id(id_user=id_user)
    data = await state.get_data()
    action_black_list = data['action_black_list']
    # Добавление пользователя
    if action_black_list == 'add':
        if data.get('BL', 0):
            await callback.message.edit_text(text=f'Пользователь <a href="tg://user?id={user.tg_id}">{user.username}</a>'
                                                  f' добавлен в <b>черный список</b> во всех группах бота')
            await bot.send_message(chat_id=user.tg_id,
                                   text=f'Администратор <a href="tg://user?id={callback.from_user.id}">'
                                        f'@{callback.from_user.username}</a> добавил вас в <b>черный список</b>, '
                                        f'вы не можете публиковать объявления в боте')
        else:
            await callback.message.edit_text(text=f'Пользователь <a href="tg://user?id={user.tg_id}">{user.username}</a>'
                                                  f' добавлен в <b>черный список</b>')
            await bot.send_message(chat_id=user.tg_id,
                                   text=f'Партнер <a href="tg://user?id={callback.from_user.id}"> '
                                        f'{callback.from_user.username}</a> добавил вас в <b>черный список</b>, '
                                        f'вы не можете публиковать объявления в его группах')

        data_black_list = {
            "tg_id_partner": callback.from_user.id,
            "tg_id": user.tg_id,
            "ban_all": data.get('BL', 0)
        }
        await rq.add_user_black_list(data=data_black_list)

    else:
        if data.get('BL', 0):
            await callback.message.edit_text(
                text=f'Пользователь <a href="tg://user?id={user.tg_id}">{user.username}</a>'
                     f' удален из <b>черного списка</b> бота')
            await bot.send_message(chat_id=user.tg_id,
                                   text=f'Администратор <a href="tg://user?id={callback.from_user.id}"> '
                                        f'{callback.from_user.username}</a> исключил вас из <b>черного списка</b>, '
                                        f'теперь вы можете публиковать объявления во всех группах бота')
        else:
            await callback.message.edit_text(text=f'Пользователь <a href="tg://user?id={user.tg_id}">{user.username}</a>'
                                                  f' удален из <b>черного списка</b>')
            await bot.send_message(chat_id=user.tg_id,
                                   text=f'Партнер <a href="tg://user?id={callback.from_user.id}"> '
                                        f'{callback.from_user.username}</a> исключил вас из <b>черного списка</b>, '
                                        f'теперь вы можете публиковать объявления в его группах')
        await rq.del_blacklist_partner(tg_partner=callback.from_user.id,
                                       tg_user=user.tg_id,
                                       ban_all=data.get('BL', 0))
    await callback.answer()
