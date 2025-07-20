from aiogram import Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums.chat_member_status import ChatMemberStatus

from database.models import Subscribe, Frame, Group, User, Post
from database import requests as rq
from filter.user_filter import check_role

import logging
from datetime import datetime


async def get_user_group_for_publish(user_tg_id: int, bot: Bot) -> str:
    """
    Получаем список групп в которых пользователь имеет право публиковать посты
    :param user_tg_id:
    :param bot:
    :return:
    """
    logging.info(f'process_select_group_manager')
    subscribes: list[Subscribe] = await rq.get_subscribes_user(tg_id=user_tg_id)
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
    str_group_ids = ''
    if await check_role(tg_id=user_tg_id, role=rq.UserRole.admin) or\
            await check_role(tg_id=user_tg_id, role=rq.UserRole.partner):
        for active_subscribe in list_active_subscribe:
            if await rq.get_blacklist_group_all(tg_id=user_tg_id):
                break
            info_frame: Frame = await rq.get_frame_id(id_=active_subscribe.frame_id)
            if not await rq.get_blacklist_group(tg_id_partner=info_frame.tg_id_creator,
                                                tg_id=user_tg_id):
                str_group_ids += active_subscribe.group_id_list
        groups_partner: list[Group] = await rq.get_group_partner(tg_id_partner=user_tg_id)
        for group in groups_partner:
            str_group_ids += f',{group.id}'
    else:
        if not active_subscribe:
            pass
        else:
            for active_subscribe in list_active_subscribe:
                if await rq.get_blacklist_group_all(tg_id=user_tg_id):
                    await bot.send_message(chat_id=user_tg_id,
                                           text='Вы заблокированы во всех группа бота, кроме своих')
                    break
                info_frame: Frame = await rq.get_frame_id(id_=active_subscribe.frame_id)
                if not await rq.get_blacklist_group(tg_id_partner=info_frame.tg_id_creator,
                                                    tg_id=user_tg_id):
                    str_group_ids += active_subscribe.group_id_list

    return str_group_ids


def keyboard_post_link_manager(user_tg_id: int) -> InlineKeyboardMarkup:
    logging.info("keyboard_post_link_manager")
    button_1 = InlineKeyboardButton(text='👤ОТКЛИКНУТЬСЯ 👤',  url=f'tg://user?id={user_tg_id}')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]])
    return keyboard


def keyboard_post_link_manager_and_location(user_tg_id: int, location: str) -> InlineKeyboardMarkup:
    logging.info("keyboard_post_link_manager_and_location")
    button_1 = InlineKeyboardButton(text='👤ОТКЛИКНУТЬСЯ 👤',  url=f'tg://user?id={user_tg_id}')
    button_2 = InlineKeyboardButton(text='МЕСТОПОЛОЖЕНИЕ', url=location)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2]])
    return keyboard


async def publish_post(id_post: int, callback: CallbackQuery, bot: Bot):
    """
    Публикация поста
    :param id_post:
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param bot:
    :return:
    """
    logging.info(f'publish_post: {callback.from_user.id}')
    info_post: Post = await rq.get_post_id(id_=id_post)
    str_group_ids: str = await get_user_group_for_publish(user_tg_id=callback.from_user.id, bot=bot)
    list_ids_group: list = list(set(str_group_ids.split(',')))
    message_chat = []
    # posts = await rq.get_posts()
    # count_posts = [post for post in posts]
    # post_managers = await rq.get_post_manager(tg_id_manager=callback.from_user.id)
    # count_post_manager = len([post for post in post_managers])
    info_user: User = await rq.get_user(tg_id=callback.from_user.id)
    data_reg = info_user.data_reg
    current_date = datetime.now()
    data_reg_datetime = datetime(year=int(data_reg.split('-')[-1]),
                                 month=int(data_reg.split('-')[1]),
                                 day=int(data_reg.split('-')[0]))
    count_day = (current_date - data_reg_datetime).days
    info_autor = f'№ {id_post} 👉 <a href="tg://user?id={callback.from_user.id}">' \
                 f'{callback.from_user.username}</a>\n' \
                 f'Создано заказов {info_user.count_order}\n' \
                 f'Зарегистрирован {count_day} день назад\n\n'
    check_publish = False
    for i, group_id in enumerate(list_ids_group):
        group: Group = await rq.get_group_id(id_=group_id)
        if not group:
            continue
        bot_ = await bot.get_chat_member(chat_id=group.group_id, user_id=bot.id)
        if bot_.status != ChatMemberStatus.ADMINISTRATOR:
            await callback.message.answer(text=f'Бот не может опубликовать пост в группу <b>{group.title}</b>'
                                               f' так как не является администратором, обратитесь к'
                                               f' <a href="tg://user?id={group.tg_id_partner}">владельцу</a> ')
        else:
            if info_post.post_location == '':
                post = await bot.send_message(chat_id=group.group_id,
                                              text=f"{info_autor}{info_post.posts_text}\n"
                                                   f"По всем вопросам пишите <a href='tg://user?id="
                                                   f"{callback.from_user.id}'>"
                                                   f"{callback.from_user.username}</a>",
                                              reply_markup=keyboard_post_link_manager(
                                                  user_tg_id=callback.from_user.id))
            else:
                post = await bot.send_message(chat_id=group.group_id,
                                              text=f"{info_autor}{info_post.posts_text}\n"
                                                   f"По всем вопросам пишите <a href='tg://user?id="
                                                   f"{callback.from_user.id}'>"
                                                   f"{callback.from_user.username}</a>",
                                              reply_markup=keyboard_post_link_manager_and_location(
                                                  user_tg_id=callback.from_user.id,
                                                  location=info_post.post_location))
            check_publish = True
            message_chat.append(f'{group.group_id}!{post.message_id}')
            await callback.message.answer(text=f'Пост опубликован в группе {group.title}')
    await callback.message.answer(text=f'Публикация поста по списку групп завершена',
                                  reply_markup=None)
    if check_publish:
        posts_chat_message = ','.join(message_chat)
        await rq.set_post_posts_chat_message_id(id_post=id_post,
                                                posts_chat_message=posts_chat_message)
        await rq.set_post_status(id_post=id_post,
                                 status=rq.StatusPost.publish)
        await rq.set_count_order_user(id_user=callback.from_user.id)
