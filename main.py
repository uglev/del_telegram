import asyncio
import os
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import ChatAdminRequiredError
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
SESSION_NAME = os.getenv('SESSION_NAME', 'session')
TARGET_USER_ID = int(os.getenv('TARGET_USER_ID'))
DAYS_THRESHOLD = int(os.getenv('DAYS_THRESHOLD', 10))

excluded_groups_str = os.getenv('EXCLUDED_GROUPS', '')
excluded_groups = [int(g.strip()) for g in excluded_groups_str.split(',') if g.strip()]

async def main():
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()
    print('Client started')

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=DAYS_THRESHOLD)

    async for dialog in client.iter_dialogs():
        # Пропускаем личные чаты
        if dialog.is_user:
            continue

        # Пропускаем группы из списка исключений по ID
        if dialog.id in excluded_groups:
            print(f'Skipping excluded group: "{dialog.name}" (ID: {dialog.id})')
            continue

        print(f'Processing chat: "{dialog.name}" (ID: {dialog.id})')

        try:
            async for message in client.iter_messages(dialog, from_user=TARGET_USER_ID):
                if message.date >= cutoff_date:
                    # Сообщение свежее порога, пропускаем
                    continue

                try:
                    await client.delete_messages(dialog, message, revoke=True)
                    print(f'[LOG] Deleted message ID {message.id} '
                          f'from user {TARGET_USER_ID} in chat "{dialog.name}" (ID: {dialog.id}) '
                          f'at {message.date.isoformat()}')
                except ChatAdminRequiredError:
                    print(f'[LOG] No rights to delete messages in chat "{dialog.name}" (ID: {dialog.id}), skipping.')
                    break
                except Exception as e:
                    print(f'[LOG] Error deleting message ID {message.id} in chat "{dialog.name}": {e}')
        except Exception as e:
            print(f'[LOG] Error processing chat "{dialog.name}": {e}')

    await client.disconnect()
    print('Finished removal')


if __name__ == '__main__':
    asyncio.run(main())
