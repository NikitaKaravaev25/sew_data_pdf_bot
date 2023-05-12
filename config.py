from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    token: str
    ADMIN: str
    USERS: list[int]


@dataclass
class Config:
    tg_bot: TgBot


def load_config(path: str | None) -> Config:
    env: Env = Env()
    env.read_env(path)

    admin_str = env.str('USERS')
    admin_dict = {}
    for item in admin_str.split(','):
        key, value = item.split(':')
        admin_dict[int(key)] = value

    return Config(tg_bot=TgBot(token=env('BOT_TOKEN'), ADMIN=int(env('ADMIN')), USERS=admin_dict))
