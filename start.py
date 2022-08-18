import os
import time
from datetime import datetime as dt
from datetime import timedelta

import telegram
from dotenv import load_dotenv
from fast_bitrix24 import Bitrix
from imap_tools import MailBox

import mail_parsing as parsing
import statistic
from models import Users

load_dotenv()

IMAP = os.getenv('IMAP')
FROM_ = os.getenv('FROM')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
secret_login = os.getenv('LOGIN')
secret_pass = os.getenv('PASSWORD')
RETRY_TIME = 30
BITRIX24_TOKEN = os.getenv('BITRIX24_TOKEN')
ROLE = {
    'all': Users.select(),
    'stuff': Users.select().where(Users.role == '1'),
}


def check_env():
    """Проверка заполнения переменных окружения."""

    check_list = [
        IMAP,
        FROM_,
        secret_login,
        secret_pass,
        TELEGRAM_TOKEN,
        BITRIX24_TOKEN,
    ]
    for check in check_list:
        if not check:
            return False
    return True


def send_message(bot, message, group):
    """Отправка сообщения ботом."""

    users = ROLE[group]
    for user in users:
        chat_id = user.id_gram
        bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='HTML',
        )
        time.sleep(1)


def get_mail(bot):
    """Проверка почты"""

    mailbox = MailBox(IMAP).login(secret_login, secret_pass)
    messages = parsing.get_mail(mailbox, FROM_)
    mailbox.logout()
    if messages:
        for message in reversed(messages):
            group = 'all'
            send_message(bot, message, group)


def get_statistic(day_week, bitrix, bot):
    """Запрос статистики"""

    if day_week != '6' and day_week != '0':
        call_message = statistic.call(bitrix)
        group = 'all'
        send_message(bot, call_message, group)
        time.sleep(5)
        message = statistic.payer()
        send_message(bot, message, group)


def main():
    """Основная логика работы бота."""

    if not check_env():
        error_env = (
            'Не заполнены переменные окружения. '
            'Работа программы остановлена'
        )
        raise ValueError(error_env)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    bitrix = Bitrix(BITRIX24_TOKEN)

    day_now = dt.now()
    send_statistic_time = dt(
        day_now.year, day_now.month, day_now.day, 12, 15, 0
    )
    if send_statistic_time < day_now:
        send_statistic_time += timedelta(days=1)

    cache_message = ''
    while True:
        try:
            day_now = dt.now()
            day_week = day_now.strftime('%w')
            get_mail(bot)
            if send_statistic_time < day_now:
                send_statistic_time += timedelta(days=1)
                get_statistic(day_week, bitrix, bot)
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'<b>Сбой в работе программы:</b> {error}'
            if message != cache_message:
                group = 'stuff'
                send_message(bot, message, group)
                cache_message = message
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
