from datetime import datetime as dt
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from peewee import fn

import ranks
from models import Payers

KPI_DAY = 12
KPI_WEEK = 60
DAYS_DICT = {
    '1': 'Понедельник',
    '2': 'Вторник',
    '3': 'Среда',
    '4': 'Четверг',
    '5': 'Пятница',
}
SALES_DEPARTMENT = 5


def get_time():
    """Все точки времени для статистики"""

    date_now = dt.now()
    date_now = dt(date_now.year, date_now.month, date_now.day, 0, 0)
    if date_now.strftime('%w') == '1':
        date_now -= timedelta(days=2)
    date_yesterday = date_now - timedelta(days=1)
    date_week = date_now - relativedelta(weeks=1)
    date_month = date_now - relativedelta(months=1)
    date_year = date_now - relativedelta(years=1)
    date_yes_year = date_yesterday - relativedelta(years=1)
    date_week_year = date_now - relativedelta(years=1, weeks=1)

    week_day = DAYS_DICT[date_yesterday.strftime('%w')]

    return {
        'date_now': date_now,
        'date_yesterday': date_yesterday,
        'date_week': date_week,
        'date_month': date_month,
        'date_year': date_year,
        'date_yes_year': date_yes_year,
        'date_week_year': date_week_year,
        'week_day': week_day,
    }


def get_payers(date_start, date_stop):
    """Список покупателей"""

    return Payers.select().where(
        (Payers.date >= date_start) & (Payers.date <= date_stop)
    )


def get_sum(payaers):
    """Суммирование сумм заказов"""

    if payaers:
        return payaers.select(fn.SUM(Payers.sum)).scalar()
    return 0


def get_payers_count(payaers, date_start, date_stop):
    """Количество новых и повторных покупателей"""

    old_payer = 0
    new_payer = 0
    for payer in payaers:
        start = date_start
        while start <= date_stop:
            count = (
                Payers.select()
                .where((Payers.code == payer.code) & (Payers.date <= start))
                .count()
            )
            if count > 1:
                old_payer += 1
                break
            elif count == 1:
                new_payer += 1
                break
            else:
                start += timedelta(days=1)
    return old_payer, new_payer


def get_message_payer(period, date, sum, new_payer, old_payer):
    """Сообщение для бота по покупателям"""

    return (
        f'\U0001F5D2 <b>{period}</b> <i>({date})</i>\n\n'
        f'<b>Сумма:</b> {sum} руб.\n'
        f'<b>Новые сделки:</b> {new_payer}\n'
        f'<b>Повторные сделки:</b> {old_payer}\n\n'
    )


def payer():
    """Статистика продаж"""

    time_period = get_time()
    week_day = time_period['week_day']
    date_yesterday = time_period['date_yesterday'].date()
    date_week = time_period['date_week'].date()
    date_month = time_period['date_month'].date()

    payaers_yesterday = get_payers(date_yesterday, date_yesterday)
    payaers_week = get_payers(date_week, date_yesterday)
    payaers_month = get_payers(date_month, date_yesterday)

    day_sum = get_sum(payaers_yesterday)
    week_sum = get_sum(payaers_week)
    month_sum = get_sum(payaers_month)

    old_payer_yesterday, new_payer_yesterday = get_payers_count(
        payaers_yesterday, date_yesterday, date_yesterday
    )
    old_payer_week, new_payer_week = get_payers_count(
        payaers_week, date_week, date_yesterday
    )
    old_payer_month, new_payer_month = get_payers_count(
        payaers_month, date_month, date_yesterday
    )

    day_sum = ranks.get_sum_text(f'{round(day_sum, 2):.2f}')
    week_sum = ranks.get_sum_text(f'{round(week_sum, 2):.2f}')
    month_sum = ranks.get_sum_text(f'{round(month_sum, 2):.2f}')

    start_message = '\U0001F4B0 <b>СТАТИСТИКА ПО ОПЛАТАМ</b>\n\n'
    yesterday_message = get_message_payer(
        week_day,
        date_yesterday.strftime("%d.%m.%Y"),
        day_sum,
        new_payer_yesterday,
        old_payer_yesterday,
    )
    week_message = get_message_payer(
        'Неделя',
        f'{date_week.strftime("%d.%m.%Y")} - '
        f'{date_yesterday.strftime("%d.%m.%Y")}',
        week_sum,
        new_payer_week,
        old_payer_week,
    )
    month_message = get_message_payer(
        'Месяц',
        f'{date_month.strftime("%d.%m.%Y")} - '
        f'{date_yesterday.strftime("%d.%m.%Y")}',
        month_sum,
        new_payer_month,
        old_payer_month,
    )

    return start_message + yesterday_message + week_message + month_message


