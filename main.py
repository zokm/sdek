import csv
import datetime
import os
import re
import traceback

import telebot
from telebot import types
import json
import config
from api import *

bot = telebot.TeleBot(config.TOKEN)

data_dict = {}
order_dict = {}
data_dimensions_dict = {}

file = 'db.csv'
order_file = 'order_db.csv'

weight_array = []
dimensions_array = []


class DataDimensions:
    def __init__(self):
        self.length = None
        self.width = None
        self.height = None
        self.dimensions_name = None


class DataHuman:
    def __init__(self):
        self.fio = None
        self.number_phone = None
        self.city = None
        self.item_sdek = None
        self.chat_id = None
        self.mode = None


class DataOrder:
    def __init__(self):
        self.chat_id = None
        self.fio = None
        self.sender_city = None
        self.number_phone = None
        self.from_city = None
        self.to_city = None
        self.weight = None
        self.weight_full = None
        self.dimensions = None
        self.type_package = None
        self.street = 'Улица СДЕКА'
        self.house = 'Номер дома СДЕКА'
        self.company = 'Компания СДЕКА'
        self.fio_destination = None
        self.number_phone_destination = None
        self.street_destination = None
        self.house_destination = None
        self.door_destination = None
        self.insurance = None
        self.tariff_code = None
        self.count_package = None
        self.price_package = None

        self.number_departure = 1
        self.add_fee = 0
        self.true_seller = 1

        self.from_or_to = None
        self.code_city_sender = None
        self.code_city_receiver = None
        self.address_storage_sender = None
        self.address_storage_receiver = None
        self.code_office_sender = None
        self.code_office_receiver = None

        self.change_data = False

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)


def check_user(message):
    chat_id = message.chat.id
    size_file = os.stat(file).st_size
    exist = False

    user_fio = ''
    with open(file) as f:
        if size_file != 0:
            try:
                lines = f.readlines()[1:]

                for line in lines:
                    id_user = int(line.split('\t')[0])
                    user_fio = line.split('\t')[1]
                    # print('id_user in check_user: ', id_user)
                    if chat_id == id_user:
                        exist = True

            except Exception as e:
                print(e)
        else:
            with open(file, 'a') as f:
                f.write('chat_id' + '\t' + 'fio' + '\t' + 'number_phone' + '\t' + 'city' + '\t' 'item_sdek')

    if exist:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        do_order = types.KeyboardButton('СДЕЛАТЬ ЗАКАЗ')
        check_status = types.KeyboardButton('ПРОВЕРИТЬ СТАТУС')
        markup.add(do_order, check_status)
        msg = bot.send_message(chat_id, "Привет, " + user_fio, reply_markup=markup)
        bot.register_next_step_handler(msg, type_delivery)

    else:
        msg = bot.send_message(chat_id, "Привет. Я бот, давай пройдем регистрацию. Введите фамилию, имя, "
                                        "отчество")
        bot.register_next_step_handler(msg, process_write_fio, 'new')


def edit_user(message):
    chat_id = message.chat.id

    msg = bot.send_message(chat_id, "Привет. Я бот, давай пройдем корректировку данных. Введите фамилию, имя, "
                                    "отчество")
    bot.register_next_step_handler(msg, process_write_fio, 'edit')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        check_user(message)

    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in send_welcome. /start')


@bot.message_handler(commands=['edit'])
def edit(message):
    try:
        edit_user(message)

    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in edit. /start')


def process_write_fio(message, mode):
    try:
        chat_id = message.chat.id
        fio = message.text
        if re.search("^[А-ЯA-Z][а-яa-zА-ЯA-Z\\-]*\\s[А-ЯA-Z][а-яa-zА-ЯA-Z\\-]+(\\s[А-ЯA-Z]["
                     "а-яa-zА-ЯA-Z\\-]+)?$", fio):
            data = DataHuman()
            data.fio = fio
            data.mode = mode
            data.chat_id = chat_id
            data_dict[chat_id] = data
            msg = bot.send_message(chat_id, "Введите Ваш номер телефона в формате +79203351425 или 79203351425")
            bot.register_next_step_handler(msg, process_number_phone)
        else:
            msg = bot.send_message(chat_id, "ФИО указано не правильно, попробуйте снова")
            bot.register_next_step_handler(msg, process_write_fio)

    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in process_write_fio. /start')


def process_number_phone(message):
    try:
        chat_id = message.chat.id
        number_phone = message.text
        if re.search("\\+?7\\d{10}", number_phone):
            data_dict[chat_id].number_phone = number_phone
            msg = bot.send_message(chat_id, "Введите город проживания")
            bot.register_next_step_handler(msg, process_city)
        else:
            msg = bot.send_message(chat_id, "Номер телефона указан не правильно, попробуйте снова")
            bot.register_next_step_handler(msg, process_number_phone)
    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in process_number_phone. /start')


def choose_item_sdek(message):
    try:
        chat_id = message.chat.id
        item_sdek = message.text
        data_dict[chat_id].item_sdek = item_sdek
        print(data_dict[chat_id].chat_id, data_dict[chat_id].fio, data_dict[chat_id].number_phone)
        if data_dict[chat_id].mode == 'new':
            with open(file, 'a') as f:
                f.write('\n' + str(data_dict[chat_id].chat_id) + '\t' + str(data_dict[chat_id].fio) + '\t' +
                        str(data_dict[chat_id].number_phone) + '\t' + str(data_dict[chat_id].city) + '\t' +
                        str(data_dict[chat_id].item_sdek))
        elif data_dict[chat_id].mode == 'edit':
            print('edit in IF')

            file_db = open(file, "r")
            replacement = ""
            # using the for loop
            for line in file_db:
                id_user = line.split('\t')[0]
                changes = line
                if str(chat_id) == id_user:
                    print(line)

                    changes = str(data_dict[chat_id].chat_id) + '\t' + str(data_dict[chat_id].fio) + '\t' + str(
                        data_dict[chat_id].number_phone) + '\t' + str(data_dict[chat_id].city) + '\t' + str(
                        data_dict[chat_id].item_sdek)

                replacement = replacement + changes

            file_db.close()
            # opening the file in write mode
            fout = open(file, "w")
            fout.write(replacement)
            fout.close()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        do_order = types.KeyboardButton('СДЕЛАТЬ ЗАКАЗ')
        check_status = types.KeyboardButton('ПРОВЕРИТЬ СТАТУС')
        markup.add(do_order, check_status)
        if data_dict[chat_id].mode == 'new':
            msg = bot.send_message(chat_id, "Регистрация завершена успешно, " + data_dict[chat_id].fio + '!',
                                   reply_markup=markup)
        elif data_dict[chat_id].mode == 'edit':
            msg = bot.send_message(chat_id, "Корректировка данных прошла успешно, " + data_dict[chat_id].fio + '!',
                                   reply_markup=markup)
        bot.register_next_step_handler(msg, type_delivery)

    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in choose_item_sdek. /start')


