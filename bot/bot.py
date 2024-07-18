import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import redis
import os

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')

bot = Bot(token=os.getenv('TELEGRAM_API_TOKEN'))
dispatcher = Dispatcher()
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

@dispatcher.message(F.text, Command("exchange"))
async def handle_exchange_command(message: types.Message):
    """
    Обрабатывает команду /exchange для конвертации валют.
    Пример команды: /exchange USD RUB 10
    """
    try:
        _, from_currency, to_currency, amount = message.text.split()
        amount = float(amount)

        from_rate = redis_client.get(from_currency)
        to_rate = redis_client.get(to_currency)

        if from_rate is None or to_rate is None:
            await message.reply(f'Не удалось найти курс для {from_currency} или {to_currency}')
            return

        from_rate = float(from_rate.decode('utf-8'))
        to_rate = float(to_rate.decode('utf-8'))
        
        result = amount * from_rate / to_rate
        await message.reply(f'{amount} {from_currency} = {result:.2f} {to_currency}')
    except ValueError:
        await message.reply('Неверный формат команды. Используйте: /exchange <FROM> <TO> <AMOUNT>')
    except Exception as error:
        await message.reply(f'Ошибка: {str(error)}')

@dispatcher.message(F.text, Command("rates"))
async def handle_rates_command(message: types.Message):
    """
    Обрабатывает команду /rates для получения актуальных курсов валют.
    """
    try:
        keys = redis_client.keys('*')
        if not keys:
            await message.reply('Не удалось получить курсы валют. Попробуйте позже.')
            return

        rates = [f'{key.decode("utf-8")}: {redis_client.get(key).decode("utf-8")}' for key in keys]
        await message.reply('\n'.join(rates))
    except Exception as error:
        await message.reply(f'Ошибка: {str(error)}')

async def main():
    """
    Основная функция для запуска бота.
    """
    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
