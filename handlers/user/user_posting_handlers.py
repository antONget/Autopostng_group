from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter
from aiogram.enums.chat_member_status import ChatMemberStatus

from utils.error_handling import error_handler
from filter.user_filter import check_role
from database import requests as rq
from keyboards.user import user_posting_keyboards as kb
from config_data.config import Config, load_config
from database.models import User, Frame, Group, Subscribe, Post
import validators

import logging
from datetime import datetime


config: Config = load_config()
router = Router()
router.message.filter(F.chat.type == "private")


class ManagerState(StatesGroup):
    text_post = State()
    location = State()
    check_pay = State()


@router.message(F.text == 'Опубликовать пост')
@error_handler
async def user_group_for_publish(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Менеджер выбирает группу
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info('process_select_group_manager')
    subscribes: list[Subscribe] = await rq.get_subscribes_user(tg_id=message.from_user.id)
    active_subscribe = False
    list_active_subscribe = []
    if subscribes:
        for subscribe in subscribes:
            date_format = '%d-%m-%Y %H:%M'
            current_date = datetime.now().strftime('%d-%m-%Y %H:%M')
            delta_time = (datetime.strptime(subscribe.date_completion, date_format) -
                          datetime.strptime(current_date, date_format))
            if delta_time.days >= 0:
                active_subscribe = True
                list_active_subscribe.append(subscribe)

    if await check_role(tg_id=message.from_user.id,
                        role=rq.UserRole.admin) or await check_role(tg_id=message.from_user.id,
                                                                    role=rq.UserRole.partner):
        text = ''
        str_group_ids = ''
        for active_subscribe in list_active_subscribe:
            # last_subscribe: Subscribe = subscribes[-1]
            info_frame: Frame = await rq.get_frame_id(id_=active_subscribe.frame_id)
            text += f'Ваш тариф - <b>{info_frame.title_frame}</b>\n' \
                    f'Подписка до: <b>{active_subscribe.date_completion}</b>\n' \
                    f'Группы в которых вы можете размещать заявки:\n'
            count = 0
            for group_id in active_subscribe.group_id_list.split(','):
                if group_id.isdigit():
                    group: Group = await rq.get_group_id(id_=int(group_id))
                    if group:
                        count += 1
                        text += f'{count}. {group.title}\n'
            str_group_ids += active_subscribe.group_id_list
        groups_partner: list[Group] = await rq.get_group_partner(tg_id_partner=message.from_user.id)
        self_group_text = f'Группы в которых вы можете размещать заявки:\n'
        for group in groups_partner:
            str_group_ids += f',{group.id}'
            self_group_text += f'{group.title}\n'
        await state.update_data(str_group_ids=str_group_ids)
        await message.answer(text=f'{text}\n\n{self_group_text}',
                             reply_markup=kb.keyboard_user_publish())
    else:
        if not subscribes or not active_subscribe:
            list_groups: list = await rq.get_group_partner_not(tg_id_partner=message.from_user.id)
            if list_groups:
                await message.answer(text='У вас нет активных подписок, выберите группу и продлите подписку',
                                     reply_markup=kb.keyboards_list_group(list_group=list_groups,
                                                                          block=0))
            else:
                await message.answer(text='Пока в бота не добавлены группы, в которых вы могли приобрести подписки')
        else:
            text = ''
            str_group_ids = ''
            for active_subscribe in list_active_subscribe:
                # last_subscribe: Subscribe = subscribes[-1]
                info_frame: Frame = await rq.get_frame_id(id_=active_subscribe.frame_id)
                text += f'Ваш тариф - <b>{info_frame.title_frame}</b>\n' \
                        f'Подписка до: <b>{active_subscribe.date_completion}</b>\n' \
                        f'Группы в которых вы можете размещать заявки:\n'
                count = 0
                for group_id in active_subscribe.group_id_list.split(','):
                    if group_id.isdigit():
                        group: Group = await rq.get_group_id(id_=int(group_id))
                        if group:
                            count += 1
                            text += f'{count}. {group.title}\n'
                str_group_ids += active_subscribe.group_id_list
            await state.update_data(str_group_ids=str_group_ids)
            await message.answer(text=text,
                                 reply_markup=kb.keyboard_user_publish())


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
    list_active_subscribe = []
    # проверка на подписку
    if subscribes:
        for subscribe in subscribes:
            date_format = '%d-%m-%Y %H:%M'
            current_date = datetime.now().strftime('%d-%m-%Y %H:%M')
            delta_time = (datetime.strptime(subscribe.date_completion, date_format) -
                          datetime.strptime(current_date, date_format))
            if delta_time.days >= 0:
                active_subscribe = True
                list_active_subscribe.append(subscribe)
    if await check_role(tg_id=callback.from_user.id,
                        role=rq.UserRole.admin) or await check_role(tg_id=callback.from_user.id,
                                                                    role=rq.UserRole.partner):
        text = ''
        str_group_ids = ''
        for active_subscribe in list_active_subscribe:
            # last_subscribe: Subscribe = subscribes[-1]
            info_frame: Frame = await rq.get_frame_id(id_=active_subscribe.frame_id)
            text += f'Ваш тариф - <b>{info_frame.title_frame}</b>\n' \
                    f'Подписка до: <b>{active_subscribe.date_completion}</b>\n' \
                    f'Группы в которых вы можете размещать заявки:\n'
            count = 0
            for group_id in active_subscribe.group_id_list.split(','):
                if group_id.isdigit():
                    group: Group = await rq.get_group_id(id_=int(group_id))
                    if group:
                        count += 1
                        text += f'{count}. {group.title}\n'
            str_group_ids += active_subscribe.group_id_list
        groups_partner: list[Group] = await rq.get_group_partner(tg_id_partner=callback.from_user.id)
        for group in groups_partner:
            str_group_ids += f',{group.id}'
        await state.update_data(str_group_ids=str_group_ids)
        await callback.message.edit_text(text="Пришлите текст заявки для размещения в группах",
                                         reply_markup=None)
        await state.set_state(ManagerState.text_post)
    else:
        # если нет активной подписки
        if not subscribes or not active_subscribe:
            list_groups: list = await rq.get_group_partner_not(tg_id_partner=callback.from_user.id)
            if list_groups:
                await callback.message.answer(text='Действие вашей подписки завершено,'
                                                   ' выберите группу и продлите подписку',
                                              reply_markup=kb.keyboards_list_group(list_group=list_groups,
                                                                                   block=0))
            else:
                await callback.message.answer(text='Пока в бота не добавлены группы,'
                                                   ' в которых вы могли приобрести подписки')
        else:
            str_group_ids = ''
            for active_subscribe in list_active_subscribe:
                str_group_ids += active_subscribe.group_id_list
            await state.update_data(str_group_ids=str_group_ids)
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
    preview = 'Предпросмотр поста для публикации:\n\n'
    await message.answer(text=f"{preview}{data['text_post']}",
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
    preview = 'Предпросмотр поста для публикации:\n\n'
    await callback.message.edit_text(text=f"{preview}{data['text_post']}",
                                     reply_markup=kb.keyboard_show_post_(user_tg_id=callback.from_user.id))
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
    # subscribes: list[Subscribe] = await rq.get_subscribes_user(tg_id=callback.from_user.id)
    # last_subscribe = subscribes[-1]
    # list_ids_group: list = last_subscribe.group_id_list.split(',')
    data = await state.get_data()
    str_group_ids: str = data['str_group_ids']
    list_ids_group: list = list(set(str_group_ids.split(',')))
    message_chat = []
    posts = await rq.get_posts()
    count_posts = len([post for post in posts])
    post_managers = await rq.get_post_manager(tg_id_manager=callback.from_user.id)
    count_post_manager = len([post for post in post_managers])
    info_user: User = await rq.get_user(tg_id=callback.from_user.id)
    data_reg = info_user.data_reg
    current_date = datetime.now()
    data_reg_datetime = datetime(year=int(data_reg.split('-')[-1]),
                                 month=int(data_reg.split('-')[1]),
                                 day=int(data_reg.split('-')[0]))
    count_day = (current_date - data_reg_datetime).days
    info_autor = f'№ {count_posts} 👉 <a href="tg://user?id={callback.from_user.id}">{callback.from_user.username}</a>\n' \
                 f'Создано заказов {count_post_manager}\n' \
                 f'Зарегистрирован {count_day} день назад\n\n'
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
                                              text=f"{info_autor}{data['text_post']}\n"
                                                   f"По всем вопросам пишите <a href='tg://user?id="
                                                   f"{callback.from_user.id}'>"
                                                   f"{callback.from_user.username}</a>",
                                              reply_markup=kb.keyboard_post_(
                                                  user_tg_id=callback.message.chat.id))
            else:
                post = await bot.send_message(chat_id=group.group_id,
                                              text=f"{info_autor}{data['text_post']}\n"
                                                   f"По всем вопросам пишите <a href='tg://user?id="
                                                   f"{callback.from_user.id}'>"
                                                   f"{callback.from_user.username}</a>",
                                              reply_markup=kb.keyboard_post(
                                                  user_tg_id=callback.message.chat.id,
                                                  location=data['location']))
            message_chat.append(f'{group.group_id}!{post.message_id}')
            await callback.message.answer(text=f'Пост опубликован в группе {group.title}')
    await callback.message.edit_text(text=f'Публикация поста по списку групп завершена',
                                     reply_markup=None)
    posts_chat_message = ','.join(message_chat)
    data_ = {'tg_id_manager': callback.message.chat.id, 'posts_text': data['text_post'],
             'posts_chat_message': posts_chat_message, 'post_date': datetime.now().strftime('%d-%m-%Y %H:%M')}
    await rq.add_post(data=data_)


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
                                     reply_markup=kb.keyboard_user_publish_one())


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