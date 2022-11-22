import logging
import os
import time
import requests
import sys
import exceptions
import telegram

from telegram import Bot, TelegramError
from http import HTTPStatus

from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logger = logging.getLogger(__name__)


def send_message(bot: Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат.
    Принимает на вход экземпляр класса Bot и строку с текстом сообщения.
    """
    logger.info('Формирование сообщения')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Сообщение успешно отправлено')
    except TelegramError as error:
        logger.error(f'Сбой при отправке сообщения в телеграм: {error}')


def get_api_answer(current_timestamp: int) -> dict:
    """Делает запрос к единственному эндпоинту API-сервиса.
    В качестве параметра функция получает временную метку.
    """
    logger.info('Выполнение запроса к API')
    timestamp = current_timestamp or int(time.time())
    request_params = dict(
        url=ENDPOINT,
        headers=HEADERS,
        params={'from_date': timestamp}
    )
    try:
        response = requests.get(**request_params)
        if response.status_code != HTTPStatus.OK:
            raise exceptions.HTTPException(
                f'Страница недоступна. Ошибка: {response.status_code}'
            )
        return response.json()
    except requests.RequestException:
        logger.error('Ошибка запроса')


def check_response(response: dict) -> dict:
    """Проверяет ответ API на корректность.
    В качестве параметра функция получает ответ API.
    Ответ приведен к типам данных Python.
    """
    logger.info('Начало проверки ответа API')
    if not isinstance(response, dict):
        raise exceptions.NotDictException(
            f'Пришел ответ в неверном формате: {type(response)}'
        )
    if 'homeworks' not in response:
        raise exceptions.HWNotExistException(
            'Домашняя работа отсутствует'
        )
    if not isinstance(response['homeworks'], list):
        response_content = response['homeworks']
        raise exceptions.NotListException(
            f'Пришел ответ в неверном формате: {type(response_content)}'
        )
    if response['homeworks'] is None:
        raise exceptions.EmptyResponseException(
            'Список домашних работ не содержит элементов'
        )
    return response['homeworks']


def parse_status(homework: dict) -> str:
    """Извлекает из информации о конкретной домашней работе статус работы.
    В качестве параметра функция получает всего один элемент из
    списка домашних работ.
    """
    logger.info('Извлечение статуса домашней работы')
    if 'homework_name' not in homework:
        raise exceptions.HWNameNotExistException(
            'Отсутствует имя домашней работы'
        )
    if 'status' not in homework:
        raise exceptions.StatusNotExistException(
            'Отсутствует статус домашней работы'
        )
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise exceptions.HWStatusNotExistException(
            f'Неизвестный статус домашней работы: {homework_status}'
        )
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверяет доступность переменных окружения.
    Если отсутствует хотя бы одна переменная окружения —
    функция должна вернуть False, иначе — True.
    """
    logger.info('Проверка доступности переменных окружения')
    if all((PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN)):
        return True
    else:
        logger.critical('Это логирование нужно для тестов')
        tokens = (
            PRACTICUM_TOKEN,
            TELEGRAM_CHAT_ID,
            TELEGRAM_TOKEN
        )
        non_existent_tokens = ()
        for token in tokens:
            if token is None:
                non_existent_tokens.add(token)
        logger.critical(f'Отсутствуют токены: {non_existent_tokens}')


def main() -> None:
    """Основная логика работы бота."""
    logger.info('Запуск бота')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    if not check_tokens():
        sys.exit('Отсутствует один или несколько токенов')
    current_timestamp = int(time.time())
    previous_message = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if len(homeworks) > 0:
                homework = homeworks[0]
                message = parse_status(homework)
                current_timestamp = response.get(
                    'current_date', current_timestamp
                )
            else:
                logger.debug('Статус работы не поменялся')
                message = 'Нет новых статусов'
        except Exception as error:
            logger.error(f'Сбой в работе программы: {error}')
            message = f'Сбой в работе программы: {error}'
        finally:
            if message != previous_message:
                send_message(bot, message)
                previous_message = message
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s, %(lineno)s',
        stream=sys.stdout
    )
    main()