def process_city(message):
    try:
        chat_id = message.chat.id
        city = message.text.upper()
        data_dict[chat_id].city = city
        msg = bot.send_message(chat_id, "Укажите свой пункт сдека")
        bot.register_next_step_handler(msg, choose_item_sdek)

    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in process_city. /start')


def type_delivery(message):
    try:
        chat_id = message.chat.id
        if message.text == 'СДЕЛАТЬ ЗАКАЗ':

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            item1 = types.KeyboardButton('Склад-Склад')  # tariff_code 136
            item2 = types.KeyboardButton('Склад-Дверь')  # tariff_code 137
            item3 = types.KeyboardButton('Дверь-Склад')  # tariff_code 138
            item4 = types.KeyboardButton('Склад-Дверь эконом')  # tariff_code 233
            item5 = types.KeyboardButton('Склад-Склад эконом')  # tariff_code 234
            # item6 = types.KeyboardButton('Склад-Склад экспресс')  # tariff_code 291
            # item7 = types.KeyboardButton('Склад-Дверь экспресс')  # tariff_code 294
            # item8 = types.KeyboardButton('Дверь-Склад экспресс')  # tariff_code 295
            markup.add(item1)
            markup.add(item2)
            markup.add(item3)
            markup.add(item4)
            markup.add(item5)
            # markup.add(item6)
            # markup.add(item7)
            # markup.add(item8)

            msg = bot.send_message(chat_id, 'Выберите тип услуги', reply_markup=markup)
            bot.register_next_step_handler(msg, choose_from_city)
        else:
            pass
    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in type_delivery. /start')


def choose_from_city(message):
    try:
        chat_id = message.chat.id
        type_del = message.text
        order_data = DataOrder()
        order_data.chat_id = chat_id
        order_data.type_package = type_del
        order_dict[chat_id] = order_data
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item1 = types.KeyboardButton('МОСКВА')
        item2 = types.KeyboardButton('ХАБАРОВСК')
        item3 = types.KeyboardButton('САНКТ-ПЕТЕРБУРГ')
        item4 = types.KeyboardButton('НОВОСИБИРСК')
        item5 = types.KeyboardButton('ЕКАТЕРИНБУРГ')
        item6 = types.KeyboardButton('НИЖНИЙ НОВГОРОД')
        item7 = types.KeyboardButton('ВЛАДИВОСТОК')
        item8 = types.KeyboardButton('СВОЙ')
        markup.add(item1, item2, item3, item4, item5, item6, item7, item8)

        msg = bot.send_message(chat_id, 'Введите город отправления', reply_markup=markup)
        bot.register_next_step_handler(msg, check_from_city)

    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in success. /start')


def choose_to_city(message):
    try:
        chat_id = message.chat.id

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item1 = types.KeyboardButton('МОСКВА')
        item2 = types.KeyboardButton('ХАБАРОВСК')
        item3 = types.KeyboardButton('САНКТ-ПЕТЕРБУРГ')
        item4 = types.KeyboardButton('НОВОСИБИРСК')
        item5 = types.KeyboardButton('ЕКАТЕРИНБУРГ')
        item6 = types.KeyboardButton('НИЖНИЙ НОВГОРОД')
        item7 = types.KeyboardButton('ВЛАДИВОСТОК')
        markup.add(item1, item2, item3, item4, item5, item6, item7)
        msg = bot.send_message(chat_id, 'Введите город назначения', reply_markup=markup)
        bot.register_next_step_handler(msg, check_to_city)

    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in choose_from_city. /start')


def check_from_city(message):
    try:
        chat_id = message.chat.id
        from_city = message.text

        if from_city == 'СВОЙ':
            with open(file) as f:
                lines = f.readlines()[1:]
                for line in lines:
                    id_user = int(line.split('\t')[0])
                    if chat_id == id_user:
                        city = line.split('\t')[3]
                        order_dict[chat_id].from_city = city
        else:
            order_dict[chat_id].from_city = from_city

        from_delivery(message)

    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in check_from_city. /start')


def check_to_city(message):
    try:
        chat_id = message.chat.id
        to_city = message.text
        order_dict[chat_id].to_city = to_city

        to_delivery(message)

    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in choose_to_city. /start')


def from_delivery(message):
    try:
        chat_id = message.chat.id
        cities = get_list_city(order_dict[chat_id].from_city)
        count = cities.count_of_city
        print('Count in from : ' + str(count))
        if count == 0:
            bot.send_message(chat_id, order_dict[chat_id].from_city + ' город не найден')
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            item1 = types.KeyboardButton('МОСКВА')
            item2 = types.KeyboardButton('ХАБАРОВСК')
            item3 = types.KeyboardButton('САНКТ-ПЕТЕРБУРГ')
            item4 = types.KeyboardButton('НОВОСИБИРСК')
            item5 = types.KeyboardButton('ЕКАТЕРИНБУРГ')
            item6 = types.KeyboardButton('НИЖНИЙ НОВГОРОД')
            item7 = types.KeyboardButton('ВЛАДИВОСТОК')
            item8 = types.KeyboardButton('СВОЙ')
            markup.add(item1, item2, item3, item4, item5, item6, item7, item8)

            msg = bot.send_message(chat_id, 'Введите город отправления снова', reply_markup=markup)
            bot.register_next_step_handler(msg, check_from_city)

        elif count == 1:
            order_dict[chat_id].code_city_sender = get_list_city(order_dict[chat_id].from_city).code
            # choose_to_city(message)
            if order_dict[chat_id].type_package == 'Дверь-Склад' or order_dict[chat_id].type_package == 'Дверь-Склад ' \
                                                                                                        'экспресс':
                choose_to_city(message)
            else:
                choose_to_city(message)
                # output_address_office(message, cities, 'from')

        else:
            chat_id = message.chat.id
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            regions = cities.region
            count_of_regions = len(regions)
            item = 0
            while count_of_regions > item:
                markup.add(types.KeyboardButton(cities.region[item]))
                item += 1

            order_dict[chat_id].from_or_to = 'from'
            msg = bot.send_message(chat_id, 'Введите регион', reply_markup=markup)
            bot.register_next_step_handler(msg, choose_region)

    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in from_delivery. /start')


