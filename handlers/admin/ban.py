from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from aiogram import Bot, Router, F
from contextlib import suppress
from aiogram.exceptions import TelegramBadRequest

from filter.filter_group import parse_time, is_admin
from filter.admin_filter import IsSuperAdmin

router = Router()
router.message.filter(F.chat.type != "private")


@router.message(Command("ban"), IsSuperAdmin())
async def func_ban(message: Message, command: CommandObject, bot: Bot):
    reply_message = message.reply_to_message

    if not reply_message:
        return await message.reply('Для применения команды /ban требуется ответить на сообщение пользователя')
    if not await is_admin(message, bot):
        await message.reply("Для использования команды /ban бот должен быть администратором в канале,"
                            " а вы администратором или владельцем")
        return

    date = parse_time(command.args)
    mention = reply_message.from_user.mention_html(reply_message.from_user.username)

    with suppress(TelegramBadRequest):
        await bot.ban_chat_member(chat_id=message.from_user.id,
                                  user_id=reply_message.from_user.id,
                                  until_date=date)
        await message.answer(f" Пользователь <b>{mention}</b> был заблокирован!")
