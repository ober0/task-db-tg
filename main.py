import telebot
import sqlite3
from telebot import types
from datetime import datetime
import threading
import time

bot = telebot.TeleBot('6426305632:AAEzKdiJQVOloUm0cdhSNTpNLktmXZptgbw')

default_notification = 7


def send_notification(time):
    db = sqlite3.connect('users_data.sql')
    cursor = db.cursor()
    cursor.execute(f'SELECT id FROM users_notification WHERE notif = {time}')
    users = cursor.fetchall()
    db.close()
    user_lst = []
    for i in users:
        i = i[0]
        if not i in user_lst:
            user_lst.append(i)
    db = sqlite3.connect('users_data.sql')
    cursor = db.cursor()
    for i in user_lst:
        cursor.execute(f'SELECT task_name FROM chat{i}')
        tasks = cursor.fetchall()
        bot.send_message(i, 'Здравствуйте! Ваши не выполненные задачи:')
        for j in tasks:
            bot.send_message(i, j[0])
        bot.send_message(i, 'Подробнее:\n/check')


# Главная функция для проверки времени и отправки уведомления
def check_time_and_send_notification():
    while True:
        current_time = datetime.now().time()
        send_notification(current_time.hour)
        time.sleep(3600)


def user_set_new_discription(message, id, rowid):
    new_text = str(message.text)
    try:
        db = sqlite3.connect('users_data.sql')
        cursor = db.cursor()
        cursor.execute(f'UPDATE chat{id} SET task_description = ? WHERE rowid = ?', (new_text, rowid))
        db.commit()
        db.close()
        bot.send_message(id, 'Успешно!')
    except Exception as ex:
        bot.send_message(id, f'Произошла ошибка СУБД: {ex}, повторите попытку!')
        bot.register_next_step_handler(message, user_set_new_discription, id, rowid)


def user_set_new_name(message, id, rowid):
    new_text = str(message.text)
    try:
        db = sqlite3.connect('users_data.sql')
        cursor = db.cursor()
        cursor.execute(f'UPDATE chat{id} SET task_name = ? WHERE rowid = ?', (new_text, rowid))
        db.commit()
        db.close()
        bot.send_message(id, 'Успешно!')
    except Exception as ex:
        bot.send_message(id, f'Произошла ошибка СУБД: {ex}, повторите попытку!')
        bot.register_next_step_handler(message, user_set_new_name, id, rowid)


def set_nottime(message):
    answer = int(message.text)
    if type(answer) == int and answer >= 0 and answer < 25:
        try:
            db = sqlite3.connect('users_data.sql')
            cursor = db.cursor()
            cursor.execute(f'UPDATE users_notification SET notif = {answer} WHERE id = {message.chat.id}')
            db.commit()
            db.close()
            bot.send_message(message.chat.id, 'Успешно!')
        except Exception as ex:
            bot.send_message(message.chat.id, f'Ошибка СУБД\n{ex}')
    else:
        bot.send_message(message.chat.id, 'Время введено не верно\nВерный формат: h\nПовторите ввод')
        bot.register_next_step_handler(message, set_nottime)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Привет! Я бот-помощник, для управления твоими задачами!\nПомощь по командам - /help')
    db = sqlite3.connect('users_data.sql')
    cursor = db.cursor()

    cursor.execute(f'''CREATE TABLE IF NOT EXISTS users_notification (id int, notif int)''')
    db.commit()
    cursor.execute(f'INSERT INTO users_notification (id, notif) VALUES ({int(message.chat.id)}, {int(default_notification)})')

    db.commit()
    cursor.execute(f'''CREATE TABLE chat{message.chat.id} (
        id int,
        task_name text,
        task_description text,
        status text
    )
    ''')
    db.commit()
    bot.send_message(message.chat.id, 'Введите во сколько часов вам удобнее получать уведомления о не выполненных задачах')
    bot.register_next_step_handler(message, set_nottime)


    db.close()

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, '''/add - добавить задачу
/edit - изменить задачу
/close - закрыть задачу
/check - список задач
/change_notification - сменить время напоминания
/report - оставить отчет об ошибке
    
    ''')



@bot.message_handler(commands=['change_notification'])
def change_notification(message):
    bot.send_message(message.chat.id,
                     'Введите во сколько часов вам удобнее получать уведомления о не выполненных задачах:')
    bot.register_next_step_handler(message, set_nottime)





@bot.message_handler(commands=['add'])
def add_step1(message):
    bot.send_message(message.chat.id, 'Введите название задачи')
    bot.register_next_step_handler(message, add_step2)

def add_step2(message):
    task_name = message.text
    bot.send_message(message.chat.id, 'Введите описание задачи')
    bot.register_next_step_handler(message, add_step3, task_name)

def add_step3(message, task_name):
    task_ds = message.text
    db = sqlite3.connect('users_data.sql')
    cursor = db.cursor()
    try:
        cursor.execute(f'''INSERT INTO chat{message.chat.id} (id, task_name, task_description, status) VALUES (
            {message.chat.id},
            "{task_name}",
            "{task_ds}",
            'Open'
        )''')
        db.commit()
        bot.send_message(message.chat.id, 'Задача успешно добавлена!')
    except Exception as ex:
        bot.send_message(message.chat.id, f'Ошибка СУБД при добавлении задачи: {ex}')
    finally:
        db.close()


