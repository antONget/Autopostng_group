from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import Post
import logging


def keyboard_type_post() -> InlineKeyboardMarkup:
    logging.info("keyboard_type_post")
    button_1 = InlineKeyboardButton(text='Опубликованные',  callback_data='type_edit_post_publish')
    button_2 = InlineKeyboardButton(text='Созданные (Архив)', callback_data='type_edit_post_create')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2]])
    return keyboard


def keyboards_list_post(block: int, id_post: int):
    """
    Клавиатура для вывода списка групп
    :param block:
    :param id_post:
    :return:
    """
    logging.info(f"keyboards_list_group {block}")
    kb_builder = InlineKeyboardBuilder()
    button_back = InlineKeyboardButton(text='Назад',
                                       callback_data=f'editpostback_{block}')
    button_next = InlineKeyboardButton(text='Вперед',
                                       callback_data=f'editpostforward_{block}')
    button_delete = InlineKeyboardButton(text=f'Редактировать',
                                         callback_data=f'editpost_{id_post}')
    button_repeat = InlineKeyboardButton(text=f'Продублировать пост',
                                         callback_data=f'repeat_{id_post}')
    kb_builder.row(button_repeat)
    kb_builder.row(button_back, button_delete, button_next)
    return kb_builder.as_markup()


def keyboard_change_post(type_post: str) -> InlineKeyboardMarkup:
    logging.info("keyboard_type_post")
    button_1 = InlineKeyboardButton(text='Текст объявления',  callback_data='changing_post_text')
    button_2 = InlineKeyboardButton(text='Местоположение', callback_data='changing_post_location')
    button_3 = InlineKeyboardButton(text='Автопостинг', callback_data='changing_post_autoposting')
    button_4 = InlineKeyboardButton(text='Подтвердить', callback_data='changing_post_confirm')
    button_5 = InlineKeyboardButton(text='Опубликовать', callback_data='changing_post_publish')
    if type_post == 'publish':
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2], [button_3], [button_4]])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2], [button_3], [button_5]])
    return keyboard


def keyboard_pass_location() -> InlineKeyboardMarkup:
    logging.info("keyboard_pass_location")
    button_1 = InlineKeyboardButton(text='Удалить местоположение',
                                    callback_data=f'pass_change_location')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]])
    return keyboard


def keyboard_change_post_autoposting(info_post: Post) -> InlineKeyboardMarkup:
    logging.info("keyboard_change_post_autoposting")
    if info_post.post_autopost_1 == '':
        button_1 = InlineKeyboardButton(text='Автопубликация 1 ❌',
                                        callback_data='autoposting_1')
    else:
        button_1 = InlineKeyboardButton(text=f'Автопубликация 1 - {info_post.post_autopost_1}',
                                        callback_data='autoposting_1')
    if info_post.post_autopost_2 == '':
        button_2 = InlineKeyboardButton(text='Автопубликация 2 ❌',
                                        callback_data='autoposting_2')
    else:
        button_2 = InlineKeyboardButton(text=f'Автопубликация 2 - {info_post.post_autopost_2}',
                                        callback_data='autoposting_2')
    if info_post.post_autopost_3 == '':
        button_3 = InlineKeyboardButton(text='Автопубликация 3 ❌',
                                        callback_data='autoposting_3')
    else:
        button_3 = InlineKeyboardButton(text=f'Автопубликация 3 - {info_post.post_autopost_3}',
                                        callback_data='autoposting_3')
    button_4 = InlineKeyboardButton(text='Подтвердить',
                                    callback_data='autoposting_confirm')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2], [button_3], [button_4]])
    return keyboard


def keyboard_delete_autoposting() -> InlineKeyboardMarkup:
    logging.info("keyboard_delete_autoposting")
    button_1 = InlineKeyboardButton(text='Убрать с автопубликации',
                                    callback_data=f'delete_autoposting')
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
