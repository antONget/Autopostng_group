from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from aiogram.enums.chat_member_status import ChatMemberStatus

from database.models import Subscribe, Frame, Group, User, Post
from database import requests as rq
from filter.user_filter import check_role
import logging
from datetime import datetime, timedelta


async def get_user_group_for_publish_task(user_tg_id: int, bot: Bot) -> str:
    """
    Проверка наличия возможности публикация в группах
    :param user_tg_id:
    :param bot:
    :return:
    """
    logging.info(f'get_user_group_for_publish_task')
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


async def publish_post_task(id_post: int, user_tg_id: int, bot: Bot):
    """
    Публикация поста
    :param id_post:
    :param user_tg_id:
    :param bot:
    :return:
    """
    logging.info(f'publish_post_task')
    info_post: Post = await rq.get_post_id(id_=id_post)
    str_group_ids: str = await get_user_group_for_publish_task(user_tg_id=user_tg_id,
                                                               bot=bot)
    list_ids_group: list = list(set(str_group_ids.split(',')))
    message_chat = []
    posts = await rq.get_posts()
    count_posts = len([post for post in posts])
    post_managers = await rq.get_post_manager(tg_id_manager=user_tg_id)
    count_post_manager = len([post for post in post_managers])
    info_user: User = await rq.get_user(tg_id=user_tg_id)
    data_reg = info_user.data_reg
    current_date = datetime.now()
    data_reg_datetime = datetime(year=int(data_reg.split('-')[-1]),
                                 month=int(data_reg.split('-')[1]),
                                 day=int(data_reg.split('-')[0]))
    count_day = (current_date - data_reg_datetime).days
    user: User = await rq.get_user(tg_id=user_tg_id)
    info_autor = f'№ {count_posts} 👉 <a href="tg://user?id={user_tg_id}">{user.username}</a>\n' \
                 f'Создано заказов {count_post_manager}\n' \
                 f'Зарегистрирован {count_day} день назад\n\n'
    for i, group_id in enumerate(list_ids_group):
        group: Group = await rq.get_group_id(id_=group_id)
        if not group:
            continue
        bot_ = await bot.get_chat_member(group.group_id, bot.id)
        if bot_.status != ChatMemberStatus.ADMINISTRATOR:
            await bot.send_message(chat_id=user_tg_id,
                                   text=f'Бот не может опубликовать пост в группу <b>{group.title}</b>'
                                        f' так как не является администратором, обратитесь к'
                                        f' <a href="tg://user?id={group.tg_id_partner}">владельцу</a> ')
        else:
            if info_post.post_location == '':
                post = await bot.send_message(chat_id=group.group_id,
                                              text=f"{info_autor}{info_post.posts_text}\n"
                                                   f"По всем вопросам пишите <a href='tg://user?id="
                                                   f"{user_tg_id}'>"
                                                   f"{user.username}</a>",
                                              reply_markup=keyboard_post_link_manager(
                                                  user_tg_id=user_tg_id))
            else:
                post = await bot.send_message(chat_id=group.group_id,
                                              text=f"{info_autor}{info_post.posts_text}\n"
                                                   f"По всем вопросам пишите <a href='tg://user?id="
                                                   f"{user_tg_id}'>"
                                                   f"{user.username}</a>",
                                              reply_markup=keyboard_post_link_manager_and_location(
                                                  user_tg_id=user_tg_id,
                                                  location=info_post.post_location))
            message_chat.append(f'{group.group_id}!{post.message_id}')
            await bot.send_message(chat_id=user_tg_id,
                                   text=f'Пост опубликован в группе {group.title}')
    await bot.send_message(chat_id=user_tg_id,
                           text=f'Публикация поста по списку групп завершена',
                           reply_markup=None)
    posts_chat_message = ','.join(message_chat)
    await rq.set_post_posts_chat_message_id(id_post=id_post,
                                            posts_chat_message=posts_chat_message)
    await rq.set_post_status(id_post=id_post,
                             status=rq.StatusPost.publish)


async def scheduler_send_post_for_group(bot: Bot):
    list_posts: list[Post] = await rq.get_posts()
    current_time = datetime.now().strftime('%H:%M')
    for info_post in list_posts:
        if current_time == info_post.post_autopost_1:
            await publish_post_task(id_post=info_post.id,
                                    user_tg_id=info_post.tg_id_manager,
                                    bot=bot)
        if current_time == info_post.post_autopost_2:
            await publish_post_task(id_post=info_post.id,
                                    user_tg_id=info_post.tg_id_manager,
                                    bot=bot)
        if current_time == info_post.post_autopost_3:
            await publish_post_task(id_post=info_post.id,
                                    user_tg_id=info_post.tg_id_manager,
                                    bot=bot)


async def scheduler_restricted(bot: Bot):
    list_subscribe: list[Subscribe] = await rq.get_subscribes_all()
    for subscribe in list_subscribe:
        date_format = '%d-%m-%Y %H:%M'
        current_date = datetime.now().strftime(date_format)
        delta_time = (datetime.strptime(subscribe.date_completion, date_format) -
                      datetime.strptime(current_date, date_format))
        if delta_time.days < 0:
            info_frame: Frame = await rq.get_frame_id(id_=subscribe.frame_id)
            for item in info_frame.list_id_group.split(','):
                group_info: Group = await rq.get_group_id(id_=item)
                if group_info:
                    await bot.restrict_chat_member(
                        chat_id=group_info.group_id,
                        user_id=int(subscribe.tg_id),
                        until_date=datetime.now() + timedelta(seconds=10),
                        permissions=ChatPermissions(
                            can_send_messages=False,
                            can_send_media_messages=False
                        )
                    )
