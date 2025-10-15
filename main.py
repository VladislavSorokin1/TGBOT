import os
import telebot
from telebot import types
import time
from random import randint
import sqlite3
import re
import asyncio
import os.path
from pathlib import Path
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

FRONT_URL = "https://myoladean.serveo.net"


# ===== Глобальные поля пользователя (как было) =====
group, phone, email, departament, surname, name, userID, course, birthday = '', '', '', '', '', '', '', '', ''
bot = telebot.TeleBot('7049824274:AAEPN7qLbCZRt3kCbN63aPm_AmQemXdNpmM')

admID = [6113448235]

# ====== Утилиты ======

def has_digits(s: str) -> bool:
    """True, если строка содержит хоть одну цифру."""
    return any(ch.isdigit() for ch in s)

def miniapp_menu(url: str):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("📲 Відкрити застосунок", web_app=WebAppInfo(url=url)))
    return kb

def is_convertible_to_str(string):
    try:
        int(string)
        return True
    except ValueError:
        return False

def check_user_auth(user_id):
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    cur.execute('SELECT userID FROM students WHERE userID = ?', (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result is not None

def validate_date(data):
    pattern = r'^\d{2}\.\d{2}\.\d{4}$'  # "дд.мм.рррр"
    return bool(re.match(pattern, data))

# ====== Админ-меню ======

def admCabinet(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    item1 = types.KeyboardButton('🕖Встановити розклад')
    item2 = types.KeyboardButton('🔍Пошук студентів')
    item3 = types.KeyboardButton('ℹНаписати повідомлення студентам')
    markup.add(item1, item2, item3)
    bot.send_message(message.chat.id, '✅Ви авторизувались як адміністратор', reply_markup=markup)

# ====== Mini App команды ======

@bot.message_handler(commands=['app'])
def open_app(message):
    bot.send_message(
        message.chat.id,
        "Натисни, щоб відкрити застосунок:",
        reply_markup=miniapp_menu(FRONT_URL)
    )

# ====== Старт ======

@bot.message_handler(commands=['start'])
def hello(message):
    global userID
    userID = message.chat.id
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    cur.execute(
        'CREATE TABLE IF NOT EXISTS students (userID int(50) ,name varchar(20) , surname varchar(20) ,birthday varchar(20), department varchar(50) , studentGroup varchar(50) , course int(2) ,  phoneNumber int(20) , email varchar(50) , status varchar(50))')
    cur.close()
    conn.close()
    # Добавим кнопку Mini App сразу в старт
    bot.send_message(message.chat.id, "📲 Швидкий доступ до застосунку:", reply_markup=miniapp_menu(FRONT_URL))

    if message.chat.id in admID:
        admCabinet(message)
    elif check_user_auth(userID):
        menu(message)
    else:
        bot.send_message(message.chat.id, '👋Вітаю, 🆕Введіть своє ім’я...')
        bot.register_next_step_handler(message, nameFunc)

# ====== Регистрация ======

def nameFunc(message):
    global name
    if has_digits(message.text):
        bot.send_message(message.chat.id, "🚫Помилка! Ім'я може вміщати тільки букви! Спробуйте ще раз...")
        bot.register_next_step_handler(message, nameFunc)
    else:
        name = message.text
        bot.send_message(message.chat.id, '✏Введіть своє Прізвище...')
        bot.register_next_step_handler(message, surnameFunc)

def surnameFunc(message):
    global surname
    if has_digits(message.text):
        bot.send_message(message.chat.id, '🚫Помилка! ✏Прізвище може вміщати тільки букви! Спробуйте ще раз...')
        bot.register_next_step_handler(message, surnameFunc)
    else:
        surname = message.text
        bot.send_message(message.chat.id, '🎂Введіть свій день народження у форматі дд.мм.рррр ...')
        bot.register_next_step_handler(message, birthdayFunc)

def birthdayFunc(message):
    global birthday
    if validate_date(message.text):
        birthday = message.text
        bot.send_message(message.chat.id, '🕶Введіть свій Факультет...')
        bot.register_next_step_handler(message, departamentFunc)
    else:
        bot.send_message(message.chat.id,
                         '🚫Помилка!🎂Дата народження повинна бути у форматі дд.мм.рррр! Спробуйте ще раз...')
        bot.register_next_step_handler(message, birthdayFunc)

def departamentFunc(message):
    global departament
    departament = message.text
    bot.send_message(message.chat.id, '🧐Введіть свій Курс...')
    bot.register_next_step_handler(message, courseFunc)

def courseFunc(message):
    global course
    course = message.text
    bot.send_message(message.chat.id, '👥Введіть свою групу...')
    bot.register_next_step_handler(message, groupFunc)

def groupFunc(message):
    global group
    group = message.text
    bot.send_message(message.chat.id, '📱Введіть свій Номер телефону(пр. 380961231231)...')
    bot.register_next_step_handler(message, phoneFunc)

def phoneFunc(message):
    global phone
    if is_convertible_to_str(message.text) and len(message.text) == 12:
        phone = message.text
        bot.send_message(message.chat.id, '📧Введіть свою електрону скриньку(пр. primary@gmail.com)...')
        bot.register_next_step_handler(message, emailFunc)
    else:
        bot.send_message(message.chat.id,
                         '🚫Помилка! 📱Номер телефону може вміщати тільки цифри (пр. 380961231231)! Спробуйте ще раз...')
        bot.register_next_step_handler(message, phoneFunc)

def emailFunc(message):
    global email
    if '@' in message.text:
        email = message.text
        insertIntoDB(message)
    else:
        bot.send_message(message.chat.id,
                         "🚫Помилка! 📧Електрона скринька має обов'язково вміщати @! Спробуйте ще раз...")
        bot.register_next_step_handler(message, emailFunc)

def insertIntoDB(message):
    global userID
    userID = message.chat.id
    global group, phone, email, departament, surname, name, course, birthday
    student_info = [userID, name, surname, birthday, departament, group, course, phone, email]
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO students (userID , name, surname, birthday , department, studentGroup, course , phoneNumber, email) VALUES (?, ?, ?, ?, ?, ?, ?, ? , ?)',
        student_info)
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, '✅Ви успішно зареєструвались')
    menu(message)

# ====== Меню ======

def menu(message):
    if message.chat.id in admID:
        admCabinet(message)
    else:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        item1 = types.KeyboardButton('👥Моя інформація')
        item2 = types.KeyboardButton('ℹСтатус')
        item3 = types.KeyboardButton('🎇Соц. Мережі')
        item4 = types.KeyboardButton('🕖Розклад')
        markup.add(item1, item2, item3, item4)
        # добавим мини-аппу в меню пользователю (доп.ряд)
        markup.row(KeyboardButton("📲 Відкрити застосунок", web_app=WebAppInfo(url=FRONT_URL)))
        bot.send_message(message.chat.id, '🛣Головне меню', reply_markup=markup)

# ====== Остальные хэндлеры (как у тебя было) ======

@bot.message_handler(func=lambda message: message.text == '👥Моя інформація')
def send_info(message):
    global userID
    userID = message.chat.id
    print(userID)
    markup = types.ReplyKeyboardMarkup(row_width=2)
    item1 = types.KeyboardButton('✏Змінити дані')
    item2 = types.KeyboardButton('🚫Назад')
    markup.add(item1, item2)
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    cur.execute('SELECT * FROM students WHERE userID = ?', (userID,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    print(result)
    name, surname, birthday, department, group, course, phone, email = result[1:9]
    info_message = f"ℹІнформація\n🆕Ім'я: {name}\n✏Прізвище: {surname}\n🎂Дата народження: {birthday}\n🕶Факультет: {department}\n👥Група: {group}\n🧐Курс: {course}\n📱Номер телефону: {phone}\n📧Електрона скринька: {email}"
    bot.send_message(message.chat.id, info_message, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '🚫Назад')
def returnToMenu(message):
    menu(message)

@bot.message_handler(func=lambda message: message.text == '✏Змінити дані')
def changeInfo(message):
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("🆕Ім'я", callback_data='name')
    button2 = types.InlineKeyboardButton("✏Прізвище", callback_data='surname')
    button3 = types.InlineKeyboardButton("🎂Дата народження", callback_data='birthday')
    button4 = types.InlineKeyboardButton("🕶Факультет", callback_data='departament')
    button5 = types.InlineKeyboardButton("👥Група", callback_data='group')
    button6 = types.InlineKeyboardButton("🧐Курс", callback_data='course')
    button7 = types.InlineKeyboardButton("📱Номер телефону", callback_data='phone')
    button8 = types.InlineKeyboardButton("📧Електрона скринька", callback_data='email')
    button9 = types.InlineKeyboardButton("🚫Назад", callback_data='menu')
    markup.add(button1, button2, button3, button4, button5, button6, button7, button8, button9)
    bot.send_message(message.chat.id, '✏Оберіть що ви хочете змінити', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    item1 = types.KeyboardButton('🚫Назад')
    markup.add(item1)
    if call.data == 'phoneDecanat':
        bot.send_message(call.message.chat.id, 'Номер телефону деканату: <code>+380123123123</code>', parse_mode='HTML')
    if call.data == 'menu':
        menu(call.message)
    if call.data == 'name':
        bot.send_message(call.message.chat.id, "Введіть нове 🆕Ім'я...", reply_markup=markup)
    elif call.data == 'surname':
        bot.send_message(call.message.chat.id, "Введіть нове ✏Прізвище...", reply_markup=markup)
    elif call.data == 'departament':
        bot.send_message(call.message.chat.id, "Введіть новий 🕶Факультет...", reply_markup=markup)
    elif call.data == 'group':
        bot.send_message(call.message.chat.id, "Введіть нову 👥групу...", reply_markup=markup)
    elif call.data == 'phone':
        bot.send_message(call.message.chat.id, "Введіть новий 📱Номер телефону...", reply_markup=markup)
    elif call.data == 'email':
        bot.send_message(call.message.chat.id, "Введіть нову 📧електрону скриньку...", reply_markup=markup)
    elif call.data == 'course':
        bot.send_message(call.message.chat.id, "Введіть новий 🧐Курс...", reply_markup=markup)
    elif call.data == 'birthday':
        bot.send_message(call.message.chat.id, "Введіть нову 🎂дату народження...", reply_markup=markup)
    bot.register_next_step_handler(call.message, insertNewData, call.message.chat.id, call)

def insertNewData(message, chat_id, call):
    newData = message.text
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    global userID
    userID = message.chat.id
    if call.data == 'name':
        if has_digits(message.text) and message.text != '🚫Назад':
            bot.send_message(message.chat.id, "🚫Помилка! Ім'я може вміщати тільки букви! Спробуйте ще раз...")
            bot.register_next_step_handler(message, insertNewData, call.message.chat.id, call)
        elif message.text != '🚫Назад':
            cur.execute("UPDATE students SET name = ? WHERE userID = ?", (newData, userID))
            bot.send_message(chat_id, "✅Ви успішно оновили дані!")
            menu(message)
    elif call.data == 'surname':
        if has_digits(message.text) and message.text != '🚫Назад':
            bot.send_message(message.chat.id, "🚫Помилка! Прізвище може вміщати тільки букви! Спробуйте ще раз...")
            bot.register_next_step_handler(message, insertNewData, call.message.chat.id, call)
        elif message.text != '🚫Назад':
            cur.execute("UPDATE students SET surname = ? WHERE userID = ?", (newData, userID))
            bot.send_message(chat_id, "✅Ви успішно оновили дані!")
            menu(message)
    elif call.data == 'departament':
        if message.text != '🚫Назад':
            cur.execute("UPDATE students SET department = ? WHERE userID = ?", (newData, userID))
            bot.send_message(chat_id, "✅Ви успішно оновили дані!")
            menu(message)
    elif call.data == 'group':
        if message.text != '🚫Назад':
            cur.execute("UPDATE students SET studentGroup = ? WHERE userID = ?", (newData, userID))
            bot.send_message(chat_id, "✅Ви успішно оновили дані!")
            menu(message)
    elif call.data == 'phone':
        if is_convertible_to_str(message.text) and message.text != '🚫Назад':
            if len(message.text) == 12:
                cur.execute("UPDATE students SET phoneNumber = ? WHERE userID = ?", (newData, userID))
                bot.send_message(chat_id, "✅Ви успішно оновили дані!")
                menu(message)
            else:
                bot.send_message(message.chat.id,
                                 "🚫Помилка! Номер телефону може вміщати тільки цифри та 12 знаків (пр. 380961231231)! Спробуйте ще раз...")
                bot.register_next_step_handler(message, insertNewData, call.message.chat.id, call)
        elif message.text != '🚫Назад':
            bot.send_message(message.chat.id,
                             "🚫Помилка! Номер телефону може вміщати тільки цифри та 12 знаків (пр. 380961231231)! Спробуйте ще раз...")
            bot.register_next_step_handler(message, insertNewData, call.message.chat.id, call)
    elif call.data == 'email':
        if '@' in message.text:
            cur.execute("UPDATE students SET email = ? WHERE userID = ?", (newData, userID))
            bot.send_message(chat_id, "✅Ви успішно оновили дані!")
            menu(message)
        elif message.text != '🚫Назад':
            bot.send_message(message.chat.id,
                             "🚫Помилка! 📧Електрона скринька має обов'язково вміщати @! Спробуйте ще раз...")
            bot.register_next_step_handler(message, insertNewData, call.message.chat.id, call)
    elif call.data == 'course':
        cur.execute("UPDATE students SET course = ? WHERE userID = ?", (newData, userID))
        bot.send_message(chat_id, "✅Ви успішно оновили дані!")
        menu(message)
    elif call.data == 'birthday':
        if validate_date(message.text):
            cur.execute("UPDATE students SET birthday = ? WHERE userID = ?", (newData, userID))
            bot.send_message(chat_id, "✅Ви успішно оновили дані!")
            menu(message)
        else:
            bot.send_message(message.chat.id,
                             '🚫Помилка!🎂Дата народження повинна бути у форматі дд.мм.рррр! Спробуйте ще раз...')
            bot.register_next_step_handler(message, insertNewData, call.message.chat.id, call)

    conn.commit()
    cur.close()
    conn.close()

@bot.message_handler(func=lambda message: message.text == 'ℹСтатус')
def status(message):
    global userID
    userID = message.chat.id
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    cur.execute('SELECT status FROM students WHERE userID = ?', (userID,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result == (None,):
        markup = types.ReplyKeyboardMarkup(row_width=2)
        item1 = types.KeyboardButton('Змінити ℹСтатус')
        item2 = types.KeyboardButton('🚫Назад')
        markup.add(item1, item2)
        bot.send_message(message.chat.id, 'Ви ще не встановили ℹСтатус', reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        item1 = types.KeyboardButton('Змінити ℹСтатус')
        item2 = types.KeyboardButton('🚫Назад')
        markup.add(item1, item2)
        result = str(result)
        result = result.replace("('", "").replace("',)", "")
        bot.send_message(message.chat.id, f'Ваш ℹСтатус:{result}', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Змінити ℹСтатус')
def changeStatus(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    item1 = types.KeyboardButton('🏡Вдома')
    item2 = types.KeyboardButton('🤒Хворий')
    item3 = types.KeyboardButton('💼Працюю')
    item4 = types.KeyboardButton('🛫За кордоном')
    markup.add(item1, item2, item3, item4)
    bot.send_message(message.chat.id, 'Оберіть один із доступних ℹСтатусів', reply_markup=markup)

    @bot.message_handler(func=lambda message: message.text == '🏡Вдома')
    def temp(message): setStatus(message, '🏡Вдома')

    @bot.message_handler(func=lambda message: message.text == '💼Працюю')
    def temp(message): setStatus(message, '💼Працюю')

    @bot.message_handler(func=lambda message: message.text == '🤒Хворий')
    def temp(message): setStatus(message, '🤒Хворий')

    @bot.message_handler(func=lambda message: message.text == '🛫За кордоном')
    def temp(message): setStatus(message, '🛫За кордоном')

def setStatus(message, statusStr):
    global userID
    userID = message.chat.id
    conn = sqlite3.connect('database.sql')
    cur = conn.cursor()
    cur.execute("UPDATE students SET status = ? WHERE userID = ?", (statusStr, userID))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, '✅Новий ℹСтатус успішно встановлено!')
    menu(message)

@bot.message_handler(func=lambda message: message.text == '🕖Розклад')
def selectCourse(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    item1 = types.KeyboardButton('1 Курс')
    item2 = types.KeyboardButton('2 Курс')
    item3 = types.KeyboardButton('3 Курс')
    item4 = types.KeyboardButton('4 Курс')
    item5 = types.KeyboardButton('5 Курс')
    item6 = types.KeyboardButton('🚫Назад')
    markup.add(item1, item2, item3, item4, item5, item6)
    bot.send_message(message.chat.id, 'Оберіть 🧐Курс', reply_markup=markup)

    @bot.message_handler(func=lambda message: message.text == '1 Курс')
    def temp(message):
        sendFile(message, '1')

    @bot.message_handler(func=lambda message: message.text == '2 Курс')
    def temp(message):
        sendFile(message, '2')

    @bot.message_handler(func=lambda message: message.text == '3 Курс')
    def temp(message):
        sendFile(message, '3')

    @bot.message_handler(func=lambda message: message.text == '4 Курс')
    def temp(message):
        sendFile(message, '4')

    @bot.message_handler(func=lambda message: message.text == '5 Курс')
    def temp(message):
        sendFile(message, '5')

    def sendFile(message, num):
        suffixes = ["txt", "pdf", "docx", "csv", "xls", "xlsx", "png"]
        file_found = False
        for suffix in suffixes:
            print(num, suffix)
            try:
                with open(f"{num}.{suffix}", 'rb') as file:
                    bot.send_document(message.chat.id, file)
                    file_found = True
                    menu(message)

            except FileNotFoundError:
                pass
        if not file_found:
            bot.send_message(message.chat.id, '🕖Розклад не знайдено')
            menu(message)

@bot.message_handler(func=lambda message: message.text == '🕖Встановити розклад')
def setTable(message):
    if message.chat.id in admID:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        item1 = types.KeyboardButton('1')
        item2 = types.KeyboardButton('2')
        item3 = types.KeyboardButton('3')
        item4 = types.KeyboardButton('4')
        item5 = types.KeyboardButton('5')
        item6 = types.KeyboardButton('🚫Назад')
        markup.add(item1, item2, item3, item4, item5, item6)
        bot.send_message(message.chat.id, '🧭Оберіть Курс якому ви хочете змінити 🕖Розклад', reply_markup=markup)

        @bot.message_handler(func=lambda message: message.text == '1')
        def setTableHandle(message):
            markup = types.ReplyKeyboardMarkup(row_width=2)
            item1 = types.KeyboardButton('🚫Назад')
            markup.add(item1)
            bot.send_message(message.chat.id, '📄Відправте файл з 🕖Розкладом', reply_markup=markup)

            @bot.message_handler(content_types=['document'])
            def handle_document(message):
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                file_extension = Path(file_info.file_path).suffix
                filename = f"1{file_extension}"
                with open(filename, 'wb') as new_file:
                    new_file.write(downloaded_file)
                bot.send_message(message.chat.id, '✅Ви успішно завантажили новий розклад')
                setTable(message)

        @bot.message_handler(func=lambda message: message.text == '2')
        def setTableHandle(message):
            markup = types.ReplyKeyboardMarkup(row_width=2)
            item1 = types.KeyboardButton('🚫Назад')
            markup.add(item1)
            bot.send_message(message.chat.id, '📄Відправте файл з 🕖Розкладом', reply_markup=markup)

            @bot.message_handler(content_types=['document'])
            def handle_document(message):
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                file_extension = Path(file_info.file_path).suffix
                filename = f"2{file_extension}"
                with open(filename, 'wb') as new_file:
                    new_file.write(downloaded_file)
                    bot.send_message(message.chat.id, '✅Ви успішно завантажили новий розклад')
                    setTable(message)

        @bot.message_handler(func=lambda message: message.text == '3')
        def setTableHandle(message):
            markup = types.ReplyKeyboardMarkup(row_width=2)
            item1 = types.KeyboardButton('🚫Назад')
            markup.add(item1)
            bot.send_message(message.chat.id, '📄Відправте файл з 🕖Розкладом', reply_markup=markup)

            @bot.message_handler(content_types=['document'])
            def handle_document(message):
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                file_extension = Path(file_info.file_path).suffix
                filename = f"3{file_extension}"
                with open(filename, 'wb') as new_file:
                    new_file.write(downloaded_file)
                    bot.send_message(message.chat.id, '✅Ви успішно завантажили новий розклад')
                    setTable(message)

        @bot.message_handler(func=lambda message: message.text == '4')
        def setTableHandle(message):
            markup = types.ReplyKeyboardMarkup(row_width=2)
            item1 = types.KeyboardButton('🚫Назад')
            markup.add(item1)
            bot.send_message(message.chat.id, '📄Відправте файл з 🕖Розкладом', reply_markup=markup)

            @bot.message_handler(content_types=['document'])
            def handle_document(message):
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                file_extension = Path(file_info.file_path).suffix
                filename = f"4{file_extension}"
                with open(filename, 'wb') as new_file:
                    new_file.write(downloaded_file)
                    bot.send_message(message.chat.id, '✅Ви успішно завантажили новий розклад')
                    setTable(message)

        @bot.message_handler(func=lambda message: message.text == '5')
        def setTableHandle(message):
            markup = types.ReplyKeyboardMarkup(row_width=2)
            item1 = types.KeyboardButton('🚫Назад')
            markup.add(item1)
            bot.send_message(message.chat.id, '📄Відправте файл з 🕖Розкладом', reply_markup=markup)

            @bot.message_handler(content_types=['document'])
            def handle_document(message):
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                file_extension = Path(file_info.file_path).suffix
                filename = f"5{file_extension}"
                with open(filename, 'wb') as new_file:
                    new_file.write(downloaded_file)
                    bot.send_message(message.chat.id, '✅Ви успішно завантажили новий розклад')
                    setTable(message)
    else:
        bot.send_message(message.chat.id, '🚫Вам відмовлено в доступі')
        menu(message)

@bot.message_handler(func=lambda message: message.text == '🔍Пошук студентів')
def searchStudents(message):
    if message.chat.id in admID:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        item1 = types.KeyboardButton('🚫Назад')
        markup.add(item1)
        bot.send_message(message.chat.id, 'Введіть ✏Прізвище студента...', reply_markup=markup)
        bot.register_next_step_handler(message, searchStudentsHandle)
    else:
        bot.send_message(message.chat.id, '🚫Вам відмовлено в доступі')
        menu(message)

def searchStudentsHandle(message):
    if message.text != '🚫Назад':
        conn = sqlite3.connect('database.sql')
        cur = conn.cursor()
        cur.execute(
            'SELECT name , surname , birthday , department , studentgroup , phoneNumber , email , status , course  FROM students WHERE surname = ?',
            (message.text,))
        result = cur.fetchall()
        cur.close()
        conn.close()
        if not result:
            bot.send_message(message.chat.id, '🚫Помилка! Студента з таким прізвищем не знайдено! Спробуйте ще раз...')
            searchStudents(message)
        for row in result:
            name = row[0]
            surname = row[1]
            birthday = row[2]
            department = row[3]
            studentGroup = row[4]
            phoneNumber = row[5]
            email = row[6]
            status = row[7]
            course = row[8]
            info_message = f"Інформація студента\n🆕Ім'я: {name}\n✏Прізвище: {surname}\n🎂Дата народження: {birthday}\n🕶Факультет: {department}\n👥Група: {studentGroup}\n🧐Курс: {course}\n📱Номер телефону: {phoneNumber}\n📧Електрона скринька: {email}\nℹСтатус: {status}"
            bot.send_message(message.chat.id, info_message)
            menu(message)

@bot.message_handler(func=lambda message: message.text == '🎇Соц. Мережі')
def socials(message):
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text="📫Instagram",
                                         url='https://www.instagram.com/fcit_nuoua?igsh=bHc2cmdxbHA1cDQ1')
    button2 = types.InlineKeyboardButton(text="🌐Веб сайт", url='https://onua.edu.ua/ua/')
    button3 = types.InlineKeyboardButton(text="🌐Веб сайт ФКІТ", url='http://moodle.onua.edu.ua')
    button4 = types.InlineKeyboardButton(text="📧Email",
                                         url='https://mail.google.com/mail/u/0/?view=cm&fs=1&to=vstup@onua.edu.ua')
    button5 = types.InlineKeyboardButton(text="📞Деканат", callback_data='phoneDecanat')
    markup.add(button1, button2, button3, button4, button5)
    bot.send_message(message.chat.id, 'Соціальні мережі навчального закладу:', reply_markup=markup)
    menu(message)

@bot.message_handler(func=lambda message: message.text == 'ℹНаписати повідомлення студентам')
def whatTypeMessage(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    item1 = types.KeyboardButton('📁Файл')
    item2 = types.KeyboardButton('📝Текст')
    item3 = types.KeyboardButton('🚫Назад')
    markup.add(item1, item2, item3)
    bot.send_message(message.chat.id, '⌨Виберіть тип повідомлення яке ви хочете розіслати...', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '📝Текст')
def whatMessage(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    item1 = types.KeyboardButton('🚫Назад')
    markup.add(item1)
    bot.send_message(message.chat.id, '⌨Введіть повідомлення яке ви хочете розіслати...', reply_markup=markup)
    bot.register_next_step_handler(message, confirmMessage)

def confirmMessage(message):
    if message.text != '🚫Назад':
        messageData = message.text
        markup = types.ReplyKeyboardMarkup(row_width=2)
        item1 = types.KeyboardButton('🚫Назад')
        item2 = types.KeyboardButton('✅Так,відправити')
        markup.add(item1, item2)
        bot.send_message(message.chat.id, f'Ви впевнені,що хочете відіслати повідомлення:\n{messageData}',
                         parse_mode='HTML', reply_markup=markup)

        @bot.message_handler(func=lambda message: message.text == '✅Так,відправити')
        def sendMessage(message):
            conn = sqlite3.connect('database.sql')
            cur = conn.cursor()
            cur.execute('SELECT userID  FROM students')
            result = cur.fetchall()
            cur.close()
            conn.close()
            result = [id[0] for id in result]
            print(messageData)
            for i in result:
                bot.send_message(i, 'Повідомлення від адміністратора:')
                bot.send_message(i, messageData)
            bot.send_message(message.chat.id, '✅Повідомлення успішно надіслано!')
            menu(message)
    else:
        menu(message)

@bot.message_handler(func=lambda message: message.text == '📁Файл')
def whatMessage(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    item1 = types.KeyboardButton('🚫Назад')
    markup.add(item1)
    bot.send_message(message.chat.id, '📁Відправте файл який ви хочете розіслати...', reply_markup=markup)

    @bot.message_handler(content_types=['document'])
    def handle_document(message):
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_extension = Path(file_info.file_path).suffix
        filename = message.document.file_name
        with open(filename, 'wb') as new_file:
            new_file.write(downloaded_file)
        conn = sqlite3.connect('database.sql')
        cur = conn.cursor()
        cur.execute('SELECT userID  FROM students')
        result = cur.fetchall()
        cur.close()
        conn.close()
        result = [id[0] for id in result]
        for i in result:
            bot.send_message(i, 'Повідомлення від адміністратора:')
            bot.send_document(i, open(filename, 'rb'))
        bot.send_message(message.chat.id, '✅Файл успішно надісланий!')
        menu(message)

bot.polling(none_stop=True)



