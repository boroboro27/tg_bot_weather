from aiogram.dispatcher.filters import Text
from aiogram import types, Router, F
from aiogram.types import ReplyKeyboardRemove
from aiogram.dispatcher.fsm.context import FSMContext 
from aiogram.dispatcher.fsm.state import State, StatesGroup

import external_api
import keyboards
from controller import logging

router = Router()  # [1]

class MenuState(StatesGroup):
    start = State()  
    waiting_city = State()
    waiting_geo = State()
    waiting_period = State()

# В aiogram 3.x если не указать фильтр content_types, 
# то хэндлер сообщения сработает даже на картинку с подписью /start
@router.message(content_types="text", commands='start')
async def start_cmd(msg: types.Message, state: FSMContext) -> None:  
    await state.set_state(MenuState.start) 
    text = (f'{msg.from_user.first_name}, привет! У природы нет плохой погоды!\U0001F308'
            '\nА прогноз дорог к обеду:)\n'
            'В общем, отправь мне название нужного населённого пункта или своё местоположение.'
    ) 
    await msg.answer(text=text, reply_markup= await keyboards.start_menu())    

# даём возможность отмены действий
@router.message(commands=["cancel"])
@router.message(F.text.casefold() == "cancel")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    await state.clear()
    await message.answer(
        "Завершено!\nДля запуска нажми /start",
        reply_markup=ReplyKeyboardRemove()
    )

# хэндлер на "Город" с предложением ввести город
@router.message(Text(text='Город'), content_types="text", state=MenuState.start)
async def type_forecast_menu(msg: types.Message, state: FSMContext) -> None:
    #await msg.delete()    
    await msg.answer(text='Введи название населенного пункта.')
    await state.set_state(MenuState.waiting_city)

# хэндлер на название города с предложением уточнить координаты
@router.message(content_types='text', state=MenuState.waiting_city)
async def get_geo(msg: types.Message, state: FSMContext) -> None:
    await msg.answer(text='Пожалуйста, немного подожди.\nОпределяю координаты...')
    cities = external_api.direct_geocoding(msg.text)    
    if cities:   
        await state.set_state(MenuState.waiting_geo)     
        await msg.answer(text= 'Нашёл следующие населенные пункты.\n'
                               '<b>Уточни</b>, пожалуйста, свой выбор:', \
                               reply_markup=await keyboards.add_buttons(cities))                
    else:
        await msg.answer(text='Проверь, пожалуйста, что ты верно указал населённый пункт и повтори ввод.\n'
                              'Для <b>отмены</b> нажми /cancel')

@router.callback_query(keyboards.GeoCallbackFactory.filter(), state=MenuState.waiting_geo)
async def callback_geo(callback: types.CallbackQuery, \
                       state: FSMContext, \
                       callback_data: keyboards.GeoCallbackFactory) -> None: 
    
    await state.update_data(lon=callback_data.lon, lat=callback_data.lat)
    
    await callback.message.answer(text='Выбери нужный <b>тип</b> погоды:', \
                              reply_markup= await keyboards.type_forecast_menu())
    await state.set_state(MenuState.waiting_period)
    await callback.answer()    

# хэндлер на отправленную пользователем геолокацию (без ввода названия города и уточнений)
@router.message(content_types="location", state=MenuState.start)
async def get_geolocation(msg: types.Location, state: FSMContext) -> None:
    cities = external_api.reverse_geocoding(lon=msg.location.longitude, lat=msg.location.latitude)
    if cities: 
        await state.set_state(MenuState.waiting_geo)       
        await msg.answer(text= 'Нашёл следующие населенные пункты.\n'
                               '<b>Уточни</b>, пожалуйста, свой выбор:', \
                               reply_markup=await keyboards.add_buttons(cities))                
    else:
        await msg.answer(text='Не удалось уточнить координаты.\n'
                              'Для <b>отмены</b> нажми /cancel')

# хэндлер на выбранный тип погоды
@router.callback_query(state=MenuState.waiting_period)
async def forecast(callback: types.CallbackQuery, state: FSMContext) -> None:
    type_forecast = callback.data
    data = await state.get_data()
    if type_forecast == 'current':
        weather = external_api.get_weather(data)
    elif type_forecast == 'forecast':
        weather = external_api.get_forecast(data)
    await callback.message.answer(weather, reply_markup= await keyboards.start_menu())
    await state.set_state(MenuState.start) 
    await callback.answer() 

# хэндлер для прочего текста
@router.message(content_types="text", state='*')
async def other_cmd(msg: types.Message, state: FSMContext) -> None:
    await state.set_state(MenuState.start)   
    await msg.reply(text='Выбери "Город" или "Отправить моё местоположение"',
                     reply_markup= await keyboards.start_menu())
