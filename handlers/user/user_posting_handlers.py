from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter
from aiogram.enums.chat_member_status import ChatMemberStatus

from utils.error_handling import error_handler
# from utils.scheduler_task import scheduler_task_cron
from filter.user_filter import check_role
from database import requests as rq
from keyboards.user import user_posting_keyboards as kb
from config_data.config import Config, load_config
from database.models import User, Frame, Group, Subscribe, Post
from handlers.user.scheduler_post import publish_post
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
    auto_post_1 = State()
    auto_post_2 = State()
    auto_post_3 = State()


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
            if await rq.get_blacklist_group_all(tg_id=message.from_user.id):
                await message.answer(text='Вы заблокированы во всех группа бота, кроме своих')
                break
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
                        if await rq.get_blacklist_group(tg_id_partner=group.tg_id_partner,
                                                        tg_id=message.from_user.id):
                            text += f'{count}. <b>{group.title}</b> ❌\n'
                        else:
                            text += f'{count}. <b>{group.title}</b>\n'
            if not await rq.get_blacklist_group(tg_id_partner=info_frame.tg_id_creator,
                                                tg_id=message.from_user.id):
                str_group_ids += active_subscribe.group_id_list
        groups_partner: list[Group] = await rq.get_group_partner(tg_id_partner=message.from_user.id)
        self_group_text = f'Группы в которых вы можете размещать заявки:\n'
        count = 0
        for group in groups_partner:
            count += 1
            str_group_ids += f',{group.id}'
            self_group_text += f'{count}. <b>{group.title}</b>\n'
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
                if await rq.get_blacklist_group_all(tg_id=message.from_user.id):
                    await message.answer(text='Вы заблокированы во всех группа бота, кроме своих')
                    break
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
                            if await rq.get_blacklist_group(tg_id_partner=group.tg_id_partner,
                                                            tg_id=message.from_user.id):
                                text += f'{count}. <b>{group.title}</b> ❌\n'
                            else:
                                text += f'{count}. <b>{group.title}</b>\n'
                text += '\n'
                if not await rq.get_blacklist_group(tg_id_partner=info_frame.tg_id_creator,
                                                    tg_id=message.from_user.id):
                    str_group_ids += active_subscribe.group_id_list
            if not str_group_ids:
                await message.answer(text=f'{text}\n\nУ вас нет доступных групп для публикаций')
                return
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
    data_ = {'tg_id_manager': message.chat.id,
             'posts_text': data['text_post'],
             'post_location': message.text,
             'post_date_create': datetime.now().strftime('%d-%m-%Y %H:%M'),
             'status': rq.StatusPost.create}
    post_id: int = await rq.add_post(data=data_)
    await state.update_data(post_id=post_id)
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
    await state.update_data(location='')
    data = await state.get_data()
    data_ = {'tg_id_manager': callback.message.chat.id,
             'posts_text': data['text_post'],
             'post_location': '',
             'post_date_create': datetime.now().strftime('%d-%m-%Y %H:%M'),
             'status': rq.StatusPost.create}
    post_id: int = await rq.add_post(data=data_)
    await state.update_data(post_id=post_id)
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
    :param callback: publishpost
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'publish_post: {callback.message.chat.id}')
    data = await state.get_data()
    post_id = data['post_id']
    await publish_post(id_post=post_id, callback=callback, state=state, bot=bot)
    # str_group_ids: str = data['str_group_ids']
    # list_ids_group: list = list(set(str_group_ids.split(',')))
    # message_chat = []
    # posts = await rq.get_posts()
    # count_posts = len([post for post in posts])
    # post_managers = await rq.get_post_manager(tg_id_manager=callback.from_user.id)
    # count_post_manager = len([post for post in post_managers])
    # info_user: User = await rq.get_user(tg_id=callback.from_user.id)
    # data_reg = info_user.data_reg
    # current_date = datetime.now()
    # data_reg_datetime = datetime(year=int(data_reg.split('-')[-1]),
    #                              month=int(data_reg.split('-')[1]),
    #                              day=int(data_reg.split('-')[0]))
    # count_day = (current_date - data_reg_datetime).days
    # info_autor = f'№ {count_posts} 👉 <a href="tg://user?id={callback.from_user.id}">{callback.from_user.username}</a>\n' \
    #              f'Создано заказов {count_post_manager}\n' \
    #              f'Зарегистрирован {count_day} день назад\n\n'
    # for i, group_id in enumerate(list_ids_group):
    #     group: Group = await rq.get_group_id(id_=group_id)
    #     if not group:
    #         continue
    #     bot_ = await bot.get_chat_member(group.group_id, bot.id)
    #     if bot_.status != ChatMemberStatus.ADMINISTRATOR:
    #         await callback.message.answer(text=f'Бот не может опубликовать пост в группу <b>{group.title}</b>'
    #                                            f' так как не является администратором, обратитесь к'
    #                                            f' <a href="tg://user?id={group.tg_id_partner}">владельцу</a> ')
    #     else:
    #         if not data['location']:
    #             post = await bot.send_message(chat_id=group.group_id,
    #                                           text=f"{info_autor}{data['text_post']}\n"
    #                                                f"По всем вопросам пишите <a href='tg://user?id="
    #                                                f"{callback.from_user.id}'>"
    #                                                f"{callback.from_user.username}</a>",
    #                                           reply_markup=kb.keyboard_post_(
    #                                               user_tg_id=callback.message.chat.id))
    #         else:
    #             post = await bot.send_message(chat_id=group.group_id,
    #                                           text=f"{info_autor}{data['text_post']}\n"
    #                                                f"По всем вопросам пишите <a href='tg://user?id="
    #                                                f"{callback.from_user.id}'>"
    #                                                f"{callback.from_user.username}</a>",
    #                                           reply_markup=kb.keyboard_post(
    #                                               user_tg_id=callback.message.chat.id,
    #                                               location=data['location']))
    #         message_chat.append(f'{group.group_id}!{post.message_id}')
    #         await callback.message.answer(text=f'Пост опубликован в группе {group.title}')
    # await callback.message.edit_text(text=f'Публикация поста по списку групп завершена',
    #                                  reply_markup=None)
    # posts_chat_message = ','.join(message_chat)
    # await rq.set_post_posts_chat_message_id(id_post=data['post_id'],
    #                                         posts_chat_message=posts_chat_message)
    # await rq.set_post_status(id_post=data['post_id'],
    #                          status=rq.StatusPost.publish)


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
    await callback.answer(text='Публикация поста отменена',
                          show_alert=True)
    await callback.message.edit_text(text='Выберите группу для размещение заявок',
                                     reply_markup=kb.keyboard_user_publish_one())


