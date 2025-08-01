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
import re
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


@router.message(F.text == 'Создать пост ✏️')
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
    # проверка на текущие активные подписки
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
        # проходим по оплаченным активным тарифам и формируем список групп для возможности публикации объявлений в них
        text = ''
        str_group_ids = ''
        for active_subscribe in list_active_subscribe:
            # если партнер заблокирован во всех группах бота, то прерываем проход по тприфам
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
        # получаем список групп пользователя и выводим список его групп
        groups_partner: list[Group] = await rq.get_group_partner(tg_id_partner=message.from_user.id)
        self_group_text = f'Группы в которых вы можете размещать заявки:\n'
        count = 0
        for group in groups_partner:
            count += 1
            str_group_ids += f',{group.id}'
            self_group_text += f'{count}. <b>{group.title}</b>\n'
        await state.update_data(str_group_ids=str_group_ids)
        #!!! await message.answer(text=f'{text}\n\n{self_group_text}',
        #                      reply_markup=kb.keyboard_user_publish())
        await message.answer(text=f'{text}\n\n{self_group_text}',
                             reply_markup=kb.keyboard_user_publish_new())
    else:
        # пользователь не является администратором или партнером
        # если нет активных подписок у пользователя
        if not subscribes or not active_subscribe:
            # получаем список групп для покупки подписки
            list_groups: list = await rq.get_group_partner_not(tg_id_partner=message.from_user.id)
            # предлагаем ему приобрести один из тарифов
            if list_groups:
                await message.answer(text='У вас нет активных подписок, выберите группу и продлите подписку',
                                     reply_markup=kb.keyboards_list_group(list_group=list_groups,
                                                                          block=0))
            else:
                await message.answer(text='Пока в бота не добавлены группы, в которых вы могли приобрести подписки')
        else:
            # проходим по списку активных подписок
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
                # получаем список групп в тарифе, и отмечаем группы в которых пользователь заблокирован
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
            await message.answer(text=f"{text}Пришлите текст заявки для размещения в группах",
                                 reply_markup=None)
            await state.set_state(ManagerState.text_post)
            # await message.answer(text=text,
            #                      reply_markup=kb.keyboard_user_publish())


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
    logging.info(f'process_publish_post: {callback.from_user.id}')
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
    logging.info(f'get_text_post: {message.from_user.id}')
    if message.text in ['Приобрести подписку 🧾', 'Создать пост ✏️', 'Редактировать пост 🗒', 'Удалить пост ❌']:
        await message.answer(text='Создание поста отменено')
        await state.set_state(state=None)
        return
    await state.update_data(text_post=message.html_text)
    # await message.answer(text='Пришлите ссылку на местоположение',
    #                      reply_markup=kb.keyboard_pass_location())
    # await state.set_state(ManagerState.location)
    await state.update_data(location='')
    data = await state.get_data()
    data_ = {'tg_id_manager': message.from_user.id,
             'posts_text': data['text_post'],
             'post_location': '',
             'post_date_create': datetime.now().strftime('%d-%m-%Y %H:%M'),
             'status': rq.StatusPost.create}
    post_id: int = await rq.add_post(data=data_)
    await state.update_data(post_id=post_id)
    preview = 'Предпросмотр поста для публикации:\n\n'
    await message.answer(text=f"{preview}{data['text_post']}",
                         reply_markup=kb.keyboard_show_post_(user_tg_id=message.from_user.id))
    await state.set_state(state=None)


