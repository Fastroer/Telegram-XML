import os
import aiohttp
import asyncio
import xml.etree.ElementTree as ET
import redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import pytz

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
CURRENCY_URL = 'https://www.cbr.ru/scripts/XML_daily.asp'
MOSCOW_TZ = pytz.timezone('Europe/Moscow')

async def fetch_currency_data():
    """
    Асинхронная функция для получения XML файла с курсами валют с сайта ЦБ РФ.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(CURRENCY_URL) as response:
            return await response.text()

def parse_currency_data(xml_data):
    """
    Парсит XML данные и возвращает словарь с курсами валют.
    
    :param xml_data: строка с XML данными
    :return: словарь с курсами валют
    """
    root = ET.fromstring(xml_data)
    currency_dict = {}
    for currency in root.findall('Valute'):
        code = currency.find('CharCode').text
        value = float(currency.find('Value').text.replace(',', '.'))
        currency_dict[code] = value
    return currency_dict

def update_redis(currency_dict):
    """
    Обновляет курсы валют в Redis.
    
    :param currency_dict: словарь с курсами валют
    """
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    for code, value in currency_dict.items():
        redis_client.set(code, value)

async def update_currency_rates():
    """
    Основная функция для получения и обновления курсов валют.
    """
    xml_data = await fetch_currency_data()
    currency_dict = parse_currency_data(xml_data)
    update_redis(currency_dict)

def schedule_tasks():
    """
    Планирует задачи с использованием APScheduler.
    """
    scheduler = AsyncIOScheduler(timezone=MOSCOW_TZ)
    scheduler.add_job(update_currency_rates, 'cron', hour=0, minute=0)
    scheduler.start()
    return scheduler

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(update_currency_rates())
    scheduler = schedule_tasks()
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
