from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore


async def scheduler_task_cron():
    REDIS = {
        'host': '127.0.0.1',
        'port': '6379',
        'db': 15
    }

    jobstores = {
        'redis': RedisJobStore(**REDIS)
    }
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow", jobstores=jobstores)
    scheduler.start()
    return scheduler
