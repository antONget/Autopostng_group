from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import Post
import logging


def keyboard_user_publish_new() -> InlineKeyboardMarkup:
    logging.info("keyboard_user_publish_new")
    button_1 = InlineKeyboardButton(text='Опубликованные посты', callback_data=f'post_publish')
    button_2 = InlineKeyboardButton(text='Изменить автопостинг', callback_data=f'mypostautoposting')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2]])
    return keyboard


def keyboard_my_publish_post(post_id: int) -> InlineKeyboardMarkup:
    logging.info("keyboard_my_publish_post")
    button_1 = InlineKeyboardButton(text='Автопостинг', callback_data=f'mypost_autoposting_{post_id}')
    button_2 = InlineKeyboardButton(text='Редактировать',  callback_data=f'mypost_edit_{post_id}')
    button_3 = InlineKeyboardButton(text='Продублировать', callback_data=f'mypost_repeat_{post_id}')
    button_4 = InlineKeyboardButton(text='Удалить', callback_data=f'mypost_delete_{post_id}')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2], [button_3], [button_4]])
    return keyboard


def keyboard_change_my_publish_post() -> InlineKeyboardMarkup:
    logging.info("keyboard_change_my_publish_post")
    button_1 = InlineKeyboardButton(text='Текст объявления',  callback_data='mypost_changing_text')
    button_2 = InlineKeyboardButton(text='Местоположение', callback_data='mypost_changing_location')
    button_3 = InlineKeyboardButton(text='Подтвердить', callback_data='mypost_changing_confirm')
    button_4 = InlineKeyboardButton(text='Опубликовать', callback_data='mypost_changing_publish')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_3]])
    return keyboard


def keyboard_delete_location() -> InlineKeyboardMarkup:
    logging.info("keyboard_delete_location")
    button_1 = InlineKeyboardButton(text='Удалить местоположение',
                                    callback_data=f'delete_mypost_location')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]])
    return keyboard


def keyboard_change_post_autoposting(info_post: Post) -> InlineKeyboardMarkup:
    logging.info("keyboard_change_post_autoposting")
    if info_post.post_autopost_1 == '':
        button_1 = InlineKeyboardButton(text='Автопубликация 1 ❌',
                                        callback_data='mypost_addautoposting_1')
    else:
        button_1 = InlineKeyboardButton(text=f'Автопубликация 1 - {info_post.post_autopost_1}',
                                        callback_data='mypost_addautoposting_1')
    if info_post.post_autopost_2 == '':
        button_2 = InlineKeyboardButton(text='Автопубликация 2 ❌',
                                        callback_data='mypost_addautoposting_2')
    else:
        button_2 = InlineKeyboardButton(text=f'Автопубликация 2 - {info_post.post_autopost_2}',
                                        callback_data='mypost_addautoposting_2')
    if info_post.post_autopost_3 == '':
        button_3 = InlineKeyboardButton(text='Автопубликация 3 ❌',
                                        callback_data='mypost_addautoposting_3')
    else:
        button_3 = InlineKeyboardButton(text=f'Автопубликация 3 - {info_post.post_autopost_3}',
                                        callback_data='mypost_addautoposting_3')
    button_4 = InlineKeyboardButton(text='Подтвердить',
                                    callback_data='mypost_addautoposting_confirm')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2], [button_3], [button_4]])
    return keyboard


def keyboard_delete_autoposting(num_autoposting: int) -> InlineKeyboardMarkup:
    logging.info("keyboard_delete_autoposting")
    button_1 = InlineKeyboardButton(text=f'Отменить автопубликацию {num_autoposting}',
                                    callback_data=f'delmypost_autoposting')
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
