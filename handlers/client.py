from aiogram import types, Dispatcher
from create_bot import bot, ADMIN, USERS
from logic.client_logic import get_link
from keyboards.client_kb import get_start_kb, get_cancel
from aiogram.dispatcher.storage import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
import asyncio

from db import db_control

import re

from datetime import datetime
import requests
import os

texts = {"help": "Это бот для получения полных технических данных оборудования SEW по серийному номеру.\n\n"
                 "Работает без VPN!\n\n"
                 "Отправь боту sn в формате XX.XXXXXXXXXX.XXXX.XX и получи pdf.\n\n"
                 "Для начала нажми /start\n\n"
                 "Администратор @Karavaev_Nikita"}


async def get_users():
    global USERS
    with open('.env', 'r') as env_file:
        for line in env_file:
            if line.startswith('USERS'):
                USERS = line.split('=')[1].strip().split(',')
                USERS = {int(uid.split(':')[0]): uid.split(':')[1] for uid in USERS}
                break


class UserStatesGroup(StatesGroup):
    add_user = State()
    send_message = State()


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
                             f"Запрос на доступ к функционалу бота отправлен Администратору!\n"
                             f"Ожидай подтверждение!\n\n"
                             f"Если в вашем профиле отсутствует фамилия - отправьте запрос администратору!",
                             reply_markup=get_start_kb())

        await bot.send_message(ADMIN, text=f"Запрос на доступ:\n"
                                           f"Username: {message.from_user.username}\n"
                                           f"full_name: {message.from_user.full_name}\n")
        await bot.send_message(ADMIN, text=f"{message.from_user.id}:{message.from_user.last_name}")


async def admin_command(message: types.Message):
    if message.from_user.id == ADMIN:
        await message.answer("Команды:\n"
                             "/add_user - добавить нового пользователя\n"
                             "/users_len - количество пользователей\n"
                             "/smfb - отправить всем сообщение",
                             )


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
                if line.startswith('USERS'):

                    users = line[len('USERS='):].strip().split(',')

                    if message.text not in users:
                        users.append(message.text)

                    env_lines[i] = f"USERS={','.join(users)}\n"
                    env_file.seek(0)
                    env_file.writelines(env_lines)
                    env_file.truncate()
                    await message.reply(f"Пользователь {message.text} успешно добавлен!",
                                        reply_markup=get_start_kb())
                    await bot.send_message(message.text, f"Доспут открыт!\n"
                                                         f"Для начала работы нажми /start")
                    await state.finish()
                    await get_users()
                    return
        await message.reply("Не удалось найти переменную USERS в файле .env.")


async def send_message_from_bot(message: types.Message):
    if message.from_user.id == ADMIN:
        await message.reply("Напиши сообщения для рассылки:",
                            reply_markup=get_cancel())
        await UserStatesGroup.send_message.set()


async def bot_send_message(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN:
        for user in USERS:
            await bot.send_message(user, f"{message.text}\n\n"
                                         f'Администратор: @Karavaev_Nikita')
    await state.finish()


async def users_len(message: types.Message):
    if message.from_user.id == ADMIN:
        await message.reply(f"В данный момент пользователей: {len(USERS)}")


async def check_serial_number(message: types.Message) -> None:
    if message.from_user.id in USERS:
        if not re.match(r"^\d{2}\.\d{10}\..*$", message.text):
            await message.reply("Неверный формат серийного номера!\n"
                                "Пример: 46.7891823501.0001.20\n"
                                "Попробуй ещё раз!")
        else:
            await get_link_to(message)


async def get_link_to(message: types.Message) -> None:
    asyncio.create_task(handle_request(message))


async def handle_request(message: types.Message) -> None:
    user_id = message.from_user.id

    if user_id in USERS:
        await message.reply("Файл загрузится в течение 30 секунд!")

        link = await get_link(message.text)

        if not link or link.startswith('Exception'):
            await handle_error(user_id, message.text, link, message)
        else:
            try:
                pdf_path = await process_request(message.text, link)
                await send_document(message.chat.id, pdf_path)
                await process_quotation(user_id, message.text, message)
                await remove_file(pdf_path)
            except Exception as e:
                await handle_exception(user_id, message.text, e, message)


async def handle_error(user_id: int, message_text: str, link: str, message: types.Message) -> None:
    error_message = (
        "Что-то пошло не так:\n\n"
        "1. Попробуй ещё раз!\n"
        "2. Файла с тех. данными по запрашиваемому номеру не существует!"
    )

    await message.reply(error_message)

    await bot.send_message(
        ADMIN,
        text=f"<b>НЕ ВЫПОЛНЕНО!</b>\n"
             f"{USERS[user_id]}\n"
             f"{message_text}\n"
             f"Error: {link}",
        parse_mode='html'
    )


async def process_request(message_text: str, link: str) -> str:
    pdf_name = message_text + ".pdf"
    pdf_path = os.path.join(os.getcwd(), pdf_name)

    with open(pdf_path, 'wb') as f:
        f.write(requests.get(link).content)

    return pdf_path


async def send_document(chat_id: int, pdf_path: str) -> None:
    with open(pdf_path, 'rb') as f:
        await bot.send_document(chat_id, f)


async def process_quotation(user_id: int, message_text: str, message: types.Message) -> None:
    users_from_db = await db_control.db_get_users(message_text)
    current_date = datetime.now().strftime("%d.%m.%Y")

    if users_from_db:
        await bot.send_message(
            message.chat.id,
            f'Запрос по такому sn был уже выполнен от: {users_from_db}'
        )

        new_users_from_db = ', '.join((users_from_db, f'{USERS[user_id]} - {current_date}'))
        await db_control.edit_quotation(message_text, new_users_from_db)
    else:
        await db_control.add_quotation(message_text, f'{USERS[user_id]} - {current_date}')


async def remove_file(file_path: str) -> None:
    os.remove(file_path)


async def handle_exception(user_id: int, exception: Exception, message: types.Message) -> None:
    await bot.send_message(
        ADMIN,
        text=f"<b>НЕ ВЫПОЛНЕНО!</b>\n"
             f"{USERS[user_id]}\n"
             f"{message.text}\n"
             f"{exception}",
            parse_mode='html'
    )


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(help_command_client, commands=['help'])
    dp.register_message_handler(cancel_command, commands=['canсel'], state="*")
    dp.register_message_handler(start_command_client, commands=['start'])
    dp.register_message_handler(admin_command, commands=['admin'])
    dp.register_message_handler(add_user, commands=['add_user'])
    dp.register_message_handler(get_users, commands=['get_users'])
    dp.register_message_handler(set_user, state=UserStatesGroup.add_user)
    dp.register_message_handler(send_message_from_bot, commands=['smfb'])
    dp.register_message_handler(bot_send_message, state=UserStatesGroup.send_message)
    dp.register_message_handler(users_len, commands=['users_len'])
    dp.register_message_handler(check_serial_number)
    dp.register_message_handler(get_link_to)
    dp.register_message_handler(handle_request)

