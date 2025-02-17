from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Bot
from database import requests as rq
from filter.filter_group import is_admin_bot_in_group
import logging


def keyboard_select_action_black_list() -> InlineKeyboardMarkup:
    logging.info("keyboard_select_action_black_list")
    button_1 = InlineKeyboardButton(text='Добавить в черный список',  callback_data=f'blacklist_add')
    button_2 = InlineKeyboardButton(text='Удалить из черного списка', callback_data=f'blacklist_del')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2]])
    return keyboard


def keyboards_black_list(black_list: list, block: int):
    """
    Клавиатура для вывода списка пользователей добавленных в черный список
    :param black_list:
    :param block:
    :return:
    """
    logging.info(f"keyboards_black_list {len(black_list)}, {block}")
    kb_builder = InlineKeyboardBuilder()
    buttons = []
    for manager in black_list[block*6:(block+1)*6]:
        if manager.role == rq.UserRole.admin:
            continue
        buttons.append(InlineKeyboardButton(text=manager.username,
                                            callback_data=f'blacklistselect_{manager.id}'))
    button_back = InlineKeyboardButton(text='Назад',
                                       callback_data=f'blacklistback_{block}')
    button_next = InlineKeyboardButton(text='Вперед',
                                       callback_data=f'blacklistforward_{block}')
    button_page = InlineKeyboardButton(text=f'{block+1}',
                                       callback_data=f'none')
    kb_builder.row(*buttons, width=1)
    kb_builder.row(button_back, button_page, button_next)
    return kb_builder.as_markup()


async def keyboards_list_group(list_group: list, block: int, change_manager: str, bot: Bot):
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
        if await is_admin_bot_in_group(group_peer_id=group.group_id, bot=bot):
            buttons.append(InlineKeyboardButton(text=group.title,
                                                callback_data=f'groupselect_{group.id}'))
        else:
            buttons.append(InlineKeyboardButton(text=f'❌ {group.title}',
                                                callback_data=f'groupselect_{group.id}'))
    button_back = InlineKeyboardButton(text='Назад',
                                       callback_data=f'groupback_{block}')
    button_next = InlineKeyboardButton(text='Вперед',
                                       callback_data=f'groupforward_{block}')
    if change_manager == 'add':
        text = f'Добавить во все'
    else:
        text = f'Удалить из всех'
    button_all = InlineKeyboardButton(text=text,
                                      callback_data=f'groupall')
    kb_builder.row(*buttons, width=1)
    kb_builder.row(button_back, button_all, button_next)
    return kb_builder.as_markup()