def to_delivery(message):
    try:
        chat_id = message.chat.id
        cities = get_list_city(order_dict[chat_id].to_city)
        count = cities.count_of_city
        print('Count in to: ' + str(count))
        if count == 0:
            bot.send_message(chat_id, order_dict[chat_id].to_city + ' не имеет офисов')
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            item1 = types.KeyboardButton('МОСКВА')
            item2 = types.KeyboardButton('ХАБАРОВСК')
            item3 = types.KeyboardButton('САНКТ-ПЕТЕРБУРГ')
            item4 = types.KeyboardButton('НОВОСИБИРСК')
            item5 = types.KeyboardButton('ЕКАТЕРИНБУРГ')
            item6 = types.KeyboardButton('НИЖНИЙ НОВГОРОД')
            item7 = types.KeyboardButton('ВЛАДИВОСТОК')
            markup.add(item1, item2, item3, item4, item5, item6, item7)
            msg = bot.send_message(chat_id, 'Введите город назначения снова', reply_markup=markup)
            bot.register_next_step_handler(msg, check_to_city)
        elif count == 1:
            if order_dict[chat_id].type_package == 'Склад-Дверь' or order_dict[
                chat_id].type_package == 'Склад-Дверь эконом' \
                    or order_dict[chat_id].type_package == 'Склад-Дверь экспресс':

                order_dict[chat_id].code_city_receiver = get_list_city(order_dict[chat_id].to_city).code
                choose_weight_package(message)
            else:
                order_dict[chat_id].code_city_receiver = get_list_city(order_dict[chat_id].to_city).code
                output_address_office(message, order_dict[chat_id].code_city_receiver, 'to')

        else:
            chat_id = message.chat.id
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            regions = cities.region
            count_of_regions = len(regions)
            item = 0
            while count_of_regions > item:
                markup.add(types.KeyboardButton(cities.region[item]))
                item += 1

            order_dict[chat_id].from_or_to = 'to'
            msg = bot.send_message(chat_id, 'Введите регион', reply_markup=markup)
            bot.register_next_step_handler(msg, choose_region)
    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in to_delivery. /start')


def choose_region(message):
    try:
        chat_id = message.chat.id
        region = message.text

        print(region)
        print(order_dict[chat_id].from_or_to)
        if order_dict[chat_id].from_or_to == 'from':
            city = order_dict[chat_id].from_city
        else:
            city = order_dict[chat_id].to_city
        print("city in main choose_region: " + str(city))
        cities = get_list_city(city)
        print('cities.region in main choose region: ' + str(cities.region))
        count_of_reg = 0
        reg = 0
        while len(cities.region) > count_of_reg:
            if cities.region[count_of_reg] == region:
                reg = count_of_reg
            count_of_reg += 1
        # print(reg)
        # print(count_of_reg)
        # print(region)
        # print(cities.region[reg])
        code_city = cities.code[reg]

        if order_dict[chat_id].from_or_to == 'from':
            order_dict[chat_id].code_city_sender = code_city
            choose_to_city(message)

        else:
            order_dict[chat_id].code_city_receiver = code_city
            address = order_dict[chat_id].address_storage_receiver
            print('Адрес склада получения в main: ' + str(address))
            # offices = get_office(code_city, address)
            # count_office = offices.count_of_office_city
            if order_dict[chat_id].type_package == 'Дверь-Склад' or order_dict[chat_id].type_package == 'Склад-Склад' or \
                    order_dict[chat_id].type_package == 'Склад-Склад эконом' or \
                    order_dict[chat_id].type_package == 'Склад-Склад экспресс' or \
                    order_dict[chat_id].type_package == 'Дверь-Склад экспресс':
                order_dict[chat_id].code_city_receiver = code_city

                output_address_office(message, code_city, 'to')
            elif order_dict[chat_id].type_package == 'Склад-Дверь' or \
                    order_dict[chat_id].type_package == 'Склад-Дверь эконом' or \
                    order_dict[chat_id].type_package == 'Склад-Дверь экспресс':

                order_dict[chat_id].code_city_receiver = code_city
                choose_weight_package(message)
        print('Code city: ' + str(code_city))

    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in choose_region. /start')


def output_address_office(message, code_city, type):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    if order_dict[chat_id].from_or_to == 'from':
        offices = get_office(code_city, order_dict[chat_id].address_storage_sender)
    else:
        offices = get_office(code_city, order_dict[chat_id].address_storage_receiver)

    print('Code of city: ' + str(code_city))

    count_of_address = offices.count_of_office_city
    item = 0
    while count_of_address > item:
        markup.add(types.KeyboardButton(offices.address_office[item]))
        item += 1
    print('Количество адресов в городе: ' + str(count_of_address))

    msg = bot.send_message(chat_id, 'Выберите адрес склада', reply_markup=markup)
    if type == 'from':
        order_dict[chat_id].code_city_sender = code_city
        print('type = from')
        bot.register_next_step_handler(msg, choose_to_city)
    else:
        order_dict[chat_id].code_city_receiver = code_city
        print('type = to')

        print('двигаемся для ввода веса поссылки')
        bot.register_next_step_handler(msg, choose_weight_package)


