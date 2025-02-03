from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import logging


def keyboard_main_admin() -> ReplyKeyboardMarkup:
    logging.info("keyboard_main_admin")
    button_1 = KeyboardButton(text='Мои группы')
    button_3 = KeyboardButton(text='Партнеры')
    button_4 = KeyboardButton(text='Тарифы')
    keyboard = ReplyKeyboardMarkup(keyboard=[[button_1], [button_3], [button_4]], resize_keyboard=True)
    return keyboard


def keyboard_main_partner() -> ReplyKeyboardMarkup:
    logging.info("keyboard_main_partner")
    button_1 = KeyboardButton(text='Мои группы')
    button_3 = KeyboardButton(text='Группы для публикации')
    button_4 = KeyboardButton(text='Тарифы')
    keyboard = ReplyKeyboardMarkup(keyboard=[[button_1], [button_3], [button_4]], resize_keyboard=True)
    return keyboard


def keyboard_main_manager() -> ReplyKeyboardMarkup:
    logging.info("keyboard_main_manager")
    button_1 = KeyboardButton(text='Выбрать группу')
    button_2 = KeyboardButton(text='Группы для публикации')
    keyboard = ReplyKeyboardMarkup(keyboard=[[button_1], [button_2]], resize_keyboard=True)
    return keyboard


def keyboard_main_manager_inline() -> InlineKeyboardMarkup:
    logging.info("keyboard_main_manager_inline")
    button_1 = InlineKeyboardButton(text='Опубликовать пост', callback_data='publish_post')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]])
    return keyboard