from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter
from aiogram.enums.chat_member_status import ChatMemberStatus

from utils.error_handling import error_handler
from database import requests as rq
from keyboards.user import my_publish_keyboards as kb
from config_data.config import Config, load_config
from database.models import Post, User, Group
from handlers.user.scheduler_post import publish_post

from datetime import datetime
import validators
import re
import logging


config: Config = load_config()
router = Router()
router.message.filter(F.chat.type == "private")


class ChangePost(StatesGroup):
    text_post_change = State()
    location_post_change = State()
    autoposting_1_change = State()
    autoposting_2_change = State()
    autoposting_3_change = State()


@router.message(F.text == 'Опубликованные посты 📝')
@error_handler
async def process_my_publish(message: Message, state: FSMContext, bot: Bot):
    """
    Выбор раздела "Опубликованные посты"
    :param message
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_edit_post: {message.from_user.id}')
    await message.answer(text='Выберите раздел',
                         reply_markup=kb.keyboard_user_publish_new())


@router.callback_query(F.data == 'post_publish')
@error_handler
async def process_my_publish(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Выбор раздела "Опубликованные посты"
    :param callback: post_publish
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_edit_post: {callback.from_user.id}')
    list_posts: list[Post] = await rq.get_posts_manager_last_day(tg_id_manager=callback.from_user.id)
    if not list_posts:
        await callback.message.edit_text(text='Нет постов для редактирования.',
                                         reply_markup=None)
        await callback.answer()
        return
    else:
        await callback.message.delete()
        for item_post in list_posts:
            await callback.message.answer(text=item_post.posts_text,
                                          reply_markup=kb.keyboard_my_publish_post(post_id=item_post.id))
    await callback.answer()


@router.callback_query(F.data.startswith('mypost_edit'))
@error_handler
async def process_select_edit_mypost(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Редактирование поста
    :param callback: editpost_{id_post}
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_select_edit_mypost: {callback.from_user.id}')
    id_post = int(callback.data.split('_')[-1])
    await state.update_data(id_post_change=id_post)
    info_post: Post = await rq.get_post_id(id_=id_post)
    text_publish = info_post.posts_text
    await callback.message.edit_text(text=text_publish,
                                     reply_markup=kb.keyboard_change_my_publish_post())
    await callback.answer()


@router.callback_query(F.data.startswith('mypost_changing_'))
@error_handler
async def process_mypost_changing(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Получаем какое поле объявления необходимо изменить
    :param callback: {changing_post_text, changing_post_location, changing_post_autoposting,
     changing_post_confirm, changing_post_publish}
    :param state:
    :param bot:
    :return:
    """
    logging.info('process_change_post')
    column_post = callback.data.split('_')[-1]
    if column_post == 'text':
        await callback.message.edit_text(text='Пришлите текст заявки для размещения в группах')
        await state.set_state(ChangePost.text_post_change)
    elif column_post == 'location':
        await callback.message.edit_text(text='Пришлите ссылку на локацию или удалите локацию',
                                         reply_markup=kb.keyboard_delete_location())
        await state.set_state(ChangePost.location_post_change)
    # elif column_post == 'autoposting':
    #     data = await state.get_data()
    #     id_post_change = data['id_post_change']
    #     info_post: Post = await rq.get_post_id(id_=id_post_change)
    #     await callback.message.edit_text(text='Выберите раздел',
    #                                      reply_markup=kb.keyboard_change_post_autoposting(info_post=info_post))
    elif column_post == 'publish':
        data = await state.get_data()
        id_post_change = data['id_post_change']
        info_post: Post = await rq.get_post_id(id_=id_post_change)
        publish_flag = True
        if info_post.post_autopost_1:
            publish_flag = False
            await callback.message.answer(f'Пост будет опубликован {info_post.post_autopost_1}')
        if info_post.post_autopost_2:
            publish_flag = False
            await callback.message.answer(f'Пост будет опубликован {info_post.post_autopost_2}')
        if info_post.post_autopost_3:
            publish_flag = False
            await callback.message.answer(f'Пост будет опубликован {info_post.post_autopost_3}')
        if publish_flag:
            await publish_post(id_post=id_post_change, callback=callback, bot=bot)
    elif column_post == 'confirm':
        data = await state.get_data()
        id_post_change = data['id_post_change']
        await change_publish_post(post_id=id_post_change, callback=callback, bot=bot)
    await callback.answer()


