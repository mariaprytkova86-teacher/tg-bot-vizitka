import os
import json
import uuid
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)


# =========================================================
# ПУТИ И НАСТРОЙКИ
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Твой личный Telegram ID
OWNER_ID = 1100657461

# Твой Telegram
TEACHER_USERNAME = "@MariaPrytkova86"

# Файлы
SLOTS_FILE = BASE_DIR / "slots.json"
BOOKINGS_FILE = BASE_DIR / "bookings.json"

# Картинки
WELCOME_IMAGE = BASE_DIR / "assets" / "welcome.png"
REVIEW_1 = BASE_DIR / "reviews" / "review1.png"
REVIEW_2 = BASE_DIR / "reviews" / "review2.png"


# =========================================================
# СОХРАНЕНИЕ ДАННЫХ
# =========================================================

def load_slots():
    if not SLOTS_FILE.exists():
        save_slots([])
        return []

    try:
        with open(SLOTS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_slots(slots):
    with open(SLOTS_FILE, "w", encoding="utf-8") as file:
        json.dump(
            slots,
            file,
            ensure_ascii=False,
            indent=2
        )


def load_bookings():
    if not BOOKINGS_FILE.exists():
        save_bookings({})
        return {}

    try:
        with open(BOOKINGS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_bookings(bookings):
    with open(BOOKINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(
            bookings,
            file,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# МЕНЮ
# =========================================================

def main_menu(user_id):
    keyboard = [
        ["⭐ Отзывы", "📅 Свободные окна"],
        ["✏️ Записаться на урок"]
    ]

    # Админскую кнопку видишь только ты
    if user_id == OWNER_ID:
        keyboard.append(["⚙️ Управление окнами"])

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


def admin_menu():
    keyboard = [
        ["➕ Добавить окно"],
        ["❌ Удалить окно"],
        ["📋 Посмотреть все окна"],
        ["⬅️ Главное меню"]
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


def format_menu():
    keyboard = [
        ["👥 Группа", "👤 Индивидуально"],
        ["❌ Отменить запись"]
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


def confirmation_menu():
    keyboard = [
        ["✅ Отправить заявку"],
        ["❌ Отменить запись"]
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id

    # Сбрасываем старые режимы
    context.user_data["booking_step"] = None
    context.user_data["booking"] = {}
    context.user_data["admin_mode"] = None

    # Сначала приветственная картинка
    if WELCOME_IMAGE.exists():
        with open(WELCOME_IMAGE, "rb") as photo:
            await update.message.reply_photo(
                photo=photo
            )

    # Первый текст
    await update.message.reply_text(
        "Здравствуйте! 👋\n\n"
        "Я — персональный ассистент Марии Викторовны."
    )

    # Второй текст + меню
    await update.message.reply_text(
        "Мария Викторовна — преподаватель английского языка "
        "и основатель студии «Спики» 🦝\n\n"
        "Здесь школьники учатся понимать английский, "
        "увереннее использовать его и постепенно закрывать "
        "пробелы в школьной программе.\n\n"
        "А я помогу вам:\n"
        "⭐ посмотреть отзывы родителей\n"
        "📅 узнать свободные окошки\n"
        "✏️ оставить заявку на занятие\n\n"
        "Выберите нужный раздел 👇",
        reply_markup=main_menu(user_id)
    )


# =========================================================
# ОТЗЫВЫ
# =========================================================

async def show_reviews(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not REVIEW_1.exists() or not REVIEW_2.exists():
        await update.message.reply_text(
            "Пока не удалось загрузить отзывы.",
            reply_markup=main_menu(
                update.effective_user.id
            )
        )
        return

    with open(REVIEW_1, "rb") as photo1, \
         open(REVIEW_2, "rb") as photo2:

        media = [
            InputMediaPhoto(media=photo1),
            InputMediaPhoto(media=photo2)
        ]

        await update.message.reply_media_group(
            media=media
        )

    await update.message.reply_text(
        "💜 Спасибо родителям за тёплые слова!",
        reply_markup=main_menu(
            update.effective_user.id
        )
    )


# =========================================================
# СВОБОДНЫЕ ОКНА
# =========================================================

async def show_slots(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    slots = load_slots()

    if not slots:
        await update.message.reply_text(
            "📅 Сейчас свободных окошек нет.\n\n"
            "Вы можете написать Марии Викторовне напрямую:\n"
            f"{TEACHER_USERNAME}",
            reply_markup=main_menu(
                update.effective_user.id
            )
        )
        return

    text = "📅 Свободные окошки:\n\n"

    for number, slot in enumerate(slots, start=1):
        text += f"{number}. {slot}\n"

    text += (
        "\nЕсли нашли подходящее время, "
        "нажмите «✏️ Записаться на урок»."
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu(
            update.effective_user.id
        )
    )


# =========================================================
# НАЧАЛО ЗАПИСИ
# =========================================================

async def book_lesson(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    slots = load_slots()

    if not slots:
        await update.message.reply_text(
            "К сожалению, сейчас свободных окошек нет.\n\n"
            "Можно написать Марии Викторовне напрямую:\n"
            f"{TEACHER_USERNAME}",
            reply_markup=main_menu(
                update.effective_user.id
            )
        )
        return

    keyboard = []

    for index, slot in enumerate(slots):
        keyboard.append(
            [
                InlineKeyboardButton(
                    slot,
                    callback_data=f"slot_{index}"
                )
            ]
        )

    await update.message.reply_text(
        "✏️ Запись на занятие\n\n"
        "Выберите подходящий день и время 👇",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# ВЫБОР ОКНА
# =========================================================

async def choose_slot(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    slots = load_slots()

    try:
        index = int(
            query.data.replace("slot_", "")
        )

        selected_slot = slots[index]

    except (ValueError, IndexError):
        await query.message.reply_text(
            "Это окошко уже недоступно.\n"
            "Пожалуйста, выберите другое."
        )
        return

    context.user_data["booking"] = {
        "slot": selected_slot
    }

    context.user_data["booking_step"] = "format"

    await query.message.reply_text(
        f"Вы выбрали:\n\n"
        f"📅 {selected_slot}\n\n"
        "Какой формат занятия вас интересует?",
        reply_markup=format_menu()
    )


# =========================================================
# ПРОВЕРКА ЗАЯВКИ
# =========================================================

async def show_booking_summary(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    booking = context.user_data.get(
        "booking",
        {}
    )

    text = (
        "Проверьте данные 👇\n\n"
        f"📅 Время: {booking.get('slot')}\n"
        f"📚 Формат: {booking.get('format')}\n"
        f"👤 Родитель: {booking.get('parent_name')}\n"
        f"👦 Ребёнок: {booking.get('child_name')}\n"
        f"🏫 Класс: {booking.get('child_class')}\n"
        f"📱 Телефон: {booking.get('phone')}\n\n"
        "Если всё верно, отправьте заявку."
    )

    await update.message.reply_text(
        text,
        reply_markup=confirmation_menu()
    )


# =========================================================
# ОТПРАВКА ЗАЯВКИ
# =========================================================

async def submit_booking(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    booking = context.user_data.get(
        "booking",
        {}
    )

    selected_slot = booking.get("slot")
    slots = load_slots()

    if selected_slot not in slots:
        context.user_data["booking_step"] = None
        context.user_data["booking"] = {}

        await update.message.reply_text(
            "К сожалению, это время только что стало недоступно.\n\n"
            "Выберите другое свободное окошко.",
            reply_markup=main_menu(
                update.effective_user.id
            )
        )
        return

    # Пока заявка ждёт подтверждения,
    # окно убираем из свободных
    slots.remove(selected_slot)
    save_slots(slots)

    user = update.effective_user

    booking_id = uuid.uuid4().hex[:8]

    booking["id"] = booking_id
    booking["status"] = "pending"
    booking["user_id"] = user.id
    booking["telegram_username"] = user.username or ""
    booking["created_at"] = datetime.now().strftime(
        "%d.%m.%Y %H:%M"
    )

    bookings = load_bookings()
    bookings[booking_id] = booking
    save_bookings(bookings)

    context.user_data["booking_step"] = None
    context.user_data["booking"] = {}

    await update.message.reply_text(
        "✅ Заявка отправлена Марии Викторовне!\n\n"
        f"📅 {selected_slot}\n\n"
        "Пока заявка ожидает подтверждения, "
        "это время временно забронировано за вами.\n\n"
        "После подтверждения бот сообщит вам об этом.\n\n"
        "Связаться с Марией Викторовной:\n"
        f"{TEACHER_USERNAME}",
        reply_markup=main_menu(
            update.effective_user.id
        )
    )

    username_text = (
        f"@{user.username}"
        if user.username
        else "не указан"
    )

    owner_text = (
        "🔔 НОВАЯ ЗАЯВКА\n\n"
        f"📅 Время: {booking['slot']}\n"
        f"📚 Формат: {booking['format']}\n\n"
        f"👤 Родитель: {booking['parent_name']}\n"
        f"👦 Ребёнок: {booking['child_name']}\n"
        f"🏫 Класс: {booking['child_class']}\n"
        f"📱 Телефон: {booking['phone']}\n"
        f"💬 Telegram: {username_text}\n\n"
        "Подтвердить запись?"
    )

    owner_keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Подтвердить",
                    callback_data=f"approve_{booking_id}"
                ),
                InlineKeyboardButton(
                    "❌ Отклонить",
                    callback_data=f"reject_{booking_id}"
                )
            ]
        ]
    )

    await context.bot.send_message(
        chat_id=OWNER_ID,
        text=owner_text,
        reply_markup=owner_keyboard
    )


# =========================================================
# ПОДТВЕРЖДЕНИЕ ЗАЯВКИ
# =========================================================

async def approve_booking(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != OWNER_ID:
        return

    booking_id = query.data.replace(
        "approve_",
        ""
    )

    bookings = load_bookings()
    booking = bookings.get(booking_id)

    if not booking:
        await query.message.reply_text(
            "Заявка не найдена."
        )
        return

    if booking.get("status") != "pending":
        await query.message.reply_text(
            "Эта заявка уже обработана."
        )
        return

    booking["status"] = "confirmed"

    bookings[booking_id] = booking
    save_bookings(bookings)

    await query.edit_message_reply_markup(
        reply_markup=None
    )

    await query.message.reply_text(
        "✅ Запись подтверждена."
    )

    try:
        await context.bot.send_message(
            chat_id=booking["user_id"],
            text=(
                "🎉 Ваша запись подтверждена!\n\n"
                f"📅 {booking['slot']}\n"
                f"📚 {booking['format']}\n\n"
                "До встречи на занятии! 💜\n\n"
                "Мария Викторовна:\n"
                f"{TEACHER_USERNAME}"
            )
        )

    except Exception:
        pass


# =========================================================
# ОТКЛОНЕНИЕ ЗАЯВКИ
# =========================================================

async def reject_booking(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != OWNER_ID:
        return

    booking_id = query.data.replace(
        "reject_",
        ""
    )

    bookings = load_bookings()
    booking = bookings.get(booking_id)

    if not booking:
        await query.message.reply_text(
            "Заявка не найдена."
        )
        return

    if booking.get("status") != "pending":
        await query.message.reply_text(
            "Эта заявка уже обработана."
        )
        return

    booking["status"] = "rejected"

    bookings[booking_id] = booking
    save_bookings(bookings)

    # Возвращаем окно в свободные
    slots = load_slots()

    if booking["slot"] not in slots:
        slots.append(booking["slot"])
        save_slots(slots)

    await query.edit_message_reply_markup(
        reply_markup=None
    )

    await query.message.reply_text(
        "❌ Заявка отклонена.\n"
        "Окошко снова стало свободным."
    )

    try:
        await context.bot.send_message(
            chat_id=booking["user_id"],
            text=(
                "К сожалению, выбранное время "
                "не удалось подтвердить.\n\n"
                "Вы можете выбрать другое свободное окошко "
                "или написать Марии Викторовне напрямую:\n"
                f"{TEACHER_USERNAME}"
            )
        )

    except Exception:
        pass


# =========================================================
# АДМИНКА
# =========================================================

async def admin_panel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_user.id != OWNER_ID:
        return

    context.user_data["admin_mode"] = None

    await update.message.reply_text(
        "⚙️ Управление свободными окнами\n\n"
        "Что хотите сделать?",
        reply_markup=admin_menu()
    )


async def add_slot(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_user.id != OWNER_ID:
        return

    context.user_data["admin_mode"] = "add"

    await update.message.reply_text(
        "➕ Напишите новое свободное окно.\n\n"
        "Например:\n"
        "26 августа — 16:00\n\n"
        "Отправьте дату и время одним сообщением."
    )


async def delete_slot(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_user.id != OWNER_ID:
        return

    slots = load_slots()

    if not slots:
        await update.message.reply_text(
            "Свободных окон пока нет.",
            reply_markup=admin_menu()
        )
        return

    context.user_data["admin_mode"] = "delete"

    text = "❌ Какое окно удалить?\n\n"

    for number, slot in enumerate(
        slots,
        start=1
    ):
        text += f"{number}. {slot}\n"

    text += (
        "\nНапишите только номер.\n"
        "Например: 2"
    )

    await update.message.reply_text(text)


async def admin_show_slots(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_user.id != OWNER_ID:
        return

    slots = load_slots()

    if not slots:
        text = "📋 Список свободных окон пуст."
    else:
        text = "📋 Сейчас свободны:\n\n"

        for number, slot in enumerate(
            slots,
            start=1
        ):
            text += f"{number}. {slot}\n"

    await update.message.reply_text(
        text,
        reply_markup=admin_menu()
    )


async def back_to_main(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data["admin_mode"] = None
    context.user_data["booking_step"] = None

    await update.message.reply_text(
        "Главное меню 👇",
        reply_markup=main_menu(
            update.effective_user.id
        )
    )


# =========================================================
# ОТМЕНА ЗАПИСИ
# =========================================================

async def cancel_booking(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    context.user_data["booking_step"] = None
    context.user_data["booking"] = {}

    await update.message.reply_text(
        "Запись отменена.",
        reply_markup=main_menu(
            update.effective_user.id
        )
    )


# =========================================================
# ОБРАБОТКА ТЕКСТА
# =========================================================

async def handle_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # ---------- АДМИНКА ----------

    admin_mode = context.user_data.get(
        "admin_mode"
    )

    if user_id == OWNER_ID and admin_mode == "add":
        slots = load_slots()

        if text in slots:
            context.user_data["admin_mode"] = None

            await update.message.reply_text(
                "Такое окно уже есть.",
                reply_markup=admin_menu()
            )
            return

        slots.append(text)
        save_slots(slots)

        context.user_data["admin_mode"] = None

        await update.message.reply_text(
            f"✅ Добавлено новое окно:\n\n{text}",
            reply_markup=admin_menu()
        )
        return


    if user_id == OWNER_ID and admin_mode == "delete":
        slots = load_slots()

        try:
            number = int(text)
            index = number - 1

            if index < 0 or index >= len(slots):
                raise ValueError

        except ValueError:
            await update.message.reply_text(
                "Не понимаю этот номер.\n"
                "Напишите номер окна из списка."
            )
            return

        deleted_slot = slots.pop(index)

        save_slots(slots)

        context.user_data["admin_mode"] = None

        await update.message.reply_text(
            f"✅ Окно удалено:\n\n"
            f"{deleted_slot}",
            reply_markup=admin_menu()
        )
        return


    # ---------- ЗАПИСЬ КЛИЕНТА ----------

    booking_step = context.user_data.get(
        "booking_step"
    )

    booking = context.user_data.get(
        "booking",
        {}
    )


    if booking_step == "format":

        if text not in [
            "👥 Группа",
            "👤 Индивидуально"
        ]:
            await update.message.reply_text(
                "Пожалуйста, выберите формат кнопкой ниже.",
                reply_markup=format_menu()
            )
            return

        booking["format"] = text

        context.user_data["booking"] = booking
        context.user_data["booking_step"] = "parent_name"

        await update.message.reply_text(
            "Как вас зовут?\n\n"
            "Напишите имя родителя."
        )
        return


    if booking_step == "parent_name":

        booking["parent_name"] = text

        context.user_data["booking"] = booking
        context.user_data["booking_step"] = "child_name"

        await update.message.reply_text(
            "Как зовут ребёнка?"
        )
        return


    if booking_step == "child_name":

        booking["child_name"] = text

        context.user_data["booking"] = booking
        context.user_data["booking_step"] = "child_class"

        await update.message.reply_text(
            "В каком классе учится ребёнок?\n\n"
            "Например: 4 класс"
        )
        return


    if booking_step == "child_class":

        booking["child_class"] = text

        context.user_data["booking"] = booking
        context.user_data["booking_step"] = "phone"

        await update.message.reply_text(
            "Оставьте номер телефона для связи.\n\n"
            "Например:\n"
            "+7 999 123-45-67"
        )
        return


    if booking_step == "phone":

        booking["phone"] = text

        context.user_data["booking"] = booking
        context.user_data["booking_step"] = "confirm"

        await show_booking_summary(
            update,
            context
        )
        return


    if booking_step == "confirm":

        if text == "✅ Отправить заявку":
            await submit_booking(
                update,
                context
            )
            return

        await update.message.reply_text(
            "Чтобы отправить заявку, "
            "нажмите кнопку «✅ Отправить заявку».",
            reply_markup=confirmation_menu()
        )


# =========================================================
# МОЙ TELEGRAM ID
# =========================================================

async def my_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        f"Ваш Telegram ID:\n\n"
        f"{update.effective_user.id}"
    )


# =========================================================
# ЗАПУСК БОТА
# =========================================================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "Не найден BOT_TOKEN в файле .env"
        )

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Команды
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("myid", my_id)
    )

    # Главное меню
    app.add_handler(
        MessageHandler(
            filters.Regex("^⭐ Отзывы$"),
            show_reviews
        )
    )

    app.add_handler(
        MessageHandler(
            filters.Regex("^📅 Свободные окна$"),
            show_slots
        )
    )

    app.add_handler(
        MessageHandler(
            filters.Regex("^✏️ Записаться на урок$"),
            book_lesson
        )
    )

    # Отмена записи
    app.add_handler(
        MessageHandler(
            filters.Regex("^❌ Отменить запись$"),
            cancel_booking
        )
    )

    # Админка
    app.add_handler(
        MessageHandler(
            filters.Regex("^⚙️ Управление окнами$"),
            admin_panel
        )
    )

    app.add_handler(
        MessageHandler(
            filters.Regex("^➕ Добавить окно$"),
            add_slot
        )
    )

    app.add_handler(
        MessageHandler(
            filters.Regex("^❌ Удалить окно$"),
            delete_slot
        )
    )

    app.add_handler(
        MessageHandler(
            filters.Regex("^📋 Посмотреть все окна$"),
            admin_show_slots
        )
    )

    app.add_handler(
        MessageHandler(
            filters.Regex("^⬅️ Главное меню$"),
            back_to_main
        )
    )

    # Выбор окошка
    app.add_handler(
        CallbackQueryHandler(
            choose_slot,
            pattern=r"^slot_"
        )
    )

    # Подтверждение и отклонение заявок
    app.add_handler(
        CallbackQueryHandler(
            approve_booking,
            pattern=r"^approve_"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            reject_booking,
            pattern=r"^reject_"
        )
    )

    # Остальной текст
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text
        )
    )

    print("Бот запущен!")

    app.run_polling()


if __name__ == "__main__":
    main()