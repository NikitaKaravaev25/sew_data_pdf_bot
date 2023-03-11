from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_start_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton("/start")]
    ], resize_keyboard=True)
    return kb