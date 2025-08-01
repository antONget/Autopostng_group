from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.types import FSInputFile
from database.requests import delete_group, get_group_peer_id
import logging

router = Router()


@router.callback_query()
async def all_callback(callback: CallbackQuery) -> None:
    logging.info(f'all_callback: {callback.from_user.id}')
    logging.info(callback.data)


@router.message()
async def all_message(message: Message) -> None:
    logging.info(f'all_message')
    if message.photo:
        logging.info(f'all_message message.photo')
        logging.info(message.photo[-1].file_id)

    if message.sticker:
        logging.info(f'all_message message.sticker')
        logging.info(message.sticker.file_id)

    if message.text == '/get_logfile':
        file_path = "py_log.log"
        await message.answer_document(FSInputFile(file_path))

    if message.text == '/get_dbfile':
        file_path = "database/db.sqlite3"
        await message.answer_document(FSInputFile(file_path))
    if message.text:
        if message.text.startswith('/del_group_id'):
            info_group = await get_group_peer_id(peer_id=int(message.text.split(' ')[-1]))
            await message.answer(text=f'Группа {info_group.title} найдена')
            await delete_group(id_=info_group.id)
            await message.answer(text=f'Группа удалена')

