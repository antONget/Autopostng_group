from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter, or_f
from aiogram.enums.chat_member_status import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from utils.error_handling import error_handler
from database import requests as rq
from keyboards import partner_group_keyboards as kb
from filter.admin_filter import IsSuperAdmin
from filter.user_filter import IsRolePartner
from config_data.config import Config, load_config
import logging

config: Config = load_config()
router = Router()
router.message.filter(F.chat.type == "private")


class Partner(StatesGroup):
    group_id = State()
    group_title = State()


@router.message(F.text == 'Мои группы', or_f(IsSuperAdmin(), IsRolePartner()))
@error_handler
async def change_list_my_groups(message: Message, bot: Bot) -> None:
    """
    Меню правки списка менеджеров
    :param message:
    :param bot:
    :return:
    """
    logging.info('change_list_my_groups')
    await message.answer(text='Выберите действие, которое нужно выполнить со списком групп',
                         reply_markup=kb.keyboard_change_list_group())


@router.callback_query(F.data.startswith('group_'))
@error_handler
async def select_change_group(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Изменяем список групп
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info('select_change_group')
    select = callback.data.split('_')[-1]
    if select == 'add':
        await callback.message.edit_text(text='Пришлите id группы, обязательно добавьте бота в качестве'
                                              ' администратора (Чтобы получить ID чата добавьте бота @FIND_MY_ID_BOT'
                                              ' в чат и напишите в команду'
                                              ' /id@FIND_MY_ID_BOT',
                                         reply_markup=None)
        await state.set_state(Partner.group_id)
        await callback.answer()
        return
    elif select == 'del':
        list_group = await rq.get_group_partner(tg_id_partner=callback.message.chat.id)
        if list_group:
            await callback.message.edit_text(text='Выберите группу для удаления из БД бота',
                                             reply_markup=kb.keyboards_list_group(list_group=list_group, block=0))
        else:
            await callback.answer(text='В БД нет добавленных вами групп', show_alert=True)
        await callback.answer()


@router.message(F.text, StateFilter(Partner.group_id))
@error_handler
async def process_get_group(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Добавление группы партнера
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_get_group: {message.chat.id}')
    if message.text in ['Тарифы', 'Мои группы', 'Партнеры']:
        await state.set_state(state=None)
        await message.answer(text='Добавление группы отменено')
        return

    try:
        group_id = int(message.text)
    except:
        await message.answer(text='ID чата должно быть целым числом '
                                  '(Чтобы получить ID чата добавьте бота @FIND_MY_ID_BOT в чат и напишите в команду'
                                  ' /id@FIND_MY_ID_BOT')
        return
    try:
        bot = await bot.get_chat_member(group_id, bot.id)
        if bot.status == ChatMemberStatus.ADMINISTRATOR:
            await message.answer(text='Отлично! Бот уже состоит в администраторах группы')
        else:
            await message.answer(text='Бот не добавлен администратором в группу, обязательно добавьте'
                                      ' бота администратором'
                                      ' в группу иначе он не сможет публиковать в нее посты')
        await message.answer(text='Пришлите наименование группы (до 32 символов):')
        await state.update_data(group_id=group_id)
        await state.set_state(Partner.group_title)
    except TelegramBadRequest:
        await message.answer(text='Бот не нашел такого чата, добавьте бота в чат, для того чтобы он мог публиковать'
                                  ' посты боту требуется права администратора.'
                                  ' Проверьте права бота в группе и повторите добавления')


@router.message(F.text, StateFilter(Partner.group_title))
@error_handler
async def process_get_group_title(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Добавление/удаление менеджера по username
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_get_group_title: {message.chat.id}')
    group_title = message.text
    if group_title in ['Группы для публикации', 'Менеджеры', 'Мои группы', 'Партнеры']:
        await message.answer(text='Добавление группы отменено')
        await state.set_state(state=None)
        return
    if len(group_title) <= 32:
        data = await state.get_data()
        group_id = data['group_id']
        data_add = {'tg_id_partner': message.from_user.id, 'group_id': group_id, 'title': group_title}
        await rq.add_group(group_id=group_id, data=data_add)
        await message.answer(text='Группа успешно добавлена')
        await state.set_state(state=None)
    else:
        await message.answer(text='Название канала не должно превышать 32 символа')


# Вперед
@router.callback_query(F.data.startswith('groupdelforward_'))
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
    list_group = await rq.get_group_partner(tg_id_partner=callback.message.chat.id)
    count_block = len(list_group) // 6 + 1
    num_block = int(callback.data.split('_')[-1]) + 1
    if num_block == count_block:
        num_block = 0
    keyboard = kb.keyboards_list_group(list_group=list_group, block=num_block)
    try:
        await callback.message.edit_text(text='Выберите группу для удаления из БД бота',
                                         reply_markup=keyboard)
    except:
        await callback.message.edit_text(text='Выбeритe группу для удаления из БД бота',
                                         reply_markup=keyboard)
    await callback.answer()


# Назад
@router.callback_query(F.data.startswith('groupdelback_'))
@error_handler
async def process_back_group(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Пагинация назад
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_back_group: {callback.message.chat.id}')
    list_group = await rq.get_group_partner(tg_id_partner=callback.message.chat.id)
    count_block = len(list_group) // 6 + 1
    num_block = int(callback.data.split('_')[-1]) - 1
    if num_block < 0:
        num_block = count_block - 1
    keyboard = kb.keyboards_list_group(list_group=list_group, block=num_block)
    try:
        await callback.message.edit_text(text='Выберите группу для удаления из БД бота',
                                         reply_markup=keyboard)
    except:
        await callback.message.edit_text(text='Выбeритe группу для удаления из БД бота',
                                         reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith('groupdelselect_'))
@error_handler
async def process_select_group(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Удаление выбранной группы из БД
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_select_group: {callback.message.chat.id}')
    await state.set_state(state=None)
    id_group = int(callback.data.split('_')[-1])
    await rq.delete_group(id_=id_group)
    await callback.message.answer(text='Группа успешно удалена',
                                  reply_markup=None)
    await callback.answer()



