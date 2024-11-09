from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import requests as rq
import logging


def keyboard_start_menu() -> InlineKeyboardMarkup:
    logging.info("keyboard_start_menu")
    button_1 = InlineKeyboardButton(text='Добавить партнера',  callback_data=f'partner_add')
    button_2 = InlineKeyboardButton(text='Удалить партнера', callback_data=f'partner_del')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2]])
    return keyboard


def keyboards_list_partner(list_partner: list, block: int):
    """
    Клавиатура для вывода списка партнеров
    :param list_partner:
    :param block:
    :return:
    """
    logging.info(f"keyboards_order_item {len(list_partner)}, {block}")
    kb_builder = InlineKeyboardBuilder()
    buttons = []
    for partner in list_partner[block*6:(block+1)*6]:
        if partner.role == rq.UserRole.admin:
            continue
        buttons.append(InlineKeyboardButton(text=partner.username,
                                            callback_data=f'partnerselectadd_{partner.id}'))
    button_back = InlineKeyboardButton(text='Назад',
                                       callback_data=f'partnerback_{block}')
    button_next = InlineKeyboardButton(text='Вперед',
                                       callback_data=f'partnerforward_{block}')
    button_page = InlineKeyboardButton(text=f'{block+1}',
                                       callback_data=f'none')
    kb_builder.row(*buttons, width=1)
    kb_builder.row(button_back, button_page, button_next)
    return kb_builder.as_markup()
