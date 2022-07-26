import logging
from datetime import datetime, timedelta, timezone

import pycountry  # docs https://pypi.org/project/pycountry/
import pymorphy2
import requests

import config
from weather_pics import code_to_unipic

logger = logging.getLogger(__name__)

# OWM_TOKEN= os.getenv('OWM_TOKEN')
# MTT_TOKEN= os.getenv('MTT_TOKEN')

def mtt_api(text: str) -> str:
    '''Microsoft Translator Text API 
    https://rapidapi.com/ru/microsoft-azure-org-microsoft-cognitive-services/api/microsoft-translator-text/
    '''       
    
    try:
        url = "https://microsoft-translator-text.p.rapidapi.com/translate"

        querystring = {
            "to[0]":"ru",
            "api-version":"3.0",
            "from":"en",
            "profanityAction":"NoAction",
            "textType":"plain"
        }

        payload = [{"Text": text}]
        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": config.MTT_TOKEN,
            "X-RapidAPI-Host": "microsoft-translator-text.p.rapidapi.com"
        }

        response = requests.request(
            "POST", 
            url, 
            json=payload, 
            headers=headers, 
            params=querystring
        )

        if response.status_code != 200:
            logger.error(
                'Microsoft Translator Text API: код %r на POST-запрос: %r',
                response.status_code, 
                querystring
            )            
        
        return response.json()
    except Exception as _ex:
        logger.error('Microsoft Translator Text API: %r', _ex)


def direct_geocoding(city: str) -> dict:
    '''OpenWeather Direct Geocoding API
    https://openweathermap.org/api/geocoding-api
    '''
    
    try:
        response = requests.get(
            f'http://api.openweathermap.org/geo/1.0/direct?q={city}&limit={10}&appid={config.OWM_TOKEN}'
        )
        if response.status_code != 200:
            logger.error(
                'OpenWeather Direct Geocoding API: ответ код %r на геокодирование города: %r',
                response.status_code, 
                city
            )
            dict_full = {}
            return dict_full        
        
        dict_full = parse_geocode(response.json())
        return dict_full 
        
    except Exception as _ex:
        logger.error('OpenWeather Direct Geocoding API: %r', _ex)

def reverse_geocoding(lon: str, lat: str) -> dict:
    '''OpenWeather Reverse Geocoding API
    https://openweathermap.org/api/geocoding-api
    '''
    
    try:
        response = requests.get(
            f'http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=10&appid={config.OWM_TOKEN}'
        )
        if response.status_code != 200:
            logger.error(
                'OpenWeather Reverse Geocoding API: ответ код %r на обратное геокодирование координат: %r, %r',
                response.status_code, 
                lat,
                lon
            )
            dict_full = {}
            return dict_full

        dict_full = parse_geocode(response.json())
        return dict_full
        
    except Exception as _ex:
        logger.error('OpenWeather Reverse Geocoding API: %r', _ex)

def parse_geocode(data: dict) -> dict:   
    dict_all = {} # новый словарь словарей для переведённых на русский язык результатов парсинга             
    counter = 0
    for city in data:  
        # новый словарь для каждого отдельного варианта города       
        dict_one = {counter : {"name" : '', "state" : "", "country" : "", "geo" : {"lat" : "", "lon" : ""}}}            
        try: 
            dict_one[counter]['name'] = city['local_names']['ru'] # город уже сразу на русском языке
        except:
            dict_one[counter]['name'] = mtt_api(city['name'])[0]['translations'][0]['text']  # перевод города

        try:             
            dict_one[counter]['state'] = mtt_api(city['state'])[0]['translations'][0]['text'] # перевод региона
        except:
            dict_one[counter]['state'] = ''

        #координаты для коллбэков в инлайн кнопки и отправки уточненной геопозиции       
        dict_one[counter]['geo']['lat'] = city['lat']
        dict_one[counter]['geo']['lon'] = city['lon']

        #получаем объект страны из api iso3166 (коды стран мира)
        try:
            country_iso3166 = pycountry.countries.get(alpha_2=city['country']) 
            country = mtt_api(country_iso3166.name)[0]['translations'][0]['text']  #перевод названия страны
            if country == 'Российская Федерация': country = 'РФ'
            dict_one[counter]['country'] = country
        except Exception as _ex:
            logger.error('pycountry (iso3166): %r', _ex)

        dict_all.update(dict_one) # добавляем отдельный словарь в общий
        counter += 1

    return dict_all
      
def get_weather(geo: dict) -> str:
    '''OpenWeather Current Weather API
    https://openweathermap.org/current
    '''    

    try:
        response = requests.get('https://api.openweathermap.org/data/2.5/weather',
                                params={"lat" : geo['lat'], 
                                "lon" : geo['lon'],
                                "appid" : config.OWM_TOKEN, 
                                "units" : "metric", 
                                "lang" : "ru"}
                            )
        
        if response.status_code != 200:
            logger.error(
                'OpenWeather Current Weather API: ответ код %r на координаты: %r, %r',
                response.status_code, 
                geo['lat'],
                geo['lon']
            )

        text = parse_weather(response.json())
        return text
        
    except Exception as _ex:
        logger.error('OpenWeather Current Weather API: %r', _ex)