def choose_weight_package(message):
    try:
        chat_id = message.chat.id

        if order_dict[chat_id].type_package == 'Дверь-Склад' or order_dict[chat_id].type_package == 'Склад-Склад' or \
                order_dict[chat_id].type_package == 'Склад-Склад эконом' or \
                order_dict[chat_id].type_package == 'Склад-Склад экспресс' or \
                order_dict[chat_id].type_package == 'Дверь-Склад экспресс':
            address_receiver_sklad = message.text

            order_dict[chat_id].address_storage_receiver = address_receiver_sklad
            print('Адрес скалада получения в  main: ' + str(order_dict[chat_id].address_storage_receiver))

            # get_office(order_dict[chat_id].code_city_receiver, address_receiver_sklad)  # добавил из за возникновении
            # ошибки в api calc_by_code При тарифе с режимом доставки от/до склада, склад должен существовать
            # в городе-отправителе и/или городе-получателе соответственно

            address_receiver_sklad_replace = address_receiver_sklad.replace('ул.', '')
            address_receiver_sklad_split = address_receiver_sklad_replace.split(',')
            street_destination = address_receiver_sklad_split[0]
            house_destination = address_receiver_sklad_split[1]
            order_dict[chat_id].street_destination = street_destination
            order_dict[chat_id].house_destination = house_destination

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

        if order_dict[chat_id].type_package == 'Дверь-Склад' or \
                order_dict[chat_id].type_package == 'Дверь-Склад экспресс':

            item1 = types.KeyboardButton('Своя упаковка')
            markup.add(item1)

        else:
            item1 = types.KeyboardButton('Своя упаковка')
            item2 = types.KeyboardButton('Пакет А2 (42х35х13 см)')
            item3 = types.KeyboardButton('Пакет А3 (20х23х12 см)')
            item4 = types.KeyboardButton('(34x23x12 см)')
            item5 = types.KeyboardButton('(20х20х10 см)')
            item6 = types.KeyboardButton('(10х10х5 см)')
            markup.add(item1)
            markup.add(item2)
            markup.add(item3)
            markup.add(item4)
            markup.add(item5)
            markup.add(item6)

            item7 = types.KeyboardButton('Коробка XS (0,5 кг 17х12х9 см)')
            item9 = types.KeyboardButton('Коробка S (2 кг 21х20х11 см)')
            item10 = types.KeyboardButton('Коробка (3 кг 24х24х21 см)')
            item11 = types.KeyboardButton('Коробка M (5 кг 33х25х15 см)')
            item12 = types.KeyboardButton('Коробка L (12 кг 34х33х26 см)')

            markup.add(item7)
            markup.add(item9)
            markup.add(item10)
            markup.add(item11)
            markup.add(item12)

        msg = bot.send_message(chat_id, 'Выберите габариты посылки или выберите свой вариант(Вводить габариты '
                                        'следует через знак "х")', reply_markup=markup)

        bot.register_next_step_handler(msg, add_more_package)
    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in choose_weight_package. /start')


def choose_weight_for_custom_dimension(message):
    try:
        chat_id = message.chat.id
        dimensions = message.text
        print('dimensions in choose_weight_for_custom_dimension: ' + str(dimensions))
        # if order_dict[chat_id].change_data:
        #     dimensions_array.clear()

        dimensions_array.append(dimensions)
        params_array = re.split('х|x', dimensions)
        print('params_array in choose_weight_for_custom_dimension: ' + str(params_array))
        # data_dimens = DataDimensions()
        data_dimensions_dict[chat_id].length = params_array[0]
        data_dimensions_dict[chat_id].width = params_array[1]
        data_dimensions_dict[chat_id].height = params_array[2]
        # data_dimensions_dict[chat_id] = data_dimens
        order_dict[chat_id].dimensions = dimensions_array
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item1 = types.KeyboardButton('0.5кг')
        item2 = types.KeyboardButton('2кг')
        item3 = types.KeyboardButton('5кг')
        item4 = types.KeyboardButton('12кг')
        item5 = types.KeyboardButton('20кг')
        item6 = types.KeyboardButton('25кг')
        markup.add(item1, item2, item3, item4, item5, item6)

        msg = bot.send_message(chat_id, 'Выберите вес посылки или введите свой вариант ', reply_markup=markup)
        bot.register_next_step_handler(msg, choose_weight)
    except Exception as ex:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in choose_weight_package. /start')


def choose_weight(message):
    try:
        chat_id = message.chat.id
        weight_full = message.text

        weight_number = weight_full.replace('кг', '')
        order_dict[chat_id].weight = weight_number
        # if float(weight_number) < 30:
        #
        #     print(order_dict[chat_id].change_data)
        #     if order_dict[chat_id].change_data:
        #         weight_array.clear()
        #         # print('УДАЛЕНИЕ weight_array')
        #     weight_array.append(weight_number)
        #     order_dict[chat_id].weight = weight_array
        #     order_dict[chat_id].count_package = len(weight_array)
        #     print("count_package in choose_weight: " + str(order_dict[chat_id].count_package))
        #     markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        #     print('tariff_code in choose_weight: ' + str(order_dict[chat_id].type_package))

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton('ДОБАВИТЬ ЕЩЕ МЕСТО')
        item2 = types.KeyboardButton('ПРОДОЛЖИТЬ')
        markup.add(item1, item2)
        msg = bot.send_message(chat_id, 'Добавить еще место или продолжить дальше оформлять заказ?',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, choose_dimensions)

        # else:
        #     msg = bot.send_message(chat_id, 'Масса посылки должна быть менее 30 кг, попробуйте снова')
        #     bot.register_next_step_handler(msg, choose_weight_for_custom_dimension)
    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in choose_weight. /start')


def add_dimensions_own_package(message):
    try:
        chat_id = message.chat.id
        dimensions = message.text
        print(dimensions)

        msg = bot.send_message(chat_id, 'Введите габариты посылки. Вводить габариты следует через знак "х"')
        bot.register_next_step_handler(msg, choose_weight_for_custom_dimension)
    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in add_dimensions_own_package. /start')


def add_more_package(message):
    try:
        chat_id = message.chat.id
        dimensions_text = message.text

        data_dimens = DataDimensions()
        data_dimens.dimensions_name = dimensions_text
        data_dimensions_dict[chat_id] = data_dimens

        print('dimensions_name in add_more_package: ' + str(dimensions_text))

        if dimensions_text != 'Своя упаковка':
            dimensions = re.findall("(\\d{1,2}[х|x]\\d{1,2}[х|x]\\d{1,2})", dimensions_text)
            print(dimensions[0])

            if order_dict[chat_id].change_data:
                dimensions_array.clear()

            dimensions_array.append(dimensions[0])
            params_array = re.split('х|x', dimensions[0])

            data_dimensions_dict[chat_id].length = params_array[0]
            data_dimensions_dict[chat_id].width = params_array[1]
            data_dimensions_dict[chat_id].height = params_array[2]
            # data_dimensions_dict[chat_id] = data_dimens
            order_dict[chat_id].dimensions = dimensions_array

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1 = types.KeyboardButton('ДОБАВИТЬ ЕЩЕ МЕСТО')
            item2 = types.KeyboardButton('ПРОДОЛЖИТЬ')
            markup.add(item1, item2)
            msg = bot.send_message(chat_id, 'Добавить еще место или продолжить дальше оформлять заказ?',
                                   reply_markup=markup)
            bot.register_next_step_handler(msg, choose_dimensions)
        else:
            add_dimensions_own_package(message)

    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in add_more_package. /start')


