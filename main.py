import telebot
import sqlite3

bot = telebot.TeleBot('6426305632:AAEzKdiJQVOloUm0cdhSNTpNLktmXZptgbw')

default_notification = 7


def set_nottime(message):
    answer = int(message.text)
    if type(answer) == int and answer > 0 and answer < 25:
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







bot.polling(none_stop=True)