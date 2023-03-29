from aiogram import types, Dispatcher
from create_bot import bot, USERS, ADMIN
from logic.client_logic import get_link
from keyboards.client_kb import get_start_kb, get_cancel
from aiogram.dispatcher.storage import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
import asyncio

import re

import requests
import os

texts = {"help": "Это бот для получения полных технических данных оборудования SEW по серийному номеру.\n\n"
                 "Работает без VPN!\n\n"
                 "Отправь боту sn в формате XX.XXXXXXXXXX.XXXX.XX и получи pdf.\n\n"
                 "Для начала нажми /start\n\n"
                 "Администратор @Karavaev_Nikita"}


async def get_users(message: types.Message):
    global USERS
    with open('.env', 'r') as env_file:
        for line in env_file:
            if line.startswith('USERS_IDS'):
                USERS = line.split('=')[1].strip().split(',')
                USERS = {int(uid.split(':')[0]): uid.split(':')[1] for uid in USERS}
                break


class UserStatesGroup(StatesGroup):
    add_user = State()


async def help_command_client(message: types.Message) -> None:
    if message.from_user.id in USERS:
        await message.answer(texts['help'],
                             reply_markup=get_start_kb())


async def cancel_command(message: types.Message, state: FSMContext) -> None:
    if message.from_user.id == ADMIN:
        if state is None:
            return
        await message.reply('Действие отменено!',
                            reply_markup=get_start_kb())

        await state.finish()


async def start_command_client(message: types.Message) -> None:
    if message.from_user.id in USERS:
        await message.answer(f"Привет, {message.from_user.first_name}!\n"
                             f"Пришли мне серийный номер:",
                             reply_markup=get_start_kb())
    else:
        await message.answer(f"Здравствуй, {message.from_user.first_name}!\n"
                             f"Напиши свою фамилию и запрос на доступ к функционалу бота будет отправлен Администратору!\n",
                             reply_markup=get_start_kb())

        await bot.send_message(ADMIN, text=f"Запуск бота:\n"
                                           f"Username: {message.from_user.username}\n"
                                           f"full_name: {message.from_user.full_name}\n"
                                           f"id: {message.from_user.id}")

async def text_not_from_user(message: types.Message) -> None:
    if message.from_user.id not in USERS:
        await bot.send_message(ADMIN, text=f"Запрос доступа:")
        await bot.send_message(ADMIN, text=f"{message.from_user.id}:{message.text}")
        await message.reply(f"Запрос на доступ отправлен, ожидайте!")

async def add_user(message: types.Message):
    if message.from_user.id == ADMIN:
        await message.reply("Для добавления отправь:\n"
                            "id:last_name",
                            reply_markup=get_cancel())
        await UserStatesGroup.add_user.set()


async def set_user(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN:
        with open('.env', 'r+') as env_file:
            env_lines = env_file.readlines()

            for i, line in enumerate(env_lines):
                if line.startswith('USERS_IDS'):

                    users = line[len('USERS_IDS='):].strip().split(',')

                    if message.text not in users:
                        users.append(message.text)

                    env_lines[i] = f"USERS_IDS={','.join(users)}\n"
                    env_file.seek(0)
                    env_file.writelines(env_lines)
                    env_file.truncate()
                    await message.reply(f"Пользователь {message.text} успешно добавлен!",
                                        reply_markup=get_start_kb())
                    await bot.send_message(message.text, f"Доспут открыт!\n"
                                                         f"Для начала работы нажми /start")
                    await state.finish()
                    await get_users(message)
                    return
        await message.reply("Не удалось найти переменную USERS_IDS в файле .env.")


async def check_serial_number(message: types.Message) -> None:
    if message.from_user.id in USERS:
        if not re.match(r"\d{2}\.\d{10}\.\d{4}\.\d{2}", message.text):
            await message.reply("Неверный формат серийного номера!\n"
                                "Пример: 46.7891823501.0001.20\n"
                                "Попробуй ещё раз!")
        else:
            await get_link_to(message)


async def get_link_to(message: types.Message) -> None:
    asyncio.create_task(handle_request(message))


async def handle_request(message: types.Message) -> None:
    if message.from_user.id in USERS:
        await message.reply("Файл загрузится в течение 30 секунд!")
        link = await get_link(message.text)
        if not link:
            await message.reply(f"Что-то пошло не так:\n\n"
                                f"1. Попробуй ещё раз!\n"
                                f"2. Файла с тех. данными по запрашиваемому номеру не существует!")
            await bot.send_message(ADMIN,
                                   text=f"<b>НЕ ВЫПОЛНЕНО!</b>\n"
                                        f"{USERS[message.from_user.id]}\n"
                                        f"{message.text}",
                                   parse_mode='html')
        else:
            pdf_name = message.text + ".pdf"
            pdf_path = f"{os.getcwd()}/{pdf_name}"

            with open(pdf_path, 'wb') as f:
                f.write(requests.get(link).content)

            with open(pdf_path, 'rb') as f:
                await bot.send_document(message.chat.id, f)

            await bot.send_message(ADMIN,
                                   text=f"<b>УСПЕШНО!</b>\n"
                                        f"{USERS[message.from_user.id]}\n"
                                        f"{message.text}",
                                   parse_mode='html')
            os.remove(pdf_path)


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(help_command_client, commands=['help'])
    dp.register_message_handler(cancel_command, commands=['canсel'], state="*")
    dp.register_message_handler(start_command_client, commands=['start'])
    dp.register_message_handler(text_not_from_user)
    dp.register_message_handler(add_user, commands=['add_user'])
    dp.register_message_handler(get_users, commands=['get_users'])
    dp.register_message_handler(set_user, state=UserStatesGroup.add_user)
    dp.register_message_handler(check_serial_number)
    dp.register_message_handler(get_link_to)
