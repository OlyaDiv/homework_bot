import logging
import os
import time
import requests
import sys
import exceptions

from telegram import Bot, TelegramError
from http import HTTPStatus

from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(message)s, %(name)s, %(lineno)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False


def send_message(bot: Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат.
    Принимает на вход экземпляр класса Bot и
    строку с текстом сообщения.
    """
    logger.debug('Формирование сообщения')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except TelegramError:
        logger.error('Сбой при отправке сообщения в телеграм')


def get_api_answer(current_timestamp: int) -> dict:
    """Делает запрос к единственному эндпоинту API-сервиса.
    В качестве параметра функция получает временную метку.
    """
    logger.debug('Выполнение запроса к API')
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    request_params = dict(
        url=ENDPOINT,
        headers=HEADERS,
        params=params
    )
    response = requests.get(**request_params)
    if response.status_code != HTTPStatus.OK:
        status_code = response.status_code
        raise exceptions.MyHTTPErrorException(
            f'Страница недоступна.Ошибка при запросе к API: {status_code}'
        )
    return response.json()


def check_response(response: dict) -> dict:
    """Проверяет ответ API на корректность.
    В качестве параметра функция получает ответ API.
    Ответ приведен к типам данных Python.
    """
    logger.debug('Начало проверки ответа API')
    if not isinstance(response, dict):
        raise TypeError('Некорректный ответ от API')
    if not isinstance(response['homeworks'], list):
        raise TypeError('Некорректный ответ от API')
    if response['homeworks'] is None:
        raise ValueError('Список домашних работ не содержит элементов')
    if 'homeworks' not in response:
        raise KeyError('Ключ homeworks отсутствует')
    return response['homeworks'][0]


def parse_status(homework: dict) -> str:
    """Извлекает из информации о конкретной домашней работе статус работы.
    В качестве параметра функция получает всего один элемент из
    списка домашних работ.
    """
    logger.debug('Извлечение статуса домашней работы')
    if 'homework_name' not in homework:
        logger.error('Неизвестное имя домашней работы')
        raise KeyError('Неизвестное имя домашней работы')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        logger.error('Неизвестный статус домашней работы')
        raise KeyError('Неизвестный статус домашней работы')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверяет доступность переменных окружения.
    Если отсутствует хотя бы одна переменная окружения —
    функция должна вернуть False, иначе — True.
    """
    logger.debug('Проверка доступности переменных окружения')
    if all((PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN)):
        return True


def main() -> None:
    """Основная логика работы бота."""
    logger.debug('Запуск бота')
    if not check_tokens():
        logger.critical('Отсутствует один или несколько токенов')
        sys.exit('Отсутствует один или несколько токенов')

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    previous_message = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            current_timestamp = response.get('current_date', current_timestamp)
        except Exception as error:
            logger.error('Сбой в работе программы')
            message = f'Сбой в работе программы: {error}'
        else:
            logger.debug('Статус работы не поменялся')
            message = 'Нет новых статусов'
        finally:
            if message != previous_message:
                send_message(bot, message)
                logger.info('Сообщение успешно отправлено')
                previous_message = message
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s, %(lineno)s'
    )
    main()
