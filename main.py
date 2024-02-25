from dotenv import load_dotenv
import asyncio
from database import DB_API
from bot import create_app
from pyrogram import idle
from pyrogram.types import Message, User
from pyrogram.handlers import MessageHandler
from typing import List
from models import UserStatusEnum

load_dotenv('.env')

db_api = DB_API()

GLOBAL_TRIGGERS = ['прекрасно', 'ожидать']
TIMEOUT = 5

async def handle_incoming(client, message: Message):
    user_id = message.from_user.id
    user = await db_api.get_user_by_tg_id(user_id)
    user_name = message.from_user.first_name + ' ' + message.from_user.last_name

    if not user:
        print(f'Got a new user: {user_name}. Adding to DB...')
        await db_api.add_user(user_id)
        return

    if user.status != UserStatusEnum.ALIVE:
        return

    # Если закончились ответы
    if not user.next_response:
        print(f'Sent last message to: {user_name}. Finishing.')
        await db_api.set_user_status(user_id, UserStatusEnum.FINISHED)

    # Если есть триггеры
    for trigger in GLOBAL_TRIGGERS:
        if trigger in message.text.lower():
            print(f'Got a global trigger from: {user_name}. Finishing.')
            await db_api.set_user_status(user_id, UserStatusEnum.FINISHED)
            return
        
    if not user.next_response.cancel_triggers:
        return
    
    for trigger in user.next_response.cancel_triggers:
        if trigger in message.text.lower():
            print(f'Got a cancel trigger from: {user_name}. Skipping response.')
            await db_api.set_user_next_question(user_id)
            return

async def app_thread():
    async with create_app('app_thread') as app:
        handler = MessageHandler(handle_incoming)
        app.add_handler(handler)
        await idle()
        await app.stop()

async def send_message(to: int, message: str):
    async with create_app('sending') as app:
        user = await app.get_users(to)

        if user.is_deleted:
            await db_api.set_user_status(to, UserStatusEnum.DEAD)
            return
        
        await app.send_message(to, message)
        await db_api.set_user_next_question(to)

async def main():
    while True:
        ready_users = await db_api.get_ready_users()
        for user in ready_users:
            await send_message(user[0].telegram_id, user[1])
        await asyncio.sleep(TIMEOUT)

async def entry():
    await db_api.add_default_messages()
    await asyncio.gather(main(), app_thread())

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(entry())