@router.message(F.text, StateFilter(ChangePost.text_post_change))
@error_handler
async def get_text_change_mypost(message: Message, state: FSMContext, bot: Bot):
    """
    Получаем обновленный текст объявления
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'get_text_change_mypost: {message.from_user.id}')
    text_change = message.text
    data = await state.get_data()
    id_post_change = data['id_post_change']
    await rq.set_post_text_id(id_post=id_post_change,
                              text=text_change)
    info_post: Post = await rq.get_post_id(id_=id_post_change)
    text_publish = info_post.posts_text
    await message.answer(text=text_publish,
                         reply_markup=kb.keyboard_change_my_publish_post())
    await state.set_state(state=None)


@router.message(F.text, StateFilter(ChangePost.location_post_change))
@error_handler
async def get_location_mypost(message: Message, state: FSMContext, bot: Bot):
    """
    Получаем локацию
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'get_location_mypost: {message.from_user.id}')
    if not validators.url(message.text):
        await message.answer(text='Ссылка не валидна, проверьте правильность введенных данных')
        return
    location_change = message.text
    data = await state.get_data()
    id_post_change = data['id_post_change']
    await rq.set_post_location_id(id_post=id_post_change,
                                  location=location_change)
    info_post: Post = await rq.get_post_id(id_=id_post_change)
    text_publish = info_post.posts_text
    await message.answer(text=text_publish,
                         reply_markup=kb.keyboard_change_my_publish_post())
    await state.set_state(state=None)


