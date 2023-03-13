from aiogram import Bot, Dispatcher
from config import load_config
from aiogram.contrib.fsm_storage.memory import MemoryStorage

config = load_config('.env')
bot_token = config.tg_bot.token
USERS = config.tg_bot.USERS
ADMIN = config.tg_bot.ADMIN

storage = MemoryStorage()
bot = Bot(bot_token)
dp = Dispatcher(bot, storage=storage)
