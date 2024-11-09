from filter.filter_group import parse_time, is_admin
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from aiogram import Bot, Router, F

router = Router()
router.message.filter(F.chat.type != "private")


@router.message(Command("unban"))
async def func_unban(message: Message, bot: Bot):
    reply_message = message.reply_to_message

    if not reply_message:
        return await message.reply('Для применения команды /unban требуется ответить на сообщение пользователя')
    if not await is_admin(message, bot):
        await message.reply("Для использования команды /unban бот должен быть администратором в канале,"
                            " а вы администратором или владельцем")
        return
    await bot.unban_chat_member(chat_id=message.chat.id, user_id=reply_message.from_user.id, only_if_banned=True)
    await message.answer(" Блокировка была снята")