from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import Frame
import logging


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
                                       callback_data=f'deletepostback_{block}')
    button_next = InlineKeyboardButton(text='Вперед',
                                       callback_data=f'deletepostforward_{block}')
    button_delete = InlineKeyboardButton(text=f'Удалить',
                                         callback_data=f'deletepost_{id_post}')
    kb_builder.row(button_back, button_delete, button_next)
    return kb_builder.as_markup()
