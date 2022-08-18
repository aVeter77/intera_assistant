from models import Users

ROLE = {'0': 'Пользователь', '1': 'Администратор'}


def back_menu():
    print('\n[ENTER] венуться назад', end='')
    input()


def start_menu():
    """Основное меню"""

    print(
        '\nОСНОВНОЕ МЕНЮ\n'
        '1. Список пользователей\n'
        '2. Добавить пользователя\n'
        '3. Удалить пользователя\n'
        '4. Поменять права пользователя\n'
        '5. Выйти\n'
    )
    print('Пункт: ', end='')
    return input()


def user_list():
    """Вывод списка пользователей"""

    users = Users.select()
    print('\nСписок пользователей:\n' '[ID] - [NAME] - [ID_GRAM] - [ROLE]\n')
    for user in users:
        role = ROLE[user.role]
        print(f'{user.id} - {user.name} - {user.id_gram} - {role}')

    back_menu()


def add_new_user():
    """Добавление пользователя"""

    print('\nДОБАВИТЬ ПОЛЬЗОВАТЕЛЯ')
    print('Имя нового пользователя: ', end='')
    user_name = input()
    print('Telegram ID: ', end='')
    id_gram = input()
    if not user_name or not id_gram:
        print('\n[ERROR] Все поля обязательны к заполнению')
        back_menu()
        return True
    if Users.select().where(Users.id_gram == id_gram).exists():
        print('\n[ERROR] Пользователь с таким Telegram ID уже существует')
    else:
        Users.create(name=user_name, id_gram=id_gram)
        print('\n[OK] Пользователь добавлен')
    back_menu()


def del_user():
    """Удалить пользователя"""

    print('\nID пользователя: ', end='')
    user_id = input()
    if Users.select().where(Users.id == user_id).exists():
        Users.delete().where(Users.id == user_id).execute()
        print('\n[OK] Пользователь удален')
    else:
        print('[ERROR] Пользователя с таким ID не существует')
    back_menu()


def edit_role():
    """Изменить права пользователя"""

    print('\nID пользователя: ', end='')
    user_id = input()
    if Users.select().where(Users.id == user_id).exists():
        user = Users.get(Users.id == user_id)
        print('\nВыбран пользователь:', user.name)
        print(
            '\n0 - Пользователи\n1 - Администраторы\n\nНомер прав: ',
            end='',
        )
        user_role = input()
        if user_role in ROLE:
            user.update(role=user_role).where(Users.id == user_id).execute()
            print('\n[OK] Права пользователя изменены')
        else:
            print('\n[ERROR] Такого номера прав нет')
    else:
        print('[ERROR] Пользователя с таким ID не существует')
    back_menu()


def main():
    """Главная функция"""

    while True:
        user_option = start_menu()
        if user_option == '1':
            user_list()
        elif user_option == '2':
            add_new_user()
        elif user_option == '3':
            del_user()
        elif user_option == '4':
            edit_role()
        elif user_option == '5':
            print('\nВыход')
            break


if __name__ == '__main__':
    main()
