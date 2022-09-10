import logging.config

from aiogram import F, Router, types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove
from logconf import LOGGING_CONFIG
import external_api
import keyboards
from database import Database

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("__name__")
router = Router()  # [1]
db = Database()

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
    if (not db.user_exists(user_id=msg.from_user.id)):
        db.add_user(user_id=msg.from_user.id, full_name=msg.from_user.full_name)
        logger.info("Пользователь уже внесен в БД ранее")
    text = (f'{msg.from_user.first_name}, привет! \U0001F308'
            '\nЕсть поговорка -  прогноз дорог к обеду:)\n'
            'В общем, жмите "Город" или отправляйте своё местоположение.'
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

    logger.info("Cancelling state %r", current_state)
    await state.clear()
    await message.answer(
        "Завершено!\nДля запуска нажми /start",
        reply_markup=ReplyKeyboardRemove()
    )

# хэндлер на "Город" с предложением ввести город
@router.message(Text(text='Город'), content_types="text", state=MenuState.start)
async def type_forecast_menu(msg: types.Message, state: FSMContext) -> None:
    await msg.delete()  
    await state.set_state(MenuState.waiting_city)  
    await msg.answer(text='Введите название населенного пункта.')
    

# хэндлер на название города с предложением уточнить координаты
@router.message(content_types='text', state=MenuState.waiting_city)
async def get_geo(msg: types.Message, state: FSMContext) -> None:
    await msg.answer(text='Определяю координаты...')
    cities = external_api.direct_geocoding(msg.text)    
    if cities:   
        await state.set_state(MenuState.waiting_geo)     
        await msg.answer(text= '<b>Уточните</b>, пожалуйста, ваш выбор:', \
                               reply_markup=await keyboards.add_buttons(cities))                
    else:
        await msg.answer(text='Проверьте, пожалуйста, что вы верно указали населённый пункт и повторите ввод.\n'
                              'Для <b>отмены</b> нажмите /cancel')
        logger.warning('Город %r не распознан', msg.text)

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
    lon=msg.location.longitude
    lat=msg.location.latitude
    cities = external_api.reverse_geocoding(lon=lon, lat=lat)
    if cities: 
        await state.set_state(MenuState.waiting_geo)       
        await msg.answer(text= '<b>Уточни</b>, пожалуйста, свой выбор:', \
                               reply_markup=await keyboards.add_buttons(cities))                
    else:
        await msg.answer(text='Не удалось уточнить координаты.\n'
                              'Для <b>отмены</b> нажми /cancel')
        logger.warning('Не удалось уточнить координаты: %r,%r', lat, lon)

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
    await callback.message.answer_location(latitude=data['lat'], longitude=data['lon'])
    await state.set_state(MenuState.start) 
    await callback.answer() 

# хэндлер для прочего текста
@router.message(state='*')
async def other_cmd(msg: types.Message, state: FSMContext) -> None:
    await state.set_state(MenuState.start)   
    await msg.reply(text='Нажми "Город" или "Отправить моё местоположение"',
                     reply_markup= await keyboards.start_menu())
