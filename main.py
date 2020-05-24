import telebot
from telebot import types
import requests
import datetime
import re
import config_bot

"""This project was changing a lot during development
   There are some redundant stuff but basically it's ok
   This is reincarnation cause 1st version was disgusting(my first developing experience)
"""



bot = telebot.TeleBot(config_bot.TOKEN)

crm_domen = config_bot.crm_domen
crm_login = config_bot.crm_login
crm_rest_api = config_bot.crm_rest_api


cache = {}  # Cache to divide info from different user's
cur_processes_is_asked = False  # Variable to avoid creating alternative paths, and using same functions

procedure_list = ['Yumi brows', 'Yumi lashes']

BROWS = False
LASHES = False


rating_list = [1, 2, 3, 4, 5]

# Creating cache
@bot.message_handler(commands=['start'])
def start(message):
    global cache
    cache[message.chat.id] = {}
    welcome(message)


def welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    but1 = types.KeyboardButton('Создать запись')
    but2 = types.KeyboardButton('Мои записи')
    markup.add(but1, but2)

    bot.send_message(message.chat.id, 'Доброго времени суток!\n'
                                      'Выберите желаемую операцию', reply_markup=markup)

    bot.register_next_step_handler(message, start_decider)


def start_decider(message):
    """Handler's and deciders(same) are functions which forwards flow to other needed function"""
    global cur_processes_is_asked
    if message.text == 'Создать запись':
        procedure_selection(message)
    elif message.text == 'Мои записи':
        cur_processes_is_asked = True
        get_number(message)
    else:  # If input is random reasking for input
        welcome(message)


