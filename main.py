# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import asyncio
import random
import string
import time
from json import JSONDecodeError
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from aiohttp import ClientSession
import json
from telethon.sync import TelegramClient, Button, events
from telethon import errors
from datetime import datetime, timedelta
import sqlite3
import logging
import traceback
import sys

from appication.formatters import search_text_to_link, change_domain
from payments.cryptobot import crypto_pay_create_invoice, crypto_pay_check_invoice
from model import ItemInfo
from xl_module import create_xl_file, create_txt_file

from config import server_list, block_list

log_file_name = "./logs/" + str(datetime.now().strftime("%m_%d_%Y_%H_%M")) + ".log"
name_encoding = [logging.FileHandler(filename=log_file_name, encoding='utf-8', mode='a+')]
logging.basicConfig(handlers=name_encoding, format='[%(asctime)s | %(levelname)s]: %(message)s',
                    datefmt='%m.%d.%Y %H:%M:%S', level=logging.INFO)


def log_uncaught_exceptions(ex_cls, ex, tb):
    text = '{}: {}:\n'.format(ex_cls.__name__, ex)
    text += ''.join(traceback.format_tb(tb))
    logging.info(text)


sys.excepthook = log_uncaught_exceptions

conn = sqlite3.connect('users.db')
cur = conn.cursor()
for region in ['PL', 'FR', 'AT', 'CZ', 'BE', 'DE', 'IT', 'LT', 'LU', 'ES', 'SK', 'NL', 'PT', 'COM', 'HU', 'COUK', 'SE']:
    cur.execute(f"""CREATE TABLE IF NOT EXISTS {region}_USERS(
ID INTEGER PRIMARY KEY AUTOINCREMENT,
USER_ID INT,
USERNAME TEXT,
CHATING_STATUS TEXT,
BILLING_DATETIME TEXT,
ITEM_DATE_LIMIT INT,
UNIQUE_FILTER INT,
RATING_FILTER INT,
SELLER_DATE_LIMIT INT,
SELLER_ITEMS_LIMIT INT,
ITEM_VIEWS_LIMIT INT,
PROFILE_FEEDBACK_FILTER INT,
GIVE_TAKE_FILTER INT,
COUNTRY_FILTER INT,
SELLER_FILTER INT);
""")
cur.execute("""CREATE TABLE IF NOT EXISTS ITEMS(
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   ITEM_ID INT,
   USER_IDS TEXT);
""")
cur.execute("""CREATE TABLE IF NOT EXISTS CURRENT_DOMAIN(
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   USER_ID INT,
   USER_NAME TEXT,
   DOMAIN TEXT);
""")
cur.execute("""CREATE TABLE IF NOT EXISTS SELLERS(
   ID INTEGER PRIMARY KEY AUTOINCREMENT,
   SELLER_ID INT,
   BLACKLIST INT);
""")
cur.execute("""CREATE TABLE IF NOT EXISTS report_constructor(
   t_id INTEGER DEFAULT 1,
   title INTEGER DEFAULT 1,
   price INTEGER DEFAULT 1,
   location INTEGER DEFAULT 1,
   description INTEGER DEFAULT 1,
   views INTEGER DEFAULT 1,
   post_date INTEGER DEFAULT 1,
   chat_link INTEGER DEFAULT 1,
   direct_link INTEGER DEFAULT 1,
   photo_link INTEGER DEFAULT 1,
   seller_username INTEGER DEFAULT 1,
   seller_rating INTEGER DEFAULT 1,
   seller_date INTEGER DEFAULT 1,
   seller_posted INTEGER DEFAULT 1,
   seller_sold INTEGER DEFAULT 1,
   seller_bought INTEGER DEFAULT 1,
   parser_views_count INTEGER DEFAULT 1,
   txt_link INTEGER DEFAULT 0,
   excel INTEGER DEFAULT 1);
""")
conn.commit()
# cur.execute(f"SELECT * FROM CURRENT_DOMAIN")
# users = cur.fetchall()
# for user in users:
#     cur.execute(f"""INSERT INTO report_constructor (t_id, title) VALUES('{user[1]}', 1)""")
# conn.commit()

spam_filter = {}
api_id = 124234
api_hash = 'sfg'
admin_list = [216541641, 5062129675, 1762673072, 895312150]
join_groups_list = ['@wollery1', '@wollechat']
crypto_cloud_api_key = 'srg'
crypto_cloud_shop_id = '23423423423'


def update_blacklist_dict(user_id):
    my_tuple = ()
    if user_id in spam_filter:
        spam_filter[user_id].append(datetime.now().timestamp())
        for i in range(len(spam_filter[user_id]) - 1, -1, -1):
            if datetime.now().timestamp() - spam_filter[user_id][i] > 15:
                del spam_filter[user_id][i]
        if len(spam_filter[user_id]) == 0:
            del spam_filter[user_id]
        if len(spam_filter[user_id]) > 2:
            my_tuple = (user_id)
    else:
        spam_filter[user_id] = [datetime.now().timestamp()]
    print(spam_filter)
    return my_tuple


