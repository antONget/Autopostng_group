from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter, or_f
from aiogram.enums.chat_member_status import ChatMemberStatus
from utils.error_handling import error_handler
from database import requests as rq
from keyboards import manager_keyboards as kb
from filter.admin_filter import IsSuperAdmin
from filter.user_filter import IsRolePartner, IsRoleManager
from config_data.config import Config, load_config
from database.models import User, Frame, Group, Subscribe, Post
import logging
from datetime import datetime, timedelta
import validators

config: Config = load_config()
router = Router()
router.message.filter(F.chat.type == "private")


class ManagerState(StatesGroup):
    text_post = State()
    location = State()
    check_pay =State()


@router.message(F.text == 'Выбрать группу')
@error_handler
async def process_select_group_manager(message: Message, bot: Bot) -> None:
    """
    Пользователь выбирает группу
    :param message:
    :param bot:
    :return:
    """
    logging.info('process_select_group_manager')
    list_groups: list = await rq.get_all_group()
    if list_groups:
        await message.answer(text='Подберите для себя группу для размещения в ней заявок',
                             reply_markup=kb.keyboards_list_group(list_group=list_groups,
                                                                  block=0))
    else:
        await message.answer(text='Пока в бота не добавлены группы, в которых вы могли бы разместить объявления')


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
    list_groups: list = await rq.get_all_group()
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
    list_groups: list = await rq.get_all_group()
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
    # group = await rq.get_group_id(id_=group_id)
    # user = await rq.get_user(tg_id=group.tg_id_partner)
    # await callback.message.answer(text=f'Запрос на добавление вас в группу в качестве администратора направлен'
    #                                    f' владельцу чата @{user.username}, для ускорения процедуры добавления можете'
    #                                    f' написать ему')
    # try:
    #     await bot.send_message(chat_id=user.tg_id,
    #                            text=f'Менеджер @{callback.from_user.username} запросил доступ к чату {group.title}')
    # except:
    #     pass
    frames: list[Frame] = await rq.get_frames()
    group_in_frame: list[Frame] = []
    info_group: Group = await rq.get_group_id(id_=group_id)
    text = f'Для публикации в группу {info_group.title} выберите тариф:\n'
    num = 0
    for frame in frames:
        if num == 1:
            pass
        list_id_group: list = frame.list_id_group.split(',')
        info_frame: Frame = await rq.get_frame_id(id_=frame.id)
        print(str(group_id), list_id_group, str(group_id) in list_id_group)
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
    await callback.message.answer(text=f'Для публикации объявлений необходимо произвести оплату по инструкции.\n\n'
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
    await callback.message.answer(text='Отправьте чек об оплате')
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


@router.message(F.text == 'Группы для публикации')
@error_handler
async def user_group_for_publish(message: Message, bot: Bot) -> None:
    """
    Менеджер выбирает группу
    :param message:
    :param bot:
    :return:
    """
    logging.info('process_select_group_manager')
    subscribes: list[Subscribe] = await rq.get_subscribes_user(tg_id=message.from_user.id)
    active_subscribe = False
    if subscribes:
        last_subscribe: Subscribe = subscribes[-1]
        date_format = '%d-%m-%Y %H:%M'
        current_date = datetime.now().strftime('%d-%m-%Y %H:%M')
        delta_time = (datetime.strptime(last_subscribe.date_completion, date_format) -
                      datetime.strptime(current_date, date_format))
        if delta_time.days >= 0:
            active_subscribe = True
    if not subscribes or not active_subscribe:
        list_groups: list = await rq.get_all_group()
        if list_groups:
            await message.answer(text='Действие вашей подписки завершено, выберите группу и продлите подписку',
                                 reply_markup=kb.keyboards_list_group(list_group=list_groups,
                                                                      block=0))
        else:
            await message.answer(text='Пока в бота не добавлены группы, в которых вы могли бы разместить объявления')
    else:
        last_subscribe: Subscribe = subscribes[-1]
        info_frame: Frame = await rq.get_frame_id(id_=last_subscribe.frame_id)
        text = f'Ваш тариф - <b>{info_frame.title_frame}</b>\n' \
               f'Подписка до: <b>{last_subscribe.date_completion}</b>\n' \
               f'Ваши группы в которых вы можете размещать заявки:\n'
        count = 0
        for group_id in last_subscribe.group_id_list.split(','):
            if group_id.isdigit():
                group: Group = await rq.get_group_id(id_=int(group_id))
                if group:
                    count += 1
                    text += f'{count}. {group.title}\n'
        await message.answer(text=text,
                             reply_markup=kb.keyboard_manager_publish())

    # user = await rq.get_user(tg_id=message.chat.id)
    # if user.role == rq.UserRole.manager:
    #     manager: Manager = await rq.get_manager(tg_id_manager=message.chat.id)
    #     if manager:
    #         list_ids_group: list[str] = manager.group_ids.split(',')
    #         if list_ids_group == ['0']:
    #             await message.answer(text='Вы не добавлены не в одну группу')
    #         else:
    #             text = 'Ваши группы в которых вы можете размещать заявки:\n\n'
    #             i = 0
    #             for group_id in list_ids_group:
    #                 group = await rq.get_group_id(id_=int(group_id))
    #                 if group:
    #                     i += 1
    #                     text += f'<b>{i}. {group.title}</b>\n'
    #             await message.answer(text=text,
    #                                  reply_markup=kb.keyboard_manager_publish())
    #     else:
    #         await message.answer(text='Для публикации постов вам необходимо быть менеджером')
    # elif user.role == rq.UserRole.partner:
    #     groups = await rq.get_group_partner(tg_id_partner=message.chat.id)
    #     # список своих групп
    #     list_ids_group: list[int] = [group.id for group in groups]
    #     manager: Manager = await rq.get_manager(tg_id_manager=message.chat.id)
    #     if manager:
    #         list_ids_group_manager: list[str] = manager.group_ids.split(',')
    #         for group_id in list_ids_group_manager:
    #             if int(group_id) not in list_ids_group:
    #                 list_ids_group.append(int(group_id))
    #
    #     if not list_ids_group or list_ids_group == [0]:
    #         await message.answer(text='Вы не добавлены не в одну группу')
    #     else:
    #         text = 'Ваши группы в которых вы можете размещать заявки:\n\n'
    #         i = 0
    #         for group_id in list_ids_group:
    #             group = await rq.get_group_id(id_=group_id)
    #             if group:
    #                 i += 1
    #                 text += f'<b>{i}. {group.title}</b>\n'
    #         await message.answer(text=text,
    #                              reply_markup=kb.keyboard_manager_publish())


@router.callback_query(F.data == 'publish_post')
@error_handler
async def process_publish_post(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Публикация поста
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_publish_post: {callback.message.chat.id}')
    subscribes: list[Subscribe] = await rq.get_subscribes_user(tg_id=callback.from_user.id)
    active_subscribe = False
    if subscribes:
        last_subscribe: Subscribe = subscribes[-1]
        date_format = '%d-%m-%Y %H:%M'
        current_date = datetime.now().strftime('%d-%m-%Y %H:%M')
        delta_time = (datetime.strptime(last_subscribe.date_completion, date_format) -
                      datetime.strptime(current_date, date_format))
        if delta_time.days >= 0:
            active_subscribe = True
    if not subscribes or not active_subscribe:
        list_groups: list = await rq.get_all_group()
        if list_groups:
            await callback.message.answer(text='Действие вашей подписки завершено, выберите группу и продлите подписку',
                                          reply_markup=kb.keyboards_list_group(list_group=list_groups,
                                                                               block=0))
        else:
            await callback.message.answer(text='Пока в бота не добавлены группы, в которых вы могли бы разместить'
                                               ' объявления')
    else:
        await callback.message.edit_text(text="Пришлите текст заявки для размещения в группах",
                                         reply_markup=None)
        await state.set_state(ManagerState.text_post)
    await callback.answer()


@router.message(F.text, StateFilter(ManagerState.text_post))
@error_handler
async def get_text_post(message: Message, state: FSMContext, bot: Bot):
    """
    Публикация поста
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'get_text_post: {message.chat.id}')
    await state.update_data(text_post=message.html_text)
    await message.answer(text='Пришлите ссылку на местоположение',
                         reply_markup=kb.keyboard_pass_location())
    await state.set_state(ManagerState.location)


@router.message(F.text, StateFilter(ManagerState.location))
@error_handler
async def get_location(message: Message, state: FSMContext, bot: Bot):
    """
    Получаем локацию
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'get_text_post: {message.chat.id}')
    if not validators.url(message.text):
        await message.answer(text='Ссылка не валидна, проверьте правильность введенных данных')
        return
    await state.update_data(location=message.text)
    data = await state.get_data()
    await message.answer(text=data['text_post'],
                         reply_markup=kb.keyboard_show_post(manager_tg_id=message.chat.id, location=message.text))
    await state.set_state(state=None)


@router.callback_query(F.data == 'pass_location')
@error_handler
async def process_pass_location(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Публикация поста
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_publish_post: {callback.message.chat.id}')
    await state.update_data(location='none')
    data = await state.get_data()
    await callback.message.edit_text(text=data['text_post'],
                                     reply_markup=kb.keyboard_show_post_(manager_tg_id=callback.message.chat.id))
    await state.set_state(state=None)
    await callback.answer()


@router.callback_query(F.data == 'publishpost')
@error_handler
async def publish_post(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Публикация поста
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'publish_post: {callback.message.chat.id}')
    subscribes: list[Subscribe] = await rq.get_subscribes_user(tg_id=callback.from_user.id)
    last_subscribe = subscribes[-1]
    list_ids_group: list = last_subscribe.group_id_list.split(',')
    data = await state.get_data()
    message_chat = []
    for i, group_id in enumerate(list_ids_group):
        group: Group = await rq.get_group_id(id_=group_id)
        if not group:
            continue
        bot_ = await bot.get_chat_member(group.group_id, bot.id)
        if bot_.status != ChatMemberStatus.ADMINISTRATOR:
            await callback.message.answer(text=f'Бот не может опубликовать пост в группу <b>{group.title}</b>'
                                               f' так как не является администратором, обратитесь к'
                                               f' <a href="tg://user?id={group.tg_id_partner}">владельцу</a> ')
        else:
            if data['location'] == 'none':
                post = await bot.send_message(chat_id=group.group_id,
                                              text=f"{data['text_post']}\n"
                                                   f"По всем вопросам пишите <a href='tg://user?id="
                                                   f"{callback.from_user.id}'>"
                                                   f"{callback.from_user.username}</a>",
                                              reply_markup=kb.keyboard_post_(
                                                  manager_tg_id=callback.message.chat.id))
            else:
                post = await bot.send_message(chat_id=group.group_id,
                                              text=f"{data['text_post']}\n"
                                                   f"По всем вопросам пишите <a href='tg://user?id="
                                                   f"{callback.from_user.id}'>"
                                                   f"{callback.from_user.username}</a>",
                                              reply_markup=kb.keyboard_post(
                                                  manager_tg_id=callback.message.chat.id,
                                                  location=data['location']))
            message_chat.append(f'{group.group_id}!{post.message_id}')
            await callback.message.answer(text=f'Пост опубликован в группе {group.title}')
    await callback.message.edit_text(text=f'Публикация поста по списку групп завершена',
                                     reply_markup=None)
    posts_chat_message = ','.join(message_chat)
    data_ = {'tg_id_manager': callback.message.chat.id, 'posts_text': data['text_post'],
             'posts_chat_message': posts_chat_message, 'post_date': datetime.now().strftime('%d-%m-%Y %H:%M')}
    await rq.add_post(data=data_)



    # user = await rq.get_user(tg_id=callback.message.chat.id)
    # if user.role == rq.UserRole.manager:
    #     manager: Manager = await rq.get_manager(tg_id_manager=callback.message.chat.id)
    #     if manager:
    #         list_ids_group: list = manager.group_ids.split(',')
    #         if list_ids_group == ['0']:
    #             await callback.message.answer(text='Вы не добавлены не в одну группу')
    #         else:
    #             await callback.message.answer(text='Публикация поста по списку групп запущена')
    #             data = await state.get_data()
    #             message_chat = []
    #             for i, group_id in enumerate(list_ids_group):
    #                 group = await rq.get_group_id(id_=group_id)
    #                 if not group:
    #                     continue
    #                 bot_ = await bot.get_chat_member(group.group_id, bot.id)
    #                 if bot_.status != ChatMemberStatus.ADMINISTRATOR:
    #                     await callback.message.answer(text=f'Бот не может опубликовать пост в группу <b>{group.title}</b>'
    #                                                        f' так как не является администратором, обратитесь к'
    #                                                        f' <a href="tg://user?id={group.tg_id_partner}">владельцу</a> ')
    #                 else:
    #                     if data['location'] == 'none':
    #                         post = await bot.send_message(chat_id=group.group_id,
    #                                                       text=f"{data['text_post']}\n"
    #                                                            f"По всем вопросам пишите <a href='tg://user?id="
    #                                                            f"{callback.message.chat.id}'>"
    #                                                            f"{callback.from_user.username}</a>",
    #                                                       reply_markup=kb.keyboard_post_(
    #                                                           manager_tg_id=callback.message.chat.id))
    #                     else:
    #                         post = await bot.send_message(chat_id=group.group_id,
    #                                                       text=f"{data['text_post']}\n"
    #                                                            f"По всем вопросам пишите <a href='tg://user?id="
    #                                                            f"{callback.message.chat.id}'>"
    #                                                            f"{callback.from_user.username}</a>",
    #                                                       reply_markup=kb.keyboard_post(
    #                                                           manager_tg_id=callback.message.chat.id,
    #                                                           location=data['location']))
    #                     message_chat.append(f'{group.group_id}!{post.message_id}')
    #                     await callback.message.answer(text=f'Бот пост опубликован в группе {group.title}')
    #             await callback.message.answer(text=f'Публикация поста по списку групп завершена')
    #             posts_chat_message = ','.join(message_chat)
    #             data_ = {'tg_id_manager': callback.message.chat.id, 'posts_text': data['text_post'],
    #                      'posts_chat_message': posts_chat_message, 'post_date': datetime.now().strftime('%d-%m-%Y %H:%M')}
    #             await rq.add_post(data=data_)
    #     else:
    #         await callback.message.answer(text='Для публикации постов вам необходимо быть менеджером')
    #     await callback.answer()
    #     return
    # if user.role == rq.UserRole.partner:
    #     groups_partner: list = await rq.get_group_partner(tg_id_partner=callback.message.chat.id)
    #     list_ids_group: list = [group.id for group in groups_partner]
    #
    #     manager: Manager = await rq.get_manager(tg_id_manager=callback.message.chat.id)
    #     if manager:
    #         list_ids_group_manager: list[str] = manager.group_ids.split(',')
    #         for group_id in list_ids_group_manager:
    #             if int(group_id) not in list_ids_group:
    #                 list_ids_group.append(int(group_id))
    #
    #     await callback.message.answer(text='Публикация поста по списку групп запущена')
    #     data = await state.get_data()
    #     message_chat = []
    #     for i, group_id in enumerate(list_ids_group):
    #         group = await rq.get_group_id(id_=group_id)
    #         if not group:
    #             continue
    #         bot_ = await bot.get_chat_member(group.group_id, bot.id)
    #         if bot_.status != ChatMemberStatus.ADMINISTRATOR:
    #             await callback.message.answer(text=f'Бот не может опубликовать пост в группу <b>{group.title}</b>'
    #                                                f' так как не является администратором, обратитесь к'
    #                                                f' <a href="tg://user?id={group.tg_id_partner}">владельцу</a> ')
    #         else:
    #             if data['location'] == 'none':
    #                 post = await bot.send_message(chat_id=group.group_id,
    #                                               text=f"{data['text_post']}\n"
    #                                                    f"По всем вопросам пишите <a href='tg://user?id="
    #                                                    f"{callback.message.chat.id}'>"
    #                                                    f"{callback.from_user.username}</a>",
    #                                               reply_markup=kb.keyboard_post_(
    #                                                   manager_tg_id=callback.message.chat.id))
    #             else:
    #                 post = await bot.send_message(chat_id=group.group_id,
    #                                               text=f"{data['text_post']}\n"
    #                                                    f"По всем вопросам пишите <a href='tg://user?id="
    #                                                    f"{callback.message.chat.id}'>"
    #                                                    f"{callback.from_user.username}</a>",
    #                                               reply_markup=kb.keyboard_post(
    #                                                   manager_tg_id=callback.message.chat.id,
    #                                                   location=data['location']))
    #             message_chat.append(f'{group.group_id}!{post.message_id}')
    #             await callback.message.answer(text=f'Бот пост опубликован в группе {group.title}')
    #     await callback.message.answer(text=f'Публикация поста по списку групп завершена')
    #     posts_chat_message = ','.join(message_chat)
    #     data_ = {'tg_id_manager': callback.message.chat.id, 'posts_text': data['text_post'],
    #              'posts_chat_message': posts_chat_message, 'post_date': datetime.now().strftime('%d-%m-%Y %H:%M')}
    #     await rq.add_post(data=data_)


@router.callback_query(F.data == 'cancelpost')
@error_handler
async def publish_post_cancel(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Отмена публикации поста
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'publish_post_cancel: {callback.message.chat.id}')
    await callback.answer(text='Публикация поста отменено',
                          show_alert=True)
    await callback.message.edit_text(text='Выберите группу для размещение заявок',
                                     reply_markup=kb.keyboard_manager_publish_one())


@router.callback_query(F.data == 'delete_post')
@error_handler
async def process_delete_post(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Удаление поста
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_delete_post: {callback.message.chat.id}')
    list_posts: list[Post] = await rq.get_post_manager(tg_id_manager=callback.message.chat.id)
    if not list_posts:
        await callback.message.edit_text(text='Нет постов для удаления.',
                                         reply_markup=None)
        await callback.answer()
        return
    await callback.message.edit_text(text=f'{list_posts[0].posts_text}',
                                     reply_markup=kb.keyboards_list_post(block=0, id_post=list_posts[0].id))
    await callback.answer()


# Вперед
@router.callback_query(F.data.startswith('deletepostforward_'))
@error_handler
async def process_forward_post(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Пагинация вперед
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_forward_post: {callback.message.chat.id}')
    list_posts: list = await rq.get_post_manager(tg_id_manager=callback.message.chat.id)
    count_block = len(list_posts)
    num_block = int(callback.data.split('_')[-1]) + 1
    if num_block == count_block:
        num_block = 0
    keyboard = kb.keyboards_list_post(block=num_block, id_post=list_posts[num_block].id)
    try:
        await callback.message.edit_text(text=f'{list_posts[num_block].posts_text}',
                                         reply_markup=keyboard)
    except:
        await callback.message.edit_text(text=f'{list_posts[num_block].posts_text}.',
                                         reply_markup=keyboard)
    await callback.answer()


# Назад
@router.callback_query(F.data.startswith('deletepostback_'))
@error_handler
async def process_back_post(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Пагинация назад
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_back_post: {callback.message.chat.id}')
    list_posts: list = await rq.get_post_manager(tg_id_manager=callback.message.chat.id)
    count_block = len(list_posts)
    num_block = int(callback.data.split('_')[-1]) - 1
    if num_block < 0:
        num_block = count_block - 1
    keyboard = kb.keyboards_list_post(block=num_block, id_post=list_posts[num_block].id)
    try:
        await callback.message.edit_text(text=f'{list_posts[num_block].posts_text}',
                                         reply_markup=keyboard)
    except:
        await callback.message.edit_text(text=f'{list_posts[num_block].posts_text}.',
                                         reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith('deletepost_'))
@error_handler
async def process_back_post(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Удаление поста
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_back_post: {callback.message.chat.id}')
    id_post = int(callback.data.split('_')[-1])
    post = await rq.get_post_id(id_=id_post)
    posts_chat_message = post.posts_chat_message
    list_chat_message = posts_chat_message.split(',')
    for chat_message in list_chat_message:
        try:
            await bot.delete_message(chat_id=chat_message.split('!')[0],
                                     message_id=chat_message.split('!')[1])
        except:
            pass
    await rq.delete_post(id_=id_post)
    await callback.message.edit_text(text='Пост удален',
                                     reply_markup=None)
    await callback.answer()