def parse_weather(data: dict)-> str: 

    #city = mtt_api(data["name"])[0]['translations'][0]['text'] #Название населенного пункта на русском языке
    city = data["name"] #Название населенного пункта на русском языке       
    cur_weather = int(round(data["main"]["temp"])) #Температура воздуха

    # weather = data["weather"][0]["main"] #короткое описание погоды
    weather_id = data["weather"][0]["id"] #код погоды для выбора картинки
    weather_description = data["weather"][0]["description"] #подробное описание погоды на русском языке        
    
    # определение направления ветра
    winddirections = ("С.", "С-В", "В.", "Ю-В", "Ю.", \
                        "Ю-З", "З.", "С-З")
    direction = int((data["wind"]["deg"] + 22.5) // 45 % 8)
    wind_deg = winddirections[direction]
    wind_speed = int(round(data["wind"]["speed"])) #скорость ветра

    humidity = data["main"]["humidity"] #влажность
    pressure = int(round((data["main"]["pressure"] * 3 / 4))) #давление
    

    #создание объекта часового пояса для сдвига относитьно UTC
    tz = timezone(timedelta(seconds=data["timezone"]))
    
    #Рассвет и закат по UTC, скорректированные на часовой пояс региона погоды
    sunrise = datetime.fromtimestamp(data["sys"]["sunrise"], tz=tz).strftime('%H:%M:%S')
    sunset = datetime.fromtimestamp(data["sys"]["sunset"], tz=tz).strftime('%H:%M:%S')
    
    #Продолжительность светового дня
    len_day = datetime.fromtimestamp(data["sys"]["sunset"], tz=tz) - \
                        datetime.fromtimestamp(data["sys"]["sunrise"], tz=tz)

    try:
        morph = pymorphy2.MorphAnalyzer()
        city = morph.parse(city)[0]
        city = city.inflect({'loct'}).word
    except Exception as _ex:
        logger.warning('pymorphy2: %r', _ex)
        city = data["name"]

    text = (f"*** {datetime.now(tz=tz).strftime('%d.%m.%Y %H:%M')} ***\n"
            f"Погода сейчас в <b>{city.capitalize()}</b>\nТемпература: {cur_weather}C° {weather_description} {code_to_unipic[weather_id]}\n"
            f"Влажность: {humidity}%\nДавление: {pressure} мм.рт.ст\nВетер: {wind_deg} {wind_speed} м/с\n"
            f"Восход солнца: {sunrise}\nЗакат солнца: {sunset}\n"
            f"Продолжительность дня: {len_day}\n"
            f"<u><b>Хорошего дня!</b></u>"
            )             

    return text    

def get_forecast(geo: dict) -> str:
    '''OpenWeather 5Day/3Hour Forecast API
    https://openweathermap.org/forecast5
    '''
        
    try:
        response = requests.get('https://api.openweathermap.org/data/2.5/forecast',
                         params={"lat" : geo['lat'],
                                 "lon" : geo['lon'],
                                 'appid': config.OWM_TOKEN,
                                 'units': 'metric',
                                 'lang': 'ru'
                         }
                    )

        if response.status_code != 200:
            logger.error(
                'OpenWeather 5Day/3Hour Forecast API: ответ код %r на координаты: %r, %r',
                response.status_code, 
                geo['lat'],
                geo['lon']
            )
        text = parse_forecast(response.json())
        return text        

    except Exception as _ex:
        logger.error('OpenWeather 5Day/3Hour Forecast API: %r', _ex)

def parse_forecast(data: dict)-> str:
        
    city = data["city"]["name"]
    tz = timezone(timedelta(seconds=data["city"]["timezone"]))
    sunrise = datetime.fromtimestamp(data["city"]["sunrise"], tz=tz).strftime('%H:%M:%S')
    sunset = datetime.fromtimestamp(data["city"]["sunset"], tz=tz).strftime('%H:%M:%S')
    len_day = datetime.fromtimestamp(data["city"]["sunset"], tz=tz) - \
                            datetime.fromtimestamp(data["city"]["sunrise"], tz=tz)

    today = datetime.now(tz=tz)
    tomorrow = datetime.now(tz=tz) + timedelta(days=1)
    time_limit = datetime.now(tz=tz).replace(hour=20, minute=00, second=00, microsecond=0)
    if today < time_limit:
        day_forecast = today
    else:
        day_forecast = tomorrow

    try:
        morph = pymorphy2.MorphAnalyzer()
        city = morph.parse(city)[0]
        city = city.inflect({'loct'}).word
    except Exception as _ex:
        logger.warning('pymorphy2: %r', _ex)
        city = data["city"]["name"]

    text = f"Погода в {city.capitalize()}, {day_forecast.strftime('%d-%m-%Y')}"

    for item in data['list']:                   

        dt = datetime.fromtimestamp(item['dt'], tz=tz)
        temper = int(round(item["main"]["temp"]))            
        weather = item["weather"][0]["main"] #короткое описание погоды
        weather_id = item["weather"][0]["id"] #код погоды для выбора картинки
        weather_description = item["weather"][0]["description"] #подробное описание погоды на русском языке 
        
        winddirections = ("С.", "С-В", "В.", "Ю-В", "Ю.", \
                            "Ю-З", "З.", "С-З")
        direction = int((item["wind"]["deg"] + 22.5) // 45 % 8)
        wind_deg = winddirections[direction]
        wind_speed = int(round(item["wind"]["speed"]))
        humidity = item["main"]["humidity"]
        pressure = int(round((item["main"]["pressure"] * 3 / 4)))
        
        if dt.strftime('%d-%m-%Y') == day_forecast.strftime('%d-%m-%Y'):
            text = (text + \
                    f"\n{dt.strftime('%H:%M')} {code_to_unipic[weather_id]} {temper}C°, "
                    f"{wind_deg} {wind_speed} м/с.") 
    return text 

        
    
        
        