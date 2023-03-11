from aiogram import types, Dispatcher
from create_bot import bot, ADMINS
from logic.client_logic import get_link
from keyboards.client_kb import get_start_kb
from aiogram.dispatcher.storage import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

import re

import requests
import os


async def get_admins(message: types.Message):
    global ADMINS
    if message.from_user.id == ADMINS[0]:
        with open('.env', 'r+') as env_file:
            env_lines = env_file.readlines()
            for i, line in enumerate(env_lines):
                if line.startswith('ADMIN_IDS'):
                    ADMINS = line[len('ADMIN_IDS='):].strip().split(',')
                    ADMINS = list(map(int, ADMINS))

class UserStatesGroup(StatesGroup):
    add_user = State()

async def help_command_client(message: types.Message) -> None:
    if message.from_user.id in ADMINS:
        await message.answer(
            f"Это бот для получения полных технических данных оборудования SEW по серийному номеру в формате pdf.\n"
            f"VPN запускать не обязательно!\n"
            f"Для начала нажми /start",
            reply_markup=get_start_kb())


async def start_command_client(message: types.Message) -> None:
    if message.from_user.id in ADMINS:
        await message.answer(f"Привет, {message.from_user.first_name}!\n"
                             f"Пришли мне серийный номер:",
                             reply_markup=get_start_kb())
    else:
        await message.answer(f"Привет, {message.from_user.first_name}!\n"
                             f"Запрос на доступ к функционалу бота отправлен!",
                             reply_markup=get_start_kb())

        await bot.send_message(ADMINS[0], text=f"Запрос на доступ от:\n"
                                               f"Username: {message.from_user.username}\n"
                                               f"id: {message.from_user.id}\n"
                                               f"full_name: {message.from_user.first_name}")


async def add_user(message: types.Message):
    if message.from_user.id == ADMINS[0]:
        await message.reply("Кого добавляем?")
        await UserStatesGroup.add_user.set()


async def set_user(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMINS[0]:
        with open('.env', 'r+') as env_file:
            env_lines = env_file.readlines()

            for i, line in enumerate(env_lines):
                if line.startswith('ADMIN_IDS'):

                    users = line[len('ADMIN_IDS='):].strip().split(',')

                    if message.text not in users:
                        users.append(message.text)

                    env_lines[i] = f"ADMIN_IDS={','.join(users)}\n"
                    env_file.seek(0)
                    env_file.writelines(env_lines)
                    env_file.truncate()
                    await message.reply(f"Пользователь {message.text} успешно добавлен!")
                    await bot.send_message(message.text, f"Доспут открыт!\n"
                                                         f"Нажми /start")
                    await state.finish()
                    await get_admins(message)
                    return
        await message.reply("Не удалось найти переменную ADMIN_IDS в файле .env.")


async def check_serial_number(message: types.Message) -> None:
    if message.from_user.id in ADMINS:
        if not re.match(r"\d{2}\.\d{10}\.\d{4}\.\d{2}", message.text):
            await message.reply("Неверный формат серийного номера!\n"
                                "Попробуй ещё раз!")
        else:
            await get_link_to(message)


async def get_link_to(message: types.Message) -> None:
    if message.from_user.id in ADMINS:
        await message.reply("Файл загрузится через 10 секунд!")
        await bot.send_message(ADMINS[0], text=f"Username: {message.from_user.username}\n"
                                               f"Выполнил запрос {message.text}")
        link = get_link(message.text)
        if link == "Error":
            await message.reply(f"Что-то пошло не так!\n"
                                f"Попробуй ещё раз!")
        else:
            pdf_name = message.text + ".pdf"
            pdf_path = f"{os.getcwd()}/{pdf_name}"

            with open(pdf_path, 'wb') as f:
                f.write(requests.get(link).content)

            with open(pdf_path, 'rb') as f:
                await bot.send_document(message.chat.id, f)

            await bot.send_message(ADMINS[0],
                                   text=f"Ответ на запрос от  {message.from_user.username} выполнен успешно!")
            os.remove(pdf_path)


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(help_command_client, commands=['help'])
    dp.register_message_handler(start_command_client, commands=['start'])
    dp.register_message_handler(add_user, commands=['add_user'])
    dp.register_message_handler(get_admins, commands=['get_admins'])
    dp.register_message_handler(set_user, state=UserStatesGroup.add_user)
    dp.register_message_handler(check_serial_number)
    dp.register_message_handler(get_link_to)
