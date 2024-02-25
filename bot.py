import os
from pyrogram import Client

def create_app(name: str):
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')

    if not api_id or not api_hash:
        raise Exception('TELEGRAM_API_ID or TELEGRAM_API_HASH not set!')

    app = Client(f'my_account_{name}', api_id, api_hash)
    return app