# @router.message(F.text, StateFilter(ManagerState.location))
# @error_handler
# async def get_location(message: Message, state: FSMContext, bot: Bot):
#     """
#     Получаем локацию
#     :param message:
#     :param state:
#     :param bot:
#     :return:
#     """
#     logging.info(f'get_text_post: {message.from_user.id}')
#     if not validators.url(message.text):
#         await message.answer(text='Ссылка не валидна, проверьте правильность введенных данных')
#         return
#     await state.update_data(location=message.text)
#     data = await state.get_data()
#     data_ = {'tg_id_manager': message.from_user.id,
#              'posts_text': data['text_post'],
#              'post_location': message.text,
#              'post_date_create': datetime.now().strftime('%d-%m-%Y %H:%M'),
#              'status': rq.StatusPost.create}
#     post_id: int = await rq.add_post(data=data_)
#     await state.update_data(post_id=post_id)
#     preview = 'Предпросмотр поста для публикации:\n\n'
#     await message.answer(text=f"{preview}{data['text_post']}",
#                          reply_markup=kb.keyboard_show_post(manager_tg_id=message.from_user.id, location=message.text))
#     await state.set_state(state=None)
#
#
# @router.callback_query(F.data == 'pass_location')
# @error_handler
# async def process_pass_location(callback: CallbackQuery, state: FSMContext, bot: Bot):
#     """
#     Публикация поста
#     :param callback: int(callback.data.split('_')[1]) номер блока для вывода
#     :param state:
#     :param bot:
#     :return:
#     """
#     logging.info(f'process_publish_post: {callback.from_user.id}')
#     await state.update_data(location='')
#     data = await state.get_data()
#     data_ = {'tg_id_manager': callback.from_user.id,
#              'posts_text': data['text_post'],
#              'post_location': '',
#              'post_date_create': datetime.now().strftime('%d-%m-%Y %H:%M'),
#              'status': rq.StatusPost.create}
#     post_id: int = await rq.add_post(data=data_)
#     await state.update_data(post_id=post_id)
#     preview = 'Предпросмотр поста для публикации:\n\n'
#     try:
#         await callback.message.edit_text(text=f"{preview}{data['text_post']}",
#                                          reply_markup=kb.keyboard_show_post_(user_tg_id=callback.from_user.id))
#     except:
#         await callback.message.edit_text(text=f"{preview}{data['text_post']}.",
#                                          reply_markup=kb.keyboard_show_post_(user_tg_id=callback.from_user.id))
#     await state.set_state(state=None)
#     await callback.answer()


@router.callback_query(F.data == 'publishpost')
@error_handler
async def publish_post_press_button(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Публикация поста
    :param callback: publishpost
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'publish_post_press_button: {callback.from_user.id}')
    data = await state.get_data()
    post_id = data['post_id']
    await publish_post(id_post=post_id, callback=callback, bot=bot)
    try:
        await callback.message.edit_text(text='Пост успешно опубликован',
                                         reply_markup=None)
    except:
        await callback.message.edit_text(text='Пост успешно опубликован.',
                                         reply_markup=None)


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
    logging.info(f'publish_post_cancel: {callback.from_user.id}')
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
    logging.info(f'publish_post_autopost: {callback.from_user.id}')
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
    logging.info(f'publish_post_autopost: {callback.from_user.id}')
    action = callback.data.split('_')[-1]
    await callback.message.edit_text(text='Пришлите время для автопубликации, в формате: чч:мм',
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
            await callback.message.answer(f'Пост будет опубликован {info_post.post_autopost_2}')
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
            await callback.message.answer(f'Пост будет опубликован {info_post.post_autopost_3}')
        if publish_flag:
            await publish_post(id_post=id_post_change, callback=callback, bot=bot)


@router.message(F.text, StateFilter(ManagerState.auto_post_1))
@router.message(F.text, StateFilter(ManagerState.auto_post_2))
@router.message(F.text, StateFilter(ManagerState.auto_post_3))
@error_handler
async def change_post_autoposting(message: Message, state: FSMContext, bot: Bot):
    """
    Обновление даты автопостинга
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info('change_post_autoposting')
    pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
    time_autoposting = message.text
    if re.match(pattern, time_autoposting):
        await state.set_state(state=None)
        data = await state.get_data()
        post_id = data['post_id']
        num_autoposting = data['num_autoposting']
        await rq.set_post_autoposting_id(id_post=post_id, autoposting=time_autoposting, num=num_autoposting)

        info_post: Post = await rq.get_post_id(id_=post_id)
        await message.answer(text='Выберите раздел',
                             reply_markup=kb.keyboard_post_autoposting(info_post=info_post))
    else:
        await message.answer(text='Время автопубликации указано некорректно. Пришлите время для автопубликации,'
                                  ' в формате: чч:мм',
                             reply_markup=kb.keyboard_delete_autoposting())