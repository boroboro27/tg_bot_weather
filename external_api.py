import requests
import pycountry # docs https://pypi.org/project/pycountry/
import datetime
import json
from  pprint import pprint
#from yattag import Doc
from weather_pics import code_to_unipic
import config

# OWM_TOKEN= os.getenv('OWM_TOKEN')
# MTT_TOKEN= os.getenv('MTT_TOKEN')

def mtt_api(text: str) -> str:
    '''Microsoft Translator Text API 
    https://rapidapi.com/ru/microsoft-azure-org-microsoft-cognitive-services/api/microsoft-translator-text/'''       
    
    try:
        url = "https://microsoft-translator-text.p.rapidapi.com/translate"

        querystring = {"to[0]":"ru","api-version":"3.0","from":"en","profanityAction":"NoAction","textType":"plain"}

        payload = [{"Text": text}]
        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": config.MTT_TOKEN,
            "X-RapidAPI-Host": "microsoft-translator-text.p.rapidapi.com"
        }

        response = requests.request("POST", url, json=payload, headers=headers, params=querystring)

        if response.status_code != 200:
            return '<ошибка на сервере Microsoft Translator Text API>'
        
        return response.json()
    except Exception as ex:
        print(f'error mtt_api: {ex}')
    except requests.ConnectionError:
        return '<сетевая ошибка Microsoft Translator Text API>'

def owm_api_geo(city: str) -> dict:
    '''OpenWeather Geocoding API
    https://openweathermap.org/api/geocoding-api'''
    dict_full = {} # новый словарь словарей для переведённых на русский язык результатов парсинга
    try:
        r = requests.get(
            f'http://api.openweathermap.org/geo/1.0/direct?q={city}&limit={10}&appid={config.OWM_TOKEN}'
        )
        if r.status_code != 200:
            return '<ошибка на сервере OpenWeather Geocoding API>'

        data = r.json()        
        counter = 0
        for city in data:  
            # новый словарь для отдельного варианта города       
            dict_one = {counter : {"name" : '', "state" : "", "country" : "", "geo" : {"lat" : "", "lon" : ""}}}            
            try: 
                dict_one[counter]['name'] = city['local_names']['ru'] # город уже сразу на русском языке
            except:
                dict_one[counter]['name'] = mtt_api(city['name'])[0]['translations'][0]['text']  # перевод города

            try:             
                dict_one[counter]['state'] = mtt_api(city['state'])[0]['translations'][0]['text'] # перевод региона
            except:
                pass  

            #координаты для коллбэков в инлайн кнопки и отправки уточненной геопозиции       
            dict_one[counter]['geo']['lat'] = city['lat']
            dict_one[counter]['geo']['lon'] = city['lon']

            #получаем объект страны из api iso3166 (коды стран мира)
            country_iso3166 = pycountry.countries.get(alpha_2=city['country']) 
            country = mtt_api(country_iso3166.name)[0]['translations'][0]['text']  #перевод названия страны
            if country == 'Российская Федерация': country = 'Россия'
            dict_one[counter]['country'] = country

            dict_full.update(dict_one) # добавляем отдельный словарь в общий
            counter += 1

        return dict_full 
        
    except Exception as ex:
        print(ex)
        return False
        #добавить логирование
    except requests.ConnectionError:
        return '<сетевая ошибка>'

