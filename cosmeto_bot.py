from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import json

LOCATIONS = {
    "Центр": ["Пн", "Ср"],
    "Юг": ["Вт", "Чт"],
    "Север": ["Пт", "Сб"]
}

SERVICES = {
    "Центр": ["Чистка лица", "Массаж лица"],
    "Юг": ["Пилинг", "Массаж спины"],
    "Север": ["Уходовые процедуры", "Консультация"]
}

SLOTS = {
    "Пн": ["10:00", "12:00", "14:00"],
    "Вт": ["11:00", "13:00"],
    "Ср": ["10:00", "15:00"],
    "Чт": ["11:30", "16:00"],
    "Пт": ["10:00", "12:00"],
    "Сб": ["11:00", "13:00"]
}

bookings = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[KeyboardButton(loc)] for loc in LOCATIONS.keys()]
    await update.message.reply_text(
        "Привет! Выберите место приёма:",
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )

async def location_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.text
    if location not in LOCATIONS:
        await update.message.reply_text("Пожалуйста, выбери локацию из списка.")
        return
    context.user_data['location'] = location

    services = SERVICES[location]
    buttons = [[InlineKeyboardButton(text=svc, callback_data=f"svc|{svc}")] for svc in services]
    await update.message.reply_text("Выбери услугу:", reply_markup=InlineKeyboardMarkup(buttons))

async def service_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, service = query.data.split('|')
    context.user_data['service'] = service

    location = context.user_data['location']
    days = LOCATIONS[location]
    buttons = []
    for day in days:
        for slot in SLOTS[day]:
            if not any(b['time'] == slot and b['day'] == day and b['location'] == location for b in bookings):
                buttons.append([InlineKeyboardButton(f"{day} {slot}", callback_data=f"slot|{day}|{slot}")])

    await query.edit_message_text("Выбери дату и время:", reply_markup=InlineKeyboardMarkup(buttons))

async def slot_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, day, time = query.data.split('|')

    context.user_data['day'] = day
    context.user_data['time'] = time

    contact_button = KeyboardButton("Отправить номер", request_contact=True)
    await query.edit_message_text("Почти готово! Отправь номер телефона:")
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text="Нажми кнопку ниже, чтобы отправить контакт:",
                                   reply_markup=ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True))

async def contact_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user = update.effective_user

    record = {
        "user_id": user.id,
        "name": user.full_name,
        "phone": contact.phone_number,
        "location": context.user_data['location'],
        "service": context.user_data['service'],
        "day": context.user_data['day'],
        "time": context.user_data['time']
    }
    bookings.append(record)

    admin_id = 447109757
    msg = f"📌 Новая запись:\n👤 {record['name']}\n📞 {record['phone']}\n📍 {record['location']}\n💆 {record['service']}\n🕒 {record['day']} {record['time']}"
    await update.message.reply_text("Спасибо! Вы записаны.")
    await context.bot.send_message(chat_id=admin_id, text=msg)

app = ApplicationBuilder().token("6719897607:AAHA_amX1shlCBkAUYVduP9-TGAqxukr8NE").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, location_choice))
app.add_handler(CallbackQueryHandler(service_choice, pattern="^svc\|"))
app.add_handler(CallbackQueryHandler(slot_choice, pattern="^slot\|"))
app.add_handler(MessageHandler(filters.CONTACT, contact_received))

app.run_polling()
