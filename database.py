import psycopg2
import logging

from config import host, user, password, db_name


class PSQLRequests:

    def __init__(self) -> None:
        
        try:
            # установим соединение с БД 
            self.conn = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                dbname=db_name
            )
            logging.info("PostgreSQL connection started.") 
            
            # инициализируем объект обработки строк
            self.cur = self.conn.cursor()
             # включение автоматической фиксации изменений
            self.conn.autocommit = True

            self.cur.execute(
                    "SELECT version();"
                )
            print(f"Server version: {self.cur.fetchone()}")  

        except Exception as _ex:
            logging.error("Error while working with PostgreSQL %r", _ex)        
        # finally:
        #     conn.close()
        #     logging.info("PostgreSQL connection closed.")        