def procedure_selection(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for each in procedure_list:
        but = types.KeyboardButton('{}'.format(each))
        markup.add(but)

    but3 = types.KeyboardButton('Отмена')
    markup.add(but3)

    bot.send_message(message.chat.id, 'Выберите процедуру', reply_markup=markup)
    bot.register_next_step_handler(message, procedure_handler)


def procedure_handler(message):
    global BROWS, LASHES
    if message.text == 'Yumi brows':
        BROWS = True
        cache[message.chat.id]['procedure'] = message.text
        dateselection(message)
    elif message.text == 'Yumi lashes':
        LASHES = True
        cache[message.chat.id]['procedure'] = message.text
        dateselection(message)
    elif message.text == 'Отмена':
        BROWS, LASHES = False, False
        welcome(message)
    else:
        procedure_selection(message)


def dateselection(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i in range(7):
        date = datetime.date.today() + datetime.timedelta(i)
        but = types.InlineKeyboardButton('{} - {}'.format(daytransform(date), date), callback_data='{}'.format(date))
        markup.add(but)

    cancel = types.InlineKeyboardButton('Отмена', callback_data='Cancel')
    markup.add(cancel)
    bot.send_message(message.chat.id, 'Выберите день записи', reply_markup=markup)


@bot.callback_query_handler(func=lambda call:True if re.match('^\d{4}[-]\d{2}[-]\d{2}',call.data) or call.data == 'Cancel' else False)
def date_record(call):
    global BROWS, LASHES
    if call.data == 'Cancel':
        welcome(call.message)
        BROWS = False
        LASHES = False
    else:
        cache[call.message.chat.id]['date'] = call.data
        dayhalfselection(call.message)


def dayhalfselection(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    but1 = types.KeyboardButton('8:00 - 13:00')
    but2 = types.KeyboardButton('14:00 - 18:00')
    but3 = types.KeyboardButton('Отмена')
    markup.add(but1, but2, but3)

    bot.send_message(message.chat.id, 'Ваша дата: {}'.format(cache[message.chat.id]['date']))
    bot.send_message(message.chat.id, 'Выберите временной промежуток записи', reply_markup=markup)
    bot.register_next_step_handler(message, time_decider)
    bot.delete_message(message.chat.id, message.message_id)


def time_decider(message):
    if message.text == '8:00 - 13:00':
        timeselection1(message)
    elif message.text == '14:00 - 18:00':
        timeselection2(message)
    elif message.text == 'Отмена':
        welcome(message)
    else:  # If input is random reasking for input
        dayhalfselection(message)


def timeselection1(message):
    # Keyboard
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    but1 = types.KeyboardButton('8:00')
    but2 = types.KeyboardButton('9:00')
    but3 = types.KeyboardButton('10:00')
    but4 = types.KeyboardButton('11:00')
    but5 = types.KeyboardButton('12:00')
    but6 = types.KeyboardButton('13:00')
    but7 = types.KeyboardButton('Отмена')

    markup.add(but1, but2, but3, but4, but5, but6, but7)

    bot.send_message(message.chat.id, 'Выберите время записи', reply_markup=markup)
    bot.register_next_step_handler(message, time_record)


def timeselection2(message):
    # Keyboard
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    but1 = types.KeyboardButton('14:00')
    but2 = types.KeyboardButton('15:00')
    but3 = types.KeyboardButton('16:00')
    but4 = types.KeyboardButton('17:00')
    but5 = types.KeyboardButton('18:00')
    but6 = types.KeyboardButton('Отмена')
    markup.add(but1, but2, but3, but4, but5, but6, )

    bot.send_message(message.chat.id, 'Выберите время записи', reply_markup=markup)
    bot.register_next_step_handler(message, time_record)


def time_record(message):
    cache[message.chat.id]['time'] = message.text
    if message.text == 'Отмена':
        welcome(message)
    elif re.match('^\d{1,2}[:][0][0]$', message.text):  # Checking if message is time-like
        get_contact(message)
    else:  # If input is random reasking for input
        dayhalfselection(message)


def get_contact(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    but = types.KeyboardButton(text='Отправить контакт', request_contact=True)
    markup.add(but)

    bot.send_message(message.chat.id, 'Ваш контакт', reply_markup=markup)
    bot.register_next_step_handler(message, contact_record)


def contact_record(message):
    if type(message.contact) == type(None):  # Protection vs non-contact input
        get_contact(message)
        bot.send_message(message.chat.id, 'P.S. Имя и номер телефона можна будет изменить')
    else:
        cache[message.chat.id]['name'] = message.contact.first_name
        cache[message.chat.id]['number'] = message.contact.phone_number
        summary(message)


def summary(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    but1 = types.KeyboardButton('Подтвердить запись')
    but2 = types.KeyboardButton('Изменить время')
    but4 = types.KeyboardButton('Изменить номер телефона')
    but5 = types.KeyboardButton('Изменить имя')
    but6 = types.KeyboardButton('Отмена')
    markup.add(but1, but2, but4, but5, but6)
    bot.send_message(message.chat.id,
                     '{0}, Вы сделали заявку на {1}, в {2}\nВаша процедура: {4}\n'
                     'Ваш номер телефона: {3} '
                     .format(
                         cache[message.chat.id]['name'], cache[message.chat.id]['date'],
                         cache[message.chat.id]['time'],
                         cache[message.chat.id]['number'], cache[message.chat.id]['procedure']),
                     reply_markup=markup)
    bot.register_next_step_handler(message, summary_decider)


def summary_decider(message):
    global BROWS, LASHES
    if message.text == 'Подтвердить запись':
        confirm(message)
    elif message.text == 'Изменить время':
        dateselection(message)
    elif message.text == 'Изменить номер телефона':
        del (cache[message.chat.id]['number'])
        get_number(message)
    elif message.text == 'Изменить имя':
        get_name(message)
    elif message.text == 'Отмена':
        BROWS = False
        LASHES = False
        welcome(message)
    else:
        summary(message)


def get_number(message):
    if 'number' in cache[message.chat.id]:  # Don't ask if it already given
        cur_processes(message)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        but1 = types.KeyboardButton('Отправить контакт', request_contact=True)
        markup.add(but1)

        bot.send_message(message.chat.id, 'Ваш номер телефона?\n(начиная с 380)', reply_markup=markup)
        bot.register_next_step_handler(message, number_record)


def number_record(message):
    if type(message.contact) == type(None):  # Protection vs non-contact input
        if re.match('^380\d{9}$', message.text):  # Cheking if input is a phone number
            cache[message.chat.id]['number'] = message.text
            if cur_processes_is_asked:
                cur_processes(message)
            else:
                summary(message)
        else:
            bot.send_message(message.chat.id, 'Номер в неправильном формате!')
            get_number(message)
    else:
        cache[message.chat.id]['number'] = message.contact.phone_number
        if cache[message.chat.id]['number'].startswith('+'):
            cache[message.chat.id]['number'] = cache[message.chat.id]['number'][1:]
        if cur_processes_is_asked:
            cur_processes(message)
        else:
            summary(message)


# name changing
def get_name(message):
    bot.send_message(message.chat.id, 'Введите желаемое имя')
    bot.register_next_step_handler(message, name_record)


def name_record(message):
    cache[message.chat.id]['name'] = message.text
    summary(message)


# Parsing current processe and displaying info
def cur_processes(message):
    global cur_processes_is_asked
    cur_processes_is_asked = False

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    but1 = types.KeyboardButton('Создать запись')
    but2 = types.KeyboardButton('Мои записи')
    markup.add(but1, but2)

    if cache[message.chat.id]['number'].startswith('+'):
        cache[message.chat.id]['number'] = cache[message.chat.id]['number'][1:]

    try:
        URL_GET = '{0}/api/orders/get/?login={1}' \
                  '&password={2}' \
                  '&workflowid=32' \
                  '&clientphone={3}'.format(crm_domen,
                                            crm_login,
                                            crm_rest_api,
                                            cache[message.chat.id]['number'])

        r_update = requests.get(url=URL_GET)

        processes = r_update.json()
        process = processes['orders']
        for i in range(len(process)):
            result = process[i]

            orderid = result['orderid']

            dateto = result['dateto']

            clientname = result['clientname']

            managerid = result['managerid']

            statusname = result['statusname']

            if managerid == '7':
                manager_name = 'Звягина Катя'
            elif managerid == '4504':
                manager_name = 'Александрова Яна'
            elif managerid == '4505':
                manager_name = 'Алекс'
            elif managerid == '3247':
                manager_name = 'Сигурий Наташа'
            else:
                manager_name = ''
            bot.send_message(message.chat.id,
                             '\n{2}, ваша заявка с id {0},\nДата процедуры {1}\nСтатус заявки: {3}'
                             .format(
                                 orderid,
                                 dateto,
                                 clientname,
                                 statusname),
                             reply_markup=markup)

            if statusname == 'Визит завершен':
                feedback(message, orderid, dateto)
        if len(processes) == 0:
            bot.send_message(message.chat.id, 'К сожалению, у вас нету активных записей')
    finally:
        bot.register_next_step_handler(message, start_decider)



def confirm(message):

    # PROCEDURE ID
    procedure_id = 0
    if BROWS:
        procedure_id = 8
    elif LASHES:
        procedure_id = 9

    # Deleting + if it's in number(need this to send request)
    if cache[message.chat.id]['number'].startswith('+'):
        cache[message.chat.id]['number'] = cache[message.chat.id]['number'][1:]

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    but1 = types.KeyboardButton('Создать запись')
    but2 = types.KeyboardButton('Мои записи')
    markup.add(but1, but2)
    URL_ADD = '{}api/orders/add/?login={}' \
              '&password={}' \
              '&workflowid=32' \
              '&clientnamefirst={}' \
              '&clientphone={}' \
              '&managerphone=12020' \
              '&dateto={}%20{}' \
              '&productArray[0][id]={}' \
              '&productArray[0][count]=1'.format(crm_domen,
                                                 crm_login,
                                                 crm_rest_api,
                                                 cache[message.chat.id]['name'],
                                                 cache[message.chat.id]['number'],
                                                 cache[message.chat.id]['date'],
                                                 cache[message.chat.id]['time'],
                                                 procedure_id)


    r_update = requests.get(url=URL_ADD)
    data = r_update.json()

    new_process_id = data['orderId']

    bot.send_message(309410262, "Створена нова заявка в OneBox\n"
                                "Процедура: {0}\n"
                                "Номер клієнта: {1}\n"
                                "Посилання: {3}/admin/customorder/zakaz-klienta/{2}/edit/"
                     .format(cache[message.chat.id]['procedure'],
                             cache[message.chat.id]['number'],
                             new_process_id,
                             crm_domen))

    new_data = datetime.datetime.strptime(cache[message.chat.id]['date'], "%Y-%m-%d").strftime('%Y%m%d')
    new_time = datetime.datetime.strptime(cache[message.chat.id]['time'], "%H:%M").strftime('%H')

    if str(new_time) == '08':
        new_time = '06'
    elif str(new_time) == '09':
        new_time = '07'
    elif str(new_time) == '10':
        new_time = '08'
    elif str(new_time) == '11':
        new_time = '09'
    else:
        new_time = int(new_time) - 2
    # Link for adding record into clients Google Calendar (with link)
    bot.send_message(message.chat.id, 'Ваша запись успешно создана!\n'
                                      '[Добавить запись в Google Calendar]'
                                      '(https://calendar.google.com/calendar/r/'
                                      'eventedit?text=Запись+на+процедуру+YUMI+LASHES'
                                      '&dates={0}T{1}0000Z/{0}T{1}3002Z'
                                      '&details=За+деталями,+відвідайте+наш+сайт:+'
                                      '{2}'
                                      '&location=YUMI+Lashes+Ukraine,'
                                      '+вул.+Бойчука+,+11,+офіс+9,+Kyiv,'
                                      '+Ukraine,+01103)'.format(new_data,
                                                                new_time,
                                                                crm_domen,
                                                                ), reply_markup=markup, parse_mode='Markdown')
    bot.register_next_step_handler(message, start_decider)


def daytransform(date):
    if date.weekday() == 0:
        return 'Понедельник'
    elif date.weekday() == 1:
        return 'Вторник'
    elif date.weekday() == 2:
        return 'Среда'
    elif date.weekday() == 3:
        return 'Четверг'
    elif date.weekday() == 4:
        return 'Пятниця'
    elif date.weekday() == 5:
        return 'Субота'
    elif date.weekday() == 6:
        return 'Воскресенье'


def feedback(message, order_id, dateto):
    markup = types.InlineKeyboardMarkup(row_width=1)
    but1 = types.InlineKeyboardButton('⭐', callback_data='1{}'.format(order_id))
    but2 = types.InlineKeyboardButton('⭐⭐', callback_data='2{}'.format(order_id))
    but3 = types.InlineKeyboardButton('⭐⭐⭐', callback_data='3{}'.format(order_id))
    but4 = types.InlineKeyboardButton('⭐⭐⭐⭐', callback_data='4{}'.format(order_id))
    but5 = types.InlineKeyboardButton('⭐⭐⭐⭐⭐', callback_data='5{}'.format(order_id))
    markup.add(but1, but2, but3, but4, but5)

    bot.send_message(message.chat.id, 'Оцените, пожалуйста, ваш визит {}'.format(dateto[:11]), reply_markup=markup)

@bot.callback_query_handler(func= lambda call: True  if re.match('^\d{5}$', call.data) else False)
def feedback_record(call):


    URL_UPDATE = '{}/api/orders/update/?login={}' \
                 '&password={}' \
                 '&orderid={}' \
                 '&customorder_feedback73={}'.format(crm_domen,
                                                     crm_login,
                                                     crm_rest_api,
                                                     call.data[1:],
                                                     call.data[0])
    r_update = requests.get(url=URL_UPDATE)

    bot.edit_message_text('Спасибо за отзыв!', message_id=call.message.message_id, chat_id=call.message.chat.id)

bot.polling(none_stop=True)
