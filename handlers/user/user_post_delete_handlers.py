from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter
from aiogram.enums.chat_member_status import ChatMemberStatus

from utils.error_handling import error_handler
from filter.user_filter import check_role
from database import requests as rq
from keyboards.user import user_post_delete_keyboards as kb
from config_data.config import Config, load_config
from database.models import User, Frame, Group, Subscribe, Post
import validators

import logging
from datetime import datetime


config: Config = load_config()
router = Router()
router.message.filter(F.chat.type == "private")


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