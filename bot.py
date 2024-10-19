import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram import Router, F
import asyncio
import datetime

API_TOKEN = '7472821995:AAGiFRrRVPqMbRiT7yK0snTjWWQF4BROF78'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

# Список учасників
participants = {}
queue = {}  # Використовуємо словник для узгодженості
unsubscribed = {}
MAX_PARTICIPANTS = 21

# Створення події
event = {"name": "", "time": ""}

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
    
    # Додаємо кнопку до клавіатури
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])

    # Відправляємо повідомлення з інформацією про подію та клавіатурою
    await bot.send_message(chat_id, f"Подія: {event['name']} на {event['time']}\n\nНатисніть кнопку нижче, щоб зареєструватися.", reply_markup=keyboard)

# Функція для створення клавіатури "Запис" або "Відписатися"
def get_registration_keyboard(user_id):
    if user_id in participants:
        button = InlineKeyboardButton(text="Відписатися", callback_data="unsubscribe")
    elif user_id in queue:
        button = InlineKeyboardButton(text="Залишити чергу", callback_data="leave_queue")
    else:
        button = InlineKeyboardButton(text="Записатися", callback_data="register")
    return InlineKeyboardMarkup(inline_keyboard=[[button]])

# Обробка запису
@router.callback_query(F.data == 'register')
async def handle_register(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user_name = callback_query.from_user.full_name
    registration_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    if len(participants) < MAX_PARTICIPANTS:
        # Додаємо користувача до списку учасників
        if user_id not in participants:
            participants[user_id] = {"name": user_name, "time": registration_time}
            await callback_query.answer("Ви зареєстровані на подію!")
        else:
            await callback_query.answer("Ви вже зареєстровані на подію!")
            return
    else:
        # Додаємо в чергу
        if user_id not in queue:
            queue[user_id] = {"name": user_name, "time": registration_time}
            await callback_query.answer("Вас додано до черги!")
        else:
            await callback_query.answer("Ви вже в черзі!")
            return

    # Оновлюємо клавіатуру
    keyboard = get_registration_keyboard(user_id)
    await bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard
    )

    # Оновлюємо список учасників
    await update_participant_list(callback_query.message.chat.id, callback_query.message.message_id, user_id)

# Обробник події, коли користувач натискає на кнопку "Відписатися"
@router.callback_query(F.data == 'unsubscribe')
async def handle_unregister(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user_name = callback_query.from_user.full_name
    unregistration_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    # Видаляємо користувача зі списку учасників
    if user_id in participants:
        unsubscribed[user_id] = {"name": participants[user_id]['name'], "time": unregistration_time}
        del participants[user_id]
        await callback_query.answer("Ви відписалися від події.")

        # Якщо є черга, переміщаємо першого учасника в список
        if queue:
            first_in_queue_id, first_in_queue = next(iter(queue.items()))
            participants[first_in_queue_id] = first_in_queue
            del queue[first_in_queue_id]
    else:
        await callback_query.answer("Ви не зареєстровані на подію.")
        return

    # Оновлюємо клавіатуру
    keyboard = get_registration_keyboard(user_id)
    await bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard
    )

    # Оновлюємо список учасників
    await update_participant_list(callback_query.message.chat.id, callback_query.message.message_id, user_id)

async def update_participant_list(chat_id, message_id, user_id):
    # Формуємо заголовок з інформацією про подію
    event_info = f"Подія: {event['name']} на {event['time']}\n\n"
    
    # Формуємо список учасників
    response = event_info + "Учасники:\n"
    for index, participant in enumerate(participants.values(), start=1):
        response += f"{index}. {participant['name']} (записався {participant['time']})\n"

    # Формуємо список черги
    if queue:
        response += "\nЧерга:\n"
        for index, participant in enumerate(queue.values(), start=1):
            response += f"{index}. {participant['name']} (в черзі {participant['time']})\n"

    # Формуємо список відписаних
    if unsubscribed:
        response += "\nВідписані:\n"
        for index, participant in enumerate(unsubscribed.values(), start=1):
            response += f"{index}. <s>{participant['name']}</s> (відписався {participant['time']})\n"

    # Додаємо кнопку "Відписатися" або "Записатися"
    keyboard = get_registration_keyboard(user_id)

    # Оновлюємо текст повідомлення
    await bot.edit_message_text(response, chat_id=chat_id, message_id=message_id, reply_markup=keyboard, parse_mode='HTML')

async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)



# --- Функція main() ---
async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)

    # Стартуємо бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

