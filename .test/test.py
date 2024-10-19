import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router
from aiogram import F
import asyncio
import datetime

API_TOKEN = '7472821995:AAGiFRrRVPqMbRiT7yK0snTjWWQF4BROF78'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

participants = []
queue = []
MAX_PARTICIPANTS = 21
event = {"name": "", "time": ""}

@router.message(F.text.startswith("/start"))
async def start_command(message: types.Message):
    await message.answer("Привіт! Використайте /create_event, щоб створити подію.")

@router.message(F.text.startswith("/create_event"))
async def create_event(message: types.Message):
    event_data = message.text.split(maxsplit=2)
    if len(event_data) < 3:
        await message.reply("Будь ласка, введіть назву та час події. Наприклад: /create_event Футбол 18:00")
        return
    
    event["name"] = event_data[1]
    event["time"] = event_data[2]
    
    await message.answer(f"Подію '{event['name']}' на {event['time']} створено!")
    await send_event_info(message.chat.id)

async def send_event_info(chat_id):
    # Створюємо клавіатуру з кнопкою "Запис" або "Черга"
    button = InlineKeyboardButton(text="Запис", callback_data="register")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
    await bot.send_message(chat_id, f"Подія: {event['name']} на {event['time']}\nУчасники: {len(participants)}/{MAX_PARTICIPANTS}", reply_markup=keyboard)

class TestMessage:
    def __init__(self, chat_id):
        self.chat = types.Chat(id=chat_id, type='private')
        self.message_id = 1

async def add_fake_participants(test_message):
    for i in range(1, 26):
        fake_user = {
            'id': f"fake_user_{i}",
            'name': f"Fake User {i}",
            'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        }
        if len(participants) < MAX_PARTICIPANTS:
            participants.append(fake_user)
        else:
            queue.append(fake_user)
        await update_participant_list(test_message)

async def update_participant_list(message: types.Message):
    response = f"Подія: {event['name']} на {event['time']}\n\nУчасники:\n"
    for i, participant in enumerate(participants, 1):
        response += f"{i}. {participant['name']} (записався {participant['time']})\n"
    
    if queue:
        response += "\nЧерга:\n"
        for i, q_participant in enumerate(queue, 1):
            response += f"{i + MAX_PARTICIPANTS}. {q_participant['name']} (в черзі {q_participant['time']})\n"

    await bot.edit_message_text(response, chat_id=message.chat.id, message_id=message.message_id)

async def test_queue():
    event["name"] = "Тест Подія"
    event["time"] = "18:00"
    test_message = TestMessage(chat_id=YOUR_ACTUAL_CHAT_ID)  # Замість YOUR_ACTUAL_CHAT_ID поставте свій chat_id
    await send_event_info(test_message.chat.id)
    await add_fake_participants(test_message)

async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())


