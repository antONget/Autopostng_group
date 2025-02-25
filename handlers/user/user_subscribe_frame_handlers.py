from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter
from utils.error_handling import error_handler
from database import requests as rq
from keyboards.user import user_subscribe_keyboards as kb
from config_data.config import Config, load_config
from database.models import User, Frame, Group
import logging
from datetime import datetime, timedelta

config: Config = load_config()
router = Router()
router.message.filter(F.chat.type == "private")


class ManagerState(StatesGroup):
    text_post = State()
    location = State()
    check_pay = State()


@router.message(F.text == 'Приобрести подписку 🧾')
@error_handler
async def process_select_group_manager(message: Message, bot: Bot) -> None:
    """
    Пользователь выбирает группу
    :param message:
    :param bot:
    :return:
    """
    logging.info('process_select_group_manager')
    list_groups: list = await rq.get_group_partner_not(tg_id_partner=message.from_user.id)
    if list_groups:
        await message.answer(text='Подберите для себя группу для размещения в ней заявок',
                             reply_markup=kb.keyboards_list_group(list_group=list_groups,
                                                                  block=0))
    else:
        await message.answer(text='Пока в бота не добавлены группы, в которых вы могли бы приобрести подписку')


# Вперед
@router.callback_query(F.data.startswith('groupmanagerforward_'))
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
    list_groups: list = await rq.get_group_partner_not(tg_id_partner=callback.from_user.id)
    count_block = len(list_groups) // 6 + 1
    num_block = int(callback.data.split('_')[-1]) + 1
    if num_block == count_block:
        num_block = 0
    keyboard = kb.keyboards_list_group(list_group=list_groups,
                                       block=num_block)
    try:
        await callback.message.edit_text(text='Подберите для себя группу для размещения в ней заявок',
                                         reply_markup=keyboard)
    except:
        await callback.message.edit_text(text='Подберитe для себя группу для размещения в ней заявок',
                                         reply_markup=keyboard)
    await callback.answer()


