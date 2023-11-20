from aiogram import executor
from create_bot import dp
from Bot_cost.handlers.client import register_handler_client


async def on_startup(_):
    print("БОТ ЗАПУЩЕН")

register_handler_client(dp)

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)

