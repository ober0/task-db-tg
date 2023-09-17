import telebot
import sqlite3
from telebot import types

bot = telebot.TeleBot('6426305632:AAEzKdiJQVOloUm0cdhSNTpNLktmXZptgbw')

default_notification = 7

def user_set_new_discription(message, id, rowid):
    new_text = str(message.text)
    # try:
    db = sqlite3.connect('users_data.sql')
    cursor = db.cursor()
    cursor.execute(f'UPDATE chat{id} SET task_description = ? WHERE rowid = ?', (new_text, rowid))
    db.commit()
    db.close()
    bot.send_message(id, 'Успешно!')
    # except Exception as ex:
    #     bot.send_message(id, f'Произошла ошибка СУБД: {ex}, повторите попытку!')
    #     bot.register_next_step_handler(message, user_set_new_discription, id, rowid)


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
/list - список задач
/change_notification - сменить время напоминания
    
    ''')



@bot.message_handler(commands=['change_notification'])
def change_notification(message):
    bot.send_message(message.chat.id,
                     'Введите во сколько часов вам удобнее получать уведомления о не выполненных задачах:')
    bot.register_next_step_handler(message, set_nottime)


@bot.message_handler(commands=['test'])
def test(message):
    db = sqlite3.connect('users_data.sql')
    cursor = db.cursor()
    cursor.execute(f'SELECT * FROM chat{message.chat.id}')
    test = cursor.fetchall()
    print(test)



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
bot.polling(none_stop=True)