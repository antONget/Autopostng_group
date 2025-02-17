from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import requests as rq
import logging


def keyboard_change_list_group() -> InlineKeyboardMarkup:
    logging.info("keyboard_start_menu")
    button_1 = InlineKeyboardButton(text='Добавить группу',  callback_data=f'group_add')
    button_2 = InlineKeyboardButton(text='Удалить группу', callback_data=f'group_del')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2]])
    return keyboard


def keyboards_list_group(list_group: list, block: int):
    """
    Клавиатура для вывода списка групп
    :param list_group:
    :param block:
    :return:
    """
    logging.info(f"keyboards_list_group {len(list_group)}, {block}")
    kb_builder = InlineKeyboardBuilder()
    buttons = []
    for group in list_group[block*6:(block+1)*6]:
        buttons.append(InlineKeyboardButton(text=group.title,
                                            callback_data=f'groupdelselect_{group.id}'))
    button_back = InlineKeyboardButton(text='Назад',
                                       callback_data=f'groupdelback_{block}')
    button_next = InlineKeyboardButton(text='Вперед',
                                       callback_data=f'groupdelforward_{block}')
    button_page = InlineKeyboardButton(text=f'{block+1}',
                                       callback_data=f'none')
    kb_builder.row(*buttons, width=1)
    kb_builder.row(button_back, button_page, button_next)
    return kb_builder.as_markup()