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
from handlers.admin import admin_handlers, ban, unban
from handlers.partner import partner_handlers, partner_requisites_handlers, partner_group_handlers, \
    partner_frames_handlers
from handlers.user import user_subscribe_frame_handlers, user_posting_handlers, \
    user_post_delete_handlers, user_post_edit_handlers
from handlers import start_handlers, other_handlers
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.models import async_main
from notify_admins import on_startup_notify
from utils.scheduler_task_posting import scheduler_send_post_for_group
# Инициализируем logger
logger = logging.getLogger(__name__)


# Функция конфигурирования и запуска бота
async def main():
    await async_main()
    # Конфигурируем логирование
    logging.basicConfig(
        level=logging.INFO,
        # filename="py_log.log",
        # filemode='w',
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

    # Выводим в консоль информацию о начале запуска бота
    logger.info('Starting bot')

    # Загружаем конфиг в переменную config
    config: Config = load_config()

    # Инициализируем бот и диспетчер
    bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(func=scheduler_send_post_for_group, trigger='cron', minute='*', args=(bot,))
    scheduler.start()
    await on_startup_notify(bot=bot)
    # Регистрируем router в диспетчере
    dp.include_router(start_handlers.router)
    dp.include_routers(admin_handlers.router, ban.router, unban.router)
    dp.include_routers(partner_handlers.router,
                       partner_requisites_handlers.router,
                       partner_group_handlers.router,
                       partner_frames_handlers.router)
    dp.include_routers(user_subscribe_frame_handlers.router,
                       user_posting_handlers.router,
                       user_post_delete_handlers.router,
                       user_post_edit_handlers.router)
    dp.include_router(other_handlers.router)
    # dp.message.middleware(SchedulerMiddleware())
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
