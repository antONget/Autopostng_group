from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import Frame
import logging


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
                                            callback_data=f'groupmanagerselect_{group.id}'))
    button_back = InlineKeyboardButton(text='Назад',
                                       callback_data=f'groupmanagerback_{block}')
    button_next = InlineKeyboardButton(text='Вперед',
                                       callback_data=f'groupmanagerforward_{block}')

    button_all = InlineKeyboardButton(text=f'{block+1}',
                                      callback_data=f' ')
    kb_builder.row(*buttons, width=1)
    kb_builder.row(button_back, button_all, button_next)
    return kb_builder.as_markup()


def keyboards_list_group_in_frame(list_frame: list[Frame]):
    """
    Клавиатура для вывода списка тарифов
    :param list_frame:
    :return:
    """
    logging.info(f"keyboards_list_group_in_frame")
    kb_builder = InlineKeyboardBuilder()
    buttons = []
    for frame in list_frame:
        buttons.append(InlineKeyboardButton(text=f'{frame.title_frame} - {frame.cost_frame} ₽',
                                            callback_data=f'frameselectpay_{frame.id}'))

    kb_builder.row(*buttons, width=1)
    return kb_builder.as_markup()


def keyboard_check_payment(id_frame: int) -> InlineKeyboardMarkup:
    logging.info("keyboard_check_payment")
    button_1 = InlineKeyboardButton(text='Отправить чек',  callback_data=f'send_check_{id_frame}')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]])
    return keyboard


def keyboard_check_payment_partner(user_tg_id: int, id_frame: str) -> InlineKeyboardMarkup:
    logging.info("keyboard_check_payment_partner")
    button_1 = InlineKeyboardButton(text='Спам',  callback_data=f'payment_cancel_{user_tg_id}_{id_frame}')
    button_2 = InlineKeyboardButton(text='Подтвердить', callback_data=f'payment_confirm_{user_tg_id}_{id_frame}')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1, button_2]])
    return keyboard


def keyboard_manager_publish_one() -> InlineKeyboardMarkup:
    logging.info("keyboard_manager_publish_one")
    button_1 = InlineKeyboardButton(text='Опубликовать пост',  callback_data=f'publish_post')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]])
    return keyboard


def keyboard_manager_publish() -> InlineKeyboardMarkup:
    logging.info("keyboard_manager_publish")
    button_1 = InlineKeyboardButton(text='Опубликовать пост',  callback_data=f'publish_post')
    button_2 = InlineKeyboardButton(text='Удалить пост', callback_data=f'delete_post')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2]])
    return keyboard


def keyboard_pass_location() -> InlineKeyboardMarkup:
    logging.info("keyboard_pass_location")
    button_1 = InlineKeyboardButton(text='Пропустить',  callback_data=f'pass_location')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]])
    return keyboard


def keyboard_show_post(manager_tg_id: int, location: str) -> InlineKeyboardMarkup:
    logging.info("keyboard_manager_publish")
    button_1 = InlineKeyboardButton(text='👤ОТКЛИКНУТЬСЯ 👤',  url=f'tg://user?id={manager_tg_id}')
    button_2 = InlineKeyboardButton(text='МЕСТОПОЛОЖЕНИЕ', url=location)
    button_3 = InlineKeyboardButton(text='Опубликовать',  callback_data=f'publishpost')
    button_4 = InlineKeyboardButton(text='Отменить', callback_data=f'cancelpost')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2], [button_3], [button_4]])
    return keyboard


def keyboard_show_post_(manager_tg_id: int) -> InlineKeyboardMarkup:
    logging.info("keyboard_manager_publish")
    button_1 = InlineKeyboardButton(text='👤ОТКЛИКНУТЬСЯ 👤',  url=f'tg://user?id={manager_tg_id}')
    button_3 = InlineKeyboardButton(text='Опубликовать',  callback_data=f'publishpost')
    button_4 = InlineKeyboardButton(text='Отменить', callback_data=f'cancelpost')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_3], [button_4]])
    return keyboard


def keyboard_post(manager_tg_id: int, location: str) -> InlineKeyboardMarkup:
    logging.info("keyboard_manager_publish")
    button_1 = InlineKeyboardButton(text='👤ОТКЛИКНУТЬСЯ 👤',  url=f'tg://user?id={manager_tg_id}')
    button_2 = InlineKeyboardButton(text='МЕСТОПОЛОЖЕНИЕ', url=location)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2]])
    return keyboard


def keyboard_post_(manager_tg_id: int) -> InlineKeyboardMarkup:
    logging.info("keyboard_manager_publish")
    button_1 = InlineKeyboardButton(text='👤ОТКЛИКНУТЬСЯ 👤',  url=f'tg://user?id={manager_tg_id}')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]])
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
                                       callback_data=f'deletepostback_{block}')
    button_next = InlineKeyboardButton(text='Вперед',
                                       callback_data=f'deletepostforward_{block}')
    button_delete = InlineKeyboardButton(text=f'Удалить',
                                         callback_data=f'deletepost_{id_post}')
    kb_builder.row(button_back, button_delete, button_next)
    return kb_builder.as_markup()
