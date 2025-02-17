from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import logging


def keyboard_main_admin() -> ReplyKeyboardMarkup:
    logging.info("keyboard_main_admin")
    button_1 = KeyboardButton(text='Мои группы')
    button_2 = KeyboardButton(text='Тарифы')
    button_3 = KeyboardButton(text='Опубликовать пост')
    button_4 = KeyboardButton(text='Приобрести подписку')
    button_5 = KeyboardButton(text='Реквизиты')
    button_6 = KeyboardButton(text='Партнеры')
    button_7 = KeyboardButton(text='Черный список')
    keyboard = ReplyKeyboardMarkup(keyboard=[[button_1, button_2],
                                             [button_3, button_4],
                                             [button_5, button_6],
                                             [button_7]],
                                   resize_keyboard=True)
    return keyboard


def keyboard_main_partner() -> ReplyKeyboardMarkup:
    logging.info("keyboard_main_partner")
    button_1 = KeyboardButton(text='Мои группы')
    button_2 = KeyboardButton(text='Тарифы')
    button_3 = KeyboardButton(text='Опубликовать пост')
    button_4 = KeyboardButton(text='Приобрести подписку')
    button_5 = KeyboardButton(text='Реквизиты')
    button_6 = KeyboardButton(text='Черный список')
    keyboard = ReplyKeyboardMarkup(keyboard=[[button_1, button_2], [button_3, button_4], [button_5], [button_6]],
                                   resize_keyboard=True)
    return keyboard


def keyboard_main_manager() -> ReplyKeyboardMarkup:
    logging.info("keyboard_main_manager")
    button_1 = KeyboardButton(text='Приобрести подписку')
    button_2 = KeyboardButton(text='Опубликовать пост')
    keyboard = ReplyKeyboardMarkup(keyboard=[[button_1], [button_2]], resize_keyboard=True)
    return keyboard


def keyboard_main_manager_inline() -> InlineKeyboardMarkup:
    logging.info("keyboard_main_manager_inline")
    button_1 = InlineKeyboardButton(text='Опубликовать пост', callback_data='publish_post')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]])
    return keyboard