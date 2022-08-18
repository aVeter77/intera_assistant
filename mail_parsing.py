from html2text import html2text
from imap_tools import A

import ranks
from models import Payers


def find_text(text, find_str, stop_symb):
    """Парсинг данных платежа."""

    start = text.find(find_str) + len(find_str)
    stop = text.find(stop_symb, start)
    return text[start:stop]


def convert_date(date_text):
    """Преобразование строки в формат даты"""

    date_list = date_text.split('.')
    dd = date_list[0]
    mm = date_list[1]
    yy = '20' + date_list[2]
    return f'{yy}-{mm}-{dd}'


def get_mail(mailbox, from_):
    """Проверка почты."""

    messages = []
    for msg in mailbox.fetch(A(from_=from_), reverse=True):
        text_msg = ' '.join(
            [text.strip() for text in html2text(msg.html).split('\n')]
        )
        uid = msg.uid
        sum = find_text(text_msg, 'на сумму ', '.').replace(',', '.')
        payer = find_text(text_msg, 'Плательщик: ', ' Счет')
        code_company = find_text(text_msg, 'ИНН: ', ' КПП')
        purpose = find_text(text_msg, 'Назначение платежа: ', ' С уважением')
        date_text = find_text(text_msg, 'в дату ', ' платеж')
        date_pay = convert_date(date_text)

        if not Payers.select().where(Payers.uid == uid).exists():
            Payers.create(
                uid=uid,
                name=payer,
                code=code_company,
                sum=sum,
                purpose=purpose,
                date=date_pay,
            )
            sum_text = ranks.get_sum_text(sum)
            messages.append(
                '\U0001F680 <b>ПОСТУПИЛА ОПЛАТА</b>\n\n'
                f'\U0001F4B5 <b>На сумму:</b> {sum_text} руб.\n\n'
                f'<b>Плательщик:</b> {payer}\n'
                f'<b>ИНН:</b> {code_company}\n'
                f'<b>Назначение платежа:</b> {purpose}\n'
            )
        else:
            break
    return messages
