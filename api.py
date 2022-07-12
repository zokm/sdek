import re
import time

import requests
import telebot.types

import config
import json

import main


class Order:
    def __init__(self):
        self.uuid = None
        self.date_time = None
        self.state = None
        self.url = None
        self.payment_uuid = None
        self.pdf_url = None
        self.country = None
        self.count_of_city = None
        self.code = None
        self.region = None
        self.count_of_office_city = None
        self.address_office = None
        self.code_of_office = None
        self.sdek_number = None


def auth():
    url = "https://api.cdek.ru/v2/oauth/token?parameters"

    payload = 'grant_type=client_credentials&client_id=' + config.USER_SDEK + '&client_secret' \
                                                                              '=' + config.PASSWORD_SDEK
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    json_data = json.loads(response.text)
    # print(response.text)
    token = json_data['access_token']

    return token


def create_order(city_sender, fio_sender, number_sender, from_street, from_house, code_city_sender, code_city_receiver,
                 fio_recipient, number_recipient, to_city, to_street, to_house, company,
                 insurance, weight, weight_full, length, width, height, tariff_code, count_package, code_office_sender,
                 code_office_receiver):
    url = "https://api.cdek.ru/v2/orders"

    payload_s_s = json.dumps({
        "comment": "Новый заказ",
        "delivery_recipient_cost": {
            "value": 0  # доп сбор всегда 0
        },

        "shipment_point": code_office_sender,
        "delivery_point": code_office_receiver,

        "packages": [{
            "number": "bar-001",
            "comment": "Упаковка",
            "height": height,
            "items": [{
                "ware_key": "00055",
                "payment": {
                    "value": 0
                },
                "name": "Товар",
                "cost": insurance,
                "amount": count_package,
                "weight": weight,
                "url": "www.item.ru"
            }],
            "length": length,
            "weight": weight_full,
            "width": width
        }],
        "recipient": {
            "name": fio_recipient,
            "phones": [{
                "number": number_recipient
            }]
        },
        "sender": {
            "name": fio_sender,
        },
        "tariff_code": tariff_code
    })

    payload_d_s = json.dumps({
        "comment": "Новый заказ",
        "delivery_recipient_cost": {
            "value": 0
        },

        "delivery_point": code_office_receiver,

        "from_location": {
            "code": code_city_sender,
            "fias_guid": "",
            "postal_code": "",
            "longitude": "",
            "latitude": "",
            "country_code": "",
            "region": "",
            "sub_region": "",
            "city": city_sender,
            "kladr_code": "",
            "address": "ул. " + from_street + ", " + from_house
        },

        "packages": [{
            "number": "bar-001",
            "comment": "Упаковка",
            "height": height,
            "items": [{
                "ware_key": "00055",
                "payment": {
                    "value": 0
                },
                "name": "Товар",
                "cost": insurance,
                "amount": count_package,
                "weight": weight,
                "url": "www.item.ru"
            }],
            "length": length,
            "weight": weight_full,
            "width": width
        }],
        "recipient": {
            "name": fio_recipient,
            "phones": [{
                "number": number_recipient
            }]
        },
        "sender": {
            "name": fio_sender,
        },
        "tariff_code": tariff_code
    })

    payload_s_d = json.dumps({
        "comment": "Новый заказ",
        "delivery_recipient_cost": {
            "value": 0
        },

        "shipment_point": code_office_sender,

        "to_location": {
            "code": code_city_receiver,
            "fias_guid": "",
            "postal_code": "",
            "longitude": "",
            "latitude": "",
            "country_code": "",
            "region": "",
            "sub_region": "",
            "city": to_city,
            "kladr_code": "",
            "address": "ул. " + to_street + ", " + to_house
        },

        "packages": [{
            "number": "bar-001",
            "comment": "Упаковка",
            "height": height,
            "items": [{
                "ware_key": "00055",
                "payment": {
                    "value": 0
                },
                "name": "Товар",
                "cost": insurance,
                "amount": count_package,
                "weight": weight,
                "url": "www.item.ru"
            }],
            "length": length,
            "weight": weight_full,
            "width": width
        }],
        "recipient": {
            "name": fio_recipient,
            "phones": [{
                "number": number_recipient
            }]
        },
        "sender": {
            "name": fio_sender,
        },
        "tariff_code": tariff_code
    })

    payload = None

    print('Тариф код в api: ' + str(tariff_code))
    if tariff_code == 136 or tariff_code == 234 or tariff_code == 291:
        payload = payload_s_s
    elif tariff_code == 137 or tariff_code == 233 or tariff_code == 294:
        payload = payload_s_d
    else:
        payload = payload_d_s

    headers = {
        'Authorization': 'Bearer ' + auth(),
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    # print(response.text)
    json_data = json.loads(response.text)
    print("Create_order json file: " + str(json_data))
    state = json_data['requests'][0]['state']
    print('CREATE_ORDER: ' + str(state))
    uuid = json_data['entity']['uuid']
    date = json_data['requests'][0]['date_time']

    result = Order()
    result.uuid = uuid
    result.date_time = date
    result.state = state

    # print(uuid)
    sdek_number = info_order(uuid)
    result.sdek_number = sdek_number

    return create_payment(result)


def create_payment(order):
    url = "https://api.cdek.ru/v2/print/orders"

    payload = json.dumps({
        "orders": [
            {
                "order_uuid": order.uuid
            }
        ],
        "copy_count": 2
    })
    headers = {
        'Authorization': 'Bearer ' + auth(),
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print('Create payment')
    print("Payment: " + response.text)
    print('----------------------')
    json_data = json.loads(response.text)
    print('create_payment json file: ' + str(json_data))
    state = json_data['requests'][0]['state']
    uuid = json_data['entity']['uuid']
    print('UUID: ' + str(uuid))
    order.payment_uuid = uuid
    return get_payment_url(order)


def get_payment_url(order):
    try:
        url = "https://api.cdek.ru/v2/print/orders/" + order.payment_uuid
        # print('GET_PAYMENT_URL: ' + str(url))
        headers = {
            'Authorization': 'Bearer ' + auth(),
            'Content-Type': 'application/json'
        }
        response = requests.request("GET", url, headers=headers)
        json_data = json.loads(response.text)
        time.sleep(5)
        print("json get_payment_url: ")
        print(json_data)

        pdf = json_data['entity']['url']

        order.pdf_url = pdf
        print('PDF: ' + str(pdf))
        # number_package = json_data['entity']['cdek_number']
        # print('Number package: ' + str(number_package))
        return get_payment_pdf(order)

    except KeyError as ke:
        print("Невозможно определить ссылку " + str(ke))


def get_payment_pdf(order):
    url = order.pdf_url
    # print(url)
    headers = {
        'Authorization': 'Bearer ' + auth()
    }
    response = requests.request("GET", url, headers=headers)
    open(order.payment_uuid + '.pdf', 'wb').write(response.content)
    # json_data = json.loads(response.text)
    # print(json_data)
    # pdf = json_data['entity']['url']
    # print(pdf)
    return order


def get_list_city(city):
    url = "https://api.cdek.ru/v2/location/cities/?country_codes=RU,BY,AM,KZ,KG&city=" + city

    headers = {
        'Authorization': 'Bearer ' + auth()
    }
    response = requests.request("GET", url, headers=headers)
    json_data = json.loads(response.text)
    code_array = []
    region_array = []

    count_of_city = len(json_data)
    order = Order()
    order.count_of_city = count_of_city

    if count_of_city == 1:
        print(count_of_city)
        code = json_data[0]['code']
        order.code = code
        country_code = json_data[0]['country_code']  # country_code для рассчета таможни
        order.country = country_code  # country_code для рассчета таможни

    elif count_of_city > 1:
        print(count_of_city)
        count = 0
        while count_of_city > count:
            code_array.append(json_data[count]['code'])
            region_array.append(json_data[count]['region'])  # country_code для рассчета таможни
            country_code = json_data[count]['country_code']  # country_code для рассчета таможни

            count += 1
        order.code = code_array
        order.region = region_array
        order.country = country_code  # country_code для рассчета таможни

    return order


def get_office(code, address_office):
    url = "https://api.cdek.ru/v2/deliverypoints?weight_max=30&city_code=" + str(code) + "&type=PVZ"

    headers = {
        'Authorization': 'Bearer ' + auth()
    }
    response = requests.request("GET", url, headers=headers)
    json_data = json.loads(response.text)
    # print(json_data)
    print('office: ')
    # print(json_data)
    count_of_office_city = len(json_data)
    order = Order()
    order.count_of_office_city = count_of_office_city

    print(order.code_of_office)
    print('Количество офисов в городе: ' + str(order.count_of_office_city))
    item = 0
    address_array = []
    while count_of_office_city > item:
        address_array.append(json_data[item]['location']['address'])
        order.address_office = address_array
        item += 1
    print(address_array)
    print('-------------------------')

    if count_of_office_city == 1:
        order.code_of_office = json_data[0]['code']
    else:
        count_of = 0
        item_of = 0
        # print('JSON_DATA in get_office ' + str(json_data[count_of]['location']['address']))
        # print('address: ' + str(address_office))
        # print('Количество офисов в городе: ' + str(count_of_office_city))

        while count_of_office_city > count_of:
            if json_data[count_of]['location']['address'] == address_office:
                item_of = count_of
                # print(json_data[count_of]['location']['address'])
                # print('= or != ' + str(count_of))
                # print(address_office)
                # print('item_of == ' + str(item_of))
            count_of += 1

        print('Номер элемента в массиве адресов склада: ' + str(item_of))
        order.code_of_office = json_data[item_of]['code']
        print("get_office: " + str(json_data[item_of]))
        # code_of_office_sub = re.sub('\d', '', code_of_office)
        # order.code_of_office = code_of_office_sub + str(7)
        # print('SUB: ' + str(code_of_office_sub))
        # print('order.code_of_office in api.py: ' + str(order.code_of_office))

    return order


def calc_by_code(code_sender, code_receiver, weight, length, width, height, type_box, tariff_code):
    try:
        url = "https://api.cdek.ru/v2/calculator/tariff"
        payload_from_sklad = json.dumps({

            "currency": "1",
            "tariff_code": tariff_code,
            "from_location": {
                "code": code_sender
            },
            "to_location": {
                "code": code_receiver
            },
            "services": [
                {
                    "code": " " + type_box,
                    "parameter": "2"
                }
            ],
            "packages": [
                {
                    "height": height,
                    "length": length,
                    "weight": weight,
                    "width": width
                }
            ]
        })

        payload_from_door = json.dumps({
            "currency": "1",
            "tariff_code": tariff_code,
            "from_location": {
                "code": code_sender
            },
            "to_location": {
                "code": code_receiver
            },

            "packages": [
                {
                    "height": height,
                    "length": length,
                    "weight": weight,
                    "width": width
                }
            ]
        })
        payload = None
        if tariff_code == 138 or tariff_code == 295 or type_box == '':
            payload = payload_from_door
        else:
            payload = payload_from_sklad

        headers = {
            'Authorization': 'Bearer ' + auth(),
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        json_data = json.loads(response.text)
        json_data["total_sum"] = main.price_for_client(json_data['total_sum'])
        # json_data["delivery_sum"] = main.price_for_client(json_data['delivery_sum'])
        price = json_data["total_sum"]

        print("calc_by_code: ")
        print(json_data)

        # print('calc in method: ' + str(price))

        return price
    except Exception as ex:
        print(str(ex))


# def calc_by_customs(weight, cost):
#     try:
#         url = 'https://api.cdek.ru/v2/ddp'
#         payload = json.dumps({
#             "weight": weight,
#             "cost": cost
#         })
#         headers = {
#             'Authorization': 'Bearer ' + auth(),
#             'Content-Type': 'application/json'
#         }
#         response = requests.request("POST", url, headers=headers, data=payload)
#         json_data = json.loads(response.text)
#         print("calc_by_customs:")
#         print(json_data)
#         total_price = json_data['total_amount']
#         return total_price
#     except Exception as ex:
#         print(ex)
#

def info_order(uuid):
    try:
        url = "https://api.cdek.ru/v2/orders/" + uuid
        headers = {
            'Authorization': 'Bearer ' + auth()
        }
        response = requests.request("GET", url, headers=headers)
        json_data = json.loads(response.text)
        print()
        print("INFO ORDER json file: " + str(json_data))
        sdek_number = json_data['entity']['cdek_number']
        return sdek_number
    except KeyError as ke:
        print("Не получается определить номер накладной " + str(ke))
