from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter
from aiogram.enums.chat_member_status import ChatMemberStatus

from utils.error_handling import error_handler
from database import requests as rq
from keyboards.user import my_autoposting_keyboards as kb
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


@router.callback_query(F.data == 'mypostautoposting')
@error_handler
async def process_mypostautoposting(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Выбор раздела "Опубликованные посты"
    :param callback: post_publish
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'process_mypostautoposting: {callback.from_user.id}')
    list_posts: list[Post] = await rq.get_posts_active_autoposting(tg_id_manager=callback.from_user.id)
    if not list_posts:
        await callback.message.edit_text(text='Нет постов c активным автопостингом',
                                         reply_markup=None)
        await callback.answer()
        return
    else:
        for item_post in list_posts:
            await callback.message.answer(text=item_post.posts_text,
                                          reply_markup=kb.keyboard_change_post_autoposting(info_post=item_post))
    await callback.answer()


@router.callback_query(F.data.startswith('mypostaddautoposting_'))
@error_handler
async def change_mypost_autoposting(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Обновление автопостинга опубликованного поста
    :param callback:
    :param state:
    :param bot:
    :return:
    """
    logging.info(f'change_mypost_autoposting: {callback.from_user.id} {callback.data}')
    action = callback.data.split('_')[-2]
    post_id = callback.data.split('_')[-1]
    id_post_change = await state.update_data(id_post_change=post_id)
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
        if text_autopost != 'Время автопостинга установлено:\n':
            await callback.message.edit_text(text=text_autopost)
        else:
            await callback.message.delete()
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


@router.callback_query(F.data == 'delmypostautoposting')
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