def choose_dimensions(message):
    try:
        chat_id = message.chat.id
        more_package = message.text
        type_box = type_package(message, int(data_dimensions_dict[chat_id].length),
                                int(data_dimensions_dict[chat_id].width), int(data_dimensions_dict[chat_id].height))
        dimensions_name = data_dimensions_dict[chat_id].dimensions_name
        print("dimensions_name in preview: " + str(dimensions_name))

        if dimensions_name != 'Своя упаковка':
            weight = weight_box(type_box, data_dimensions_dict[chat_id].length)
        else:
            weight = order_dict[chat_id].weight

        print("weight in choose_dimensions: " + str(weight))

        if float(weight) < 30:
            # if order_dict[chat_id].change_data:
            #     weight_array.clear()

            weight_array.append(weight)
            order_dict[chat_id].weight = weight_array
            print('weight_array in choose_dimensions: ' + str(weight_array))
            order_dict[chat_id].count_package = len(weight_array)

        else:
            msg = bot.send_message(chat_id, 'Масса посылки должна быть менее 30 кг, попробуйте снова')
            bot.register_next_step_handler(msg, choose_weight)

        if more_package == 'ДОБАВИТЬ ЕЩЕ МЕСТО':

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            if order_dict[chat_id].type_package == 'Дверь-Склад' or \
                    order_dict[chat_id].type_package == 'Дверь-Склад экспресс':

                item1 = types.KeyboardButton('Своя упаковка')
                markup.add(item1)

            else:
                item1 = types.KeyboardButton('Своя упаковка')
                item2 = types.KeyboardButton('Пакет А2 (42х35х13 см)')
                item3 = types.KeyboardButton('Пакет А3 (20х23х12 см)')
                item4 = types.KeyboardButton('(34x23x12 см)')
                item5 = types.KeyboardButton('(20х20х10 см)')
                item6 = types.KeyboardButton('(10х10х5 см)')
                markup.add(item1)
                markup.add(item2)
                markup.add(item3)
                markup.add(item4)
                markup.add(item5)
                markup.add(item6)

                item7 = types.KeyboardButton('Коробка XS (0,5 кг 17х12х9 см)')
                item9 = types.KeyboardButton('Коробка S (2 кг 21х20х11 см)')
                item10 = types.KeyboardButton('Коробка (3 кг 24х24х21 см)')
                item11 = types.KeyboardButton('Коробка M (5 кг 33х25х15 см)')
                item12 = types.KeyboardButton('Коробка L (12 кг 34х33х26 см)')

                markup.add(item7)
                markup.add(item9)
                markup.add(item10)
                markup.add(item11)
                markup.add(item12)

            msg = bot.send_message(chat_id, 'Выберите габариты посылки или выберите свой вариант(Вводить габариты '
                                            'следует через знак "х")', reply_markup=markup)

            bot.register_next_step_handler(msg, add_more_package)
        else:

            type_service(message)
    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in choose_dimensions. /start')


def who_receiver(message):
    try:
        chat_id = message.chat.id
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item1 = types.KeyboardButton('СЕБЕ')
        item2 = types.KeyboardButton('ДРУГОМУ')
        markup.add(item1, item2)
        msg = bot.send_message(chat_id, 'Выберите кому отправить посылку', reply_markup=markup)
        bot.register_next_step_handler(msg, choose_receiver)
    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in who_receiver. /start')


def choose_receiver(message):
    try:
        chat_id = message.chat.id
        receiver = message.text
        if receiver == 'СЕБЕ':
            with open(file) as f:
                lines = f.readlines()[1:]
                for line in lines:
                    id_user = int(line.split('\t')[0])
                    if chat_id == id_user:
                        fio = line.split('\t')[1]
                        order_dict[chat_id].fio_destination = fio
                        number_phone = line.split('\t')[2]
                        order_dict[chat_id].number_phone_destination = number_phone
            # print(order_dict[chat_id].type_package)
            if order_dict[chat_id].type_package == 'Склад-Склад' or \
                    order_dict[chat_id].type_package == 'Склад-Склад эконом' or \
                    order_dict[chat_id].type_package == 'Склад-Склад экспресс':

                if order_dict[chat_id].type_package == 'Склад-Склад':
                    order_dict[chat_id].tariff_code = 136
                elif order_dict[chat_id].type_package == 'Склад-Склад эконом':
                    order_dict[chat_id].tariff_code = 234
                else:
                    order_dict[chat_id].tariff_code = 291
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                item1 = types.KeyboardButton('ДА')
                item2 = types.KeyboardButton('НЕТ')
                markup.add(item1, item2)
                msg = bot.send_message(chat_id, 'Требуется страховка?', reply_markup=markup)
                bot.register_next_step_handler(msg, switch_insurance)

            elif order_dict[chat_id].type_package == 'Дверь-Склад' or \
                    order_dict[chat_id].type_package == 'Дверь-Склад экспресс':
                if order_dict[chat_id].type_package == 'Дверь-Склад':
                    order_dict[chat_id].tariff_code = 138
                else:
                    order_dict[chat_id].tariff_code = 295
                msg = bot.send_message(chat_id, 'Введите улицу отправления')
                bot.register_next_step_handler(msg, process_street)

            else:
                if order_dict[chat_id].type_package == 'Склад-Дверь':
                    order_dict[chat_id].tariff_code = 137
                elif order_dict[chat_id].type_package == 'Склад-Дверь эконом':
                    order_dict[chat_id].tariff_code = 233
                else:
                    order_dict[chat_id].tariff_code = 294
                msg = bot.send_message(chat_id, 'Введите улицу назначения')
                bot.register_next_step_handler(msg, street_destination)
        else:
            msg = bot.send_message(chat_id, 'Введите ФИО получателя')
            bot.register_next_step_handler(msg, fio_destination)
    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in choose_receiver. /start')


