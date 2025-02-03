from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter, or_f
from aiogram.enums.chat_member_status import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

from utils.error_handling import error_handler
from database import requests as rq
from database.models import Frame, Group
from keyboards import partner_frames_keyboards as kb
from filter.admin_filter import IsSuperAdmin
from filter.user_filter import IsRolePartner
from config_data.config import Config, load_config
import logging

config: Config = load_config()
router = Router()
router.message.filter(F.chat.type == "private")


class FrameState(StatesGroup):
    title_frame = State()
    cost_frame = State()
    period_frame = State()
    change_column = State()


@router.message(F.text == 'Тарифы', or_f(IsSuperAdmin(), IsRolePartner()))
@error_handler
async def press_button_frames(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Список тарифов партнера
    :param message:
    :param bot:
    :param state:
    :return:
    """
    logging.info('press_button_frames')
    await state.set_state(state=None)
    await message.answer(text='Выберите действие с тарифом',
                         reply_markup=kb.keyboard_action_frames())


@router.callback_query(F.data == 'frame_create')
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
    await callback.message.edit_text(text='Пришлите название тарифа',
                                     reply_markup=None)
    await state.set_state(FrameState.title_frame)
    await callback.answer()


@router.message(F.text, StateFilter(FrameState.title_frame))
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
    title_frame = message.text
    if title_frame in ['Тарифы', 'Мои группы', 'Партнеры']:
        await message.answer(text='Добавление тарифа отменено')
        await state.set_state(state=None)
        return
    await state.update_data(title_frame=title_frame)
    await state.set_state(FrameState.cost_frame)
    await message.answer(text='Пришлите стоимость тарифа')


@router.message(F.text, StateFilter(FrameState.cost_frame))
@error_handler
async def process_get_cost_frame(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Получаем стоимость создаваемого тарифа
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_get_cost_frame: {message.chat.id}')
    cost_frame = message.text
    if cost_frame in ['Тарифы', 'Мои группы', 'Партнеры']:
        await message.answer(text='Добавление тарифа отменено')
        await state.set_state(state=None)
        return
    if cost_frame.isdigit():
        await state.update_data(cost_frame=cost_frame)
        await state.set_state(FrameState.period_frame)
        await message.answer(text='Пришлите период тарифа')
    else:
        await message.answer(text='Стоимость тарифа должно быть целым числом, повторите ввод')


@router.message(F.text, StateFilter(FrameState.period_frame))
@error_handler
async def process_get_period_frame(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Получаем длительность периода
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_get_period_frame: {message.chat.id}')
    period_frame = message.text
    if period_frame in ['Тарифы', 'Мои группы', 'Партнеры']:
        await message.answer(text='Добавление тарифа отменено')
        await state.set_state(state=None)
        return
    if period_frame.isdigit():
        await state.set_state(state=None)
        await state.update_data(period_frame=period_frame)
        await state.set_state(FrameState.period_frame)
        data = await state.get_data()
        dict_frame = {"tg_id_creator": message.from_user.id,
                      "title_frame": data["title_frame"],
                      "cost_frame": data["cost_frame"],
                      "period_frame": data["period_frame"]}
        id_frame = await rq.add_frame(data=dict_frame)
        print(id_frame)
        await state.update_data(id_frame=id_frame)
        list_group = await rq.get_group_partner(tg_id_partner=message.chat.id)
        await message.answer(text='Выберите группы для добавления в тариф',
                             reply_markup=kb.keyboards_list_group_frame(list_group=list_group,
                                                                        block=0,
                                                                        list_id_group=[]))
    else:
        await message.answer(text='Длительность тарифа должно быть целым числом, повторите ввод')


# Вперед
@router.callback_query(F.data.startswith('groupframeforward_'))
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
    list_group: list[Group] = await rq.get_group_partner(tg_id_partner=callback.message.chat.id)
    count_block = len(list_group) // 6 + 1
    num_block = int(callback.data.split('_')[-1]) + 1
    if num_block == count_block:
        num_block = 0
    data = await state.get_data()
    str_id_group: Frame = await rq.get_frame_id(id_=data["id_frame"])
    list_id_group: list = str_id_group.list_id_group.split(',')
    keyboard = kb.keyboards_list_group_frame(list_group=list_group, block=num_block, list_id_group=list_id_group)
    try:
        await callback.message.edit_text(text='Выберите группу для удаления из БД бота',
                                         reply_markup=keyboard)
    except:
        await callback.message.edit_text(text='Выбeритe группу для удаления из БД бота',
                                         reply_markup=keyboard)
    await callback.answer()


# Назад
@router.callback_query(F.data.startswith('groupframeback_'))
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
    data = await state.get_data()
    str_id_group: Frame = await rq.get_frame_id(id_=data["id_frame"])
    list_id_group: list = str_id_group.list_id_group.split(',')
    keyboard = kb.keyboards_list_group_frame(list_group=list_group, block=num_block, list_id_group=list_id_group)
    try:
        await callback.message.edit_text(text='Выберите группу для удаления из БД бота',
                                         reply_markup=keyboard)
    except:
        await callback.message.edit_text(text='Выбeритe группу для удаления из БД бота',
                                         reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith('groupframeselect_'))
@error_handler
async def process_select_group(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Добавление/удаление выбранной группы в тариф
    :param callback: int(callback.data.split('_')[1]) номер группы
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_select_group: {callback.message.chat.id}')
    id_group = callback.data.split('_')[-1]
    data = await state.get_data()
    await rq.set_frame_id(id_frame=data['id_frame'], id_group=id_group)
    list_group: list[Group] = await rq.get_group_partner(tg_id_partner=callback.message.chat.id)
    info_frame: Frame = await rq.get_frame_id(id_=data['id_frame'])
    str_id_group: str = info_frame.list_id_group
    list_id_group: list = str_id_group.split(',')
    print(data['id_frame'])
    print(list_id_group)
    keyboard = kb.keyboards_list_group_frame(list_group=list_group,
                                             block=0,
                                             list_id_group=list_id_group)
    try:
        await callback.message.edit_text(text='Выберите группу для удаления из БД бота',
                                         reply_markup=keyboard)
    except:
        await callback.message.edit_text(text='Выбeритe группу для удаления из БД бота',
                                         reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == 'confirm_attach_group_frame')
@error_handler
async def process_confirm_attach_group_frame(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Подтверждение создание тарифа
    :param callback: int(callback.data.split('_')[1]) номер группы
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_confirm_attach_group_frame: {callback.message.chat.id}')
    await state.set_state(state=None)
    data = await state.get_data()
    info_frame: Frame = await rq.get_frame_id(id_=data['id_frame'])
    print(info_frame.list_id_group)
    if not info_frame.list_id_group:
        await callback.answer(text=f'Тариф не может быть пустым, добавьте хотя бы одну группу',
                              show_alert=True)
        return
    title_frame: str = info_frame.title_frame
    cost_frame: str = info_frame.cost_frame
    period_frame: str = info_frame.period_frame
    list_id_group: str = info_frame.list_id_group
    text = ''
    i = 0
    for id_group in list_id_group.split(','):
        if id_group.isdigit():
            info_group = await rq.get_group_id(id_=int(id_group))
            text += f'{i+1}. {info_group.title}\n'
    await callback.message.edit_text(text=f'<b>ТАРИФ</b>:\n\n'
                                          f'Название: {title_frame}\n'
                                          f'Стоимость: {cost_frame} ₽\n'
                                          f'Период: {period_frame} дней\n\n'
                                          f'Группы:\n{text}\n\n'
                                          f'Успешно добавлен в БД',
                                     reply_markup=None)
    await callback.answer()


@router.callback_query(F.data == 'frame_edit')
@router.callback_query(F.data == 'frame_del')
@error_handler
async def process_frame_delete(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Удаление тарифа партнера
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_frame_delete {callback.data}')
    action_frame: str = callback.data.split('_')[-1]
    await state.update_data(action_frame=action_frame)
    if action_frame == 'edit':
        text = 'Выберите тариф для удаления'
        text_1 = 'редактирования'
    else:
        text = 'Выберите тариф для редактирования'
        text_1 = 'удаления'
    frames: list[Frame] = await rq.get_frame_tg_id(tg_id=callback.from_user.id)
    if frames:
        await callback.message.edit_text(text=text,
                                         reply_markup=kb.keyboards_list_frame(list_frame=frames, block=0))
    else:
        await callback.message.edit_text(text=f'У вас нет тарифов для {text_1}')
    await callback.answer()


# Вперед
@router.callback_query(F.data.startswith('frameforward_'))
@error_handler
async def process_frame_forward(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Пагинация вперед
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_frame_forward: {callback.message.chat.id}')
    data = await state.get_data()
    action_frame = data['action_frame']
    if action_frame == 'edit':
        text = 'удаления'
    else:
        text = 'редактирования'
    frames: list[Frame] = await rq.get_frame_tg_id(tg_id=callback.from_user.id)
    count_block = len(frames) // 6 + 1
    num_block = int(callback.data.split('_')[-1]) + 1
    if num_block == count_block:
        num_block = 0
    keyboard = kb.keyboards_list_frame(list_frame=frames, block=num_block)
    try:
        await callback.message.edit_text(text=f'Выберите тариф для {text} из БД бота',
                                         reply_markup=keyboard)
    except:
        await callback.message.edit_text(text=f'Выбeритe тариф для {text} из БД бота',
                                         reply_markup=keyboard)
    await callback.answer()


# Назад
@router.callback_query(F.data.startswith('frameback_'))
@error_handler
async def process_frame_back(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Пагинация назад
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_frame_back: {callback.message.chat.id}')
    data = await state.get_data()
    action_frame = data['action_frame']
    if action_frame == 'edit':
        text = 'удаления'
    else:
        text = 'редактирования'
    frames: list[Frame] = await rq.get_frame_tg_id(tg_id=callback.from_user.id)
    count_block = len(frames) // 6 + 1
    num_block = int(callback.data.split('_')[-1]) - 1
    if num_block < 0:
        num_block = count_block - 1
    keyboard = kb.keyboards_list_frame(list_frame=frames, block=num_block)
    try:
        await callback.message.edit_text(text=f'Выберите тариф для {text} из БД бота',
                                         reply_markup=keyboard)
    except:
        await callback.message.edit_text(text=f'Выбeритe тариф для {text} из БД бота',
                                         reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith('changeframeselect_'))
@error_handler
async def process_select_delete_frame(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Добавление/удаление выбранной группы в тариф
    :param callback: int(callback.data.split('_')[1]) номер группы
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_select_delete_frame: {callback.message.chat.id}')
    data = await state.get_data()
    action_frame = data['action_frame']
    id_frame = callback.data.split('_')[-1]
    info_frame: Frame = await rq.get_frame_id(id_=int(id_frame))
    if action_frame == 'del':
        await rq.del_frame_id(id_=int(id_frame))
        await callback.message.edit_text(text=f'Тариф {info_frame.title_frame} успешно удален',
                                         reply_markup=None)
    else:
        await state.update_data(id_frame=id_frame)
        msg_change = await callback.message.edit_text(text=f'Выберите поля тарифа {info_frame.title_frame}'
                                                           f' для его редактирования\n'
                                                           f'Для завершения нажмите "Подтвердить"',
                                                      reply_markup=kb.keyboard_column_frame(info_frame=info_frame))
        await state.update_data(message_id_change=msg_change.message_id)
    await callback.answer()


@router.callback_query(F.data.startswith('change_'))
@error_handler
async def process_frame_edit(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Редактирование полей тарифа партнера
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info('process_frame_edit')
    column_frame: str = callback.data.split('_')[-1]
    await callback.message.edit_text(text='Пришлите новое значение поля',
                                     reply_markup=None)
    await state.update_data(column_frame=column_frame)
    if column_frame != 'listgroup':
        await state.set_state(FrameState.change_column)
        await state.update_data(change_column=column_frame)
    else:
        data = await state.get_data()
        id_frame = data['id_frame']
        list_group: list[Group] = await rq.get_group_partner(tg_id_partner=callback.from_user.id)
        info_frame: Frame = await rq.get_frame_id(id_=int(id_frame))
        list_id_group: list = info_frame.list_id_group.split(',')
        await callback.message.answer(text='Выберите группы для добавления в тариф',
                                      reply_markup=kb.keyboards_list_group_frame(list_group=list_group,
                                                                                 block=0,
                                                                                 list_id_group=list_id_group,
                                                                                 flag_change=True))

    await callback.answer()


@router.message(F.text, StateFilter(FrameState.change_column))
@error_handler
async def get_new_name_column(message: Message, state: FSMContext, bot: Bot):
    """
    Получаем новое значение для поля тарифа
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info('get_new_name_column')
    data = await state.get_data()
    change_column = data['change_column']
    id_frame = data['id_frame']
    if change_column in ['cost', 'period']:
        if not message.text.isdigit():
            await message.edit_text(text='Некорректные данные. Введите целое число')
            return
    await rq.set_frame_id_column(id_frame=id_frame,
                                 column=change_column,
                                 change=message.text)
    await message.delete()
    info_frame: Frame = await rq.get_frame_id(id_=int(id_frame))
    await bot.edit_message_text(chat_id=message.from_user.id,
                                message_id=data['message_id_change'],
                                text=f'Выберите поля тарифа {info_frame.title_frame} для его редактирования\n'
                                     f'Для завершения нажмите "Подтвердить"',
                                reply_markup=kb.keyboard_column_frame(info_frame=info_frame))
    await state.set_state(state=None)


@router.callback_query(F.data == 'confirm_change_group_frame')
@error_handler
async def confirm_change_group_frame(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Подтверждение изменения списка групп добавленных в тариф
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info('confirm_change_group_frame')
    data = await state.get_data()
    id_frame = data['id_frame']
    data = await state.get_data()
    info_frame: Frame = await rq.get_frame_id(id_=data['id_frame'])
    if not info_frame.list_id_group:
        await callback.answer(text=f'Тариф не может быть пустым, добавьте хотя бы одну группу',
                              show_alert=True)
        return
    info_frame: Frame = await rq.get_frame_id(id_=int(id_frame))
    await callback.message.edit_text(text=f'Выберите поля тарифа {info_frame.title_frame} для его редактирования\n'
                                          f'Для завершения нажмите "Подтвердить"',
                                     reply_markup=kb.keyboard_column_frame(info_frame=info_frame))