def get_weather(geo: dict) -> str:
    '''OpenWeather Current Weather API
    https://openweathermap.org/current'''    

    try:
        r = requests.get('https://api.openweathermap.org/data/2.5/weather',
                          params={"lat" : geo['lat'], "lon" : geo['lon'], "appid" : config.OWM_TOKEN, "units" : "metric", "lang" : "ru"}
        )
        
        if r.status_code != 200:
            return '<ошибка на сервере погоды>'

        data = r.json()
        pprint(data)


        city = mtt_api(data["name"])[0]['translations'][0]['text'] #Название населенного пункта на русском языке
        cur_weather = round(data["main"]["temp"], 0) #Температура воздуха

        # weather = data["weather"][0]["main"] #короткое описание погоды
        weather_id = data["weather"][0]["id"] #код погоды для выбора картинки
        weather_description = data["weather"][0]["description"] #подробное описание погоды на русском языке        
        
        # определение направления ветра
        winddirections = ("Сев.", "С-В", "Вост.", "Ю-В", "Юж.", \
                          "Ю-З", "Зап.", "С-З")
        direction = int((data["wind"]["deg"] + 22.5) // 45 % 8)
        wind_deg = winddirections[direction]

        humidity = data["main"]["humidity"] #влажность
        pressure = round((data["main"]["pressure"] * 3 / 4), 0) #давление
        wind_speed = round(data["wind"]["speed"], 0) #скорость ветра

        #создание объекта часового пояса для сдвига относитьно UTC
        tz = datetime.timezone(datetime.timedelta(seconds=data["timezone"]))
        
        #Рассвет и закат по UTC, скорректированные на часовой пояс региона погоды
        sunrise_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunrise"], tz=tz).strftime('%H:%M:%S')
        sunset_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunset"], tz=tz).strftime('%H:%M:%S')
        
        #Продолжительность светового дня
        length_of_the_day = datetime.datetime.fromtimestamp(data["sys"]["sunset"], tz=tz) - \
                            datetime.datetime.fromtimestamp(data["sys"]["sunrise"], tz=tz)

        text = (f"*** {datetime.datetime.now(tz=tz).strftime('%d.%m.%Y %H:%M')} ***\n"
                f"Погода сейчас в <b>{city}</b>\nТемпература: {cur_weather}C° {weather_description} {code_to_unipic[weather_id]}\n"
                f"Влажность: {humidity}%\nДавление: {pressure} мм.рт.ст\nВетер: {wind_deg} {wind_speed} м/с\n"
                f"Восход солнца: {sunrise_timestamp}\nЗакат солнца: {sunset_timestamp}\n"
                f"Продолжительность дня: {length_of_the_day}\n"
                f"<u><b>Хорошего дня!</b></u>"
                )             

        return text

    except Exception as ex:
        print(ex)
    except requests.ConnectionError:
        return '<сетевая ошибка (ошибка соединения)>'

def get_forecast(geo: dict, timestamps: int) -> str:
    '''OpenWeather 5Day/3Hour Forecast API
    https://openweathermap.org/forecast5'''
    geo_list = geo.split('_')
    
    try:
        r = requests.get('https://api.openweathermap.org/data/2.5/forecast',
            params={"lat" : geo['lat'], "lon" : geo['lon'], 'appid': config.OWM_TOKEN, \
                    'cnt': timestamps, 'units': 'metric', 'lang': 'ru'}
        )

        if r.status_code != 200:
            return '<ошибка на сервере OpenWeather 5Day/3Hour Forecast API>'
        data = r.json()

        text = ''
        city = mtt_api(data["city"]["name"])[0]['translations'][0]['text']

        for i in data['list']:                   

            
            forecast_temp = round(data["main"]["temp"], 0)

            weather = data["weather"][0]["main"]
            # if weather in code_to_smile:
            #     wpic = code_to_smile[weather]
            # else:
            #     wpic = code_to_smile['other']

            weather_icon = data["weather"][0]["icon"]
            
            winddirections = ("С", "С-В", "В", "Ю-В", "Ю", \
                              "Ю-З", "З", "С-З")
            direction = int((data["wind"]["deg"] + 22.5) // 45 % 8)
            wind_deg = winddirections[direction]

            humidity = data["main"]["humidity"]
            pressure = round((data["main"]["pressure"] * 3 / 4), 0)
            wind_speed = round(data["wind"]["speed"], 0)
            tz = datetime.timezone(datetime.timedelta(seconds=data["city"]["timezone"]))
            sunrise_timestamp = datetime.datetime.fromtimestamp(data["city"]["sunrise"], tz=tz).strftime('%H:%M:%S')
            sunset_timestamp = datetime.datetime.fromtimestamp(data["city"]["sunset"], tz=tz).strftime('%H:%M:%S')
            length_of_the_day = datetime.datetime.fromtimestamp(data["city"]["sunset"], tz=tz) - \
                                datetime.datetime.fromtimestamp(data["city"]["sunrise"], tz=tz)

            # text = (f"*** {datetime.datetime.now(tz=tz).strftime('%d.%m.%Y %H:%M')} ***\n"
            #         f"Погода сейчас в : {city}\nТемпература: {cur_weather}C° {wd}\n"
            #         f"Влажность: {humidity}%\nДавление: {pressure} мм.рт.ст\nВетер: {wind_deg} {wind_speed} м/с\n"
            #         f"Восход солнца: {sunrise_timestamp}\nЗакат солнца: {sunset_timestamp}\n"
            #         f"Продолжительность дня: {length_of_the_day}\n"
            #         f"Хорошего дня!"
            #         )


            # doc, tag, text = Doc().tagtext()
        # with tag('h1'):
        #     text('Заголовок первого уровня')
        #     with tag('h2'):
        #         text('Заголовок второго уровня')
        # text = '''
        #         <!DOCTYPE html>
        #         <html>
        #         <head>
        #             <title>be1.ru</title>
        #         </head>
        #         <body>
        #         <p>ыва</p>
        #         </body>
        #         </html>''' 

            text = f'{text}\n' + (i['dt_txt'] + '{0:+3.0f}'.format(i['main']['temp']) + i['weather'][0]['description'])

        return text        

    except Exception as ex:
        print(ex)
    except requests.ConnectionError:
        return '<сетевая ошибка>'
        