def type_service(message):
    try:
        chat_id = message.chat.id
        # type_package = message.text
        # order_dict[chat_id].type_package = type_package
        size_order_file = os.stat(order_file).st_size
        if size_order_file == 0:
            with open(order_file, 'a') as f:
                f.write('chat_id' + '\t' + 'fio' + '\t' + 'number_phone' + '\t' + 'from_city' + '\t' + 'to_city' +
                        '\t' + 'weight' + '\t' + 'dimensions' + '\t' + 'type_package' + '\t' + 'street' + '\t' +
                        'house' + '\t' + 'company' + '\t' + 'fio_destination' + '\t' + 'number_phone_destination' +
                        '\t' + 'street_destination' + '\t' + 'house_destination' + '\t' + 'door_destination' + '\t' +
                        'insurance' + '\t' + 'number_departure' + '\t' + 'add_fee' + '\t' + 'true_seller' + '\t' +
                        'tariff_code')

        who_receiver(message)
        data_from_db_users(message)

    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in type_service. /start')


def data_from_db_users(message):
    try:
        chat_id = message.chat.id
        with open(file) as f:
            lines = f.readlines()[1:]
            for line in lines:
                id_user = int(line.split('\t')[0])
                if chat_id == id_user:
                    fio = line.split('\t')[1]
                    order_dict[chat_id].fio = fio
                    number_phone = line.split('\t')[2]
                    order_dict[chat_id].number_phone = number_phone
                    city = line.split('\t')[3]
                    order_dict[chat_id].sender_city = city
    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in data_from_db_users. /start')


def process_street(message):
    try:
        chat_id = message.chat.id
        street = message.text
        order_dict[chat_id].street = street
        msg = bot.send_message(chat_id, 'Введите номер дома')
        bot.register_next_step_handler(msg, process_house)
    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in process_street. /start')


def process_house(message):
    try:
        chat_id = message.chat.id
        house = message.text
        order_dict[chat_id].house = house

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item1 = types.KeyboardButton('ДА')
        item2 = types.KeyboardButton('НЕТ')
        markup.add(item1, item2)
        msg = bot.send_message(chat_id, 'Требуется страховка?', reply_markup=markup)
        bot.register_next_step_handler(msg, switch_insurance)

    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in process_house. /start')


def fio_destination(message):
    try:
        chat_id = message.chat.id
        fio = message.text

        if re.search("^[А-ЯA-Z][а-яa-zА-ЯA-Z\\-]*\\s[А-ЯA-Z][а-яa-zА-ЯA-Z\\-]+(\\s[А-ЯA-Z]["
                     "а-яa-zА-ЯA-Z\\-]+)?$", fio):
            order_dict[chat_id].fio_destination = fio
            msg = bot.send_message(chat_id, "Введите Ваш номер телефона в формате +79203351425 или 79203351425")
            bot.register_next_step_handler(msg, number_phone_destination)
        else:
            msg = bot.send_message(chat_id, "ФИО указано не правильно, попробуйте снова")
            bot.register_next_step_handler(msg, fio_destination)

    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in fio_destination. /start')


def number_phone_destination(message):
    try:
        chat_id = message.chat.id
        number_phone = message.text

        if re.search("\\+?7\\d{10}", number_phone):
            order_dict[chat_id].number_phone_destination = number_phone
            if order_dict[chat_id].type_package == 'Склад-Дверь':
                order_dict[chat_id].tariff_code = 137
            if order_dict[chat_id].type_package == 'Склад-Дверь эконом':
                order_dict[chat_id].tariff_code = 233
            if order_dict[chat_id].type_package == 'Склад-Дверь экспресс':
                order_dict[chat_id].tariff_code = 294
                msg = bot.send_message(chat_id, "Введите улицу назначения")
                bot.register_next_step_handler(msg, street_destination)
            else:

                markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                item1 = types.KeyboardButton('ДА')
                item2 = types.KeyboardButton('НЕТ')
                markup.add(item1, item2)

                if order_dict[chat_id].type_package == 'Склад-Склад':
                    order_dict[chat_id].tariff_code = 136
                if order_dict[chat_id].type_package == 'Склад-Склад эконом':
                    order_dict[chat_id].tariff_code = 234
                if order_dict[chat_id].type_package == 'Склад-Склад экспресс':
                    order_dict[chat_id].tariff_code = 291

                if order_dict[chat_id].type_package == 'Дверь-Склад':
                    order_dict[chat_id].tariff_code = 138
                if order_dict[chat_id].type_package == 'Дверь-Склад экспресс':
                    order_dict[chat_id].tariff_code = 295

                msg = bot.send_message(chat_id, 'Требуется страховка?', reply_markup=markup)
                bot.register_next_step_handler(msg, switch_insurance)

        else:
            msg = bot.send_message(chat_id, "Номер телефона указан не правильно, попробуйте снова")
            bot.register_next_step_handler(msg, number_phone_destination)
    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in number_phone_destination. /start')


def street_destination(message):
    try:
        chat_id = message.chat.id
        street = message.text
        order_dict[chat_id].street_destination = street
        msg = bot.send_message(chat_id, 'Введите номер дома назначения')
        bot.register_next_step_handler(msg, house_destination)
    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in street_destination. /start')


def house_destination(message):
    try:
        chat_id = message.chat.id
        house = message.text
        order_dict[chat_id].house_destination = house
        msg = bot.send_message(chat_id, 'Введите номер квартиры назначения')
        bot.register_next_step_handler(msg, door_destination)
    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in house_destination. /start')


def door_destination(message):
    try:
        chat_id = message.chat.id
        door = message.text
        order_dict[chat_id].door_destination = door

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        item1 = types.KeyboardButton('ДА')
        item2 = types.KeyboardButton('НЕТ')
        markup.add(item1, item2)
        msg = bot.send_message(chat_id, 'Требуется страховка?', reply_markup=markup)
        bot.register_next_step_handler(msg, switch_insurance)

    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in door_destination. /start')


def switch_insurance(message):
    try:
        chat_id = message.chat.id
        need_insurance = message.text
        if need_insurance == 'ДА':
            msg = bot.send_message(chat_id, 'Укажите сумму страхования')
            bot.register_next_step_handler(msg, preview)
        else:
            preview(message)

    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in switch_insurance. /start')


