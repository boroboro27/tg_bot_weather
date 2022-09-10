import asyncio
import logging.config
#import logging

from aiogram import Bot, Dispatcher

import handlers
from config import TELEGRAM_TOKEN
from logconf import LOGGING_CONFIG

#import os      

# Включаем логирование, чтобы не пропустить важные сообщения
logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)
#logging.basicConfig(level=logging.DEBUG, stream="sample.log")
logger.info("sfsdfs")
dispatcher = logging.getLogger("aiogram.dispatcher")
dispatcher.setLevel(10)
# TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')    

# Запуск бота
async def main():
    """
    The main entry point of the application
    """
    bot = Bot(token=TELEGRAM_TOKEN, parse_mode='HTML')    
    dp = Dispatcher()
    

    dp.include_router(handlers.router) # подключаем роутер к диспетчеру 
    # Запускаем бота и пропускаем все накопленные входящие
    # Да, этот метод можно вызвать даже если поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)       

if __name__ == "__main__":
    asyncio.run(main())
    