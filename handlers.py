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
    await msg.answer(text='Привет! Отправь мне название нужного населённого пункта или своё местоположение.',
                     reply_markup= await keyboards.start_menu())    

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
        "Завершено.",
        reply_markup=ReplyKeyboardRemove()
    )

# хэндлер на "Указать город" с предложением ввести город
@router.message(Text(text='Указать город'), content_types="text")
async def type_forecast_menu(msg: types.Message, state: FSMContext) -> None:
    await msg.delete()    
    await msg.answer(text='Введи и отправь название населенного пункта.')
    await state.set_state(MenuState.waiting_city)

# хэндлер на название города с предложением уточнить координаты
@router.message(content_types='text', state=MenuState.start)
async def get_geo(msg: types.Message, state: FSMContext) -> None:
    await msg.answer(text='Пожалуйста, подожди.\nУточняю координаты...')
    cities = external_api.owm_api_geo(msg.text)    
    if cities:        
        await msg.answer(text= f'Найдены следующие населенные пункты.\n'
                               f'{msg.from_user.first_name}, <b>подтвердите</b>, пожалуйста, ваш выбор:', \
                               reply_markup=await keyboards.add_buttons(cities))
        await state.set_state(MenuState.waiting_geo)        
    else:
        await msg.answer(text='Проверьте, что вы верно указали населённый пункт и повторите ввод.\nДля <b>отмены</b> нажмите /cancel')  



# @router.callback_query(state=MenuState.waiting_period)
# async def callback_period(callback: types.CallbackQuery, state: FSMContext) -> None:     
#     await callback.message.answer('Введите <b><u>название</u></b> населенного пункта:')
#     await state.update_data(period=callback.data)    
#     await state.set_state(MenuState.waiting_city)
#     await callback.answer()

@router.callback_query(keyboards.GeoCallbackFactory.filter(), state=MenuState.waiting_geo)
async def callback_geo(callback: types.CallbackQuery, \
                       state: FSMContext, \
                       callback_data: keyboards.GeoCallbackFactory) -> None: 
    
    await state.update_data(lon=callback_data.lon, lat=callback_data.lat)
    
    await callback.message.answer(text='Выберите нужный <b><u>период</u></b> погоды:', \
                              reply_markup= await keyboards.type_forecast_menu())
    await state.set_state(MenuState.waiting_period)
    await callback.answer()    

# хэндлер на отправленную пользователем геолокацию (без ввода названия города и уточнений)
@router.message(content_types="location", state=MenuState.start)
async def geolocation(msg: types.Location, state: FSMContext) -> None:    
    await msg.answer(text='Выберите нужный <b><u>период</u></b> погоды:', \
                     reply_markup= await keyboards.type_forecast_menu())
    await state.set_state(MenuState.waiting_period)
    await state.update_data(lon=msg.location.longitude, lat=msg.location.latitude)

# хэндлер на выбранный тип погоды
@router.callback_query(state=MenuState.waiting_period)
async def forecast(callback: types.CallbackQuery, state: FSMContext) -> None:
    type_forecast = callback.data
    data = await state.get_data()
    if type_forecast == 'current':
        weather = external_api.get_weather(data)
    elif type_forecast == 'forecast':
        weather = external_api.get_forecast(data)
    await callback.message.answer(weather)
    await state.clear()
    await callback.answer() 

# хэндлер для прочего текста
@router.message(content_types="text", state='*')
async def other_cmd(msg: types.Message, state: FSMContext) -> None:  
    await state.set_state(MenuState.start)  
    await msg.reply(text='Привет! Отправь мне название населённого пункта или своё местоположение.',
                     reply_markup= await keyboards.start_menu())
