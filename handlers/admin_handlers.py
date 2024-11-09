from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter

from utils.error_handling import error_handler
from database import requests as rq
from keyboards import admin_keyboards as kb
from filter.admin_filter import IsSuperAdmin
from config_data.config import Config, load_config
import logging

config: Config = load_config()
router = Router()
router.message.filter(F.chat.type == "private")


class Admin(StatesGroup):
    partner = State()


@router.message(F.text == 'Партнеры', IsSuperAdmin())
@error_handler
async def change_list_partner(message: Message, bot: Bot) -> None:
    """
    Меню правки списка партнеров
    :param message:
    :param bot:
    :return:
    """
    logging.info('change_list_partner')
    await message.answer(text='Выберите действие, которое нужно выполнить со списком партнеров',
                         reply_markup=kb.keyboard_start_menu())


@router.callback_query(F.data.startswith('partner_'))
@error_handler
async def select_change(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Изменяем список партнеров
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info('change_list_partner')
    select = callback.data.split('_')[-1]
    if select == 'add':
        list_partners = await rq.get_all_not_partner()
        await state.update_data(change_partner='add')
        if list_partners:
            await callback.message.edit_text(text='Выберите партнера для добавления или пришлите его username'
                                                  ' (например, @partner)',
                                             reply_markup=kb.keyboards_list_partner(list_partner=list_partners, block=0))
        else:
            await callback.answer(text='Нет пользователей в БД для назначения партнерами', show_alert=True)

    elif select == 'del':
        await state.update_data(change_partner='del')
        list_partners = await rq.get_all_partner()
        if list_partners:
            await callback.message.edit_text(text='Выберите партнера для удаления или пришлите его username'
                                                  ' (например, @partner)',
                                             reply_markup=kb.keyboards_list_partner(list_partner=list_partners, block=0))
        else:
            await callback.answer(text='Нет пользователей в БД для удаления из партнеров', show_alert=True)
    await callback.answer()
    await state.set_state(Admin.partner)


# Вперед
@router.callback_query(F.data.startswith('partnerforward_'))
@error_handler
async def process_forward_add_partner(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Пагинация вперед
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_forward_add_partner: {callback.message.chat.id}')
    data = await state.get_data()
    change_partner = data['change_partner']
    if change_partner == 'add':
        list_partners = await rq.get_all_not_partner()
    else:
        list_partners = await rq.get_all_partner()
    count_block = len(list_partners) // 6 + 1
    num_block = int(callback.data.split('_')[-1]) + 1
    if num_block == count_block:
        num_block = 0
    keyboard = kb.keyboards_list_partner(list_partner=list_partners, block=num_block)
    try:
        await callback.message.edit_text(text='Выберите партнера для добавления или пришлите его username'
                                              ' (например, @partner)',
                                         reply_markup=keyboard)
    except:
        await callback.message.edit_text(text='Выбeрите партнера для добавления или пришлите его username'
                                              ' (например, @partner)',
                                         reply_markup=keyboard)
    await state.set_state(Admin.partner)
    await callback.answer()


# Назад
@router.callback_query(F.data.startswith('partnerback_'))
@error_handler
async def process_forward_back_partner(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Пагинация назад
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_forward_back_partner: {callback.message.chat.id}')
    data = await state.get_data()
    change_partner = data['change_partner']
    if change_partner == 'add':
        list_partners = await rq.get_all_not_partner()
    else:
        list_partners = await rq.get_all_partner()
    count_block = len(list_partners) // 6 + 1
    num_block = int(callback.data.split('_')[-1]) - 1
    if num_block < 0:
        num_block = count_block - 1
    keyboard = kb.keyboards_list_partner(list_partner=list_partners, block=num_block)
    try:
        await callback.message.edit_text(text='Выберите партнера для добавления или пришлите его username'
                                              ' (например, @partner)',
                                         reply_markup=keyboard)
    except:
        await callback.message.edit_text(text='Выбeрите партнера для добавления или пришлите его username'
                                              ' (например, @partner)',
                                         reply_markup=keyboard)
    await state.set_state(Admin.partner)
    await callback.answer()


@router.callback_query(F.data.startswith('partnerselectadd_'))
@error_handler
async def process_select_partner(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Пагинация назад
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_forward_back_partner: {callback.message.chat.id}')
    await state.set_state(state=None)
    id_user = int(callback.data.split('_')[-1])
    data = await state.get_data()
    change_partner = data['change_partner']
    user = await rq.get_user_id(id_user=id_user)
    if change_partner == 'add':
        await rq.set_role_user(id_user=id_user, role=rq.UserRole.partner)
        await callback.message.edit_text(text=f'Партнер @{user.username} успешно добавлен',
                                         reply_markup=None)
    else:
        await rq.set_role_user(id_user=id_user, role=rq.UserRole.user)
        await callback.message.edit_text(text=f'Партнер @{user.username} успешно удален',
                                         reply_markup=None)
    await callback.answer()


@router.message(F.text, StateFilter(Admin.partner))
@error_handler
async def process_get_partner(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Пагинация назад
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_get_partner: {message.chat.id}')
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id-1)
    try:
        username_ = message.text.split('@')[-1]
        user = await rq.get_user_username(username=username_)
        if user:
            data = await state.get_data()
            change_partner = data['change_partner']
            if change_partner == 'add':
                await rq.set_role_user(id_user=user.id, role=rq.UserRole.partner)
                await message.answer(text=f'Партнер @{user.username} успешно добавлен',
                                     reply_markup=None)
                await bot.send_message(chat_id=user.tg_id,
                                       text='Администратор проекта добавил вас партнером. Перезапустите бота /start')
                await state.set_state(state=None)
            elif change_partner == 'del':
                await rq.set_role_user(id_user=user.id, role=rq.UserRole.user)
                await message.answer(text=f'Партнер @{user.username} успешно удален',
                                     reply_markup=None)
                await bot.send_message(chat_id=user.tg_id,
                                       text='Администратор проекта удалил вас из партнеров')
                await state.set_state(state=None)
        else:
            await message.answer(text='Пользователь не найден в БД проверьте введенные данные')
    except:
        await message.answer(text='Некорректные данные')