def preview(message):
    try:
        chat_id = message.chat.id
        need_insurance = message.text
        if need_insurance == 'НЕТ':
            insurance = 1
        else:
            insurance = need_insurance
        if int(insurance) >= 1:
            order_dict[chat_id].insurance = insurance
            print('Сумма страховки: ' + str(insurance))
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            item1 = types.KeyboardButton('ДАННЫЕ КОРРЕКТНЫ')
            item2 = types.KeyboardButton('ИЗМЕНИТЬ ДАННЫЕ')
            markup.add(item1, item2)

            code_of_city_sender = order_dict[chat_id].code_city_sender
            print('preview: ')
            print(code_of_city_sender)
            code_of_city_receiver = order_dict[chat_id].code_city_receiver
            print(code_of_city_receiver)
            # weight = order_dict[chat_id].weight

            length = data_dimensions_dict[chat_id].length
            width = data_dimensions_dict[chat_id].width
            height = data_dimensions_dict[chat_id].height
            # dimensions_name = data_dimensions_dict[chat_id].dimensions_name

            type_box = type_package(message, int(length), int(width), int(height))

            weight_full = 0
            item = 0
            weight_full_kg = 0
            while len(order_dict[chat_id].weight) > item:
                weight_full_kg += float(order_dict[chat_id].weight[item])
                weight_full += float(order_dict[chat_id].weight[item]) * 1000
                item += 1

            tariff_code = order_dict[chat_id].tariff_code
            print('type_box in preview: ' + str(type_box))
            print('tariff_code in preview: ' + str(tariff_code))
            print("weight_full in preview: " + str(weight_full))
            order_dict[chat_id].weight_full = weight_full

            price_delivery_package = round(calc_by_code(code_of_city_sender, code_of_city_receiver, int(weight_full),
                                                        length, width, height, type_box, tariff_code), 2)

            print("price_delivery_package in preview: " + str(price_delivery_package))

            insurance_price_package = (calculation_insurance(float(insurance)))

            print("insurance_price_package in preview: " + str(insurance_price_package))
            if insurance == 1:
                total_price_package = float(price_delivery_package)
                insurance_price_package = 0
            else:
                total_price_package = float(price_delivery_package) + float(insurance_price_package)

            order_dict[chat_id].price_package = total_price_package

            msg = bot.send_message(chat_id, 'Отправитель: \nГород: ' + order_dict[chat_id].from_city
                                   + '\nПолучатель:\nГород: ' + str(order_dict[chat_id].to_city) + ',\nФИО: ' +
                                   str(order_dict[chat_id].fio_destination) + ',\nНомер телефона: ' +
                                   str(order_dict[chat_id].number_phone_destination) + ',\nГабариты: ' + str(
                order_dict[chat_id].dimensions) + ',\nВес: ' + str(weight_full) + ',\nСтоимость страховки: ' +
                                   str(insurance_price_package) + ',\nСтоимость доставки: ' + str(
                price_delivery_package),
                                   reply_markup=markup)
            bot.register_next_step_handler(msg, insurance_package)
        else:
            msg = bot.send_message(chat_id, 'Введите корректную сумму страховки(Сумма страховки должна быть больше 0)')
            bot.register_next_step_handler(msg, preview)
    except TypeError as te:
        bot.send_message(message, str(te) + ', не получается рассчитать итоговую стоимость доставки посылки. /start')
    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in preview. /start')


def insurance_package(message):
    try:
        chat_id = message.chat.id
        correct = message.text
        if correct == 'ДАННЫЕ КОРРЕКТНЫ':

            # здесь выполняем расчет полнной стоимости
            code_of_city_sender = order_dict[chat_id].code_city_sender
            print('code_of_city_sender: ' + str(code_of_city_sender))
            code_of_city_receiver = order_dict[chat_id].code_city_receiver
            print('code_of_city_receiver: ' + str(code_of_city_receiver))

            if order_dict[chat_id].type_package == 'Склад-Дверь' or \
                    order_dict[chat_id].type_package == 'Склад-Дверь эконом' or \
                    order_dict[chat_id].type_package == 'Склад-Дверь экспресс':
                code_office_sender = get_office(code_of_city_sender,
                                                order_dict[chat_id].address_storage_sender).code_of_office
                code_office_receiver = 0
            elif order_dict[chat_id].type_package == 'Склад-Склад' or \
                    order_dict[chat_id].type_package == 'Склад-Склад эконом' or \
                    order_dict[chat_id].type_package == 'Склад-Склад экспресс':

                code_office_sender = get_office(code_of_city_sender,
                                                order_dict[chat_id].address_storage_sender).code_of_office
                code_office_receiver = get_office(code_of_city_receiver,
                                                  order_dict[chat_id].address_storage_receiver).code_of_office
                print("code office receiver in main s_s: " + code_office_receiver)
            else:
                code_office_sender = 0
                code_office_receiver = get_office(code_of_city_receiver,
                                                  order_dict[chat_id].address_storage_receiver).code_of_office

            order_dict[chat_id].code_office_sender = code_office_sender
            order_dict[chat_id].code_office_receiver = code_office_receiver
            print('код офиса отправления в main: ' + str(code_office_sender))
            print('код офиса получения в main: ' + str(code_office_receiver))
            print("count_package in insurance_package: " + str(order_dict[chat_id].count_package))
            print("weight in insurance_package: " + str(order_dict[chat_id].weight))
            weight_kg = order_dict[chat_id].weight[0]
            # print('weight_kg in insurance_package: ' + str(weight_kg))
            weight = float(weight_kg) * 1000

            info(message)

            check_order = create_order(order_dict[chat_id].sender_city, order_dict[chat_id].fio,
                                       order_dict[chat_id].number_phone, order_dict[chat_id].street,
                                       order_dict[chat_id].house,
                                       code_of_city_sender, code_of_city_receiver, order_dict[chat_id].fio_destination,
                                       order_dict[chat_id].number_phone_destination,
                                       order_dict[chat_id].to_city, order_dict[chat_id].street_destination,
                                       order_dict[chat_id].house_destination, order_dict[chat_id].company,
                                       order_dict[chat_id].insurance,
                                       int(weight), int(order_dict[chat_id].weight_full),
                                       data_dimensions_dict[chat_id].length,
                                       data_dimensions_dict[chat_id].width, data_dimensions_dict[chat_id].height,
                                       order_dict[chat_id].tariff_code, order_dict[chat_id].count_package,
                                       code_office_sender, code_office_receiver)

            if check_order.state == 'ACCEPTED':
                bot.send_message(chat_id,
                                 'Накладная успешно создана с номером: ' + str(check_order.sdek_number) + ',' +
                                 '\nДата создания: ' + check_order.date_time + '\nЦена: ' +
                                 str(order_dict[chat_id].price_package))

                bot.send_document(chat_id=chat_id, document=open(check_order.payment_uuid + '.pdf', 'rb'))
                # bot.register_next_step_handler(msg, pay_order)
            else:
                bot.send_message(chat_id, 'Ошибка при формировании заказа')
        else:
            order_dict[chat_id].change_data = True
            order_dict[chat_id].dimensions.clear()
            order_dict[chat_id].weight.clear()
            print("change_data in изменить данные: " + str(order_dict[chat_id].change_data))
            print(order_dict[chat_id].dimensions)
            print(order_dict[chat_id].weight)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1 = types.KeyboardButton('МОСКВА')
            item2 = types.KeyboardButton('ХАБАРОВСК')
            item3 = types.KeyboardButton('САНКТ-ПЕТЕРБУРГ')
            item4 = types.KeyboardButton('НОВОСИБИРСК')
            item5 = types.KeyboardButton('ЕКАТЕРИНБУРГ')
            item6 = types.KeyboardButton('НИЖНИЙ НОВГОРОД')
            item7 = types.KeyboardButton('ВЛАДИВОСТОК')
            item8 = types.KeyboardButton('СВОЙ')
            markup.add(item1, item2, item3, item4, item5, item6, item7, item8)

            msg = bot.send_message(chat_id, 'Введите город отправления', reply_markup=markup)
            bot.register_next_step_handler(msg, check_from_city)

    except Exception as ex:
        print(str(ex))


