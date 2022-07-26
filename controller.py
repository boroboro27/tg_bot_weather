import asyncio
from logging import handlers
from aiogram import Bot, Dispatcher
import handlers
import config

import logging
import sys
#import os    
    

# Запуск бота
async def main():
    # Включаем логирование, чтобы не пропустить важные сообщения
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    #sqlite_db.sql_start()

    # TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')           

    bot = Bot(token=config.TELEGRAM_TOKEN, parse_mode='HTML')    
    dp = Dispatcher()

    dp.include_router(handlers.router) # подключаем роутер к диспетчеру

    # client.register_handlers_client(dp)
    
    # Запускаем бота и пропускаем все накопленные входящие
    # Да, этот метод можно вызвать даже если у вас поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)       

if __name__ == "__main__":
    asyncio.run(main())


    



    