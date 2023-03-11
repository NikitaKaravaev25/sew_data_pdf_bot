from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_start_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton("/start")],
        [KeyboardButton("/help")]
    ], resize_keyboard=True)
    return kb