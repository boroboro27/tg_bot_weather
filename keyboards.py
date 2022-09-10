from aiogram.dispatcher.filters.callback_data import CallbackData
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

#from typing import Optional #если нужно сделать одно из значений фабрики не обязательным
# например,
# class NumbersCallbackFactory(CallbackData, prefix="fabnum"):
#     action: str
#     value: Optional[int]

# Создаем класс для колбэк-фабрики
# Префикс — это общая подстрока в начале, 
# по которой фреймворк будет определять, какая структура лежит в колбэке.
class GeoCallbackFactory(CallbackData, prefix="geo"):
    lat: str
    lon: str

async def add_buttons(data: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()    
    for item in data.values():
        btn_text = f"{item['name']}, {item['country']} {item['state']}"  # текст кнопки
        btn_callback = GeoCallbackFactory(lat=item['geo']['lat'], lon=item['geo']['lon'])  # создаем коллбек-фабрику (словарь)
        builder.add(InlineKeyboardButton(text=btn_text, callback_data=btn_callback.pack())) # запакуем коллбек фабрику в строку 
    
    builder.adjust(1) # Выравниваем кнопки по 1 в ряд
    return builder.as_markup()   # преобразуем объект-билдер в клавиатуру

async def type_forecast_menu() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text='Текущая погода', callback_data="current"),
            InlineKeyboardButton(text="Прогноз", callback_data="forecast")
        ]
    ]        
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    return keyboard 

async def start_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    # метод row позволяет явным образом сформировать ряд
    # из одной или нескольких кнопок. Например, первый ряд
    # будет состоять из двух кнопок...
    builder.row(
        KeyboardButton(text='Город'),
        KeyboardButton(text='Отправить моё местоположение', request_location=True)
    )

    return builder.as_markup(resize_keyboard=True)
