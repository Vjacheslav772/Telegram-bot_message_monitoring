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
API_ID = os.getenv('API_ID')  # Например, '1234567'
API_HASH = os.getenv('API_HASH')  # Например, '1234567890abcdef1234567890abcdef'
PHONE = os.getenv('PHONE')  # Например, '+79991234567'
CHANNEL_ID = os.getenv('CHANNEL_ID')  # Например, '-1001234567890'

# Преобразуем API_ID и CHANNEL_ID в числа (они приходят как строки из .env)
API_ID = int(API_ID)
CHANNEL_ID = int(CHANNEL_ID)

# Список чатов для мониторинга (можно оставить в коде или тоже вынести в .env)
CHATS_TO_MONITOR = [int(chat_id) for chat_id in os.getenv('CHATS_TO_MONITOR').split(',')]

# Ключевые слова и исключения (оставляем в коде, так как они не конфиденциальны)
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

# Далее код остается без изменений...

# Функция для получения времени и даты в московском формате
def get_moscow_time():
    moscow_time = datetime.datetime.now()  # Текущие время и дата
    return moscow_time.strftime('%d-%m-%Y %H:%M:%S')  # Формат: дд-мм-гггг чч:мм:сс

# Отправка уведомления о запуске
async def send_start_message():
    start_message = (
        f"Бот запущен\n"
        f"Время по Москве: {get_moscow_time()}\n"
        f"Мониторинг идет со следующих чатов: {CHATS_TO_MONITOR}\n"
        f"Ключевые слова: {KEYWORDS}\n"
        f"Исключения: {EXCEPTIONS}"
    )
    await client.send_message(CHANNEL_ID, start_message)
    logging.info("Бот запущен")  # Запись в лог

# Проверка текста на наличие ключевых слов
def check_message(text):
    if not text:  # Если текста нет, возвращаем None
        return None
    text_lower = text.lower()  # Приводим текст к нижнему регистру для удобства
    for exception in EXCEPTIONS:
        if exception in text_lower:  # Если есть исключение, пропускаем
            return None
    for keyword in KEYWORDS:
        if keyword in text_lower:  # Если есть ключевое слово, возвращаем его
            return keyword
    return None

# Обработчик новых сообщений
@client.on(events.NewMessage(chats=CHATS_TO_MONITOR))
async def handle_new_message(event):
    try:
        # Получаем текст сообщения
        message_text = event.message.text
        chat_id = event.chat_id
        matched_keyword = check_message(message_text)

        if matched_keyword:  # Если найдено ключевое слово
            # Формируем сообщение для пересылки
            forward_message = (
                f"{message_text}\n"
                f"{'*' * 20}\n"
                f"Время по Москве: {get_moscow_time()}\n"
                f"Чат: {chat_id}\n"
                f"Ключевое слово: {matched_keyword}"
            )
            await client.send_message(CHANNEL_ID, forward_message)
            logging.info(f"Переслано сообщение из чата {chat_id} с ключевым словом '{matched_keyword}'")
    except Exception as e:
        # Если возникла ошибка
        error_message = (
            f"Проблема: {str(e)}\n"
            f"Время по Москве: {get_moscow_time()}"
        )
        await client.send_message(CHANNEL_ID, error_message)
        logging.error(f"Ошибка: {str(e)}")

# Основная функция запуска бота
async def main():
    await client.start(phone=PHONE)  # Запускаем клиента с вашим номером
    await send_start_message()  # Отправляем сообщение о запуске
    print("Бот запущен и мониторит чаты...")
    await client.run_until_disconnected()  # Держим бота активным

# Запуск бота
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Если вы остановили код вручную (Ctrl+C)
        stop_message = f"Код остановлен\nВремя по Москве: {get_moscow_time()}"
        asyncio.run(client.send_message(CHANNEL_ID, stop_message))
        logging.info("Код остановлен пользователем")
    except Exception as e:
        # Если произошла другая ошибка при запуске
        error_message = f"Проблема при запуске: {str(e)}\nВремя по Москве: {get_moscow_time()}"
        asyncio.run(client.send_message(CHANNEL_ID, error_message))
        logging.error(f"Ошибка при запуске: {str(e)}")