def get_calls(bitrix, start_date, stop_date):
    """Все вызовы за интервал времени"""

    return bitrix.get_all(
        'voximplant.statistic.get',
        params={
            'filter': {
                '>CALL_START_DATE': f'{start_date.date()}T00:00:00+03:00',
                '<CALL_START_DATE': f'{stop_date.date()}T00:00:00+03:00',
            },
        },
    )


def get_phone_list(calls):
    """Cписок уникальных номеров, длительность разговоров, пропущенные"""

    duration = 0
    missed = 0
    phone_list = []
    managers_durations = {}
    for call in calls:
        duration += int(call['CALL_DURATION'])
        if call['CALL_FAILED_CODE'] == '304':
            missed += 1
        if call['PORTAL_USER_ID'] in managers_durations:
            managers_durations[call['PORTAL_USER_ID']] += int(
                call['CALL_DURATION']
            )
        else:
            managers_durations[call['PORTAL_USER_ID']] = int(
                call['CALL_DURATION']
            )
        phone_number = call['PHONE_NUMBER'].replace('+', '')
        if phone_number not in phone_list:
            phone_list.append(phone_number)
    return phone_list, managers_durations, missed


def get_new_calls(bitrix, phone_list, date_start, date_stop):
    """Список новых телефонов"""

    phone_list_plus = [f'+{phone}' for phone in phone_list]
    phone_list_plus += phone_list
    all_calls = bitrix.get_all(
        'voximplant.statistic.get',
        params={
            'filter': {'PHONE_NUMBER': phone_list_plus},
        },
    )

    new_calls = []
    for phone in phone_list:
        data = date_start
        while data < date_stop:
            count = 0
            for call in all_calls:
                if phone in call['PHONE_NUMBER']:
                    date_call = dt.fromisoformat(call['CALL_START_DATE'][:10])
                    if date_call <= data:
                        count += 1
                    if count > 1:
                        break
            if count == 1:
                new_calls.append(phone)
                break
            data += timedelta(days=1)

    return new_calls


def get_managers(bitrix, yesterday, week, year):
    """Получить имена всех менеджеров"""

    all_ids = list((set(list(yesterday) + list(week) + list(year))))

    all_managers = bitrix.get_all(
        'user.get',
        params={
            'filter': {'ID': all_ids},
        },
    )
    return {
        manager['ID']: [
            f"{manager['LAST_NAME']} {manager['NAME'][:1]}.",
            manager['UF_DEPARTMENT'],
        ]
        for manager in all_managers
    }


def duration_manager(managers_durations, managers_dict, kpi):
    """Подставить имена менеджеров"""

    message = ''
    duration_period = 0
    for key, value in managers_durations.items():
        name, departments = managers_dict[key]
        if SALES_DEPARTMENT in departments:
            duration = value // 60
            duration_period += value
            emoji = '\U00002705'
            if duration < kpi:
                emoji = '\U0000274C'
            message += (
                f'{emoji} <b>{name}</b>: ' f'{duration} мин {value % 60} с\n'
            )

    return message, duration_period


