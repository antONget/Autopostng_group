from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter, or_f

from utils.error_handling import error_handler
from database import requests as rq
from keyboards import partner_keyboards as kb
from filter.admin_filter import IsSuperAdmin
from filter.user_filter import IsRolePartner
from config_data.config import Config, load_config
import logging

config: Config = load_config()
router = Router()
router.message.filter(F.chat.type == "private")


class Partner(StatesGroup):
    manager = State()


@router.message(F.text == 'Менеджеры', or_f(IsSuperAdmin(), IsRolePartner()))
@error_handler
async def change_list_manager(message: Message, bot: Bot) -> None:
    """
    Меню правки списка менеджеров
    :param message:
    :param bot:
    :return:
    """
    logging.info('change_list_manager')
    await message.answer(text='Выберите действие, которое нужно выполнить со списком менеджеров',
                         reply_markup=kb.keyboard_change_list_manager())


@router.callback_query(F.data.startswith('manager_'))
@error_handler
async def select_change_manager(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Изменяем список менеджер
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info('select_change_manager')
    select = callback.data.split('_')[-1]
    # Добавление менеджера
    if select == 'add':
        list_manager: list = await rq.get_all_users()
        await state.update_data(change_manager='add')
        if list_manager:
            await callback.message.edit_text(text='Выберите пользователя для добавления его менеджером или пришлите'
                                                  ' его username (например, @manager)',
                                             reply_markup=kb.keyboards_list_manager(list_manager=list_manager, block=0))
        else:
            await callback.answer(text='Нет пользователей в БД для назначения менеджерами', show_alert=True)
    # Удаление менеджера
    elif select == 'del':
        await state.update_data(change_manager='del')
        list_managers: list = await rq.get_all_manager_partner(tg_id_partner=callback.message.chat.id)
        if list_managers:
            await callback.message.edit_text(text='Выберите менеджера для удаления или пришлите его username'
                                                  ' (например, @manager)',
                                             reply_markup=kb.keyboards_list_manager(list_manager=list_managers,
                                                                                    block=0))
        else:
            await callback.answer(text='Нет пользователей в БД для удаления из менеджеров', show_alert=True)
    await callback.answer()
    await state.set_state(Partner.manager)


# Вперед
@router.callback_query(F.data.startswith('managerforward_'))
@error_handler
async def process_forward_manager(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Пагинация вперед
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_forward_manager: {callback.message.chat.id}')
    data = await state.get_data()
    change_manager = data['change_manager']
    if change_manager == 'add':
        list_managers = await rq.get_all_users()
    else:
        list_managers = await rq.get_all_manager_partner(tg_id_partner=callback.message.chat.id)
    count_block = len(list_managers) // 6 + 1
    num_block = int(callback.data.split('_')[-1]) + 1
    if num_block == count_block:
        num_block = 0
    keyboard = kb.keyboards_list_manager(list_manager=list_managers, block=num_block)
    try:
        await callback.message.edit_text(text='Выберите пользователя или пришлите его username'
                                              ' (например, @manager)',
                                         reply_markup=keyboard)
    except:
        await callback.message.edit_text(text='Выбeрите пользователя или пришлите его username'
                                              ' (например, @manager)',
                                         reply_markup=keyboard)
    await state.set_state(Partner.manager)
    await callback.answer()


# Назад
@router.callback_query(F.data.startswith('managerback_'))
@error_handler
async def process_forward_back_manager(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Пагинация назад
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_forward_back_manager: {callback.message.chat.id}')
    data = await state.get_data()
    change_manager = data['change_manager']
    if change_manager == 'add':
        list_managers = await rq.get_all_users()
    else:
        list_managers = await rq.get_all_manager_partner(tg_id_partner=callback.message.chat.id)
    count_block = len(list_managers) // 6 + 1
    num_block = int(callback.data.split('_')[-1]) - 1
    if num_block < 0:
        num_block = count_block - 1
    keyboard = kb.keyboards_list_manager(list_manager=list_managers, block=num_block)
    try:
        await callback.message.edit_text(text='Выберите пользователя или пришлите его username'
                                              ' (например, @manager)',
                                         reply_markup=keyboard)
    except:
        await callback.message.edit_text(text='Выбeрите пользователя или пришлите его username'
                                              ' (например, @manager)',
                                         reply_markup=keyboard)
    await state.set_state(Partner.manager)
    await callback.answer()


@router.callback_query(F.data.startswith('managerselect_'))
@error_handler
async def process_select_manager(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Выбор менеджера
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_select_manager: {callback.message.chat.id}')
    await state.set_state(state=None)
    id_user = int(callback.data.split('_')[-1])
    user = await rq.get_user_id(id_user=id_user)
    await state.update_data(manager_tg_id=user.tg_id)
    # manager = await rq.get_manager(tg_id_manager=user.tg_id)
    data = await state.get_data()
    change_manager = data['change_manager']
    # Добавление менеджера
    if change_manager == 'add':
        partner = await rq.get_user(tg_id=callback.message.chat.id)
        if user.id == partner.id:
            await callback.answer(text='Вы можете публиковать посты в своих группах', show_alert=True)
            return
        list_groups: list = await rq.get_group_partner(tg_id_partner=callback.message.chat.id)
        if list_groups:
            await callback.message.edit_text(text='Выберите группу для добавления менеджера',
                                             reply_markup=await kb.keyboards_list_group(list_group=list_groups,
                                                                                        block=0,
                                                                                        change_manager='add',
                                                                                        bot=bot))
        else:
            await callback.answer(text='Группы в БД не найдены', show_alert=True)
    else:
        list_groups = await rq.get_group_manager_partner(tg_id_manager=user.tg_id,
                                                         tg_id_partner=callback.message.chat.id)
        if list_groups:
            await callback.message.edit_text(text='Выберите группу для удаления менеджера',
                                             reply_markup=await kb.keyboards_list_group(list_group=list_groups,
                                                                                        block=0,
                                                                                        change_manager='del',
                                                                                        bot=bot))
        else:
            await callback.answer(text='Группы в БД не найдены', show_alert=True)
    await callback.answer()


@router.message(F.text, StateFilter(Partner.manager))
@error_handler
async def process_get_manager(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Добавление/удаление менеджера по username
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_get_manager: {message.chat.id}')
    try:
        username = message.text.split('@')[-1]
        user = await rq.get_user_username(username=username)
        if user:
            data = await state.get_data()
            change_manager = data['change_manager']
            await state.update_data(manager_tg_id=user.tg_id)
            if change_manager == 'add':
                list_groups: list = await rq.get_group_partner(tg_id_partner=message.chat.id)
                if list_groups:
                    await message.edit_text(text='Выберите группу для добавления менеджера',
                                            reply_markup=await kb.keyboards_list_group(list_group=list_groups,
                                                                                       block=0,
                                                                                       change_manager='add',
                                                                                       bot=bot))
                else:
                    await message.answer(text='Группы в БД не найдены')
                await state.set_state(state=None)
            elif change_manager == 'del':
                list_groups = await rq.get_group_manager_partner(tg_id_manager=user.tg_id,
                                                                 tg_id_partner=message.chat.id)
                if list_groups:
                    await message.edit_text(text='Выберите группу для удаления менеджера',
                                            reply_markup=await kb.keyboards_list_group(list_group=list_groups,
                                                                                       block=0,
                                                                                       change_manager='del',
                                                                                       bot=bot))
                else:
                    await message.answer(text='Группы в БД не найдены')
                await state.set_state(state=None)
        else:
            await message.answer(text='Пользователь не найден в БД проверьте введенные данные')
    except:
        await message.answer(text='Некорректные данные')


# Вперед
@router.callback_query(F.data.startswith('groupforward_'))
@error_handler
async def process_forward_group(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Пагинация вперед
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_forward_group: {callback.message.chat.id}')
    data = await state.get_data()
    change_manager = data['change_manager']
    if change_manager == 'add':
        list_groups: list = await rq.get_group_partner(tg_id_partner=callback.message.chat.id)
    else:
        list_groups: list = await rq.get_all_group()
    count_block = len(list_groups) // 6 + 1
    num_block = int(callback.data.split('_')[-1]) + 1
    if num_block == count_block:
        num_block = 0
    keyboard = await kb.keyboards_list_group(list_group=list_groups,
                                             block=num_block,
                                             change_manager='del',
                                             bot=bot)
    try:
        await callback.message.edit_text(text='Выберите группу для удаления менеджера',
                                         reply_markup=keyboard)
    except:
        await callback.message.edit_text(text='Выбeритe группу для удаления менеджера',
                                         reply_markup=keyboard)
    await callback.answer()


# Назад
@router.callback_query(F.data.startswith('groupback_'))
@error_handler
async def process_forward_back_manager(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Пагинация назад
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_forward_back_manager: {callback.message.chat.id}')
    data = await state.get_data()
    change_manager = data['change_manager']
    if change_manager == 'add':
        list_groups: list = await rq.get_group_partner(tg_id_partner=callback.message.chat.id)
    else:
        list_groups: list = await rq.get_all_group()
    count_block = len(list_groups) // 6 + 1
    num_block = int(callback.data.split('_')[-1]) - 1
    if num_block < 0:
        num_block = count_block - 1
    keyboard = await kb.keyboards_list_group(list_group=list_groups,
                                             block=num_block,
                                             change_manager='del',
                                             bot=bot)
    try:
        await callback.message.edit_text(text='Выберите группу для удаления менеджера',
                                         reply_markup=keyboard)
    except:
        await callback.message.edit_text(text='Выбeритe группу для удаления менеджера',
                                         reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith('groupselect_'))
@error_handler
async def process_select_group(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Выбор группы для добавления мнеджера
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_select_group: {callback.message.chat.id}')
    # получаем id группы
    group_id: str = callback.data.split('_')[-1]
    data = await state.get_data()
    manager_tg_id = data['manager_tg_id']
    data = await state.get_data()
    change_manager = data['change_manager']
    user = await rq.get_user(tg_id=manager_tg_id)
    group = await rq.get_group_id(id_=int(group_id))
    # Добавляем менеджера в группу
    if change_manager == 'add':
        if not user.role == rq.UserRole.partner:
            await rq.set_role_user(id_user=user.id, role=rq.UserRole.manager)
        data_ = {"tg_id_manager": user.tg_id, 'group_ids': group_id}
        await rq.add_manager(tg_id=user.tg_id, data=data_)
        await callback.message.edit_text(text=f'Менеджер @{user.username} успешно добавлен в группу {group.title}',
                                         reply_markup=None)
        try:
            await bot.send_message(chat_id=user.tg_id,
                                   text=f'Партнер {callback.from_user.username} добавил вас менеджером в группу {group.title}'
                                        f'Перезапуститe бота /start при необходимости')
        except:
            pass
    else:
        await rq.delete_manager(tg_id_manager=user.tg_id, group_id=group_id)
        await callback.message.edit_text(text=f'Менеджер @{user.username} успешно удален из группы {group.title}',
                                         reply_markup=None)
        try:
            await bot.send_message(chat_id=user.tg_id,
                                   text=f'Партнер {callback.from_user.username} удалил вас из группы {group.title} как менеджера')
        except:
            pass
    await callback.answer()


@router.callback_query(F.data.startswith('groupall'))
@error_handler
async def process_select_group(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """

    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_select_group: {callback.message.chat.id}')
    data = await state.get_data()
    change_manager = data['change_manager']
    manager_tg_id = data['manager_tg_id']
    user = await rq.get_user(tg_id=manager_tg_id)
    if change_manager == 'add':
        if not user.role == rq.UserRole.partner:
            await rq.set_role_user(id_user=user.id, role=rq.UserRole.manager)
        groups_partner = await rq.get_group_partner(tg_id_partner=callback.message.chat.id)
        list_group_id_partner = [group.id for group in groups_partner]
        data_ = {"tg_id_manager": user.tg_id, 'group_ids': list_group_id_partner}
        await rq.add_manager_all_group(tg_id=user.tg_id, data=data_)
        await callback.message.edit_text(text=f'Менеджер @{user.username} успешно добавлен во все ваши группы',
                                         reply_markup=None)
        try:
            await bot.send_message(chat_id=user.tg_id,
                                   text=f'Партнер {callback.from_user.username} добавил вас менеджером во все свои группы. '
                                        f'Перезапуститe бота /start при необходимости')
        except:
            pass
    else:
        groups_partner = await rq.get_group_partner(tg_id_partner=callback.message.chat.id)
        list_group_id_partner = [group.id for group in groups_partner]
        await rq.delete_manager_all_group(tg_id_manager=user.tg_id, group_ids=list_group_id_partner)
        await callback.message.edit_text(text=f'Менеджер @{user.username} успешно удален из всех ваших группы',
                                         reply_markup=None)
        try:
            await bot.send_message(chat_id=user.tg_id,
                                   text=f'Партнер {callback.from_user.username} удалил вас как менеджера из всех своих групп. '
                                        f'Перезапуститe бота /start при необходимости')
        except:
            pass
    await callback.answer()
