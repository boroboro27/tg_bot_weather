import logging

import psycopg2

from config import db_name, host, password, user

logger = logging.getLogger(__name__)

class Database:
    """ 
    Класс для работы с БД 
    """

    def __init__(self):        
        try:
            # установим соединение с БД 
            self.conn = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                dbname=db_name
            )                     
             # включение автоматической фиксации изменений
            self.conn.autocommit = True
            logger.info("DB connection started.")
        except Exception as _ex:
            logger.error("Error during DB connection initiation: %s", _ex)  

    def close(self):
        self.conn.close()
        logger.info("DB connection closed.")

    def add_user(self, user_id, full_name):
        try:
            with self.conn.cursor() as curs:
                curs.execute("INSERT INTO tg_bot_weather_users (user_id, full_name) VALUES (%s, %s);", (user_id, full_name))
        except Exception as _ex:
            logger.error("Error while adding user in DB: %s", _ex)        
    
    def user_exists(self, user_id) -> bool:
        try:
            with self.conn.cursor() as curs:
                    result = curs.execute("SELECT * FROM tg_bot_weather_users WHERE user_id = %s;", (user_id,))  
                    result = curs.fetchall()

            return bool(len(result))

        except Exception as _ex:
            logger.error("Error while adding user in DB: %s", _ex)
        