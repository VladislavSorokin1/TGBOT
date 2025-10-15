import telebot
from telebot import types
from telebot.types import WebAppInfo

# --- ОСНОВНЫЕ НАСТРОЙКИ ---

# Ваш постоянный URL для фронтенда
FRONT_URL = "https://myoladean.serveo.net"

# Ваш актуальный токен бота
BOT_TOKEN = '7049824274:AAEPN7qLbCZRt3kCbN63aPm_AmQemXdNpmM'  # Используйте самый свежий токен

bot = telebot.TeleBot(BOT_TOKEN)


# --- ОБРАБОТЧИКИ КОМАНД ---

@bot.message_handler(commands=['start', 'app'])
def send_welcome(message):
    """
    Этот обработчик отправляет приветственное сообщение
    с инлайн-кнопкой для запуска Mini App.
    """
    # Создаем инлайн-клавиатуру
    markup = types.InlineKeyboardMarkup()

    # Создаем кнопку, которая открывает Mini App
    button = types.InlineKeyboardButton(
        text="🚀 Запустити додаток",
        web_app=WebAppInfo(url=FRONT_URL)
    )
    markup.add(button)

    # Отправляем сообщение с этой кнопкой
    bot.send_message(
        message.chat.id,
        "👋 Вітаю!\n\nНатисніть кнопку нижче, щоб запустити додаток.",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: True)
def handle_all_other_messages(message):
    """
    Этот обработчик "ловит" любые другие текстовые сообщения
    и предлагает пользователю открыть приложение.
    """
    # Мы просто повторно отправляем кнопку запуска
    send_welcome(message)


# --- ЗАПУСК БОТА ---

print("Бот запущен и готов к работе...")
bot.polling(none_stop=True)