@router.callback_query(F.data == 'autopost')
@error_handler
async def publish_post_autopost(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Автопостинг
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'publish_post_autopost: {callback.message.chat.id}')
    data = await state.get_data()
    id_post_change = data['post_id']
    info_post: Post = await rq.get_post_id(id_=id_post_change)
    await callback.message.edit_text(text='Выберите раздел',
                                     reply_markup=kb.keyboard_post_autoposting(info_post=info_post))


@router.callback_query(F.data.startswith('addautopost'))
@error_handler
async def publish_post_autopost(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Автопостинг
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'publish_post_autopost: {callback.message.chat.id}')
    action = callback.data.split('_')[-1]
    await callback.message.edit_text(text='Пришлите время для автопубликации, в формате: дд.мм.гггг чч:мм',
                                     reply_markup=kb.keyboard_delete_autoposting())
    if action == '1':
        await state.set_state(ManagerState.auto_post_1)
        await state.update_data(num_autoposting=action)
    elif action == '2':
        await state.set_state(ManagerState.auto_post_2)
        await state.update_data(num_autoposting=action)
    elif action == '3':
        await state.set_state(ManagerState.auto_post_3)
        await state.update_data(num_autoposting=action)
    elif action == 'confirm':
        data = await state.get_data()
        id_post_change = data['post_id']
        info_post: Post = await rq.get_post_id(id_=id_post_change)
        publish_flag = True
        if info_post.post_autopost_1:
            publish_flag = False
            # hour = int(info_post.post_autopost_1.split(' ')[1].split(':')[0])
            # minute = int(info_post.post_autopost_1.split(' ')[1].split(':')[1])
            # year = int(info_post.post_autopost_1.split(' ')[0].split('.')[-1])
            # month = int(info_post.post_autopost_1.split(' ')[0].split('.')[-2])
            # day = int(info_post.post_autopost_1.split(' ')[0].split('.')[0])
            # scheduler = await scheduler_task_cron()
            # scheduler.add_job(func=publish_post, trigger='cron', year=year, month=month, day=day, hour=hour,
            #                   minute=minute,
            #                   args=(id_post_change, callback, state, bot))
            await callback.message.answer(f'Пост будет опубликован {info_post.post_autopost_1}')
        if info_post.post_autopost_2:
            publish_flag = False
            # hour = int(info_post.post_autopost_2.split(' ')[1].split(':')[0])
            # minute = int(info_post.post_autopost_2.split(' ')[1].split(':')[1])
            # year = int(info_post.post_autopost_2.split(' ')[0].split('.')[-1])
            # month = int(info_post.post_autopost_2.split(' ')[0].split('.')[-2])
            # day = int(info_post.post_autopost_2.split(' ')[0].split('.')[0])
            # scheduler = await scheduler_task_cron()
            # scheduler.add_job(func=publish_post, trigger='cron', year=year, month=month, day=day, hour=hour,
            #                   minute=minute,
            #                   args=(id_post_change, callback, state, bot))
            await callback.message.answer(f'Пост будет опубликован {info_post.post_autopost_1}')
        if info_post.post_autopost_3:
            publish_flag = False
            # hour = int(info_post.post_autopost_3.split(' ')[1].split(':')[0])
            # minute = int(info_post.post_autopost_3.split(' ')[1].split(':')[1])
            # year = int(info_post.post_autopost_3.split(' ')[0].split('.')[-1])
            # month = int(info_post.post_autopost_3.split(' ')[0].split('.')[-2])
            # day = int(info_post.post_autopost_3.split(' ')[0].split('.')[0])
            # scheduler = await scheduler_task_cron()
            # scheduler.add_job(func=publish_post, trigger='cron', year=year, month=month, day=day, hour=hour,
            #                   minute=minute,
            #                   args=(id_post_change, callback, state, bot))
            await callback.message.answer(f'Пост будет опубликован {info_post.post_autopost_1}')
        if publish_flag:
            await publish_post(id_post=id_post_change, callback=callback, state=state, bot=bot)