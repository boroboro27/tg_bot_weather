import asyncio
from logging import handlers
from aiogram import Bot, Dispatcher
import handlers
import config
import psycopg2
from config import host, user, password, db_name

import logging
import sys 
import os      

def conn_psql():
    try:
        #подключаемся к БД PostgreSQL
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            dbname=db_name
        )
        logging.info("PostgreSQL connection started.")

        #создаем курсор для оперирования БД
        with conn.cursor() as cur:
            cur.execute(
                "SELECT version();"
            )
            print(f"Server version: {cur.fetchone()}")        

    except Exception as _ex:
        logging.error("Error while working with PostgreSQL %r", _ex)        
    finally:
        conn.close()
        logging.info("PostgreSQL connection closed.")        


# Запуск бота
async def main():
    # Включаем логирование, чтобы не пропустить важные сообщения
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    
    #sqlite_db.sql_start()

    # TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

    #подключаем БД
    conn_psql()           

    bot = Bot(token=config.TELEGRAM_TOKEN, parse_mode='HTML')    
    dp = Dispatcher()

    dp.include_router(handlers.router) # подключаем роутер к диспетчеру    
    
    # Запускаем бота и пропускаем все накопленные входящие
    # Да, этот метод можно вызвать даже если поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)       

if __name__ == "__main__":
    asyncio.run(main())


    



    