# Назад
@router.callback_query(F.data.startswith('groupmanagerback_'))
@error_handler
async def process_back_manager(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Пагинация назад
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_back_manager: {callback.message.chat.id}')
    list_groups: list = await rq.get_group_partner_not(tg_id_partner=callback.from_user.id)
    count_block = len(list_groups) // 6 + 1
    num_block = int(callback.data.split('_')[-1]) - 1
    if num_block < 0:
        num_block = count_block - 1
    keyboard = kb.keyboards_list_group(list_group=list_groups,
                                       block=num_block)
    try:
        await callback.message.edit_text(text='Подберите для себя группу для размещения в ней заявок',
                                         reply_markup=keyboard)
    except:
        await callback.message.edit_text(text='Подберитe для себя группу для размещения в ней заявок',
                                         reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith('groupmanagerselect_'))
@error_handler
async def process_select_group(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """

    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_select_group: {callback.message.chat.id}')
    group_id = int(callback.data.split('_')[-1])
    frames: list[Frame] = await rq.get_frames()
    group_in_frame: list[Frame] = []
    info_group: Group = await rq.get_group_id(id_=group_id)
    black_list_user = await rq.get_blacklist_group(tg_id_partner=info_group.tg_id_partner,
                                                   tg_id=callback.from_user.id)
    if black_list_user:
        await callback.message.edit_text(text=f'Вы не можете приобрести подписку,'
                                              f' так <a href="tg://user?id={info_group.tg_id_partner}">владелец</a>'
                                              f' заблокировал вас в своих группах')
        return
    text = f'Для публикации в группу {info_group.title} выберите тариф:\n'
    num = 0
    for frame in frames:
        if num == 1:
            pass
        list_id_group: list = frame.list_id_group.split(',')
        info_frame: Frame = await rq.get_frame_id(id_=frame.id)
        if str(group_id) in list_id_group:
            num += 1
            group_in_frame.append(frame)
            text += f'<b>{num}. {frame.title_frame}</b>:\n' \
                    f'<i>Группы:</i>\n'
            for group_id_ in list_id_group:
                info_group: Group = await rq.get_group_id(id_=group_id_)
                if info_group:
                    text += f'{info_group.title}\n'
            text += f'<i>Стоимость:</i> {info_frame.cost_frame} ₽\n' \
                    f'<i>Период:</i> {info_frame.period_frame} дней\n\n'
    if text == f'Для публикации в группу {info_group.title} выберите тариф:\n':
        await callback.message.edit_text(text=f'Для группы {info_group.title} тарифы не определены',
                                         reply_markup=None)
    else:
        await callback.message.edit_text(text=text,
                                         reply_markup=kb.keyboards_list_group_in_frame(list_frame=group_in_frame))
    await callback.answer()


@router.callback_query(F.data.startswith('frameselectpay_'))
@error_handler
async def process_select_frame_to_pay(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Инструкция по оплате тарифа
    :param callback: frameselectpay_{frame.id}
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_select_frame_to_pay: {callback.message.chat.id}')
    frame_id: int = int(callback.data.split('_')[-1])
    info_frame: Frame = await rq.get_frame_id(id_=frame_id)
    info_partner: User = await rq.get_user(tg_id=info_frame.tg_id_creator)
    await callback.message.edit_text(text=f'Для публикации объявлений необходимо произвести оплату по инструкции.\n\n'
                                          f'{info_partner.requisites}\n\n'
                                          f'После оплаты сохраните чек и пришлите его нажав кнопку "Отправить чек"',
                                     reply_markup=kb.keyboard_check_payment(id_frame=frame_id))
    await callback.answer()


@router.callback_query(F.data.startswith('send_check_'))
@error_handler
async def process_get_check(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Запрос на отправку чека оплаты
    :param callback: send_check_{id_frame}
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_get_check: {callback.message.chat.id}')
    await callback.message.edit_text(text='Отправьте чек об оплате')
    await state.update_data(id_frame=callback.data.split('_')[-1])
    await state.set_state(ManagerState.check_pay)
    await callback.answer()


@router.message(F.photo, StateFilter(ManagerState.check_pay))
@error_handler
async def get_check_payment(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Запрос на отправку чека оплаты
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'get_check_payment: {message.chat.id}')
    await message.answer(text='Данные отправлены на проверку!')
    await state.set_state(state=None)
    data = await state.get_data()
    id_frame: str = data['id_frame']
    info_frame: Frame = await rq.get_frame_id(id_=int(id_frame))
    await bot.send_photo(chat_id=info_frame.tg_id_creator,
                         photo=message.photo[-1].file_id,
                         caption=f'<a href="tg://user?id={message.from_user.id}">Пользователь</a> оплатил тариф'
                                 f' {info_frame.title_frame}',
                         reply_markup=kb.keyboard_check_payment_partner(user_tg_id=message.from_user.id,
                                                                        id_frame=id_frame))


@router.callback_query(F.data.startswith('payment_'))
@error_handler
async def process_confirm_cancel_payment(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Подтверждение или отклонение оплаты
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_get_check: {callback.message.chat.id}')
    payment: str = callback.data.split('_')[-3]
    user_tg_id: str = callback.data.split('_')[-2]
    id_frame: str = callback.data.split('_')[-1]
    info_frame: Frame = await rq.get_frame_id(id_=int(id_frame))
    await callback.message.edit_reply_markup(reply_markup=None)
    if payment == 'cancel':
        await callback.message.answer(text='Платеж отклонен')
        await bot.send_message(chat_id=user_tg_id,
                               text='Ваш платеж отклонен!')
    elif payment == 'confirm':
        await callback.message.answer(text=f'<a href="tg://user?id={user_tg_id}">Пользователю</a>'
                                           f' успешно активирован тариф {info_frame.title_frame}')
        await bot.send_message(chat_id=user_tg_id,
                               text=f'Подписка на тариф {info_frame.title_frame} активирована!')
        current_date = datetime.now()
        current_date_str = current_date.strftime('%d-%m-%Y %H:%M')
        date_completion = current_date + timedelta(days=int(info_frame.period_frame))
        date_completion_str = date_completion.strftime('%d-%m-%Y %H:%M')
        data_subscribe = {'tg_id': user_tg_id,
                          'frame_id': int(id_frame),
                          'date_start': current_date_str,
                          'date_completion': date_completion_str,
                          'group_id_list': info_frame.list_id_group}
        await rq.add_subscribe(data=data_subscribe)
    await callback.answer()