@bot.message_handler(commands=['edit'])
def edit(message):
    db = sqlite3.connect('users_data.sql')
    cursor = db.cursor()
    cursor.execute(f'SELECT task_name, task_description FROM chat{message.chat.id}')
    all_data = cursor.fetchall()
    num = 0
    bot.send_message(message.chat.id, '<b>Выберите номер задачи:</b>',parse_mode='html')
    for i in all_data:
        num += 1
        bot.send_message(message.chat.id, f'{num}) {i[0]}')
    markup = types.InlineKeyboardMarkup(row_width=5)
    for i in range(num):
        btn = types.InlineKeyboardButton(i+1, callback_data=f'user_check_btn_key={i+1}')
        markup.row(btn)
        print(f'user_check_btn_key={i+1}')
    bot.send_message(message.chat.id,'Нажмите на соответствующую кнопку:', reply_markup=markup)
    db.close()


@bot.message_handler(commands=['report'])
def report(message):
    bot.send_message(message.chat.id, 'Опишите вашу проблему')
    db = sqlite3.connect('reports.sql')
    cursor = db.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS reports (
    user_id int,
    user_message text,
    status text
    )
    ''')
    db.commit()
    db.close()
    bot.register_next_step_handler(message, report_step2)

def report_step2(message):
    user_message = message.text
    try:
        db = sqlite3.connect('reports.sql')
        cursor = db.cursor()
        cursor.execute('INSERT INTO reports (user_id, user_message, status) VALUES (?, ?, "open")', (message.chat.id, user_message))
        db.commit()
        db.close()
        bot.send_message(message.chat.id, 'Успешно!')
        bot.send_message(947827934, '<b>Получен новый репорт!</b>\n/check_reports\n/work_reports', parse_mode='html')
    except Exception as ex:
        bot.send_message(message.chat.id, f'Ошибка СУБД: {ex}')

@bot.message_handler(commands=['check_reports'])
def check_reports_verification(message):
    if message.chat.id != 947827934:
        bot.send_message(message.chat.id, 'Введите логин:')
        bot.register_next_step_handler(message, check_reports_verification_step2)
    else:
        check_reports(message)
def check_reports_verification_step2(message):
    login = message.text
    bot.delete_message(message.chat.id, message.message_id)
    bot.send_message(message.chat.id, 'Введите пароль:')
    bot.register_next_step_handler(message, check_reports_verification_step3, login)

def check_reports_verification_step3(message, login):
    password = message.text
    bot.delete_message(message.chat.id, message.message_id)
    if login == 'admin' and password == 'admin':
        check_reports(message)
    else:
        bot.send_message(message.chat.id, 'Профиль не найден')

def check_reports(message):
    db = sqlite3.connect('reports.sql')
    cursor = db.cursor()
    cursor.execute('SELECT *, rowid FROM reports WHERE status = "open" ORDER BY rowid ')
    report = cursor.fetchone()
    markup = types.InlineKeyboardMarkup()
    try:
        btn1 = types.InlineKeyboardButton('В работу', callback_data=f'report_in_work:{report[3]}')
        btn2 = types.InlineKeyboardButton('Закрыть', callback_data=f'report_close:{report[3]}')
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, f'Статус {report[2]}\nРепорт: {report[1]}', reply_markup=markup)
    except:
        bot.send_message(message.chat.id, 'Репортов нет')

@bot.message_handler(commands=['work_reports'])
def work_reports_verifycation_step1(message):
    if message.chat.id != 947827934:
        bot.send_message(message.chat.id, 'Введите логин:')
        bot.register_next_step_handler(message, check_reports_verification_step2)
    else:
        work_reports(message)


def work_reports_verification_step2(message):
    login = message.text
    bot.delete_message(message.chat.id, message.message_id)
    bot.send_message(message.chat.id, 'Введите пароль:')
    bot.register_next_step_handler(message, check_reports_verification_step3, login)


def work_reports_verification_step3(message, login):
    password = message.text
    bot.delete_message(message.chat.id, message.message_id)
    if login == 'admin' and password == 'admin':
        work_reports(message)
    else:
        bot.send_message(message.chat.id, 'Профиль не найден')

def work_reports(message):
    db = sqlite3.connect('reports.sql')
    cursor = db.cursor()
    cursor.execute('SELECT *, rowid FROM reports WHERE status = "work" ORDER BY rowid')
    report = cursor.fetchone()
    markup = types.InlineKeyboardMarkup()
    try:
        btn1 = types.InlineKeyboardButton('Закрыть', callback_data=f'report_close:{report[3]}')
        markup.add(btn1)
        bot.send_message(message.chat.id, f'Статус {report[2]}\nРепорт: {report[1]}', reply_markup=markup)
    except:
        bot.send_message(message.chat.id, 'Репортов нет')

@bot.message_handler(commands=['close'])
def close(message):
    db = sqlite3.connect('users_data.sql')
    cursor = db.cursor()
    cursor.execute(f'SELECT task_name, task_description FROM chat{message.chat.id}')
    all_data = cursor.fetchall()
    num = 0
    bot.send_message(message.chat.id, '<b>Выберите номер задачи для закрытия:</b>', parse_mode='html')
    for i in all_data:
        num += 1
        bot.send_message(message.chat.id, f'{num}) {i[0]}')
    markup = types.InlineKeyboardMarkup(row_width=5)
    for i in range(num):
        btn = types.InlineKeyboardButton(i + 1, callback_data=f'user_close_task={i + 1}')
        markup.add(btn)
        print(f'user_close_task={i + 1}')
    bot.send_message(message.chat.id, 'Нажмите на соответствующую кнопку:', reply_markup=markup)
    db.close()


@bot.message_handler(commands=['check'])
def check(message):
    db = sqlite3.connect('users_data.sql')
    cursor = db.cursor()
    cursor.execute(f'SELECT task_name, task_description FROM chat{message.chat.id}')
    all_data = cursor.fetchall()
    num = 0
    bot.send_message(message.chat.id, '<b>Выберите номер задачи для просмотра описания:</b>',parse_mode='html')
    for i in all_data:
        num += 1
        bot.send_message(message.chat.id, f'{num}) {i[0]}')
    markup = types.InlineKeyboardMarkup(row_width=5)
    for i in range(num):
        btn = types.InlineKeyboardButton(i+1, callback_data=f'user_check_discription={i+1}')
        markup.add(btn)
        print(f'user_check_discription={i+1}')
    bot.send_message(message.chat.id,'Нажмите на соответствующую кнопку:', reply_markup=markup)
    db.close()

@bot.callback_query_handler(func=lambda callback:True)
def callback(callback):
    print(f'call = {callback.data}')

    if callback.data.split(':')[0] == 'report_in_work':
        rowid = callback.data.split(':')[1]
        db = sqlite3.connect('reports.sql')
        cursor = db.cursor()
        cursor.execute(f'UPDATE reports SET status = "work" WHERE rowid = {rowid}')
        db.commit()
        db.close()
        bot.send_message(callback.message.chat.id, 'Успешно!')

    if callback.data.split(':')[0] == 'report_close':
        rowid = callback.data.split(':')[1]
        db = sqlite3.connect('reports.sql')
        cursor = db.cursor()
        cursor.execute(f'DELETE FROM reports WHERE rowid = {rowid}')
        db.commit()
        db.close()
        bot.send_message(callback.message.chat.id, 'Успешно!')


    if callback.data.split('=')[0] == 'user_check_btn_key':
        btn_num = int(callback.data.split('=')[1])
        db = sqlite3.connect('users_data.sql')
        cursor = db.cursor()
        cursor.execute(f'SELECT task_name, task_description FROM chat{callback.message.chat.id} WHERE rowid = {btn_num}')
        data = cursor.fetchone()
        bot.send_message(callback.message.chat.id, f'<b>{data[0]}</b>\n{data[1]}', parse_mode='html')
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Название', callback_data=f'user_edit_name:{callback.message.chat.id}:{btn_num}')
        btn2 = types.InlineKeyboardButton('Описание', callback_data=f'user_edit_discription:{callback.message.chat.id}:{btn_num}')
        markup.row(btn1, btn2)
        bot.send_message(callback.message.chat.id, 'Что меняем?', reply_markup=markup)

        db.close()

    if callback.data.split('=')[0] == 'user_check_discription':
        btn_num = int(callback.data.split('=')[1])
        db = sqlite3.connect('users_data.sql')
        cursor = db.cursor()
        cursor.execute(f'SELECT task_name, task_description FROM chat{callback.message.chat.id} WHERE rowid = {btn_num}')
        data = cursor.fetchone()
        bot.send_message(callback.message.chat.id, f'<b>{data[0]}</b>\n{data[1]}', parse_mode='html')
        db.close()

    if callback.data.split('=')[0] == 'user_close_task':
        try:
            btn_num = int(callback.data.split('=')[1])
            db = sqlite3.connect('users_data.sql')
            cursor = db.cursor()
            cursor.execute(f'DELETE FROM chat{callback.message.chat.id} WHERE rowid = {btn_num}')
            db.commit()
            db.close()
        except Exception as ex:
            bot.send_message(callback.message.chat.id, f'Ошибка СУБД: {ex}')

    if callback.data.split(':')[0] == 'user_edit_name':
        id = callback.data.split(':')[1]
        rowid = callback.data.split(':')[2]
        bot.send_message(callback.message.chat.id, 'Введите новое название:')
        bot.register_next_step_handler(callback.message, user_set_new_name, id, rowid)

    if callback.data.split(':')[0] == 'user_edit_discription':
        id = callback.data.split(':')[1]
        rowid = callback.data.split(':')[2]
        bot.send_message(callback.message.chat.id, 'Введите новое описание:')
        bot.register_next_step_handler(callback.message, user_set_new_discription, id, rowid)



if __name__ == "__main__":
    notification_thread = threading.Thread(target=check_time_and_send_notification)
    notification_thread.start()
bot.polling(none_stop=True)