# Импорт необходимых библиотек
from telethon import TelegramClient, events
from dotenv import load_dotenv  # Импорт для работы с .env
import os  # Для доступа к переменным окружения
import datetime
import logging
import asyncio

# Загружаем данные из файла .env
load_dotenv()

# Получаем значения из .env
API_ID = int(os.getenv('API_ID'))  # Например, 1234567
API_HASH = os.getenv('API_HASH')  # Например, '1234567890abcdef1234567890abcdef'
PHONE = os.getenv('PHONE')  # Например, '+79991234567'
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))  # Например, -1001234567890

# Список ID чатов для мониторинга из .env
CHATS_TO_MONITOR = [int(chat_id) for chat_id in os.getenv('CHATS_TO_MONITOR').split(',')]

# Список имен чатов из .env
CHAT_NAMES = os.getenv('CHAT_NAMES').split(',')

# Создаем словарь для соответствия ID чатов и их имен
CHAT_MAP = dict(zip(CHATS_TO_MONITOR, CHAT_NAMES))

# Ключевые слова и исключения
KEYWORDS = ['большая чаша', 'маленький стол', 'синий шар']
EXCEPTIONS = ['небольшая чаша', 'столик']

# Настройка логирования в файл
logging.basicConfig(
    filename='telegram_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Создаем объект клиента Telegram
client = TelegramClient('session_name', API_ID, API_HASH)

# Функция для получения времени и даты в московском формате
def get_moscow_time():
    moscow_time = datetime.datetime.now()
    return moscow_time.strftime('%Y-%m-%d   %H:%M:%S')

# Отправка уведомления о запуске
async def send_start_message():
    # Формируем список имен чатов для вывода
    chat_list = [f"{name} ({chat_id})" for chat_id, name in CHAT_MAP.items()]
    start_message = (
        f"Бот запущен\n"
        f"{get_moscow_time()}\n"
        f"Мониторинг идет со следующих чатов:\n{', '.join(chat_list)}\n"
        f"Ключевые слова: {KEYWORDS}\n"
        f"Исключения: {EXCEPTIONS}"
    )
    await client.send_message(CHANNEL_ID, start_message)
    logging.info("Бот запущен")

# Отправка уведомления об остановке
async def send_stop_message():
    stop_message = f"Код остановлен\n{get_moscow_time()}"
    await client.send_message(CHANNEL_ID, stop_message)
    logging.info("Код остановлен пользователем")

# Проверка текста на наличие ключевых слов
def check_message(text):
    if not text:
        return None
    text_lower = text.lower()
    for exception in EXCEPTIONS:
        if exception in text_lower:
            return None
    for keyword in KEYWORDS:
        if keyword in text_lower:
            return keyword
    return None

# Обработчик новых сообщений
@client.on(events.NewMessage(chats=CHATS_TO_MONITOR))
async def handle_new_message(event):
    try:
        message_text = event.message.text
        chat_id = event.chat_id
        matched_keyword = check_message(message_text)

        if matched_keyword:
            # Получаем имя чата из словаря
            chat_name = CHAT_MAP.get(chat_id, str(chat_id))  # Если имени нет, выводим ID
            forward_message = (
                f"{message_text}\n"
                f"{'*' * 60}\n"
                f"{get_moscow_time()}\n"
                f"Чат: {chat_name} ({chat_id})\n"
                f"Ключевое слово: {matched_keyword}"
            )
            await client.send_message(CHANNEL_ID, forward_message)
            logging.info(f"Переслано сообщение из чата {chat_id} ({chat_name}) с ключевым словом '{matched_keyword}'")
    except Exception as e:
        error_message = (
            f"Проблема: {str(e)}\n"
            f"{get_moscow_time()}"
        )
        await client.send_message(CHANNEL_ID, error_message)
        logging.error(f"Ошибка: {str(e)}")

# Основная функция запуска бота
async def main():
    await client.start(phone=PHONE)
    await send_start_message()
    print("Бот запущен и мониторит чаты...")
    await client.run_until_disconnected()

# Запуск бота с обработкой остановки
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        # Останавливаем клиент и отправляем сообщение об остановке
        loop.run_until_complete(send_stop_message())
        loop.run_until_complete(client.disconnect())
        print("Бот остановлен")
    except Exception as e:
        error_message = f"Проблема при запуске: {str(e)}\n{get_moscow_time()}"
        loop.run_until_complete(client.send_message(CHANNEL_ID, error_message))
        logging.error(f"Ошибка при запуске: {str(e)}")
    finally:
        loop.close()