@router.callback_query(F.data == 'delete_mypost_location')
@error_handler
async def process_pass_location(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Очистка локации объявления
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_publish_post: {callback.from_user.id}')
    data = await state.get_data()
    id_post_change = data['id_post_change']
    await rq.set_post_location_id(id_post=id_post_change,
                                  location='')
    info_post: Post = await rq.get_post_id(id_=id_post_change)
    text_publish = info_post.posts_text
    await callback.message.edit_text(text=text_publish,
                                     reply_markup=kb.keyboard_change_my_publish_post())
    await state.set_state(state=None)


@router.callback_query(F.data.startswith('mypost_autoposting'))
@error_handler
async def process_mypost_autoposting(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Обновление автопостинга опубликованного поста
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info('process_mypost_autoposting')
    id_post_change = int(callback.data.split('_')[-1])
    await state.update_data(id_post_change=id_post_change)
    info_post: Post = await rq.get_post_id(id_=id_post_change)
    await callback.message.edit_text(text='Выберите раздел',
                                     reply_markup=kb.keyboard_change_post_autoposting(info_post=info_post))


@router.callback_query(F.data.startswith('mypost_addautoposting'))
@error_handler
async def change_mypost_autoposting(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Обновление автопостинга опубликованного поста
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info('change_mypost_autoposting')
    action = callback.data.split('_')[-1]
    if action == '1':
        await callback.message.edit_text(text='Пришлите время для автопубликации, в формате: чч:мм',
                                         reply_markup=kb.keyboard_delete_autoposting(num_autoposting=int(action)))
        await state.set_state(ChangePost.autoposting_1_change)
        await state.update_data(num_autoposting=action)
    elif action == '2':
        await callback.message.edit_text(text='Пришлите время для автопубликации, в формате: чч:мм',
                                         reply_markup=kb.keyboard_delete_autoposting(num_autoposting=int(action)))
        await state.set_state(ChangePost.autoposting_2_change)
        await state.update_data(num_autoposting=action)
    elif action == '3':
        await callback.message.edit_text(text='Пришлите время для автопубликации, в формате: чч:мм',
                                         reply_markup=kb.keyboard_delete_autoposting(num_autoposting=int(action)))
        await state.set_state(ChangePost.autoposting_3_change)
        await state.update_data(num_autoposting=action)
    elif action == 'confirm':
        data = await state.get_data()
        id_post_change = data['id_post_change']
        info_post: Post = await rq.get_post_id(id_=id_post_change)
        text_autopost = 'Время автопостинга установлено:\n'
        count = 0
        for autopost in [info_post.post_autopost_1, info_post.post_autopost_2, info_post.post_autopost_3]:
            if autopost:
                count += 1
                text_autopost += f'{count}. {autopost}\n'
        text_publish = info_post.posts_text

        if text_autopost != 'Время автопостинга установлено:\n':
            await callback.message.edit_text(text=text_autopost)
        else:
            await callback.message.edit_text(text=text_publish,
                                             reply_markup=kb.keyboard_change_my_publish_post())
        await state.set_state(state=None)


@router.message(F.text, StateFilter(ChangePost.autoposting_1_change))
@router.message(F.text, StateFilter(ChangePost.autoposting_2_change))
@router.message(F.text, StateFilter(ChangePost.autoposting_3_change))
@error_handler
async def get_time_mypost_autoposting(message: Message, state: FSMContext, bot: Bot):
    """
    Обновление даты автопостинга
    :param message:
    :param state:
    :param bot:
    :return:
    """
    logging.info('get_time_mypost_autoposting')
    pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
    time_autoposting = message.text
    if re.match(pattern, time_autoposting):
        await state.set_state(state=None)
        data = await state.get_data()
        id_post_change = data['id_post_change']
        num_autoposting = data['num_autoposting']
        await rq.set_post_autoposting_id(id_post=id_post_change, autoposting=time_autoposting, num=num_autoposting)

        info_post: Post = await rq.get_post_id(id_=id_post_change)
        await message.answer(text='Выберите раздел',
                             reply_markup=kb.keyboard_change_post_autoposting(info_post=info_post))
    else:
        data = await state.get_data()
        num_autoposting = data['num_autoposting']
        await message.answer(text='Время автопубликации указано некорректно. Пришлите время для автопубликации,'
                                  ' в формате: чч:мм',
                             reply_markup=kb.keyboard_delete_autoposting(num_autoposting=num_autoposting))


@router.callback_query(F.data == 'delmypost_autoposting')
@error_handler
async def delete_autoposting(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Удаление автопубликации
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info('delete_autoposting')
    await state.set_state(state=None)
    data = await state.get_data()
    id_post_change = data['id_post_change']
    num_autoposting = data['num_autoposting']
    await rq.set_post_autoposting_id(id_post=id_post_change,
                                     autoposting='',
                                     num=num_autoposting)

    info_post: Post = await rq.get_post_id(id_=id_post_change)
    await callback.message.edit_text(text='Выберите раздел',
                                     reply_markup=kb.keyboard_change_post_autoposting(info_post=info_post))


async def change_publish_post(post_id: int, callback: CallbackQuery, bot: Bot):
    """
    Обновление опубликованного поста
    :param post_id:
    :param callback: int(callback.data.split('_')[1]) номер блока для вывода
    :param bot:
    :return:
    """
    logging.info(f'change_publish_post: {callback.from_user.id} post_id: {post_id}')
    # получаем информацию о посте по его id
    info_post: Post = await rq.get_post_id(id_=post_id)
    # posts_chat_message: -4528656216!27987,-1002014931432!297
    posts_chat_message: list = info_post.posts_chat_message.split(',')
    print(posts_chat_message)
    message_chat = []
    # получаем все посты
    posts = await rq.get_posts()
    # подсчитываем посты в проекте
    count_posts = len([post for post in posts])
    # получаем список постов пользователя
    post_managers: list[Post] = await rq.get_post_manager(tg_id_manager=callback.from_user.id)
    # подсчитываем посты пользователя
    count_post_manager = len([post for post in post_managers])
    # получаем информацию о пользователе
    info_user: User = await rq.get_user(tg_id=callback.from_user.id)
    # дата регистрации пользователя
    data_reg = info_user.data_reg
    # текущая дата
    current_date = datetime.now()
    data_reg_datetime = datetime(year=int(data_reg.split('-')[-1]),
                                 month=int(data_reg.split('-')[1]),
                                 day=int(data_reg.split('-')[0]))
    # получаем количество дней прошедешее после регистрации
    count_day = (current_date - data_reg_datetime).days
    # формируем сообщение с информацией о пользователе
    info_autor = f'№ {count_posts} 👉 <a href="tg://user?id={callback.from_user.id}">' \
                 f'{callback.from_user.username}</a>\n' \
                 f'Создано заказов {count_post_manager}\n' \
                 f'Зарегистрирован {count_day} день назад\n\n'
    # перебираем посты опубликованные в группах
    for i, post in enumerate(posts_chat_message):
        # получаем id группы
        group_peer_id = post.split('!')[0]
        # получаем id сообщения
        message_id = int(post.split('!')[1])
        # получаем информацию о группе
        group_info: Group = await rq.get_group_peer_id(peer_id=group_peer_id)
        if not group_info:
            continue

        bot_ = await bot.get_chat_member(chat_id=group_info.group_id,
                                         user_id=bot.id)
        if bot_.status != ChatMemberStatus.ADMINISTRATOR:
            await callback.message.answer(text=f'Бот не может редактировать пост в группе <b>{group_info.title}</b>'
                                               f' так как не является администратором, обратитесь к'
                                               f' <a href="tg://user?id={group_info.tg_id_partner}">владельцу</a> ')

        else:
            if info_post.post_location == '':
                try:
                    post = await bot.edit_message_text(chat_id=group_info.group_id,
                                                       message_id=message_id,
                                                       text=f"{info_autor}{info_post.posts_text}\n"
                                                            f"По всем вопросам пишите <a href='tg://user?id="
                                                            f"{callback.from_user.id}'>"
                                                            f"{callback.from_user.username}</a>",
                                                       reply_markup=kb.keyboard_post_(
                                                                    user_tg_id=callback.from_user.id))
                except:
                    post = await bot.edit_message_text(chat_id=group_info.group_id,
                                                       message_id=message_id,
                                                       text=f"{info_autor}{info_post.posts_text}\n"
                                                            f"По всем вопросам пишите <a href='tg://user?id="
                                                            f"{callback.from_user.id}'>"
                                                            f"{callback.from_user.username}</a>.",
                                                       reply_markup=kb.keyboard_post_(
                                                           user_tg_id=callback.from_user.id))
            else:
                try:
                    post = await bot.edit_message_text(chat_id=group_info.group_id,
                                                       message_id=message_id,
                                                       text=f"{info_autor}{info_post.posts_text}\n"
                                                            f"По всем вопросам пишите <a href='tg://user?id="
                                                            f"{callback.from_user.id}'>"
                                                            f"{callback.from_user.username}</a>",
                                                       reply_markup=kb.keyboard_post(
                                                                    user_tg_id=callback.from_user.id,
                                                                    location=info_post.post_location))
                except:
                    post = await bot.edit_message_text(chat_id=group_info.group_id,
                                                       message_id=message_id,
                                                       text=f"{info_autor}{info_post.posts_text}\n"
                                                            f"По всем вопросам пишите <a href='tg://user?id="
                                                            f"{callback.from_user.id}'>"
                                                            f"{callback.from_user.username}</a>.",
                                                       reply_markup=kb.keyboard_post(
                                                           user_tg_id=callback.from_user.id,
                                                           location=info_post.post_location))
            message_chat.append(f'{group_info.group_id}!{post.message_id}')
            await callback.message.answer(text=f'Пост обновлен в группе {group_info.title}')
    try:
        await callback.message.edit_text(text=f'Обновление поста по списку групп завершена',
                                         reply_markup=None)
    except:
        await callback.message.edit_text(text=f'Обновление поста по списку групп завершена.',
                                         reply_markup=None)
    posts_chat_message: str = ','.join(message_chat)
    await rq.set_post_posts_chat_message_id(id_post=post_id,
                                            posts_chat_message=posts_chat_message)


@router.callback_query(F.data.startswith('mypost_repeat'))
@error_handler
async def repeat_mypost(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Дублирование поста
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info('repeat_mypost')
    post_id = int(callback.data.split('_')[-1])
    info_post: Post = await rq.get_post_id(id_=post_id)
    data_ = {'tg_id_manager': callback.from_user.id,
             'posts_text':  info_post.posts_text,
             'post_location': info_post.post_location,
             'post_date_create': datetime.now().strftime('%d-%m-%Y %H:%M'),
             'status': rq.StatusPost.create}
    post_id: int = await rq.add_post(data=data_)
    await publish_post(id_post=post_id, callback=callback, bot=bot)
    await callback.message.edit_text(text='Пост продублирован')


@router.callback_query(F.data.startswith('mypost_delete_'))
@error_handler
async def process_mypost_delete(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """
    Удаление поста
    :param callback: int(callback.data.split('_')[1]) номер поста для удаления
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_mypost_delete: {callback.from_user.id} {callback.data}')
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
    await callback.message.delete()
    await callback.answer()