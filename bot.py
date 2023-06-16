from aiogram import executor

from create_bot import dp
from db import db_control

async def on_startup(_):
    await db_control.db_connect()
    print("The bot has been started successfully!")


from handlers import client

client.register_handlers_client(dp)

if __name__ == "__main__":
    executor.start_polling(dp,
                           on_startup=on_startup,
                           skip_updates=True)
