from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import Post
import logging


def keyboard_change_post_autoposting(info_post: Post) -> InlineKeyboardMarkup:
    logging.info("keyboard_change_post_autoposting")
    if info_post.post_autopost_1 == '':
        button_1 = InlineKeyboardButton(text='Автопубликация 1 ❌',
                                        callback_data=f'mypostaddautoposting_1_{info_post.id}')
    else:
        button_1 = InlineKeyboardButton(text=f'Автопубликация 1 - {info_post.post_autopost_1}',
                                        callback_data=f'mypostaddautoposting_1_{info_post.id}')
    if info_post.post_autopost_2 == '':
        button_2 = InlineKeyboardButton(text='Автопубликация 2 ❌',
                                        callback_data=f'mypostaddautoposting_2_{info_post.id}')
    else:
        button_2 = InlineKeyboardButton(text=f'Автопубликация 2 - {info_post.post_autopost_2}',
                                        callback_data=f'mypostaddautoposting_2_{info_post.id}')
    if info_post.post_autopost_3 == '':
        button_3 = InlineKeyboardButton(text='Автопубликация 3 ❌',
                                        callback_data=f'mypostaddautoposting_3_{info_post.id}')
    else:
        button_3 = InlineKeyboardButton(text=f'Автопубликация 3 - {info_post.post_autopost_3}',
                                        callback_data=f'mypostaddautoposting_3_{info_post.id}')
    button_4 = InlineKeyboardButton(text='Подтвердить',
                                    callback_data=f'mypostaddautoposting_confirm_{info_post.id}')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2], [button_3], [button_4]])
    return keyboard


def keyboard_delete_autoposting(num_autoposting: int) -> InlineKeyboardMarkup:
    logging.info("keyboard_delete_autoposting")
    button_1 = InlineKeyboardButton(text=f'Отменить автопубликацию {num_autoposting}',
                                    callback_data=f'delmypostautoposting')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]])
    return keyboard


def keyboard_post(user_tg_id: int, location: str) -> InlineKeyboardMarkup:
    logging.info("keyboard_manager_publish")
    button_1 = InlineKeyboardButton(text='👤ОТКЛИКНУТЬСЯ 👤',  url=f'tg://user?id={user_tg_id}')
    button_2 = InlineKeyboardButton(text='МЕСТОПОЛОЖЕНИЕ', url=location)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2]])
    return keyboard


def keyboard_post_(user_tg_id: int) -> InlineKeyboardMarkup:
    logging.info("keyboard_manager_publish")
    button_1 = InlineKeyboardButton(text='👤ОТКЛИКНУТЬСЯ 👤',  url=f'tg://user?id={user_tg_id}')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]])
    return keyboard
