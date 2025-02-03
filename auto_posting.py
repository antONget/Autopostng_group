import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import FSInputFile, User
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent

import traceback
from typing import Any, Dict
from config_data.config import Config, load_config
from handlers import other_handlers, user_handlers, ban, unban, admin_handlers, partner_handlers,\
    partner_group_handlers, manager_handlers, partner_frames_handlers
from database.models import async_main
from notify_admins import on_startup_notify
# Инициализируем logger
logger = logging.getLogger(__name__)


# Функция конфигурирования и запуска бота
async def main():
    await async_main()
    # Конфигурируем логирование
    logging.basicConfig(
        level=logging.INFO,
        filename="py_log.log",
        filemode='w',
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

    # Выводим в консоль информацию о начале запуска бота
    logger.info('Starting bot')

    # Загружаем конфиг в переменную config
    config: Config = load_config()

    # Инициализируем бот и диспетчер
    bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    await on_startup_notify(bot=bot)
    # Регистрируем router в диспетчере
    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router)
    dp.include_router(partner_handlers.router)
    dp.include_router(partner_group_handlers.router)
    dp.include_router(partner_frames_handlers.router)
    dp.include_router(manager_handlers.router)
    dp.include_routers(ban.router, unban.router)
    dp.include_router(other_handlers.router)

    @dp.error()
    async def error_handler(event: ErrorEvent, data: Dict[str, Any]):
        logger.critical("Критическая ошибка: %s", event.exception, exc_info=True)
        user: User = data.get('event_from_user')
        # await bot.send_message(chat_id=user.id,
        #                        text='Упс.. Что-то пошло не так( Перезапустите бота /start')
        await bot.send_message(chat_id=config.tg_bot.support_id,
                               text=f'{event.exception}')
        formatted_lines = traceback.format_exc()
        text_file = open('error.txt', 'w')
        text_file.write(str(formatted_lines))
        text_file.close()
        await bot.send_document(chat_id=config.tg_bot.support_id,
                                document=FSInputFile('error.txt'))

    # Пропускаем накопившиеся update и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
