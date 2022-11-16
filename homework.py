import http
import logging
import os
import time
import requests
import sys

from telegram import Bot

from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение успешно отправленно')
    except Exception:
        logger.error('Сбой при отправке сообщения в телеграм')


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if homework_statuses.status_code != http.HTTPStatus.OK:
        logger.error('Страница недоступна')
        raise http.exceptions.HTTPError('Страница недоступна')
    return homework_statuses.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    if type(response) != dict:
        logger.error('Ответ не является словарем')
        raise TypeError('Ответ не является словарем')
    if type(response['homeworks']) != list:
        logger.error('Ответ не является списком')
        raise TypeError('Ответ не является списком')
    if response['homeworks'] == None:
        logger.error('Список домашних работ не содержит элементов')
        raise ValueError('Список домашних работ не содержит элементов')
    if 'homeworks' not in response:
        logger.error('Ключ homeworks отсутствует')
        raise KeyError('Ключ homeworks отсутствует')
    return response['homeworks'][0]


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус этой работы."""
    if 'homework_name' not in homework:
        logger.error('Неизвестное имя домашней работы')
        raise KeyError('Неизвестное имя домашней работы')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        logger.error('Неизвестный статус домашней работы')
        raise KeyError('Неизвестный статус домашней работы')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения, которые необходимы для работы программы."""
    if all((PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN)):
        return True
    else:
        return False


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    previous_message = ''

    if not check_tokens():
        logger.critical('Отсутствует один или несколько токенов')
        raise ValueError('Отсутствует один или несколько токенов')

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            if message != previous_message:
                send_message(bot, message)
                previous_message = message
            current_timestamp = response.get('current_date', current_timestamp)
            time.sleep(RETRY_TIME)

        except Exception as error:
            logger.error('Сбой в работе программы')
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            logger.debug('Статус работы не поменялся')
            message = 'Нет новых статусов'
            send_message(bot, message)


if __name__ == '__main__':
    main()
