import asyncio
from aiogram import Bot, Dispatcher

import handlers
from config import TELEGRAM_TOKEN
from database import PSQLRequests as psql

import logging
import sys 
import os      


# Запуск бота
async def main():
    # Включаем логирование, чтобы не пропустить важные сообщения
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    # TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

    #подключаем БД
    db = psql()          

    bot = Bot(token=TELEGRAM_TOKEN, parse_mode='HTML')    
    dp = Dispatcher()

    dp.include_router(handlers.router) # подключаем роутер к диспетчеру    
    
    # Запускаем бота и пропускаем все накопленные входящие
    # Да, этот метод можно вызвать даже если поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)       

if __name__ == "__main__":
    asyncio.run(main())
    