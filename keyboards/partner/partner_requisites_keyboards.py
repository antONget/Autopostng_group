from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import Group, Frame
import logging


def keyboard_requisites_add() -> InlineKeyboardMarkup:
    logging.info("keyboard_requisites_add")
    button_1 = InlineKeyboardButton(text='Добавить',  callback_data=f'requisites_add')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]])
    return keyboard


def keyboard_requisites_update() -> InlineKeyboardMarkup:
    logging.info("keyboard_requisites_update")
    button_1 = InlineKeyboardButton(text='Обновить',  callback_data=f'requisites_update')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]])
    return keyboard
