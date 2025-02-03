from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import Group, Frame
import logging


def keyboard_action_frames() -> InlineKeyboardMarkup:
    logging.info("keyboard_action_frames")
    button_1 = InlineKeyboardButton(text='Создать',  callback_data=f'frame_create')
    button_2 = InlineKeyboardButton(text='Удалить', callback_data=f'frame_del')
    button_3 = InlineKeyboardButton(text='Редактировать', callback_data=f'frame_edit')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2], [button_3]])
    return keyboard


def keyboards_list_group_frame(list_group: list[Group], block: int, list_id_group: list = None,
                               flag_change: bool = False):
    """
    Клавиатура для вывода списка групп для добавления в тариф
    :param list_group:
    :param block:
    :param list_id_group:
    :param flag_change:
    :return:
    """
    logging.info(f"keyboards_list_group_frame {len(list_group)}, {block}")
    kb_builder = InlineKeyboardBuilder()
    buttons = []
    for group in list_group[block*6:(block+1)*6]:
        text = group.title
        if str(group.id) in list_id_group:
            text = f'{group.title} ✅'
        buttons.append(InlineKeyboardButton(text=text,
                                            callback_data=f'groupframeselect_{group.id}'))
    button_back = InlineKeyboardButton(text='Назад',
                                       callback_data=f'groupframeback_{block}')
    button_next = InlineKeyboardButton(text='Вперед',
                                       callback_data=f'groupframeforward_{block}')
    button_page = InlineKeyboardButton(text=f'{block+1}',
                                       callback_data=f'none')
    button_confirm = ''
    if flag_change:
        button_confirm = InlineKeyboardButton(text=f'Подтвердить',
                                              callback_data=f'confirm_change_group_frame')
    else:
        button_confirm = InlineKeyboardButton(text=f'Подтвердить',
                                              callback_data=f'confirm_attach_group_frame')
    kb_builder.row(*buttons, width=1)
    kb_builder.row(button_back, button_page, button_next)
    kb_builder.row(button_confirm)
    return kb_builder.as_markup()


def keyboards_list_frame(list_frame: list[Frame], block: int):
    """
    Клавиатура для вывода списка групп для добавления в тариф
    :param list_frame:
    :param block:
    :return:
    """
    logging.info(f"keyboards_list_frame {block}")
    kb_builder = InlineKeyboardBuilder()
    buttons = []
    for frame in list_frame[block*6:(block+1)*6]:
        text = frame.title_frame
        buttons.append(InlineKeyboardButton(text=text,
                                            callback_data=f'changeframeselect_{frame.id}'))
    button_back = InlineKeyboardButton(text='Назад',
                                       callback_data=f'frameback_{block}')
    button_next = InlineKeyboardButton(text='Вперед',
                                       callback_data=f'frameforward_{block}')
    button_page = InlineKeyboardButton(text=f'{block+1}',
                                       callback_data=f'none')
    button_confirm = InlineKeyboardButton(text=f'Подтвердить',
                                          callback_data=f'confirm_delete_frame')
    kb_builder.row(*buttons, width=1)
    kb_builder.row(button_back, button_page, button_next)
    kb_builder.row(button_confirm)
    return kb_builder.as_markup()


def keyboard_column_frame(info_frame: Frame) -> InlineKeyboardMarkup:
    logging.info("keyboard_column_frame")
    button_1 = InlineKeyboardButton(text=f'Название - {info_frame.title_frame}',  callback_data=f'change_title')
    button_2 = InlineKeyboardButton(text=f'Стоимость - {info_frame.cost_frame} ₽', callback_data=f'change_cost')
    button_3 = InlineKeyboardButton(text=f'Период - {info_frame.period_frame} дней', callback_data=f'change_period')
    button_4 = InlineKeyboardButton(text=f'Список групп', callback_data=f'change_listgroup')
    button_5 = InlineKeyboardButton(text=f'Подтвердить', callback_data=f'confirm_edit_frame')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2], [button_3], [button_4], [button_5]])
    return keyboard