def get_message_call(
    period, date, calls, phone_list, new, duration, duration_names, missed, kpi
):
    """Формироване сообщения для бота"""

    emoji_new = '\U00002B50'
    emoji_missed = '\U0001F6AB'
    if len(new) == 0:
        emoji_new = '\U0001F6AB'
    if missed == 0:
        emoji_missed = '\U00002B50'

    return (
        f'\U0001F5D2 <b>{period}</b> <i>({date})</i>\n\n'
        f'<b>все диалоги:</b> {len(calls)}\n'
        f'<b>уникальные диалоги:</b> {len(phone_list)}\n'
        f'<b>новые ЛИДы:</b> {len(new)} {emoji_new}\n'
        f'<b>продолжительность:</b> {duration // 60} мин '
        f'{duration % 60} c\n'
        f'<b>пропущенные вызовы:</b> {missed} {emoji_missed}\n\n'
        f'<i>-----kpi: {kpi} мин</i>\n'
        f'{duration_names}\n'
    )


def call(bitrix):
    """Статистика звонков"""

    time_period = get_time()
    week_day = time_period['week_day']
    date_yesterday = time_period['date_yesterday']
    date_week = time_period['date_week']
    date_week_year = time_period['date_week_year']
    date_now = time_period['date_now']
    date_year = time_period['date_year']
    date_yes_year = time_period['date_yes_year']

    calls_yesterday = get_calls(bitrix, date_yesterday, date_now)
    calls_week = get_calls(bitrix, date_week, date_now)
    calls_year = get_calls(bitrix, date_week_year, date_year)

    (
        phone_list_yesterday,
        managers_durations_yesterday,
        missed_yesterday,
    ) = get_phone_list(calls_yesterday)
    (
        phone_list_week,
        managers_durations_week,
        missed_week,
    ) = get_phone_list(calls_week)
    (
        phone_list_year,
        managers_durations_year,
        missed_year,
    ) = get_phone_list(calls_year)

    new_yesterday = get_new_calls(
        bitrix, phone_list_yesterday, date_yesterday, date_now
    )
    new_week = get_new_calls(bitrix, phone_list_week, date_week, date_now)
    new_year = get_new_calls(
        bitrix, phone_list_year, date_week_year, date_year
    )

    managers_dict = get_managers(
        bitrix,
        managers_durations_yesterday,
        managers_durations_week,
        managers_durations_year,
    )

    duration_names_yesterday, duration_yesterday = duration_manager(
        managers_durations_yesterday, managers_dict, KPI_DAY
    )
    (
        duration_names_week,
        duration_week,
    ) = duration_manager(managers_durations_week, managers_dict, KPI_WEEK)
    duration_names_year, duration_year = duration_manager(
        managers_durations_year, managers_dict, KPI_WEEK
    )

    message_start = '\U0000260E <b>ОТЧЕТ ПО ЗВОНКАМ</b>\n\n'
    message_yesterday = get_message_call(
        week_day,
        date_yesterday.strftime('%d.%m.%Y'),
        calls_yesterday,
        phone_list_yesterday,
        new_yesterday,
        duration_yesterday,
        duration_names_yesterday,
        missed_yesterday,
        KPI_DAY,
    )
    message_week = get_message_call(
        'Неделя',
        f'{date_week.strftime("%d.%m.%Y")} - '
        f'{date_yesterday.strftime("%d.%m.%Y")}',
        calls_week,
        phone_list_week,
        new_week,
        duration_week,
        duration_names_week,
        missed_week,
        KPI_WEEK,
    )
    message_year = get_message_call(
        'Прошлый год',
        f'{date_week_year.strftime("%d.%m.%Y")} - '
        f'{date_yes_year.strftime("%d.%m.%Y")}',
        calls_year,
        phone_list_year,
        new_year,
        duration_year,
        duration_names_year,
        missed_year,
        KPI_WEEK,
    )

    return message_start + message_yesterday + message_week + message_year