def info(message):
    try:
        chat_id = message.chat.id
        # print(order_dict[chat_id].toJSON())
        with open(order_file, 'a') as f:
            f.write('\n' + str(order_dict[chat_id].chat_id) + '\t' + str(order_dict[chat_id].fio) + '\t' +
                    str(order_dict[chat_id].number_phone) + '\t' + str(order_dict[chat_id].from_city) + '\t' +
                    str(order_dict[chat_id].to_city) + '\t' + str(order_dict[chat_id].weight) + '\t' +
                    str(order_dict[chat_id].dimensions) + '\t' + str(order_dict[chat_id].type_package) +
                    '\t' + str(order_dict[chat_id].street) + '\t' + str(order_dict[chat_id].house) + '\t' +
                    str(order_dict[chat_id].company) + '\t' + str(order_dict[chat_id].fio_destination) + '\t' + str(
                order_dict[chat_id].number_phone_destination) + '\t' + str(order_dict[chat_id].street_destination) +
                    '\t' + str(order_dict[chat_id].house_destination) + '\t' + str(
                order_dict[chat_id].door_destination) +
                    '\t' + str(order_dict[chat_id].insurance) + '\t' + str(order_dict[chat_id].number_departure) +
                    '\t' + str(order_dict[chat_id].add_fee) + '\t' + str(order_dict[chat_id].true_seller) + '\t' +
                    str(order_dict[chat_id].tariff_code))
        weight_array.clear()
        dimensions_array.clear()

    except Exception:
        traceback.print_exc()
        bot.reply_to(message, 'oops, error in info. /start')


def price_for_client(price_sdek):
    try:
        if 0 <= price_sdek <= 210:
            price = price_sdek * 1.3
        elif 211 <= price_sdek <= 250:
            price = price_sdek * 1.25
        elif 251 <= price_sdek <= 315:
            price = price_sdek * 1.2
        elif 316 <= price_sdek <= 700:
            price = price_sdek * 1.15
        elif 701 <= price_sdek <= 2000:
            price = price_sdek * 1.1
        else:
            price = price_sdek * 1.05
        return price

    except Exception as ex:
        print(ex)


def calculation_insurance(total_insurance):
    try:
        # до 50000 рублей — 0, 8 %, но не менее 50 рублей;
        # от 50000 рублей — 0, 75 %;
        # от 100000 рублей — 0, 7 %;
        # от 150000 рублей — 0, 6 %;
        # от 300000 рублей — 0, 55 %;
        # от 500000 рублей — 0, 5 %;
        # от 1000000 рублей — 0, 45 %.

        if total_insurance == 1:
            price = 0
        elif total_insurance < 50000:
            price = total_insurance * 0.008
        elif 50000 <= total_insurance < 100000:
            price = total_insurance * 0.0075
        elif 100000 <= total_insurance < 150000:
            price = total_insurance * 0.007
        elif 150000 <= total_insurance < 300000:
            price = total_insurance * 0.006
        elif 300000 <= total_insurance < 500000:
            price = total_insurance * 0.0055
        elif 500000 <= total_insurance < 1000000:
            price = total_insurance * 0.005
        else:
            price = total_insurance * 0.0045

        print("PRICE_PACKAGE:")
        print(price)

        if price != 0 and price < 50:
            price = 50

        print("PRICE_PACKAGE:")
        print(price)
        return price

    except Exception as ex:
        print(ex)


def type_package(message, length, width, height):
    chat_id = message.chat.id

    if length == 17 and width == 12 and height == 9:
        type_box = 'CARTON_BOX_XS'
    elif length == 21 and width == 20 and height == 11:
        type_box = 'CARTON_BOX_S'
    elif length == 24 and width == 24 and height == 21:
        type_box = 'CARTON_BOX_3KG'
    elif length == 33 and width == 25 and height == 15:
        type_box = 'CARTON_BOX_M'
    elif length == 34 and width == 33 and height == 26:
        type_box = 'CARTON_BOX_L'

    else:
        type_box = ''

    return type_box


def weight_box(type_box, length):
    try:
        if type_box == 'CARTON_BOX_XS':
            weight = 0.5
        elif type_box == 'CARTON_BOX_S':
            weight = 1
        elif type_box == 'CARTON_BOX_3KG':
            weight = 3
        elif type_box == 'CARTON_BOX_M':
            weight = 2
        elif type_box == 'CARTON_BOX_L':
            weight = 5
        elif type_box == '' and length == str(10):
            weight = 0.5
        else:
            weight = 1
        return weight

    except Exception as ex:
        print(ex)


if __name__ == '__main__':
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
        time.sleep(15)
