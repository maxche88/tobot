from tobot import config
from aiogram import Bot, Dispatcher
import asyncio
from tobot.user_logic import router


# Вместо BOT TOKEN HERE нужно вставить токен вашего бота,
# полученный у @BotFather
BOT_TOKEN = config.API_TOKEN
USER_ID = config.USER_ID

# Создаем объекты бота и диспетчера
bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# Регистрируем маршрутизатор
dp.include_router(router)


# Главная функция
async def main():
    await send_message_to_user()
    await dp.start_polling(bot)


# Функция для отправки сообщения
async def send_message_to_user():
    await bot.send_message(USER_ID, "Я в сети!")
    print("\nБот запущен пользователем.")


# Функция для корректного завершения программы
async def shutdown(dispatcher):
    await bot.session.close()

# Обработчик клавиатурного прерывания
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен пользователем.")
    finally:
        # Завершаем сессию бота
        asyncio.run(shutdown(dp))




