import string
import random


class User:

    def __init__(self, name: str, age: int) -> None:
        """Конструктор класса

        Args:
            name (str): Имя пользователя
            age (int): Возраст (полных лет)
        """
        self.name = name
        self.age = age
    
    def is_adult(self) -> bool:
        """Проверяет, что пользователь является совершеннолетним

        Returns:
            bool: Да или нет
        """
        if self.age >= 18:
            return True
        return False
    
    @staticmethod
    def generate_password(length: int) -> str:
        """Генерирует случайный пароль из букв и цифр

        Args:
            length (int): Необходимая длина пароля

        Returns:
            str: Сгенерированный пароль
        """
        char_list = list(string.ascii_letters + string.digits)        
        pswd = []
        for _ in range(length):
            pswd.append(random.choice(char_list))
        random.shuffle(pswd)
        return "".join(pswd)
    
    def get_name(self) -> str:
        """Возвращает имя пользователя

        Returns:
            str: Имя пользователя
        """
        return self.name

import json
from pprint import pprint

def parse_json(jsonstr: str) -> None:
try:
    result = json.loads(jsonstr)
    pprint(result)
except Exception as _ex:
    print("некорректный JSON.")

parse_json('[{"phone": "01", "name": "John"}, "2", {"phone": "033", "name": "Vasya"}, "4", {"phone": "777", "name": "Daniel"}]')