# Бот-ассистент
Telegram-бота, который обращается к API сервиса Практикум.Домашка раз в 10 минут и узнает статус отправленной на ревью домашней работы: взята ли домашка в ревью, проверена ли она, а если проверена — то принял её ревьюер или вернул на доработку.

При обновлении статуса отправляет соответствующее уведомление в Telegram;

Логирует свою работу и сообщает о важных проблемах сообщением в Telegram.

### Технологии:
* python 3.9
* python-dotenv 0.19.0
* python-telegram-bot 13.7

### Файл .env
TELEGRAM_TOKEN='TELEGRAM_TOKEN'
PRACTICUM_TOKEN='PRACTICUM_TOKEN'
TELEGRAM_CHAT_ID=357894680
* TELEGRAM_TOKEN - API Token бота полученный у BotFather
* PRACTICUM_TOKEN - token сервиса Практикум
* TELEGRAM_CHAT_ID - id пользователя Telegram

### Запуск проекта:
Клонировать репозиторий и перейти в него в командной строке:
```
git clone git@github.com:OlyaDiv/homework_bot.git
cd homework_bot
```
Создайте и активируйте виртуальное окружение:
```
python3.7 -m venv venv
source venv/bin/activate
```
Установите зависимости из файла requirements.txt
```
pip install -r requirements.txt
```
Запустить проект:
```
python homework.py
```