with TelegramClient('name', api_id, api_hash) as client:  # создаст сессию с названием name
    bot_username = client.get_entity('me').username
    print(f'logged in as {bot_username}')
    logging.info(f'logged in as {bot_username}')


    async def get_user_ids_from_group(client):
        offset = 0
        limit = 510
        all_participants = []
        while True:
            participants = await client(
                GetParticipantsRequest(-1001846605598, ChannelParticipantsSearch('*'), offset, limit,
                                       hash=0
                                       ))
            if not participants.users:
                break
            for x in participants.users:
                all_participants.append(x.id)
            offset += len(participants.users)
        return all_participants


    async def check_group_joined(client, group, sender) -> bool:
        async for user_checking in client.iter_participants(group, search=sender.username):
            if sender.id == user_checking.id:
                return True
        return False


    def create_region_keyboard():
        keyboard = [
            [Button.inline("🇵🇱 VINTED.PL", b"PL")],
            [Button.inline("🇫🇷 VINTED.FR", b"FR"), Button.inline("🇦🇹 VINTED.AT", b"AT")],
            [Button.inline("🇨🇿 VINTED.CZ", b"CZ")],
            [Button.inline("🇧🇪 VINTED.BE", b"BE"), Button.inline("🇩🇪 VINTED.DE", b"DE")],
            [Button.inline("🇮🇹 VINTED.IT", b"IT")],
            [Button.inline("🇱🇹 VINTED.LT", b"LT"), Button.inline("🇱🇺 VINTED.LU", b"LU")],
            [Button.inline("🇪🇸 VINTED.ES", b"ES")],
            [Button.inline("🇸🇰 VINTED.SK", b"SK"), Button.inline("🇳🇱 VINTED.NL", b"NL")],
            [Button.inline("🇵🇹 VINTED.PT", b"PT"), Button.inline("🇺🇸 VINTED.COM", b"COM")],
            [Button.inline("🇭🇺 VINTED.HU", b"HU"), Button.inline("🇬🇧 VINTED.CO.UK", b"COUK")],
            [Button.inline("🇸🇪 VINTED.SE", b"SE")],
        ]
        return keyboard


    def create_admin_region_keyboard():
        keyboard = [
            [Button.inline("🇵🇱 VINTED.PL", b"A_PL")],
            [Button.inline("🇫🇷 VINTED.FR", b"A_FR"), Button.inline("🇦🇹 VINTED.AT", b"A_AT")],
            [Button.inline("🇨🇿 VINTED.CZ", b"A_CZ")],
            [Button.inline("🇧🇪 VINTED.BE", b"A_BE"), Button.inline("🇩🇪 VINTED.DE", b"A_DE")],
            [Button.inline("🇮🇹 VINTED.IT", b"A_IT")],
            [Button.inline("🇱🇹 VINTED.LT", b"A_LT"), Button.inline("🇱🇺 VINTED.LU", b"A_LU")],
            [Button.inline("🇪🇸 VINTED.ES", b"A_ES")],
            [Button.inline("🇸🇰 VINTED.SK", b"A_SK"), Button.inline("🇳🇱 VINTED.NL", b"A_NL")],
            [Button.inline("🇵🇹 VINTED.PT", b"A_PT"), Button.inline("🇺🇸 VINTED.COM", b"A_COM")],
            [Button.inline("🇭🇺 VINTED.HU", b"A_HU"), Button.inline("🇬🇧 VINTED.CO.UK", b"A_COUK")],
            [Button.inline("🇸🇪 VINTED.SE", b"A_SE")],
        ]
        return keyboard


    def create_referal_region_keyboard():
        keyboard = [
            [Button.inline("🇵🇱 VINTED.PL", b"R_PL")],
            [Button.inline("🇫🇷 VINTED.FR", b"R_FR"), Button.inline("🇦🇹 VINTED.AT", b"R_AT")],
            [Button.inline("🇨🇿 VINTED.CZ", b"R_CZ")],
            [Button.inline("🇧🇪 VINTED.BE", b"R_BE"), Button.inline("🇩🇪 VINTED.DE", b"R_DE")],
            [Button.inline("🇮🇹 VINTED.IT", b"R_IT")],
            [Button.inline("🇱🇹 VINTED.LT", b"R_LT"), Button.inline("🇱🇺 VINTED.LU", b"R_LU")],
            [Button.inline("🇪🇸 VINTED.ES", b"R_ES")],
            [Button.inline("🇸🇰 VINTED.SK", b"R_SK"), Button.inline("🇳🇱 VINTED.NL", b"R_NL")],
            [Button.inline("🇵🇹 VINTED.PT", b"R_PT"), Button.inline("🇺🇸 VINTED.COM", b"R_COM")],
            [Button.inline("🇭🇺 VINTED.HU", b"R_HU"), Button.inline("🇬🇧 VINTED.CO.UK", b"R_COUK")],
            [Button.inline("🇸🇪 VINTED.SE", b"R_SE")],
        ]
        return keyboard


    def report_constructor_keyboard(report_constructor):
        keyboard = []
        if report_constructor[1] == 0:
            keyboard.append([Button.inline('🔴 Название товара', b"constructor_title")])
        elif report_constructor[1] == 1:
            keyboard.append([Button.inline('🟢 Название товара', b"constructor_title")])
        if report_constructor[2] == 0:
            keyboard.append([Button.inline('🔴 Цена товара', b"constructor_price")])
        elif report_constructor[2] == 1:
            keyboard.append([Button.inline('🟢 Цена товара', b"constructor_price")])
        if report_constructor[3] == 0:
            keyboard.append([Button.inline('🔴 Местоположение товара', b"constructor_location")])
        elif report_constructor[3] == 1:
            keyboard.append([Button.inline('🟢 Местоположение товара', b"constructor_location")])
        if report_constructor[4] == 0:
            keyboard.append([Button.inline('🔴 Описание товара', b"constructor_description")])
        elif report_constructor[4] == 1:
            keyboard.append([Button.inline('🟢 Описание товара', b"constructor_description")])
        if report_constructor[5] == 0:
            keyboard.append([Button.inline('🔴 Кол-во просмотров товара', b"constructor_views")])
        elif report_constructor[5] == 1:
            keyboard.append([Button.inline('🟢 Кол-во просмотров товара', b"constructor_views")])
        if report_constructor[6] == 0:
            keyboard.append([Button.inline('🔴 Дата создания объявления', b"constructor_date")])
        elif report_constructor[6] == 1:
            keyboard.append([Button.inline('🟢 Дата создания объявления', b"constructor_date")])
        if report_constructor[7] == 0:
            keyboard.append([Button.inline('🔴 Ссылка на чат с продавцом', b"constructor_chat")])
        elif report_constructor[7] == 1:
            keyboard.append([Button.inline('🟢 Ссылка на чат с продавцом', b"constructor_chat")])
        if report_constructor[8] == 0:
            keyboard.append([Button.inline('🔴 Ссылка на товар', b"constructor_link")])
        elif report_constructor[8] == 1:
            keyboard.append([Button.inline('🟢 Ссылка на товар', b"constructor_link")])
        if report_constructor[9] == 0:
            keyboard.append([Button.inline('🔴 Ссылка на фото', b"constructor_photo")])
        elif report_constructor[9] == 1:
            keyboard.append([Button.inline('🟢 Ссылка на фото', b"constructor_photo")])
        if report_constructor[10] == 0:
            keyboard.append([Button.inline('🔴 Имя продавца', b"constructor_seller")])
        elif report_constructor[10] == 1:
            keyboard.append([Button.inline('🟢 Имя продавца', b"constructor_seller")])
        if report_constructor[11] == 0:
            keyboard.append([Button.inline('🔴 Рейтинг продавца', b"constructor_rating")])
        elif report_constructor[11] == 1:
            keyboard.append([Button.inline('🟢 Рейтинг продавца', b"constructor_rating")])
        if report_constructor[12] == 0:
            keyboard.append([Button.inline('🔴 Дата регистрации продавца', b"constructor_registration")])
        elif report_constructor[12] == 1:
            keyboard.append([Button.inline('🟢 Дата регистрации продавца', b"constructor_registration")])
        if report_constructor[13] == 0:
            keyboard.append([Button.inline('🔴 Кол-во объявлений продавца', b"constructor_posted")])
        elif report_constructor[13] == 1:
            keyboard.append([Button.inline('🟢 Кол-во объявлений продавца', b"constructor_posted")])
        if report_constructor[14] == 0:
            keyboard.append([Button.inline('🔴 Кол-во проданных товаров продавца', b"constructor_sold")])
        elif report_constructor[14] == 1:
            keyboard.append([Button.inline('🟢 Кол-во проданных товаров продавца', b"constructor_sold")])
        if report_constructor[15] == 0:
            keyboard.append([Button.inline('🔴 Кол-во купленых товаров продавца', b"constructor_bought")])
        elif report_constructor[15] == 1:
            keyboard.append([Button.inline('🟢 Кол-во купленых товаров продавца', b"constructor_bought")])
        if report_constructor[16] == 0:
            keyboard.append([Button.inline('🔴 Просмотры пользователями парсера', b"constructor_views_c")])
        elif report_constructor[16] == 1:
            keyboard.append([Button.inline('🟢 Просмотры пользователями парсера', b"constructor_views_c")])
        if report_constructor[17] == 0:
            keyboard.append([Button.inline('🔴 Cсылки на продавца в .txt', b"constructor_txt_link")])
        elif report_constructor[17] == 1:
            keyboard.append([Button.inline('🟢 Cсылки на продавца в .txt', b"constructor_txt_link")])
        if report_constructor[18] == 0:
            keyboard.append([Button.inline('🔴 Вывод отчёта в excel', b"constructor_excel")])
        elif report_constructor[18] == 1:
            keyboard.append([Button.inline('🟢 Вывод отчёта в excel', b"constructor_excel")])
        return keyboard


    def create_start_keyboard():
        keyboard = [
            [Button.text("🚀 Начать парсинг", single_use=True, resize=True),
             Button.text("🔁 Повторить парсинг", single_use=True, resize=True)],
            [Button.text("⚙ Настройки", single_use=True, resize=True),
             Button.text("👫 Реферальная программа", resize=True)],
            [Button.text("🆘 Помощь", resize=True),
             Button.text("🤫 Ввести промокод", resize=True)],
            [Button.text("SENDER SMS 🦧", resize=True),
             ]
        ]
        return keyboard


    async def create_settings_keyboard(user_id):
        cur.execute(f"SELECT * FROM CURRENT_DOMAIN WHERE USER_ID = {user_id}")
        domain_zone = cur.fetchone()[3]
        if domain_zone == "":
            await client.send_message(user_id, 'Выберите доменную зону')
            return False
        cur.execute(f"SELECT * FROM {domain_zone}_USERS WHERE USER_ID = {user_id}")
        telegram_user_data = cur.fetchone()
        if telegram_user_data[6] == 0:
            unique_text = '🔴 Только непросмотренные обьявления'
        elif telegram_user_data[6] == 1:
            unique_text = '🟢 Только непросмотренные обьявления'
        if telegram_user_data[7] == 0:
            rating_filter_text = '🔴 Только без рейтинга'
        elif telegram_user_data[7] == 1:
            rating_filter_text = '🟢 Только без рейтинга'
        if telegram_user_data[11] == 0:
            profile_feedback_filter_text = '🔴 Только без отзывов'
        elif telegram_user_data[11] == 1:
            profile_feedback_filter_text = '🟢 Только без отзывов'
        if telegram_user_data[12] == 0:
            give_take_filter = '🔴 Только без сделок'
        elif telegram_user_data[12] == 1:
            give_take_filter = '🟢 Только без сделок'
        if telegram_user_data[13] == 0:
            country_filter = '🔴 Фильтр локации'
        elif telegram_user_data[13] == 1:
            country_filter = '🟢 Фильтр локации'
        print(telegram_user_data[14])
        if telegram_user_data[14] == 0:
            seller_filter = '🔴 Не показывать продавцов повторно'
        elif telegram_user_data[14] == 1:
            seller_filter = '🟢 Не показывать продавцов повторно'
        keyboard = [
            [Button.inline('Ограничить дату создания обьявления', b"ITEM_DATE_LIMIT")],
            # [Button.inline('Ограничить дату регистрации продавца', b"SELLER_DATE_LIMIT")],
            [Button.inline('Количество товаров продавца', b"SELLER_ITEMS_LIMIT")],
            [Button.inline('Количество просмотров обьявления', b"ITEM_VIEWS_LIMIT")],
            [Button.inline('Смена домена в ссылке', b"DOMAIN_CHANGE")],
            [Button.inline(unique_text, b"UNIQUE_FILTER")],
            [Button.inline(rating_filter_text, b"RATING_FILTER")],
            [Button.inline(profile_feedback_filter_text, b"PROFILE_FEEDBACK_FILTER")],
            [Button.inline(give_take_filter, b"GIVE_TAKE_FILTER")],
            [Button.inline(country_filter, b"COUNTRY_FILTER")],
            [Button.inline(seller_filter, b"SELLER_FILTER")],
            [Button.inline("Экспортировать пресет", b"EXPORT_PRESET")],
            [Button.inline("Конструктор отчётов", b"report_constructor")],
            [Button.inline("Список запрещённых слов", b"BLACK_LIST")]
        ]
        return keyboard


    def create_admin_keyboard():
        keyboard = [
            [Button.inline('Количество юзеров', b"PARSER_USERS_COUNT")],
            [Button.inline('Cтатистика пользователя', b"STATS")],
            [Button.inline('Создать промокод', b"PROMO")],
            [Button.inline('Сделать рассылку', b"SPAM")],
            [Button.inline('Дать\забрать подписку', b"ADMIN_REGION")]

        ]
        return keyboard


    def create_time_keyboard():
        keyboard = [
            [Button.inline('Купить на 1 день[190₽]', b"BUY_TIME1")],
            [Button.inline('Купить на 3 день[400₽]', b"BUY_TIME3")],
            [Button.inline('Купить на 7 день[700₽]', b"BUY_TIME7")],
            [Button.inline('Купить на 31 день[2900₽]', b"BUY_TIME31")]
        ]
        return keyboard


    def create_payok_time_keyboard():
        keyboard = [
            [Button.inline('Купить на 1 день[190₽]', b"BUY_TIME_1")],
            [Button.inline('Купить на 3 день[400₽]', b"BUY_TIME_3")],
            [Button.inline('Купить на 7 день[700₽]', b"BUY_TIME_7")],
            [Button.inline('Купить на 31 день[2900₽]', b"BUY_TIME_31")]
        ]
        return keyboard


    def create_crypto_bot_currency_keyboard():
        keyboard = [
            [Button.inline('BTC', b"BTC")],
            [Button.inline('TON', b"TON")],
            [Button.inline('ETH', b"ETH")],
            [Button.inline('USDT', b"USDT")],
            [Button.inline('USDC', b"USDC")]
        ]
        return keyboard


    def create_crypto_bot_time_keyboard():
        keyboard = [
            [Button.inline('Купить на 1 день[190₽]', b"BUY_TIME1_")],
            [Button.inline('Купить на 3 день[400₽]', b"BUY_TIME3_")],
            [Button.inline('Купить на 7 день[700₽]', b"BUY_TIME7_")],
            [Button.inline('Купить на 31 день[2900₽]', b"BUY_TIME31_")]
        ]
        return keyboard


    def create_payment_keyboard():
        keyboard = [
            [Button.inline('BTC, USDT, LTC, ETH', b"PAYOK")],
            [Button.inline('CryptoBot', b"crypto_bot")],
            [Button.inline('BTC BANKIR', b"BTC_BANKIR")]
        ]
        return keyboard


    async def try_check(username, code, domain_zone):
        api_id = 12355464
        api_hash = 'e3d2615cdcda1b36d0ba0d856961a5ad'
        async with TelegramClient('user_session', api_id,
                                  api_hash) as user_client:  # создаст сессию с названием user_session
            print(await client.get_entity('me'))
            print('logged as client')
            logging.info('logged as client')
            target_username = '@BTC_CHANGE_BOT'
            target = await user_client.get_entity(target_username)
            await user_client.send_message(target, "/start c_" + code)

            @user_client.on(events.NewMessage())
            async def handler(event):
                try:
                    if event.message.peer_id.user_id == target.id:
                        mes = event.message.message
                        logging.info(f'BTC banker said:\n{mes}')
                        if mes in ['Упс, кажется, данный чек успел обналичить кто-то другой 😟',
                                   '⚠️ Упс!\n\nДанный чек уже обналичили. Все детали можете узнать у создателя чека.']:
                            # mes='Вы получили 0.00011858 BTC (149,95 RUB) от /uSexualGuillermoTheFourth!'
                            await client.send_message(username,
                                                      "**Ваш баланс не был пополнен, вы ввели не верный/актуальный чек!  ❌**")
                            await user_client.disconnect()
                            return "**Ваш баланс не был пополнен, вы ввели не верный/актуальный чек!  ❌**"
                        elif mes.startswith('Вы получили'):
                            if "/u" in mes and "BTC" in mes:
                                if "RUB" in mes:
                                    balance_append = float(
                                        mes[mes.find('(') + 1:mes.find(')')].replace(' RUB', '').replace(
                                            ',', '.'))
                                    cur.execute(f"SELECT * FROM CURRENT_DOMAIN WHERE USER_NAME = '{username}'")
                                    user_in_domain = cur.fetchone()
                                    cur.execute(
                                        f"UPDATE CURRENT_DOMAIN SET SPEND = '{int(user_in_domain[9]) + int(balance_append)}' WHERE USER_NAME = '{username}'")
                                    conn.commit()
                                    discount = 1
                                    logging.info('banker1')
                                    if user_in_domain[10] is not None:
                                        discount = (100 - user_in_domain[10]) / 100
                                    if (180 * discount) < balance_append < (200 * discount):
                                        check_time = 1
                                    elif (380 * discount) < balance_append < (420 * discount):
                                        check_time = 3
                                    elif (670 * discount) < balance_append < (730 * discount):
                                        check_time = 7
                                    elif (2800 * discount) < balance_append < (3000 * discount):
                                        check_time = 31
                                    else:
                                        await client.send_message(username,
                                                                  f'Сумма:{balance_append} неверная, обратитесь к @wollery')
                                        await user_client.disconnect()
                                        return
                                    cur.execute(f"SELECT * FROM {domain_zone}_USERS WHERE USERNAME = '{username}'")
                                    target_user = cur.fetchone()
                                    logging.info('banker2')
                                    if target_user is not None:
                                        saved_date = datetime.strptime(target_user[4], '%Y-%m-%d %H:%M:%S.%f')
                                        if saved_date > datetime.now():
                                            add_time = saved_date + timedelta(days=check_time)
                                        else:
                                            add_time = datetime.now() + timedelta(days=check_time)
                                        cur.execute(
                                            f"UPDATE {domain_zone}_USERS SET BILLING_DATETIME = '{add_time}' WHERE USERNAME = '{username}'")
                                        cur.execute(
                                            f"UPDATE CURRENT_DOMAIN SET DISCOUNT = NULL WHERE USER_NAME = '{username}'")
                                        conn.commit()
                                        logging.info('banker3')
                                        await client.send_message(
                                            "a_ndri_y",
                                            f"Було куплено підписку на суму {balance_append}"
                                        )
                                        await client.send_file(username, 'static/payed.jpg',
                                                               caption=f'**Вы успешно приобрели подписку !\n\nПодписка закончится :  {str(add_time)[:str(add_time).find(".")]}\n\nСтрана : {domain_zone}**',
                                                               parse_mode='md')
                                        print('+++++++++++++++++++++++++++++++')
                                        print(f'Юзеру {username} было зачисленно:{balance_append}')
                                        print('+++++++++++++++++++++++++++++++')
                                        logging.info('+++++++++++++++++++++++++++++++')
                                        logging.info(f'Юзеру {username} было зачисленно:{balance_append}')
                                        logging.info('+++++++++++++++++++++++++++++++')
                                        cur.execute(f"SELECT * FROM CURRENT_DOMAIN WHERE USER_NAME = '{username}'")
                                        target_user = cur.fetchone()
                                        referal_id = target_user[6]
                                        logging.info('banker4')
                                        if referal_id != 0:
                                            cur.execute(
                                                f"SELECT * FROM CURRENT_DOMAIN WHERE USER_ID = {referal_id}")
                                            referal = cur.fetchone()
                                            bonus = referal[7] + 1
                                            cur.execute(
                                                f"UPDATE CURRENT_DOMAIN SET BONUS = {bonus} WHERE USER_ID = {referal_id}")
                                            conn.commit()
                                            logging.info('banker5')
                                            await client.send_message(referal_id,
                                                                      f'Реферал @{username} принёс вам бонус')
                                        await user_client.disconnect()
                                    return f'вам зачисленно {balance_append}'
                                else:
                                    await client.send_message(username, "чек не в рублях, обращаться к @wollery")
                                    await user_client.disconnect()
                                    return "чек не в рублях, обращаться к @wollery"
                        elif mes.startswith('Приветствую,'):
                            pass
                except:
                    pass

            await user_client.run_until_disconnected()


    def get_time_delta(item_time):
        ret = datetime.strptime(item_time[0:19], '%Y-%m-%dT%H:%M:%S')
        if item_time[19] == '+':
            ret -= timedelta(hours=int(item_time[19:22]), minutes=int(item_time[23:]))
        elif item_time[19] == '-':
            ret += timedelta(hours=int(item_time[19:22]), minutes=int(item_time[23:]))
        ret += timedelta(hours=6)
        item_time_delta = datetime.strptime(f"{datetime.now():%Y-%m-%d %H:%M:%S}", '%Y-%m-%d %H:%M:%S') - ret
        if item_time_delta > timedelta(days=1):
            return str(item_time_delta)[:str(item_time_delta).find('day') - 1] + ' дней назад'
        elif item_time_delta > timedelta(hours=10):
            return str(item_time_delta)[:2] + ' часов назад'
        elif item_time_delta > timedelta(hours=1):
            return str(item_time_delta)[:1] + ' часов назад'
        else:
            returning_time = str(item_time_delta)[
                             str(item_time_delta).find(':') + 1:str(item_time_delta).find(':') + 3] + ' минут назад'
            if returning_time.startswith('0'):
                returning_time = returning_time[1:]
            return returning_time


    def construct_report(report_constructor, item, chat_link, show_times):
        final_string = ''
        second_string = '\n'
        third_string = '\n'
        if report_constructor is None or report_constructor[1] == 1:
            final_string += f"🗂 Товар: {item.item_title}"
        if report_constructor is None or report_constructor[2] == 1:
            final_string += f"\n💶 Цена: {item.item_price} {item.item_price_currency}"
        if report_constructor is None or report_constructor[3] == 1:
            final_string += f"\n📍 Местоположение товара: {item.location}"
        if report_constructor is None or report_constructor[4] == 1:
            final_string += f"\n📖 Описание:\n{item.description}"
        if report_constructor is None or report_constructor[5] == 1:
            second_string += f"\n👁 Кол-во просмотров товара: {item.item_view_count}"
        if report_constructor is None or report_constructor[6] == 1:
            second_string += f"\n🕒 Дата создания объявления: {item.item_time_delta}"
        if report_constructor is None or report_constructor[7] == 1:
            second_string += f"\n🔗 Ссылка на чат с продавцом: <a href='{chat_link}'>клик</a>"
        if report_constructor is None or report_constructor[8] == 1:
            second_string += f"\n🔗 Ссылка на товар: <a href='{item.item_url}'>клак</a>"
        if report_constructor is None or report_constructor[9] == 1:
            second_string += f"\n🔗 Ссылка на фото: <a href='{item.item_photo_url}'>пдыщь</a>"
        if second_string == '\n':
            second_string = ''
        if report_constructor is None or report_constructor[10] == 1:
            third_string += f"\n🤵‍♂️ Имя продавца: {item.profile_login}"
        if report_constructor is None or report_constructor[11] == 1:
            third_string += f"\n⭐️ Рейтинг продавца {item.profile_rating}/1"
        if report_constructor is None or report_constructor[12] == 1:
            third_string += f"\n🕒 Дата регистрации продавца: {item.profile_created_delta}"
        if report_constructor is None or report_constructor[13] == 1:
            third_string += f"\n📂 Кол-во объявлений продавца: {item.profile_item_count}"
        if report_constructor is None or report_constructor[14] == 1:
            third_string += f"\n📂 Кол-во проданных товаров продавца: {item.given_item_count}"
        if report_constructor is None or report_constructor[15] == 1:
            third_string += f"\n📂 Кол-во купленых товаров продавца: {item.taken_item_count}"
        if third_string == '\n':
            third_string = ''
        final_string += second_string
        final_string += third_string
        if report_constructor is None or report_constructor[16] == 1:
            final_string += f"\n\n👷‍♂️ Это объявление видело {show_times} пользователей парсера"
        return final_string


    async def pars_pages(domain_zone, count, search_full_text, user_id):
        global server_list
        # *START* Filtered count
        send_page_limit = 50
        unique_filter_count = 0
        rating_check_count = 0
        seller_date_limit_count = 0
        seller_items_limit_count = 0
        item_views_limit_count = 0
        item_date_limit_count = 0
        profile_feedback_filter_count = 0
        give_take_filter_count = 0
        country_filter_count = 0
        seller_filter_count = 0
        black_list_filter_count = 0
        unsend_messages_count = 0
        total_parsed_items_count = 0
        total_parsed_nice_count = 0
        item_list = []
        black_list = []
        final_list = []
        print(domain_zone)
        # if user_id != 895312150:
        #     return
        # if domain_zone == "CZ":
        #     return
        if domain_zone == "COUK":
            domain_zone = "CO.UK"
        cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {user_id}")
        report_constructor = cur.fetchone()
        cur.execute(f"SELECT DOMAIN_CHANGE FROM CURRENT_DOMAIN WHERE USER_ID = {user_id}")
        domain_to_check = cur.fetchone()
        domain_to_change = domain_zone
        if domain_to_check[0] is not None:
            domain_to_change = domain_to_check[0]
        domain_to_change = domain_to_change.lower()
        cur.execute(f"SELECT BLACK_WORD FROM BLACK_LIST WHERE USER_ID = {user_id}")
        swap_black_list = cur.fetchall()
        for swap_item in swap_black_list:
            black_list.append(swap_item[0])
        finish_string = 'Парсинг завершён'
        # *END* Filtered count
        # *START* Requesting catalog with parameters
        search_list = search_full_text.split(';')
        for search_text in search_list:
            search_text = search_text.strip()
            parsed_items_count = 0
            parsed_nice_count = 0
            while_iter = 1
            while parsed_nice_count < send_page_limit:
                if parsed_items_count >= 1000:
                    finish_string = f"Парсинг завершен по максимальному количеству просмотреных страниц: " \
                                    f"{parsed_items_count}"
                    break
                parsing_url = search_text_to_link(search_text, while_iter, domain_zone)
                if not parsing_url:
                    keyboard = create_region_keyboard()
                    await client.send_file(user_id, 'static/banner.jpg',
                                           caption='Выберите английский язык на сайте, сортировку товара и '
                                                   'повторите поиск по ссылке заново',
                                           buttons=keyboard)
                    return
                async with ClientSession() as s:
                    logging.info(f"User {user_id} | Searching {parsing_url}")
                    while True:
                        try:
                            print(parsing_url)
                            if parsing_url.lower().count("cz") != 0 or parsing_url.lower().count("sk") != 0:
                                server = random.choice(['http://195.189.226.99:8080', 'http://195.189.227.251:8080',
                                                        'http://195.189.226.114:8080'])
                            else:
                                server = random.choice(server_list)
                            print(f'{server}/search')
                            response = await s.post(f'{server}/search',
                                                    params=(('parsing_url', parsing_url),))
                            break
                        except asyncio.exceptions.TimeoutError:
                            pass
                        except Exception as e:
                            print(e)
                            time.sleep(10)
                    print(response.status)
                    response_text = await response.text()
                    try:
                        response_json = json.loads(response_text)
                    except JSONDecodeError:
                        logging.critical('=' * 30 + f'{user_id}' + 'error' + '=' * 30)
                        logging.critical(response_text)
                        logging.critical('=' * 30 + 'error' + '=' * 30)
                        continue
                if response_json['status'] == 200:
                    logging.info(f"User {user_id} | Got {len(response_json['data'])} items")
                    print(response_json)
                    if len(response_json['data']) == 0:
                        finish_string = "Больше ничего по вашему запросу не найдено:"
                        break
                else:
                    logging.critical(f'User {user_id} | Response status not 200:{response_json}')
                    continue
                new_items = []
                for item in response_json['data']:
                    new_item = ItemInfo(item['item_id'], item['item_title'], item['item_price'],
                                        item['item_price_currency'], item['item_url'], item['location'],
                                        item['country_iso_code'], item['item_view_count'], item['item_time_delta'],
                                        item['profile_created_delta'], item['profile_item_count'],
                                        item['profile_rating'], item['profile_feedbacks'], item['given_item_count'],
                                        item['taken_item_count'], item['profile_url'], item['profile_login'],
                                        item['description'], item['item_photo_url'])
                    new_items.append(new_item)
                    # print(new_item.item_id)
                    # print(new_item.item_title)
                    # print(new_item.item_url)
                while_iter += 1
                for item in new_items:
                    if item.item_id in item_list:
                        continue
                    else:
                        item_list.append(item.item_id)
                # *START* Getting user settings

                cur.execute(f"SELECT * FROM {domain_zone.replace('.', '')}_USERS WHERE USER_ID = {user_id}")
                telegram_user_data = cur.fetchone()
                stop_button = telegram_user_data[3]
                item_date_limit = telegram_user_data[5]
                unique_filter = telegram_user_data[6]
                rating_check = telegram_user_data[7]
                # seller_date_limit = telegram_user_data[8]
                seller_items_limit = telegram_user_data[9]
                item_views_limit = telegram_user_data[10]
                profile_feedback_filter = telegram_user_data[11]
                give_take_filter = telegram_user_data[12]
                country_filter = telegram_user_data[13]
                seller_filter = telegram_user_data[14]
                cur.execute(f"SELECT SELLER_ID FROM SELLER_FILTER_LIST WHERE USER_ID = {user_id}")
                seller_filter_list_wrong = cur.fetchall()
                seller_filter_list = []
                for seller_filter_item_wrong in seller_filter_list_wrong:
                    seller_filter_list.append(seller_filter_item_wrong[0])
                # print(seller_filter_list)
                # *END* Getting user settings
                # Sort items by id(same as sort by date)
                new_items.sort(key=lambda x: x.item_id, reverse=True)
                for item in new_items:
                    if parsed_nice_count > send_page_limit:
                        break
                    # *START* Checking parsing stop button
                    if stop_button == '0':
                        finish_string = 'Парсинг остановлен'
                        break
                    # *END* Checking parsing stop button
                    parsed_items_count += 1

                    # *START* Skipping page coz country_iso_code
                    if country_filter == 1:
                        if domain_zone == 'COM' and item.country_iso_code == 'US':
                            pass
                        if domain_zone == 'CO.UK':
                            if item.country_iso_code != domain_zone.split('.')[1]:
                                country_filter_count += 1
                                continue
                        elif item.country_iso_code != domain_zone:
                            # print('Пропущен товар по локации:')
                            # print(item.country_iso_code)
                            country_filter_count += 1
                            continue
                    # *START* Skipping page coz country_iso_code

                    # *START* Skipping page coz item_views
                    if item_views_limit != 0:
                        if int(item.item_view_count) > item_views_limit:
                            # print('Пропущен товар по количеству просмотров:')
                            # print(item.item_view_count)
                            item_views_limit_count += 1
                            continue
                    # *END*  Skipping page coz item_views

                    # *START* stoping parsing coz item created_at_ts
                    # print('======================')
                    # print(item.item_time_delta)
                    # print('======================')
                    if item.item_time_delta.find('дней') > 0:
                        # print(item.item_time_delta.find('дней'))
                        if item_date_limit < int(item.item_time_delta[:item.item_time_delta.find(' ')]):
                            # finish_string = f"Парсинг завершен по количеству дней: {item_date_limit}"
                            item_date_limit_count += 1
                            # break
                            continue
                    # *START* stoping parsing coz item created_at_ts

                    # *START* Skipping page coz profile created at
                    # if seller_date_limit != 0:
                    #     if item.profile_created_delta.find('дней') > 0:
                    #         if int(item.profile_created_delta[
                    #                :item.profile_created_delta.find(' ')]) > seller_date_limit:
                    #             # print('Пропущен продавец по дате создания аккаунта')
                    #             # print(item.profile_created_delta)
                    #             seller_date_limit_count += 1
                    #             continue
                    # *END* Skipping page coz profile created at

                    # *START* Skipping page coz profile items count
                    if seller_items_limit != 0 and item.profile_item_count > seller_items_limit:
                        # print('Пропущен продавец по количеству товаров')
                        # print(item.profile_item_count)
                        seller_items_limit_count += 1
                        continue
                    # *END* Skipping page coz profile created at

                    # *START* Skipping page coz rating
                    if rating_check == 1 and item.profile_rating != 0:
                        # print('Пропущен продавец c рейтином')
                        # print(item.profile_rating)
                        rating_check_count += 1
                        continue
                    # *END* Skipping page coz rating

                    # *START* Skipping page coz feedback
                    if item.profile_feedbacks > 0 and profile_feedback_filter == 1:
                        # print('Пропущен продавец c отзывами')
                        # print(item.profile_feedbacks)
                        profile_feedback_filter_count += 1
                        continue
                    # *END* Skipping page coz feedback

                    # *START* Skipping page coz Give\Take
                    if give_take_filter == 1:
                        if item.given_item_count > 0 or item.taken_item_count > 0:
                            give_take_filter_count += 1
                            # print(r'Пропущен продавец c покупками\продажами')
                            # print(f'{item.given_item_count} / {item.taken_item_count}')
                            continue
                    # *END* Skipping page coz Give\Take

                    # *START* Skipping page coz BLACKLIST
                    if black_list:
                        # logging.info(f'==============???=========')
                        # logging.info(f'{user_id}')
                        # logging.info(f'{black_list}')
                        # logging.info(f'{item.description.lower()}')
                        black_check = False
                        for black_word in black_list:
                            # logging.info(f'{black_word}')
                            if item.description.lower().find(black_word) > 0:
                                # logging.info(f'worked')
                                black_list_filter_count += 1
                                black_check = True
                                break
                        if black_check:
                            # print(item.description)
                            # logging.info('Пропущен по BL')
                            continue
                    # *END* Skipping page coz BLACKLIST

                    # *START* Skipping page coz seller filter
                    if seller_filter == 1:
                        seller_id = item.profile_url[
                                    item.profile_url.find('member/') + 7:item.profile_url.find('-')]
                        if seller_id in seller_filter_list:
                            seller_filter_count += 1
                            continue
                        else:
                            seller_filter_list.append(seller_id)
                            cur.execute(f"""INSERT INTO SELLER_FILTER_LIST(SELLER_ID, USER_ID)
                                VALUES('{seller_id}', {user_id})""")
                            conn.commit()
                    # *END* Skipping page coz  seller filter

                    # *START* Counting parser users saw this page
                    show_times = 0
                    cur.execute(f"SELECT * FROM ITEMS WHERE ITEM_ID = {item.item_id}")
                    items_result = cur.fetchone()
                    if items_result:
                        old_ids = items_result[2].split()
                        show_times = len(old_ids)
                        if unique_filter == 1:
                            unique_filter_count += 1
                            # print(r'Пропущено не уникальное по просмотрам в боте обьявление')
                            # print(old_ids)
                            continue
                        else:
                            if str(user_id) not in old_ids:
                                old_ids.append(str(user_id))
                                str_ids = (" ".join(old_ids)).strip()
                                cur.execute(
                                    f"UPDATE ITEMS SET USER_IDS = '{str_ids}' WHERE ITEM_ID = '{item.item_id}'")
                                conn.commit()
                            else:
                                show_times -= 1
                    else:
                        cur.execute(f"""INSERT INTO ITEMS(ITEM_ID, USER_IDS)
                            VALUES('{item.item_id}', '{str(user_id)}')""")
                        conn.commit()
                    # *END* Counting parser users saw this page

                    parsed_nice_count += 1
                    cur.execute(f"SELECT * FROM {domain_zone.replace('.', '')}_USERS WHERE USER_ID = {user_id}")
                    telegram_user_data = cur.fetchone()
                    stop_button = telegram_user_data[3]

                    item.item_url = change_domain(item.item_url, domain_to_change)
                    final_list.append(item)
                    chat_link = f"https://www.vinted.{domain_to_change}/member/signup?button_name=message&ch=wd&item_id={item.item_id}&receiver_id={item.profile_url[item.profile_url.find('member/') + 7: item.profile_url.find('-')]}&ref_url=%2Fitems%2F{item.item_id}%2Fwant_it%2Fnew%3Fbutton_name%3Dmessage%26ch%3Dwd&receiver_id%3D{item.profile_url[item.profile_url.find('member/') + 7:item.profile_url.find('-')]}"

                    caption = construct_report(report_constructor, item, chat_link, show_times)
                    try:
                        await client.send_file(user_id, item.item_photo_url,
                                               caption=f"{caption}", parse_mode='html')
                    except Exception as e:
                        print('Ошибка отправки сообщения')
                        logging.critical(f'Ошибка отправки сообщения|{e}')
                        logging.critical(f'{item.item_photo_url=}\n{caption=}')
                        logging.critical('====================================')
                        unsend_messages_count += 1
                if finish_string == 'Парсинг остановлен' or finish_string.startswith(
                        'Парсинг завершен по количеству дней'):
                    break
            if finish_string == 'Парсинг остановлен':
                break
        total_parsed_nice_count += parsed_nice_count
        total_parsed_items_count += parsed_items_count
        keyboard = create_region_keyboard()
        message = f'{finish_string}\nВсего проверенно обьявлений: {total_parsed_items_count}\nПрошло фильтры: {total_parsed_nice_count}\nПропущено по фльтрам \nНепросмотреные обьявления: {unique_filter_count}\nКоличество дней: {item_date_limit_count}\nРейтинг продавца: {rating_check_count} \nКоличество товаров продавца: {seller_items_limit_count} \nКоличество просмотров обьявления: {item_views_limit_count} \nОтзывы на продавца: {profile_feedback_filter_count} \nСделки продавца: {give_take_filter_count}\nФильтр стран: {country_filter_count}\nФильтр продавцов: {seller_filter_count}\nСписок запрещённых слов: {black_list_filter_count}'
        try:
            if report_constructor is not None and report_constructor[18] == 1:
                try:
                    if len(final_list) > 0:
                        create_xl_file(final_list, domain_to_change, user_id)
                        await client.send_file(user_id, f'swap/{user_id}.xlsx')
                except Exception as e:
                    print('?!' * 50)
                    print(e)
                    print('?!' * 50)
                    logging.info('?!' * 50)
                    logging.info('XL')
                    logging.info(final_list)
                    logging.info(e)
                    logging.info('?!' * 50)
            if report_constructor is not None and report_constructor[17] == 1:
                try:
                    if len(final_list) > 0:
                        create_txt_file(final_list, domain_zone.replace('.', ''), domain_to_change, user_id)
                        await client.send_file(user_id, f'swap/{user_id}.txt')
                except Exception as e:
                    print('?!' * 50)
                    print(e)
                    print('?!' * 50)
                    logging.info('?!' * 50)
                    logging.info('TXT')
                    logging.info(final_list)
                    logging.info(e)
                    logging.info('?!' * 50)
            await client.send_file(user_id, 'static/banner.jpg', caption=message, buttons=keyboard)
        except errors.rpcerrorlist.UserIsBlockedError:
            print(f'User {user_id} blocked the bot')
            logging.info(f'User {user_id} blocked the bot')
        print(finish_string)
        print(f'Прошло фильтры: {total_parsed_items_count}')
        print(f'Всего проверено страниц: {total_parsed_nice_count}')
        print(f'Пропущено по фльтрам')
        print(f'Непросмотреные обьявления: {unique_filter_count}')
        print(f'Рейтинг продавца: {rating_check_count}')
        # print(f'Дата регистрации продавца: {seller_date_limit_count}')
        print(f'Количество товаров продавца: {seller_items_limit_count}')
        print(f'Количество просмотров обьявления: {item_views_limit_count}')
        print(f'Отзывы на продавца: {profile_feedback_filter_count}')
        print(f'Сделки продавца: {give_take_filter_count}')
        print(f'Фильтр стран: {country_filter_count}')
        print(f'Фильтр продавцов: {seller_filter_count}')
        print(f'Blacklist : {black_list_filter_count}')
        print(f'Не дошло сообщений: {unsend_messages_count}')


    # Message based commands
    @client.on(events.NewMessage())
    async def handler(event):
        if event.message.message == '/start':
            user_id = event.message.peer_id.user_id
            if user_id in update_blacklist_dict(user_id):
                return
        sender = await event.get_sender()
        # print(event.message)
        print(f'User:{sender.id} \nsaid: {event.message.message}')
        logging.info(f'User:{sender.id} \nsaid: {event.message.message}')
        # Username checking
        if sender.username is None:
            await client.send_message(sender.id, "Для продолжения работы нужно настроить username")
            return
        else:
            # /start command
            if event.message.message.startswith('/start'):
                keyboard = create_region_keyboard()
                cur.execute(f"SELECT * FROM CURRENT_DOMAIN WHERE USER_ID = {sender.id}")
                current_domain_item = cur.fetchone()
                caption = ""
                if not current_domain_item:
                    if len(event.message.message) > 7:
                        try:
                            referal = int(event.message.message[7:])
                            await client.send_message(referal, f'У вас новый реферал @{sender.username}')
                        except:
                            await client.send_message(sender.username, 'Неверная реферальная ссылка')
                            referal = 0
                    else:
                        referal = 0
                    cur.execute(f"""INSERT INTO CURRENT_DOMAIN (USER_ID, USER_NAME, DOMAIN, REFERAL, BONUS, LAST_SEARCH)
                                    VALUES({sender.id}, '{sender.username}', '', {referal}, 0, NULL)""")
                    conn.commit()
                else:
                    if current_domain_item[11] is None:
                        join_buttons = []
                        for group_item in join_groups_list:
                            group_entity = await client.get_entity(group_item)
                            logging.info(group_entity)
                            join_buttons.append([Button.url(group_entity.title,
                                                            f'https://t.me/{group_entity.username}')])
                        join_buttons.append([Button.inline('Проверить вступление в группы',
                                                           b"check_join")])
                        await client.send_message(sender,
                                                  'Для использования бота, вам необходимо подписаться на наши каналы:',
                                                  buttons=join_buttons)
                        return
                    domain_zone = current_domain_item[3]
                    if event.message.message.startswith('/start pre'):
                        preset_string = event.message.message[10:]
                        if domain_zone:
                            print(preset_string)
                            cur.execute(f"SELECT * FROM CURRENT_DOMAIN WHERE USER_ID = {preset_string}")
                            target_current_domain = cur.fetchone()
                            if target_current_domain:
                                print(target_current_domain)
                                cur.execute(
                                    f"SELECT * FROM {target_current_domain[3]}_USERS WHERE USER_ID = {target_current_domain[1]}")
                                target_preset = cur.fetchone()
                                cur.execute(f"""UPDATE {domain_zone}_USERS SET 
                                ITEM_DATE_LIMIT = {target_preset[5]}, 
                                UNIQUE_FILTER = {target_preset[6]}, 
                                RATING_FILTER = {target_preset[7]},
                                SELLER_DATE_LIMIT = {target_preset[8]}, 
                                SELLER_ITEMS_LIMIT = {target_preset[9]}, 
                                ITEM_VIEWS_LIMIT = {target_preset[10]}, 
                                PROFILE_FEEDBACK_FILTER = {target_preset[11]}, 
                                GIVE_TAKE_FILTER = {target_preset[12]}, 
                                COUNTRY_FILTER = {target_preset[13]},
                                SELLER_FILTER = {target_preset[14]}
                                WHERE USER_ID = {sender.id}""")
                                conn.commit()
                                caption = "Пресет успешно импортирован"
                            else:
                                caption = "Неверная ссылка на пресет"
                            # cur.execute(f"SELECT * FROM {domain_zone}_USERS WHERE USER_ID = {sender.id}")
                            # TODO добавить капшн
                        else:
                            caption = "Сначала нужно выбрать регион"
                    if domain_zone != "":
                        cur.execute(f"SELECT * FROM {domain_zone}_USERS WHERE USER_ID = {sender.id}")
                        telegram_user_data = cur.fetchone()
                        if telegram_user_data[3] == '2':
                            cur.execute(
                                f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = '0' WHERE USER_ID = '{sender.id}'")
                            conn.commit()
                await client.send_file(sender.id, 'static/banner.jpg', caption=caption, buttons=keyboard)
                return
            # /admin command
            elif event.message.message == '/admin':
                if sender.id in admin_list:
                    keyboard = create_admin_keyboard()
                    await client.send_file(sender.id, 'static/banner.jpg', caption="Выберите действие",
                                           buttons=keyboard)
                else:
                    print('???????????????????????????????')
                    print(f'отказано в доступе в админку: {sender.id} {sender.username}')
                    print('???????????????????????????????')
                    logging.info('???????????????????????????????')
                    logging.info(f'отказано в доступе в админку: {sender.id} {sender.username}')
                    logging.info('???????????????????????????????')
                    for admin_id in admin_list:
                        await client.send_message(admin_id,
                                                  f'Юзер пытался войти в админку. Предлагаю выпороть\n id: {sender.id}\nusername: {sender.username}')
            # Settings command
            elif event.message.message == '⚙ Настройки':
                keyboard = await create_settings_keyboard(sender.id)
                if keyboard:
                    await client.send_file(sender.id, 'static/banner.jpg', caption="", buttons=keyboard)
            # Referal command
            elif event.message.message == '👫 Реферальная программа':
                cur.execute(
                    f"SELECT * FROM CURRENT_DOMAIN WHERE USER_ID = {sender.id}")
                bonus = cur.fetchone()[7]
                cur.execute(
                    f"SELECT * FROM CURRENT_DOMAIN WHERE REFERAL = {sender.id}")
                ref_list = cur.fetchall()
                if bonus > 0:
                    await client.send_file(sender.id, 'static/banner.jpg',
                                           caption=f"Количество рефералов: {len(ref_list)}\nУ вас есть реферальные бонусы: {bonus}\n\nВаша реферальная ссылка:\nhttps://t.me/{bot_username}?start={sender.id}",
                                           buttons=[[Button.inline('Потратить бонусы', b"SPEND_BONUS")]])
                else:
                    await client.send_file(sender.id, 'static/banner.jpg',
                                           caption=f"Количество рефералов: {len(ref_list)}\n\nВаша реферальная ссылка:\nhttps://t.me/{bot_username}?start={sender.id}")
                # SOS command
            elif event.message.message == '🆘 Помощь':
                keyboard = create_start_keyboard()
                await client.send_file(sender.id, 'static/banner.jpg',
                                       caption="Владелец бота : @wollery\nТех.поддержка : @wolleshop_support\nМагазин аккаунтов VINTED : @wolleshop_bot",
                                       buttons=keyboard)
            elif event.message.message == '🪙КУПИТЬ TRX(TRON)🪙':
                keyboard = create_start_keyboard()
                await client.send_file(sender.id, 'static/kurwa_jezhek.jpg',
                                       caption="""**🚀 Срочно нужен [TRX](https://t.me/KrustyExchangeBot?start=zCIxvkopP04q), но не знаешь где достать? Тогда тебе к нам:**

__✌️ Коротко о [@KrustyExchangeBot](https://t.me/KrustyExchangeBot?start=zCIxvkopP04q): Уникальная и эффективная конвертация финансов в [TRX](https://t.me/KrustyExchangeBot?start=zCIxvkopP04q). Возможность оплатить ЛЮБЫМ УДОБНЫМ способом. 

Работа обменного пункта 24/7, все происходит автоматически. Минимальное кол-во TRX [TRX](https://t.me/KrustyExchangeBot?start=zCIxvkopP04q) для покупки: 5.__

**😉 Сохрани бота [@KrustyExchangeBot](https://t.me/KrustyExchangeBot?start=zCIxvkopP04q), он тебе еще пригодится…**""",
                                       parse_mode="md", supports_streaming=True)
            elif event.message.message == 'SENDER SMS 🦧':
                keyboard = create_start_keyboard()
                await client.send_file(sender.id, 'static/хто прочитав той лох.jpg',
                                       caption="""**📲 Отправь смс мамонту в оригинальную папку сервиса - @AK_SMS_bot  


💵  Только в нашем боте вы сможете вернуть деньги за  смс

Наши преимущества:**
➡️ Самый высокий процент доставки✅
➡️ Отправка на большое количество стран✅
➡️ Самый удобный интерфейс ✅
➡️ Самые низкие цены✅
➡️Большое количество подключенных команд✅

😍Доступные страны на данный момент
🇩🇪🇨🇿🇸🇰🇭🇺🇫🇷🇪🇸🇸🇬🇵🇹🇵🇱 

👌По запросу добавим любую страну!

🤝Готовы к сотрудничеству и подключению по АPI

✅Запускай бота что бы не потерять **@AK_SMS_bot**""",
                                       buttons=keyboard)

            else:
                # Domen check
                cur.execute(f"SELECT * FROM CURRENT_DOMAIN WHERE USER_ID = {sender.id}")
                domain_zone = cur.fetchone()[3]
                if domain_zone == "":
                    await client.send_message(sender.id, 'Выберите доменную зону')
                    return
                # Stop parsing command
                if event.message.message == '🚫 Остановить парсинг':
                    cur.execute(
                        f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = '0' WHERE USER_ID = '{sender.id}'")
                    conn.commit()
                    keyboard = create_start_keyboard()
                    cur.execute(f"SELECT * FROM {domain_zone}_USERS WHERE USER_ID = '{sender.id}'")
                    telegram_user_data = cur.fetchone()
                    await client.send_message(sender.id,
                                              f"Парсинг доступен до {telegram_user_data[4][:telegram_user_data[4].find('.')]}\nВыберите действие",
                                              buttons=keyboard)
                # TRY PROMOCODE
                elif event.message.message == "🤫 Ввести промокод":
                    await client.send_message(sender.id,
                                              "Введите ваш промокод")
                    cur.execute(
                        f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = 'TRY_PROMO' WHERE USER_ID = '{sender.id}'")
                    conn.commit()
                # DB required commands
                else:
                    cur.execute(f"SELECT * FROM {domain_zone}_USERS WHERE USER_ID = {sender.id}")
                    telegram_user_data = cur.fetchone()
                    if telegram_user_data:
                        user_id = event.message.peer_id.user_id
                        # Start parsing command
                        if event.message.message == '🚀 Начать парсинг':
                            saved_date = datetime.strptime(telegram_user_data[4], '%Y-%m-%d %H:%M:%S.%f')
                            all_p = await get_user_ids_from_group(client)
                            if saved_date > datetime.now() or user_id in all_p:
                                cur.execute(
                                    f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = '1' WHERE USER_ID = '{sender.id}'")
                                conn.commit()
                                await client.send_message(sender.id, "Введите слово или ссылку с фильтрами для поиска")
                            else:
                                keyboard = create_payment_keyboard()
                                await client.send_message(sender.id, "Ваша подписка закончилась\nВыберите метод оплаты",
                                                          buttons=keyboard)
                        elif event.message.message == '🔁 Повторить парсинг':
                            cur.execute(f"SELECT LAST_SEARCH FROM CURRENT_DOMAIN WHERE USER_ID = {sender.id}")
                            last_search = cur.fetchone()[0]
                            if last_search is None:
                                keyboard = create_start_keyboard()
                                await client.send_message(sender.id, f"Вы парсите в первый раз", buttons=keyboard)
                                return
                            saved_date = datetime.strptime(telegram_user_data[4], '%Y-%m-%d %H:%M:%S.%f')
                            all_p = await get_user_ids_from_group(client)
                            if saved_date > datetime.now() or user_id in all_p:
                                cur.execute(
                                    f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = '2' WHERE USER_ID = '{sender.id}'")
                                conn.commit()
                                keyboard = [
                                    [
                                        Button.text('🚫 Остановить парсинг', single_use=True, resize=True)
                                    ]
                                ]
                                await client.send_message(sender.id, f"Повторяем последний парсинг:\n{last_search}")
                                await client.send_message(sender.id, "🔎", buttons=keyboard)
                                await pars_pages(domain_zone, 50, last_search, sender.id)
                            else:
                                keyboard = create_payment_keyboard()
                                await client.send_message(sender.id, "Ваша подписка закончилась\nВыберите метод оплаты",
                                                          buttons=keyboard)
                        # Pars the word
                        elif telegram_user_data[3] == '1':
                            cur.execute(
                                f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = '2' WHERE USER_ID = '{sender.id}'")
                            cur.execute(
                                f"UPDATE CURRENT_DOMAIN SET LAST_SEARCH = '{event.message.message}' WHERE USER_ID = '{sender.id}'")
                            conn.commit()
                            keyboard = [
                                [
                                    Button.text('🚫 Остановить парсинг', single_use=True, resize=True)
                                ]
                            ]
                            await client.send_message(sender.id, "🔎", buttons=keyboard)
                            await pars_pages(domain_zone, 50, event.message.message, sender.id)
                        # Try promo
                        elif telegram_user_data[3] == 'TRY_PROMO':
                            promocode = event.message.message
                            cur.execute(f"SELECT * FROM PROMO WHERE TEXT = '{promocode}'")
                            promo_to_check = cur.fetchone()
                            if promo_to_check is None:
                                await client.send_message(sender.id, 'Промокод введён неверно, попробуйте снова')
                                return
                            if promo_to_check[3] == 'TIME':
                                cur.execute(f"SELECT * FROM {domain_zone}_USERS WHERE USER_ID = '{sender.id}'")
                                target_user = cur.fetchone()
                                saved_date = datetime.strptime(target_user[4], '%Y-%m-%d %H:%M:%S.%f')
                                if saved_date > datetime.now():
                                    add_time = saved_date + timedelta(days=promo_to_check[2])
                                else:
                                    add_time = datetime.now() + timedelta(days=promo_to_check[2])
                                cur.execute(
                                    f"UPDATE {domain_zone}_USERS SET BILLING_DATETIME = '{add_time}' WHERE USER_ID = '{sender.id}'")
                                conn.commit()
                                answer_string = f'вам зачисленно {promo_to_check[2]} дней'
                            elif promo_to_check[3] == 'DISCOUNT':
                                cur.execute(
                                    f"UPDATE CURRENT_DOMAIN SET DISCOUNT = {promo_to_check[2]} WHERE USER_ID = '{sender.id}'")
                                conn.commit()
                                answer_string = f'у вас скидка {promo_to_check[2]}%'
                            await client.send_message(sender.id,
                                                      f'Промокод введён верно, {answer_string}')
                            cur.execute(f"DELETE FROM PROMO WHERE TEXT = '{promocode}'")
                            cur.execute(
                                f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = '0' WHERE USER_ID = '{sender.id}'")
                            conn.commit()
                        # GETTING_CHECK
                        elif telegram_user_data[3] == 'GETTING_CHECK':
                            cur.execute(
                                f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = '0' WHERE USER_ID = '{sender.id}'")
                            conn.commit()
                            if event.message.message.startswith('https://telegram.me/BTC_CHANGE_BOT?start'):
                                sender = await event.get_sender()
                                code = event.message.message[
                                       event.message.message.find('BTC_CHANGE_BOT?start=c_') + 23:]
                                await try_check(sender.username, code, domain_zone)
                            else:
                                keyboard = create_time_keyboard
                                await client.send_message(sender.id, 'Чек введён неверно, попробуйте снова',
                                                          buttons=keyboard)
                        # Admin's spam command
                        elif telegram_user_data[3] == 'SPAM':
                            if sender.id in admin_list:
                                message = event.message.message
                                users_db = []
                                for region in ['PL', 'FR', 'AT', 'CZ', 'BE', 'DE', 'IT', 'LT', 'LU', 'ES', 'SK', 'NL',
                                               'PT', 'COM', 'SE', ]:
                                    cur.execute(f"SELECT * FROM {region}_USERS")
                                    users_db_swap = cur.fetchall()
                                    for user_db in users_db_swap:
                                        users_db.append(user_db[1])
                                users_db = list(set(users_db))
                                print(users_db)
                                cur.execute(
                                    f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = '0' WHERE USER_ID = '{sender.id}'")
                                conn.commit()
                                for user_id in users_db:
                                    if user_id not in admin_list:
                                        try:
                                            try:
                                                if event.message.media.photo:
                                                    await client.send_file(user_id, event.message.media.photo,
                                                                           caption=message)
                                            except AttributeError:
                                                await client.send_message(user_id, message)
                                        except Exception as e:
                                            print(e)
                                await client.send_message(sender.id, 'Рассылка завершена')
                        # Admin's create discount promo command
                        elif telegram_user_data[3] == 'PROMO_DISCOUNT':
                            if sender.id in admin_list:
                                discount_str = event.message.message
                                if discount_str.isnumeric() and 0 < int(discount_str) < 100:
                                    while True:
                                        letters = string.ascii_letters
                                        promocode = ''.join(random.choice(letters) for i in range(10))
                                        cur.execute(f"SELECT * FROM PROMO WHERE TEXT = '{promocode}'")
                                        promo_to_check = cur.fetchone()
                                        if promo_to_check is None:
                                            break
                                        await asyncio.sleep(0.1)
                                    cur.execute(f"INSERT INTO PROMO (TEXT, VALUE , TYPE) "
                                                f"VALUES('{promocode}', {discount_str}, 'DISCOUNT')")
                                    conn.commit()
                                    cur.execute(
                                        f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = '0' WHERE USER_ID = '{sender.id}'")
                                    conn.commit()
                                    await client.send_message(sender.id,
                                                              f'Промокод на скидку {discount_str}%:\n{promocode}')
                                    return
                                await client.send_message(sender.id, 'Введите верный id')
                        # Admin's create time promo command
                        elif telegram_user_data[3] == 'PROMO_TIME':
                            if sender.id in admin_list:
                                discount_str = event.message.message
                                if discount_str.isnumeric() and 0 < int(discount_str):
                                    while True:
                                        letters = string.ascii_letters
                                        promocode = ''.join(random.choice(letters) for i in range(10))
                                        cur.execute(f"SELECT * FROM PROMO WHERE TEXT = '{promocode}'")
                                        promo_to_check = cur.fetchone()
                                        if promo_to_check is None:
                                            break
                                        await asyncio.sleep(0.1)
                                    cur.execute(f"INSERT INTO PROMO (TEXT, VALUE , TYPE) "
                                                f"VALUES('{promocode}', {discount_str}, 'TIME')")
                                    conn.commit()
                                    cur.execute(
                                        f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = '0' WHERE USER_ID = '{sender.id}'")
                                    conn.commit()
                                    await client.send_message(sender.id,
                                                              f'Промокод на {discount_str} бесплатный день:\n{promocode}')
                                    return
                                await client.send_message(sender.id, 'Введите верное колличество дней')
                        # Admin's check stats command
                        elif telegram_user_data[3] == 'STATS':
                            if sender.id in admin_list:
                                target_id = event.message.message
                                if target_id.isnumeric():
                                    cur.execute(f"SELECT * FROM CURRENT_DOMAIN WHERE USER_ID = {target_id}")
                                    target_user = cur.fetchone()
                                    if target_user is not None:
                                        active_subscriptions = '\nАктивные подписки:'
                                        for region in ['PL', 'FR', 'AT', 'CZ', 'BE', 'DE', 'IT', 'LT', 'LU', 'ES', 'SK',
                                                       'NL', 'PT', 'COM', 'SE', ]:
                                            cur.execute(f"SELECT * FROM {region}_USERS WHERE USER_ID = {target_id}")
                                            target_user_iter = cur.fetchone()
                                            if target_user_iter is None:
                                                continue
                                            target_time = datetime.strptime(target_user_iter[4], '%Y-%m-%d %H:%M:%S.%f')
                                            if target_time > datetime.now():
                                                active_subscriptions += f'\n{region} до {target_time.strftime("%m.%d.%Y")}'
                                        if active_subscriptions == '\nАктивные подписки:':
                                            active_subscriptions = '\nАктивных подписок нет'
                                        answer = f'@{target_user[2]}/{target_user[1]}\nПополнения: {target_user[9]}' \
                                                 f'{active_subscriptions}' \
                                                 f'\nБонусы по реферальной программе: {target_user[7]}'
                                        cur.execute(
                                            f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = '0' WHERE USER_ID = '{sender.id}'")
                                        conn.commit()
                                        await client.send_message(sender.id, answer)
                                    else:
                                        await client.send_message(sender.id, 'Пользователь не найден')
                                    return
                                await client.send_message(sender.id, 'Введите верный id')
                        # Admin's add time command
                        elif telegram_user_data[3] == 'ADD_TIME':
                            if sender.id in admin_list:
                                message = event.message.message
                                target_username = message[:message.find(' ')]
                                if message.find(' ') < 0:
                                    # print(123)
                                    # print(message.find(' '))
                                    await client.send_message(sender.id, "Данные введены неверно")
                                    return
                                cur.execute(f"SELECT * FROM {domain_zone}_USERS WHERE USERNAME = '{target_username}'")
                                target_user = cur.fetchone()
                                if target_user is not None:
                                    try:
                                        check_time = int(message[message.find(' ') + 1:])
                                        saved_date = datetime.strptime(target_user[4], '%Y-%m-%d %H:%M:%S.%f')
                                        if saved_date > datetime.now():
                                            add_time = saved_date + timedelta(days=check_time)
                                        else:
                                            add_time = datetime.now() + timedelta(days=check_time)
                                        cur.execute(
                                            f"UPDATE {domain_zone}_USERS SET BILLING_DATETIME = '{add_time}' WHERE USERNAME = '{target_username}'")
                                        conn.commit()
                                        cur.execute(
                                            f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = '0' WHERE USER_ID = '{sender.id}'")
                                        conn.commit()
                                        await client.send_message(sender.id,
                                                                  f"Юзеру {target_username} добавлено {message[message.find(' ') + 1:]} дней!")
                                        print('+++++++++++++++++++++++++++')
                                        print(f'Админ {sender.id}, добавил юзеру {target_user} {check_time} дней')
                                        print('+++++++++++++++++++++++++++')
                                        logging.info('+++++++++++++++++++++++++++')
                                        logging.info(
                                            f'Админ {sender.id}, добавил юзеру {target_user} {check_time} дней')
                                        logging.info('+++++++++++++++++++++++++++')
                                    except:
                                        await client.send_message(sender.id, "Количество дней ввердено неверно")
                                else:
                                    await client.send_message(sender.id,
                                                              f"Пользователя с таким username нет, попробуйте ещё раз")
                        # Admin's remove time command
                        elif telegram_user_data[3] == 'REMOVE_TIME':
                            cur.execute(f"SELECT * FROM {domain_zone}_USERS WHERE USERNAME = '{event.message.message}'")
                            target_user = cur.fetchone()
                            if target_user is not None:
                                cur.execute(
                                    f"UPDATE {domain_zone}_USERS SET BILLING_DATETIME = '{str(datetime.now())}' WHERE USERNAME = '{event.message.message}'")
                                conn.commit()
                                cur.execute(
                                    f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = '0' WHERE USER_ID = '{sender.id}'")
                                conn.commit()
                                await client.send_message(sender.id,
                                                          f"Оставшееся время юзера {event.message.message} обнулено")
                            else:
                                await client.send_message(sender.id,
                                                          f"Пользователя с таким username нет, попробуйте ещё раз")
                        # Text settings
                        elif telegram_user_data[3] in ['ITEM_DATE_LIMIT', 'SELLER_DATE_LIMIT', 'SELLER_ITEMS_LIMIT',
                                                       'ITEM_VIEWS_LIMIT']:
                            try:
                                mes = int(event.message.message)
                                if mes >= 0:
                                    cur.execute(
                                        f"UPDATE {domain_zone}_USERS SET {telegram_user_data[3]} = '{mes}' WHERE USER_ID = '{sender.id}'")
                                    cur.execute(
                                        f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = '0' WHERE USER_ID = '{sender.id}'")
                                    conn.commit()
                                    # Изменение ограничений даты публикации
                                    if telegram_user_data[3] == 'ITEM_DATE_LIMIT':
                                        limit_description = 'Установлено новое ограничение по дням: '
                                    # Изменение ограничений даты регистрации продавца
                                    elif telegram_user_data[3] == 'SELLER_DATE_LIMIT':
                                        limit_description = "Установлено новое ограничение по дате регистрации продавца: "
                                    # Изменение ограничений количества товаров продавца
                                    elif telegram_user_data[3] == 'SELLER_ITEMS_LIMIT':
                                        limit_description = "Установлено новое ограничение по количеству товаров: "
                                    # Изменение ограничений количества просмотров публикации
                                    elif telegram_user_data[3] == 'ITEM_VIEWS_LIMIT':
                                        limit_description = "Установлено новое ограничение по количеству просмотров товара: "
                                    await client.send_message(sender.id, limit_description + str(mes))
                                else:
                                    await client.send_message(sender.id, "Введите верное число!")
                            except:
                                await client.send_message(sender.id, "Введите верное число")
                        elif telegram_user_data[3] == 'DOMAIN_CHANGE':
                            if event.message.message != 'None':
                                cur.execute(
                                    f"UPDATE CURRENT_DOMAIN SET DOMAIN_CHANGE = '{event.message.message}' WHERE USER_ID = '{sender.id}'")
                            else:
                                cur.execute(
                                    f"UPDATE CURRENT_DOMAIN SET DOMAIN_CHANGE = NULL WHERE USER_ID = '{sender.id}'")
                            cur.execute(f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = '0' "
                                        f"WHERE USER_ID = '{sender.id}'")
                            conn.commit()
                            await client.send_message(sender.id, "Новый домен сохранён")
                        elif telegram_user_data[3] == 'BLACK_LIST':
                            new_black_list = event.message.message.split(',')
                            cur.execute(f"DELETE FROM BLACK_LIST WHERE USER_ID = {sender.id}")
                            conn.commit()
                            for black_word in new_black_list:
                                black_word.strip().lower()
                                cur.execute(f"INSERT INTO BLACK_LIST (USER_ID, BLACK_WORD) "
                                            f"VALUES({sender.id}, '{black_word}')")
                            cur.execute(f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = '0' "
                                        f"WHERE USER_ID = '{sender.id}'")
                            conn.commit()
                            await client.send_message(sender.id, "Новый список запрещённых слов успешно сохранён")


    # CallbackQuery commands
    @client.on(events.CallbackQuery())
    async def callback(event):
        print(f'User:{event.original_update.user_id} \nclicked: {event.data}')
        logging.info(f'User:{event.original_update.user_id} \nclicked: {event.data}')
        # Check user to join channels from join_groups_list
        if event.data == b"check_join":
            cur.execute(f"SELECT * FROM CURRENT_DOMAIN WHERE USER_ID = {event.original_update.user_id}")
            current_domain_item = cur.fetchone()
            if current_domain_item[11] is None:
                for group_item in join_groups_list:
                    group_entity = await client.get_entity(group_item)
                    sender = await event.get_sender()
                    print(sender)
                    print(group_entity)
                    if not await check_group_joined(client, group_entity, sender):
                        await client.send_message(sender, f'Вы не вступили в @{group_entity.username}')
                        return
                cur.execute(
                    f"UPDATE CURRENT_DOMAIN SET GROUP_CHECK = 1 WHERE USER_ID = '{event.original_update.user_id}'")
                conn.commit()
            await client.send_file(event.original_update.user_id, 'static/banner.jpg', caption="",
                                   buttons=create_region_keyboard())
        # Country's flag button clicked
        if event.data in [b"PL", b"FR", b"CZ", b"BE", b"IT", b"LT", b"ES", b"SK", b"PT", b"AT", b"DE", b"LU", b"NL",
                          b"COM", b"HU", b"COUK", b"SE", ]:
            domain_zone = event.data.decode('utf-8')
            sender = await client.get_entity(event.original_update.user_id)
            print(type(event.data))
            # запоминаем доменную зону
            if domain_zone == b"COUK":
                domain_zone = b"CO.UK"
            cur.execute(
                f"UPDATE CURRENT_DOMAIN SET DOMAIN = '{domain_zone}', USER_NAME = '{sender.username}' WHERE USER_ID = '{sender.id}'")
            conn.commit()
            #
            if domain_zone == b"CO.UK":
                domain_zone = b"COUK"
            cur.execute(f"SELECT * FROM {domain_zone}_USERS WHERE USER_ID = {sender.id}")
            telegram_user_data = cur.fetchone()
            if telegram_user_data is None:
                if sender.username is not None:
                    username = sender.username
                else:
                    await client.send_message(sender.id, "Для продолжения работы нужено настроить username")
                    return
                billing_datetime = datetime.now()
                cur.execute(f"""INSERT INTO {domain_zone}_USERS (USER_ID, USERNAME, CHATING_STATUS, BILLING_DATETIME, ITEM_DATE_LIMIT,
                                  UNIQUE_FILTER, RATING_FILTER, SELLER_DATE_LIMIT, SELLER_ITEMS_LIMIT, ITEM_VIEWS_LIMIT,
                                  PROFILE_FEEDBACK_FILTER, GIVE_TAKE_FILTER, COUNTRY_FILTER, SELLER_FILTER)
                                     VALUES({sender.id}, '{username}', '0', '{billing_datetime}', 
                                     5, 0, 0, 0, 0, 0, 0, 0, 0, 0)""")
                conn.commit()
                keyboard = create_payment_keyboard()
                await client.send_message(sender.id, "Ваша подписка закончилась\nВыберите метод оплаты",
                                          buttons=keyboard)
            else:
                cur.execute(f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = '0' WHERE USER_ID = '{sender.id}'")
                if sender.username is not None:
                    user_name = sender.username
                else:
                    await client.send_message(sender.id, "Для продолжения работы нужено настроить username")
                    return
                cur.execute(f"UPDATE {domain_zone}_USERS SET USERNAME = '{user_name}' WHERE USER_ID = '{sender.id}'")
                conn.commit()
                keyboard = create_start_keyboard()
                user_date = datetime.strptime(telegram_user_data[4], '%Y-%m-%d %H:%M:%S.%f')
                await client.edit_message(sender.id, event.original_update.msg_id, "", buttons=keyboard)
                print("all_p")
                all_p = await get_user_ids_from_group(client)
                print(all_p)
                if sender.id in all_p:
                    await client.send_message(sender.id,
                                              f"Парсинг доступен до {telegram_user_data[4][:telegram_user_data[4].find('.')]}\nВыберите действие",
                                              buttons=keyboard)
                elif user_date < datetime.now():
                    keyboard = create_payment_keyboard()
                    await client.send_message(sender.id, "Ваша подписка закончилась\nВыберите метод оплаты",
                                              buttons=keyboard)

                else:
                    await client.send_message(sender.id,
                                              f"Парсинг доступен до {telegram_user_data[4][:telegram_user_data[4].find('.')]}\nВыберите действие",
                                              buttons=keyboard)
        # Domen checking
        else:
            cur.execute(f"SELECT * FROM CURRENT_DOMAIN WHERE USER_ID = {event.original_update.user_id}")
            domain_zone = cur.fetchone()[3]
            if domain_zone == "":
                await client.send_message(event.original_update.user_id, 'Выберите доменную зону')
                return
        # 'ITEM_DATE_LIMIT' button clicked
        if event.data == b"ITEM_DATE_LIMIT":
            cur.execute(
                f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = 'ITEM_DATE_LIMIT' WHERE USER_ID = '{event.original_update.user_id}'")
            conn.commit()
            await client.send_message(event.original_update.user_id, "Укажите ограничение по дням:")
        # 'SELLER_ITEMS_LIMIT' button clicked
        elif event.data == b"SELLER_ITEMS_LIMIT":
            cur.execute(
                f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = 'SELLER_ITEMS_LIMIT' WHERE USER_ID = '{event.original_update.user_id}'")
            conn.commit()
            await client.send_message(event.original_update.user_id,
                                      "Укажите ограничение (0 что бы снять ограничение):")
        # 'SELLER_DATE_LIMIT' button clicked
        elif event.data == b"SELLER_DATE_LIMIT":
            cur.execute(
                f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = 'SELLER_DATE_LIMIT' WHERE USER_ID = '{event.original_update.user_id}'")
            conn.commit()
            await client.send_message(event.original_update.user_id,
                                      "Укажите ограничение (0 что бы снять ограничение):")
        # 'DOMAIN_CHANGE' button clicked
        elif event.data == b"DOMAIN_CHANGE":
            cur.execute(
                f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = 'DOMAIN_CHANGE' WHERE USER_ID = '{event.original_update.user_id}'")
            conn.commit()
            await client.send_message(event.original_update.user_id,
                                      "Укажите домен (None что бы обнулить настройку):")
        # 'ITEM_VIEWS_LIMIT' button clicked
        elif event.data == b"ITEM_VIEWS_LIMIT":
            cur.execute(
                f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = 'ITEM_VIEWS_LIMIT' WHERE USER_ID = '{event.original_update.user_id}'")
            conn.commit()
            await client.send_message(event.original_update.user_id,
                                      "Укажите ограничение (0 что бы снять ограничение):")
        # 'UNIQUE_FILTER' button clicked
        elif event.data == b"UNIQUE_FILTER":
            cur.execute(f"SELECT * FROM {domain_zone}_USERS WHERE USER_ID = {event.original_update.user_id}")
            telegram_user_data = cur.fetchone()
            if telegram_user_data[6] == 0:
                cur.execute(
                    f"UPDATE {domain_zone}_USERS SET UNIQUE_FILTER = 1 WHERE USER_ID = '{event.original_update.user_id}'")
                conn.commit()

            elif telegram_user_data[6] == 1:
                cur.execute(
                    f"UPDATE {domain_zone}_USERS SET UNIQUE_FILTER = 0 WHERE USER_ID = '{event.original_update.user_id}'")
                conn.commit()
            keyboard = await create_settings_keyboard(event.original_update.user_id)
            await client.edit_message(event.original_update.user_id, event.original_update.msg_id, buttons=keyboard)
        # 'RATING_FILTER' button clicked
        elif event.data == b"RATING_FILTER":
            cur.execute(f"SELECT * FROM {domain_zone}_USERS WHERE USER_ID = {event.original_update.user_id}")
            telegram_user_data = cur.fetchone()
            if telegram_user_data[7] == 0:
                cur.execute(
                    f"UPDATE {domain_zone}_USERS SET RATING_FILTER = 1 WHERE USER_ID = '{event.original_update.user_id}'")
                conn.commit()

            elif telegram_user_data[7] == 1:
                cur.execute(
                    f"UPDATE {domain_zone}_USERS SET RATING_FILTER = 0 WHERE USER_ID = '{event.original_update.user_id}'")
                conn.commit()
            keyboard = await create_settings_keyboard(event.original_update.user_id)
            await client.edit_message(event.original_update.user_id, event.original_update.msg_id, buttons=keyboard)
        # 'PROFILE_FEEDBACK_FILTER' button clicked
        elif event.data == b"PROFILE_FEEDBACK_FILTER":
            cur.execute(f"SELECT * FROM {domain_zone}_USERS WHERE USER_ID = {event.original_update.user_id}")
            telegram_user_data = cur.fetchone()
            if telegram_user_data[11] == 0:
                cur.execute(
                    f"UPDATE {domain_zone}_USERS SET PROFILE_FEEDBACK_FILTER = 1 WHERE USER_ID = '{event.original_update.user_id}'")
                conn.commit()
            elif telegram_user_data[11] == 1:
                cur.execute(
                    f"UPDATE {domain_zone}_USERS SET PROFILE_FEEDBACK_FILTER = 0 WHERE USER_ID = '{event.original_update.user_id}'")
                conn.commit()
            keyboard = await create_settings_keyboard(event.original_update.user_id)
            await client.edit_message(event.original_update.user_id, event.original_update.msg_id, buttons=keyboard)
        # 'GIVE_TAKE_FILTER' button clicked
        elif event.data == b"GIVE_TAKE_FILTER":
            cur.execute(f"SELECT * FROM {domain_zone}_USERS WHERE USER_ID = {event.original_update.user_id}")
            telegram_user_data = cur.fetchone()
            if telegram_user_data[12] == 0:
                cur.execute(
                    f"UPDATE {domain_zone}_USERS SET GIVE_TAKE_FILTER = 1 WHERE USER_ID = '{event.original_update.user_id}'")
                conn.commit()
            elif telegram_user_data[12] == 1:
                cur.execute(
                    f"UPDATE {domain_zone}_USERS SET GIVE_TAKE_FILTER = 0 WHERE USER_ID = '{event.original_update.user_id}'")
                conn.commit()
            keyboard = await create_settings_keyboard(event.original_update.user_id)
            await client.edit_message(event.original_update.user_id, event.original_update.msg_id, buttons=keyboard)
        # 'COUNTRY_FILTER' button clicked
        elif event.data == b"COUNTRY_FILTER":
            cur.execute(f"SELECT * FROM {domain_zone}_USERS WHERE USER_ID = {event.original_update.user_id}")
            telegram_user_data = cur.fetchone()
            if telegram_user_data[13] == 0:
                cur.execute(
                    f"UPDATE {domain_zone}_USERS SET COUNTRY_FILTER = 1 WHERE USER_ID = '{event.original_update.user_id}'")
                conn.commit()
            elif telegram_user_data[13] == 1:
                cur.execute(
                    f"UPDATE {domain_zone}_USERS SET COUNTRY_FILTER = 0 WHERE USER_ID = '{event.original_update.user_id}'")
                conn.commit()
            keyboard = await create_settings_keyboard(event.original_update.user_id)
            await client.edit_message(event.original_update.user_id, event.original_update.msg_id, buttons=keyboard)
        # 'COUNTRY_FILTER' button clicked
        elif event.data == b"SELLER_FILTER":
            cur.execute(f"SELECT * FROM {domain_zone}_USERS WHERE USER_ID = {event.original_update.user_id}")
            telegram_user_data = cur.fetchone()
            if telegram_user_data[14] == 0:
                cur.execute(
                    f"UPDATE {domain_zone}_USERS SET SELLER_FILTER = 1 WHERE USER_ID = '{event.original_update.user_id}'")
                conn.commit()
            elif telegram_user_data[14] == 1:
                cur.execute(
                    f"UPDATE {domain_zone}_USERS SET SELLER_FILTER = 0 WHERE USER_ID = '{event.original_update.user_id}'")
                conn.commit()
            keyboard = await create_settings_keyboard(event.original_update.user_id)
            await client.edit_message(event.original_update.user_id, event.original_update.msg_id, buttons=keyboard)
            # 'EXPORT_PRESET' button clicked
        elif event.data == b"BLACK_LIST":
            cur.execute(
                f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = 'BLACK_LIST' WHERE USER_ID = '{event.original_update.user_id}'")
            conn.commit()
            await client.send_message(event.original_update.user_id,
                                      f"Введите список запрещённых слов через запятую")
            # 'report_constructor' button clicked
        elif event.data == b"report_constructor":
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            if report_constructor is None:
                cur.execute(
                    f"""INSERT INTO report_constructor (t_id, title) VALUES('{event.original_update.user_id}', 1)""")
                conn.commit()
                cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
                report_constructor = cur.fetchone()
            keyboard = report_constructor_keyboard(report_constructor)
            await client.send_message(event.original_update.user_id,
                                      f"Текущие настройки конструктора:",
                                      buttons=keyboard)
        # 'constructor_title' button clicked
        elif event.data == b"constructor_title":
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            if report_constructor[1] == 0:
                cur.execute(
                    f"UPDATE report_constructor SET title = 1 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            elif report_constructor[1] == 1:
                cur.execute(
                    f"UPDATE report_constructor SET title = 0 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            keyboard = report_constructor_keyboard(report_constructor)
            await client.edit_message(event.original_update.user_id,
                                      event.original_update.msg_id,
                                      f"Текущие настройки конструктора:",
                                      buttons=keyboard)
        # 'constructor_price' button clicked
        elif event.data == b"constructor_price":
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            if report_constructor[2] == 0:
                cur.execute(
                    f"UPDATE report_constructor SET price = 1 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            elif report_constructor[2] == 1:
                cur.execute(
                    f"UPDATE report_constructor SET price = 0 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            keyboard = report_constructor_keyboard(report_constructor)
            await client.edit_message(event.original_update.user_id,
                                      event.original_update.msg_id,
                                      f"Текущие настройки конструктора:",
                                      buttons=keyboard)
        # 'constructor_location' button clicked
        elif event.data == b"constructor_location":
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            if report_constructor[3] == 0:
                cur.execute(
                    f"UPDATE report_constructor SET location = 1 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            elif report_constructor[3] == 1:
                cur.execute(
                    f"UPDATE report_constructor SET location = 0 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            keyboard = report_constructor_keyboard(report_constructor)
            await client.edit_message(event.original_update.user_id,
                                      event.original_update.msg_id,
                                      f"Текущие настройки конструктора:",
                                      buttons=keyboard)
        # 'constructor_description' button clicked
        elif event.data == b"constructor_description":
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            if report_constructor[4] == 0:
                cur.execute(
                    f"UPDATE report_constructor SET description = 1 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            elif report_constructor[4] == 1:
                cur.execute(
                    f"UPDATE report_constructor SET description = 0 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            keyboard = report_constructor_keyboard(report_constructor)
            await client.edit_message(event.original_update.user_id,
                                      event.original_update.msg_id,
                                      f"Текущие настройки конструктора:",
                                      buttons=keyboard)
        # 'constructor_description' button clicked
        elif event.data == b"constructor_views":
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            if report_constructor[5] == 0:
                cur.execute(
                    f"UPDATE report_constructor SET views = 1 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            elif report_constructor[5] == 1:
                cur.execute(
                    f"UPDATE report_constructor SET views = 0 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            keyboard = report_constructor_keyboard(report_constructor)
            await client.edit_message(event.original_update.user_id,
                                      event.original_update.msg_id,
                                      f"Текущие настройки конструктора:",
                                      buttons=keyboard)
        # 'constructor_date' button clicked
        elif event.data == b"constructor_date":
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            if report_constructor[6] == 0:
                cur.execute(
                    f"UPDATE report_constructor SET post_date = 1 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            elif report_constructor[6] == 1:
                cur.execute(
                    f"UPDATE report_constructor SET post_date = 0 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            keyboard = report_constructor_keyboard(report_constructor)
            await client.edit_message(event.original_update.user_id,
                                      event.original_update.msg_id,
                                      f"Текущие настройки конструктора:",
                                      buttons=keyboard)
        # 'constructor_chat' button clicked
        elif event.data == b"constructor_chat":
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            if report_constructor[7] == 0:
                cur.execute(
                    f"UPDATE report_constructor SET chat_link = 1 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            elif report_constructor[7] == 1:
                cur.execute(
                    f"UPDATE report_constructor SET chat_link = 0 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            keyboard = report_constructor_keyboard(report_constructor)
            await client.edit_message(event.original_update.user_id,
                                      event.original_update.msg_id,
                                      f"Текущие настройки конструктора:",
                                      buttons=keyboard)
        # 'constructor_link' button clicked
        elif event.data == b"constructor_link":
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            if report_constructor[8] == 0:
                cur.execute(
                    f"UPDATE report_constructor SET direct_link = 1 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            elif report_constructor[8] == 1:
                cur.execute(
                    f"UPDATE report_constructor SET direct_link = 0 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            keyboard = report_constructor_keyboard(report_constructor)
            await client.edit_message(event.original_update.user_id,
                                      event.original_update.msg_id,
                                      f"Текущие настройки конструктора:",
                                      buttons=keyboard)
        # 'constructor_photo' button clicked
        elif event.data == b"constructor_photo":
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            if report_constructor[9] == 0:
                cur.execute(
                    f"UPDATE report_constructor SET photo_link = 1 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            elif report_constructor[9] == 1:
                cur.execute(
                    f"UPDATE report_constructor SET photo_link = 0 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            keyboard = report_constructor_keyboard(report_constructor)
            await client.edit_message(event.original_update.user_id,
                                      event.original_update.msg_id,
                                      f"Текущие настройки конструктора:",
                                      buttons=keyboard)
        # 'constructor_seller' button clicked
        elif event.data == b"constructor_seller":
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            if report_constructor[10] == 0:
                cur.execute(
                    f"UPDATE report_constructor SET seller_username = 1 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            elif report_constructor[10] == 1:
                cur.execute(
                    f"UPDATE report_constructor SET seller_username = 0 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            keyboard = report_constructor_keyboard(report_constructor)
            await client.edit_message(event.original_update.user_id,
                                      event.original_update.msg_id,
                                      f"Текущие настройки конструктора:",
                                      buttons=keyboard)
        # 'constructor_rating' button clicked
        elif event.data == b"constructor_rating":
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            if report_constructor[11] == 0:
                cur.execute(
                    f"UPDATE report_constructor SET seller_rating = 1 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            elif report_constructor[11] == 1:
                cur.execute(
                    f"UPDATE report_constructor SET seller_rating = 0 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            keyboard = report_constructor_keyboard(report_constructor)
            await client.edit_message(event.original_update.user_id,
                                      event.original_update.msg_id,
                                      f"Текущие настройки конструктора:",
                                      buttons=keyboard)
        # 'constructor_registration' button clicked
        elif event.data == b"constructor_registration":
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            if report_constructor[12] == 0:
                cur.execute(
                    f"UPDATE report_constructor SET seller_date = 1 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            elif report_constructor[12] == 1:
                cur.execute(
                    f"UPDATE report_constructor SET seller_date = 0 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            keyboard = report_constructor_keyboard(report_constructor)
            await client.edit_message(event.original_update.user_id,
                                      event.original_update.msg_id,
                                      f"Текущие настройки конструктора:",
                                      buttons=keyboard)
        # 'constructor_posted' button clicked
        elif event.data == b"constructor_posted":
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            if report_constructor[13] == 0:
                cur.execute(
                    f"UPDATE report_constructor SET seller_posted = 1 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            elif report_constructor[13] == 1:
                cur.execute(
                    f"UPDATE report_constructor SET seller_posted = 0 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            keyboard = report_constructor_keyboard(report_constructor)
            await client.edit_message(event.original_update.user_id,
                                      event.original_update.msg_id,
                                      f"Текущие настройки конструктора:",
                                      buttons=keyboard)
        # 'constructor_sold' button clicked
        elif event.data == b"constructor_sold":
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            if report_constructor[14] == 0:
                cur.execute(
                    f"UPDATE report_constructor SET seller_sold = 1 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            elif report_constructor[14] == 1:
                cur.execute(
                    f"UPDATE report_constructor SET seller_sold = 0 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            keyboard = report_constructor_keyboard(report_constructor)
            await client.edit_message(event.original_update.user_id,
                                      event.original_update.msg_id,
                                      f"Текущие настройки конструктора:",
                                      buttons=keyboard)
        # 'constructor_bought' button clicked
        elif event.data == b"constructor_bought":
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            if report_constructor[15] == 0:
                cur.execute(
                    f"UPDATE report_constructor SET seller_bought = 1 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            elif report_constructor[15] == 1:
                cur.execute(
                    f"UPDATE report_constructor SET seller_bought = 0 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            keyboard = report_constructor_keyboard(report_constructor)
            await client.edit_message(event.original_update.user_id,
                                      event.original_update.msg_id,
                                      f"Текущие настройки конструктора:",
                                      buttons=keyboard)
        # 'constructor_views_c' button clicked
        elif event.data == b"constructor_views_c":
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            if report_constructor[16] == 0:
                cur.execute(
                    f"UPDATE report_constructor SET parser_views_count = 1 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            elif report_constructor[16] == 1:
                cur.execute(
                    f"UPDATE report_constructor SET parser_views_count = 0 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            keyboard = report_constructor_keyboard(report_constructor)
            await client.edit_message(event.original_update.user_id,
                                      event.original_update.msg_id,
                                      f"Текущие настройки конструктора:",
                                      buttons=keyboard)
        # 'constructor_txt_links' button clicked
        elif event.data == b"constructor_txt_link":
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            if report_constructor[17] == 0:
                cur.execute(
                    f"UPDATE report_constructor SET txt_link = 1 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            elif report_constructor[17] == 1:
                cur.execute(
                    f"UPDATE report_constructor SET txt_link = 0 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            keyboard = report_constructor_keyboard(report_constructor)
            await client.edit_message(event.original_update.user_id,
                                      event.original_update.msg_id,
                                      f"Текущие настройки конструктора:",
                                      buttons=keyboard)
        # 'constructor_excel' button clicked
        elif event.data == b"constructor_excel":
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            if report_constructor[18] == 0:
                cur.execute(
                    f"UPDATE report_constructor SET excel = 1 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            elif report_constructor[18] == 1:
                cur.execute(
                    f"UPDATE report_constructor SET excel = 0 WHERE t_id = {event.original_update.user_id}")
                conn.commit()
            cur.execute(f"SELECT * FROM report_constructor WHERE t_id = {event.original_update.user_id}")
            report_constructor = cur.fetchone()
            keyboard = report_constructor_keyboard(report_constructor)
            await client.edit_message(event.original_update.user_id,
                                      event.original_update.msg_id,
                                      f"Текущие настройки конструктора:",
                                      buttons=keyboard)
        # 'EXPORT_PRESET' button clicked
        elif event.data == b"EXPORT_PRESET":
            await client.send_message(event.original_update.user_id,
                                      f"Ваш пресет:\nhttps://t.me/{bot_username}?start=pre{event.original_update.user_id}")
        # Spend bonus button clicked
        elif event.data == b"SPEND_BONUS":
            keyboard = create_referal_region_keyboard()
            await client.send_message(event.original_update.user_id, 'Выберите на какой сайт зачислить бонусы',
                                      buttons=keyboard)
        elif event.data in [b"R_PL", b"R_FR", b"R_CZ", b"R_BE", b"R_IT", b"R_LT", b"R_ES", b"R_SK", b"R_PT", b"R_AT",
                            b"R_DE", b"R_LU", b"R_NL", b"R_COM", b"R_HU", b"R_SE", ]:
            domain_zone = event.data.decode('utf-8')
            domain_zone = domain_zone[2:]
            cur.execute(
                f"SELECT * FROM CURRENT_DOMAIN WHERE USER_ID = {event.original_update.user_id}")
            bonus = cur.fetchone()[7]
            if bonus > 0:
                cur.execute(f"SELECT * FROM {domain_zone}_USERS WHERE USER_ID = {event.original_update.user_id}")
                target_user = cur.fetchone()
                saved_date = datetime.strptime(target_user[4], '%Y-%m-%d %H:%M:%S.%f')
                if saved_date > datetime.now():
                    add_time = saved_date + timedelta(days=bonus)
                else:
                    add_time = datetime.now() + timedelta(days=bonus)
                cur.execute(
                    f"UPDATE CURRENT_DOMAIN SET BONUS = 0 WHERE USER_ID = {event.original_update.user_id}")
                cur.execute(
                    f"UPDATE {domain_zone}_USERS SET BILLING_DATETIME = '{add_time}' WHERE USER_ID = {event.original_update.user_id}")
                conn.commit()
                await client.send_message(event.original_update.user_id,
                                          f"Вам зачислено {bonus} дней, для сайта '{domain_zone}'")
        # Payment methods button clicked
        elif event.data == b"PAYOK":
            keyboard = create_payok_time_keyboard()
            await client.send_message(event.original_update.user_id, "Метод оплаты: Crypto Cloud", buttons=keyboard)
        elif event.data == b"crypto_bot":
            keyboard = create_crypto_bot_currency_keyboard()
            await client.send_message(event.original_update.user_id, "Метод оплаты: Crypto Bot", buttons=keyboard)
        elif event.data == b"BTC_BANKIR":
            keyboard = create_time_keyboard()
            await client.send_message(event.original_update.user_id, "Метод оплаты: BTC_BANKIR", buttons=keyboard)
        # Buy time button clicked
        elif event.data in [b"BTC", b"TON", b"ETH", b"USDT", b"USDC"]:
            cur.execute(
                f"UPDATE CURRENT_DOMAIN SET currency = '{event.data.decode('utf-8')}' WHERE USER_ID = {event.original_update.user_id}")
            conn.commit()
            keyboard = create_crypto_bot_time_keyboard()
            await client.send_message(event.original_update.user_id,
                                      f"Метод оплаты: Crypto Bot\nВалюта: {event.data.decode('utf-8')}",
                                      buttons=keyboard)
        elif event.data in [b"BUY_TIME1_", b"BUY_TIME3_", b"BUY_TIME7_", b"BUY_TIME31_"]:
            bites_decode = event.data.decode('utf-8')
            time_chosen = int(bites_decode[8:][:-1])
            # Discount
            discount = 1
            cur.execute(f"SELECT * FROM CURRENT_DOMAIN WHERE USER_ID = {event.original_update.user_id}")
            user_in_domain = cur.fetchone()
            if user_in_domain[10] is not None:
                discount = (100 - user_in_domain[10]) / 100
            if time_chosen == 1:
                price = int(190 * discount)
            elif time_chosen == 3:
                price = int(400 * discount)
            elif time_chosen == 7:
                price = int(700 * discount)
            elif time_chosen == 31:
                price = int(2900 * discount)
            pay_url, invoice_id = await crypto_pay_create_invoice(user_in_domain[13], price)
            cur.execute(
                f"UPDATE CURRENT_DOMAIN SET UUID = '{invoice_id}',DAYS={time_chosen} WHERE USER_ID = '{event.original_update.user_id}'")
            conn.commit()
            message = f'''👉 Метод оплаты: Crypto Bot\n👉 Время подписки: {time_chosen} дня\n👉 Цена: {price} RUB\n👉 Площадка: VINTED.{domain_zone}\n\nПроверьте данные покупки, если все верно оплатите по ссылке:\n\n{pay_url}'''
            await client.send_message(event.original_update.user_id, message,
                                      buttons=[[Button.inline('Я оплатил', b"PAYMENT_DONE_")]])
        elif event.data == b"PAYMENT_DONE_":
            cur.execute(f"SELECT * FROM CURRENT_DOMAIN WHERE USER_ID = {event.original_update.user_id}")
            telegram_user_data = cur.fetchone()
            uuid = telegram_user_data[4]
            check_time = telegram_user_data[5]
            if await crypto_pay_check_invoice(uuid):
                cur.execute(
                    f"SELECT * FROM {domain_zone}_USERS WHERE USER_ID = '{event.original_update.user_id}'")
                target_user = cur.fetchone()
                if target_user is not None:
                    saved_date = datetime.strptime(target_user[4], '%Y-%m-%d %H:%M:%S.%f')
                    if saved_date > datetime.now():
                        add_time = saved_date + timedelta(days=check_time)
                    else:
                        add_time = datetime.now() + timedelta(days=check_time)
                    cur.execute(
                        f"UPDATE {domain_zone}_USERS SET BILLING_DATETIME = '{add_time}' WHERE USER_ID = '{event.original_update.user_id}'")
                    cur.execute(
                        f"UPDATE CURRENT_DOMAIN SET UUID = '', DAYS = 0, DISCOUNT = NULL WHERE USER_ID = '{event.original_update.user_id}'")
                    conn.commit()
                    sender = await client.get_entity(event.original_update.user_id)
                    username = sender.username
                    await client.send_message(
                        "a_ndri_y",
                        f"Було куплено підписку на {check_time} днів"
                    )
                    print('+++++++++++++++++++++++++++++++')
                    print(f'Юзер {username} провёл оплату за {check_time} дней Crypto Bot')
                    print('+++++++++++++++++++++++++++++++')
                    logging.info('+++++++++++++++++++++++++++++++')
                    logging.info(f'Юзер {username} провёл оплату за {check_time} дней Crypto Bot')
                    logging.info('+++++++++++++++++++++++++++++++')
                    add_time = str(add_time)
                    await client.send_file(event.original_update.user_id, 'static/payed.jpg',
                                           caption=f'**Вы успешно приобрели подписку !\n\nПодписка закончится :  {add_time[:add_time.find(".")]}\n\nСтрана : {domain_zone}**',
                                           parse_mode='md')
                    cur.execute(
                        f"SELECT * FROM CURRENT_DOMAIN WHERE USER_ID = {event.original_update.user_id}")
                    referal_id = cur.fetchone()[6]
                    if referal_id != 0:
                        cur.execute(
                            f"SELECT * FROM CURRENT_DOMAIN WHERE USER_ID = {referal_id}")
                        referal = cur.fetchone()
                        bonus = referal[7] + 1
                        cur.execute(
                            f"UPDATE CURRENT_DOMAIN SET BONUS = {bonus} WHERE USER_ID = {referal_id}")
                        conn.commit()
                        await client.send_message(referal_id, f'Реферал @{username} принёс вам бонус')
            else:
                await client.send_message(event.original_update.user_id,
                                          'Оплата ещё не получена, перейдите по ссылке')
        elif event.data in [b"BUY_TIME_1", b"BUY_TIME_3", b"BUY_TIME_7", b"BUY_TIME_31"]:
            bites_decode = event.data.decode('utf-8')
            time_chosen = int(bites_decode[9:])
            # Discount
            discount = 1
            cur.execute(f"SELECT * FROM CURRENT_DOMAIN WHERE USER_ID = {event.original_update.user_id}")
            user_in_domain = cur.fetchone()
            if user_in_domain[10] is not None:
                discount = (100 - user_in_domain[10]) / 100
            if time_chosen == 1:
                price = int(190 * discount)
            elif time_chosen == 3:
                price = int(400 * discount)
            elif time_chosen == 7:
                price = int(700 * discount)
            elif time_chosen == 31:
                price = int(2900 * discount)
            params = (
                ('shop_id', crypto_cloud_shop_id),
                ('currency', 'RUB'),
                ('amount', price),
            )
            headers = {
                "Authorization": f"Token {crypto_cloud_api_key}",
            }
            async with ClientSession(headers=headers) as s:
                req = await s.post('https://api.cryptocloud.plus/v1/invoice/create', data=params)
                page_content = await req.read()
                page_content = page_content.decode('utf-8')
                page_json = json.loads(await req.text())
            cur.execute(
                f"UPDATE CURRENT_DOMAIN SET UUID = '{page_json['invoice_id']}',DAYS={time_chosen} WHERE USER_ID = '{event.original_update.user_id}'")
            conn.commit()
            message = f'''👉 Метод оплаты: CryptoCloud\n👉 Время подписки: {time_chosen} дня\n👉 Цена: {price} RUB\n👉 Площадка: VINTED.{domain_zone}\n\nПроверьте данные покупки, если все верно оплатите по ссылке:\n\n{page_json['pay_url']}'''
            await client.send_message(event.original_update.user_id, message,
                                      buttons=[[Button.inline('Я оплатил', b"PAYMENT_DONE")]])

        elif event.data == b"PAYMENT_DONE":
            headers = {
                "Authorization": f"Token {crypto_cloud_api_key}",
            }
            cur.execute(f"SELECT * FROM CURRENT_DOMAIN WHERE USER_ID = {event.original_update.user_id}")
            telegram_user_data = cur.fetchone()
            uuid = telegram_user_data[4]
            check_time = telegram_user_data[5]
            async with ClientSession(headers=headers) as s:
                req = await s.get(f"https://api.cryptocloud.plus/v1/invoice/info?uuid=INV-{uuid}")
                page_json = json.loads(await req.text())
                if page_json['status'] == "success":
                    if page_json['status_invoice'] == "created":
                        await client.send_message(event.original_update.user_id,
                                                  'Оплата ещё не получена, перейдите по ссылке')
                    elif page_json['status_invoice'] == "paid":
                        cur.execute(
                            f"SELECT * FROM {domain_zone}_USERS WHERE USER_ID = '{event.original_update.user_id}'")
                        target_user = cur.fetchone()
                        if target_user is not None:
                            saved_date = datetime.strptime(target_user[4], '%Y-%m-%d %H:%M:%S.%f')
                            if saved_date > datetime.now():
                                add_time = saved_date + timedelta(days=check_time)
                            else:
                                add_time = datetime.now() + timedelta(days=check_time)
                            await client.send_message(
                                "a_ndri_y",
                                f"Було куплено підписку на суму {check_time} днів"
                            )
                            cur.execute(
                                f"UPDATE {domain_zone}_USERS SET BILLING_DATETIME = '{add_time}' WHERE USER_ID = '{event.original_update.user_id}'")
                            cur.execute(
                                f"UPDATE CURRENT_DOMAIN SET UUID = '', DAYS = 0, DISCOUNT = NULL WHERE USER_ID = '{event.original_update.user_id}'")
                            conn.commit()
                            sender = await client.get_entity(event.original_update.user_id)
                            username = sender.username
                            print('+++++++++++++++++++++++++++++++')
                            print(f'Юзер {username} провёл оплату за {check_time} дней')
                            print('+++++++++++++++++++++++++++++++')
                            logging.info('+++++++++++++++++++++++++++++++')
                            logging.info(f'Юзер {username} провёл оплату за {check_time} дней')
                            logging.info('+++++++++++++++++++++++++++++++')
                            add_time = str(add_time)
                            await client.send_file(event.original_update.user_id, 'static/payed.jpg',
                                                   caption=f'**Вы успешно приобрели подписку !\n\nПодписка закончится :  {add_time[:add_time.find(".")]}\n\nСтрана : {domain_zone}**',
                                                   parse_mode='md')
                            cur.execute(
                                f"SELECT * FROM CURRENT_DOMAIN WHERE USER_ID = {event.original_update.user_id}")
                            referal_id = cur.fetchone()[6]
                            if referal_id != 0:
                                cur.execute(
                                    f"SELECT * FROM CURRENT_DOMAIN WHERE USER_ID = {referal_id}")
                                referal = cur.fetchone()
                                bonus = referal[7] + 1
                                cur.execute(
                                    f"UPDATE CURRENT_DOMAIN SET BONUS = {bonus} WHERE USER_ID = {referal_id}")
                                conn.commit()
                                await client.send_message(referal_id, f'Реферал @{username} принёс вам бонус')
                    elif page_json['status_invoice'] == "canceled":
                        await client.send_message(event.original_update.user_id, 'Чек отменён')
                elif page_json['status'] == "error":
                    await client.send_message(event.original_update.user_id, 'Ошибка')

                    print('???????????????????????????????????????????????????????')
                    print(page_json['error'])
                    sender = await client.get_entity(event.original_update.user_id)
                    username = sender.username
                    print(username)
                    print('???????????????????????????????????????????????????????')
                    logging.info('???????????????????????????????????????????????????????')
                    logging.info(page_json['error'])
                    logging.info(username)
                    logging.info('???????????????????????????????????????????????????????')

        # Buy time button clicked

        elif event.data in [b"BUY_TIME1", b"BUY_TIME3", b"BUY_TIME7", b"BUY_TIME31"]:
            bites_decode = event.data.decode('utf-8')
            time_chosen = int(bites_decode[8:])
            # Discount
            discount = 1
            cur.execute(f"SELECT * FROM CURRENT_DOMAIN WHERE USER_ID = {event.original_update.user_id}")
            user_in_domain = cur.fetchone()
            if user_in_domain[10] is not None:
                discount = (100 - user_in_domain[10]) / 100
            if time_chosen == 1:
                price = 190 * discount
            elif time_chosen == 3:
                price = 400 * discount
            elif time_chosen == 7:
                price = 700 * discount
            elif time_chosen == 31:
                price = 2900 * discount
            message = f'''👉 Метод оплаты: BTC_BANKIR
👉 Время подписки: {time_chosen} дня
👉 Цена: {int(price)} RUB
👉 Площадка: VINTED.{domain_zone}

Обязательно поставьте курс BINANCE, иначе могут быть проблемы!!!
Проверьте данные покупки, если все верно отправьте чек на сумму {price} RUB'''
            cur.execute(
                f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = 'GETTING_CHECK' WHERE USER_ID = '{event.original_update.user_id}'")
            conn.commit()
            await client.send_message(event.original_update.user_id, message)
        # Admin's finctions
        if event.original_update.user_id in admin_list:
            if event.data == b"PARSER_USERS_COUNT":
                cur.execute("SELECT * FROM CURRENT_DOMAIN")
                users_db = cur.fetchall()
                keyboard = create_admin_keyboard()
                await client.send_message(event.original_update.user_id,
                                          f'Количество юзеров бота: {str(len(users_db))}', buttons=keyboard)
            elif event.data == b"SPAM":
                await client.send_message(event.original_update.user_id, "Введите содержимое рассылки")
                cur.execute(
                    f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = 'SPAM' WHERE USER_ID = '{event.original_update.user_id}'")
                conn.commit()
            elif event.data == b"STATS":
                await client.send_message(event.original_update.user_id, "Введите id пользователя")
                cur.execute(
                    f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = 'STATS' WHERE USER_ID = '{event.original_update.user_id}'")
                conn.commit()
            elif event.data == b"PROMO":
                await client.send_message(event.original_update.user_id, "Выберите тип промокода",
                                          buttons=[[Button.inline('Скидка', b"PROMO_DISCOUNT")],
                                                   [Button.inline('Подписка', b"PROMO_TIME")]])
            elif event.data == b"PROMO_TIME":
                await client.send_message(event.original_update.user_id,
                                          "Введите количество дней в промокоде")
                cur.execute(
                    f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = 'PROMO_TIME' WHERE USER_ID = '{event.original_update.user_id}'")
                conn.commit()
            elif event.data == b"PROMO_DISCOUNT":
                await client.send_message(event.original_update.user_id,
                                          "Введите % скидки в промокоде")
                cur.execute(
                    f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = 'PROMO_DISCOUNT' WHERE USER_ID = '{event.original_update.user_id}'")
                conn.commit()
            elif event.data == b"ADMIN_REGION":
                keyboard = create_admin_region_keyboard()
                await client.send_message(event.original_update.user_id,
                                          "Выберите регион", buttons=keyboard)
            elif event.data == b"ADD_TIME":
                await client.send_message(event.original_update.user_id,
                                          "Введите username(с учётом регистра) и количество дней, через пробел")
                cur.execute(
                    f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = 'ADD_TIME' WHERE USER_ID = '{event.original_update.user_id}'")
                conn.commit()
            elif event.data == b"REMOVE_TIME":
                await client.send_message(event.original_update.user_id, "Введите username(с учётом регистра)")
                cur.execute(
                    f"UPDATE {domain_zone}_USERS SET CHATING_STATUS = 'REMOVE_TIME' WHERE USER_ID = '{event.original_update.user_id}'")
                conn.commit()
            if event.data in [b"A_PL", b"A_FR", b"A_CZ", b"A_BE", b"A_IT", b"A_LT", b"A_ES", b"A_SK", b"A_PT", b"A_AT",
                              b"A_DE", b"A_LU", b"A_NL", b"A_COM", b"A_HU", b"A_COUK", b"A_SE", ]:
                domain_zone = event.data.decode('utf-8')[2:]
                sender = await client.get_entity(event.original_update.user_id)
                cur.execute(f"SELECT * FROM {domain_zone}_USERS WHERE USER_ID = {sender.id}")
                telegram_user_data = cur.fetchone()
                if telegram_user_data is None:
                    billing_datetime = datetime.now()
                    cur.execute(f"""INSERT INTO {domain_zone}_USERS (USER_ID, USERNAME, CHATING_STATUS, 
                    BILLING_DATETIME, ITEM_DATE_LIMIT, UNIQUE_FILTER, RATING_FILTER, SELLER_DATE_LIMIT, 
                    SELLER_ITEMS_LIMIT, ITEM_VIEWS_LIMIT, PROFILE_FEEDBACK_FILTER, GIVE_TAKE_FILTER, COUNTRY_FILTER, SELLER_FILTER) 
                    VALUES({sender.id}, '{sender.username}', '0', '{billing_datetime}', 5, 0, 0, 0, 0, 0, 0, 0, 0, 0)""")
                    conn.commit()
                cur.execute(
                    f"UPDATE CURRENT_DOMAIN SET DOMAIN = '{domain_zone}' WHERE USER_ID = '{sender.id}'")
                conn.commit()
                await client.send_message(event.original_update.user_id, "Выберите действие",
                                          buttons=[[Button.inline('Дать подписку', b"ADD_TIME")],
                                                   [Button.inline('Забрать подписку', b"REMOVE_TIME")]])


    client.run_until_disconnected()
