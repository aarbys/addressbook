#!/usr/bin/env python3

import time

from .logger import log
from . import webbook
from .confdb import config
from .errors import error_sender
from .models import Person
import os
from pprint import pprint


# phone
# Name
# email
# server
# Role


class Server:

    # Необходимо переписать инициализацию класса иначе выходит какое-то дерьмо.
    def __init__(self, urls: list, names: list):

        # Основное это номер телефона, а не имена

        # Пустые значения, для инициализации
        self.sort_by = "Inside"
        self.subdiv = ''
        self.org = ''
        self.cache = None
        self.history = None
        self.errors = None
        self.phones = None

        # Информация о сайте для пользователя
        self.info = config.get('www', 'info').encode("utf-8").decode('utf-8')

        self.path = os.path.dirname(os.path.abspath(__file__))
        # Переброс в класс ссылки, которые дадут нам данные о пользователях
        self.urls = urls
        self.names = names
        # Загрузка Головы сайта.
        log.info('Load header...')
        headerFile = os.path.join(self.path,"www","header.html")
        print(f"Header is {headerFile}")
        # os.path.join(config.get('www', 'static_location'), 'header.html')
        self.HEADER = webbook.read_template(headerFile)

        # Подгрузка ног сайта
        log.info('Load footer...')
        footerFile = os.path.join(self.path,"www","footer.html")
        # os.path.join(config.get('www', 'static_location'), 'footer.html')
        self.FOOTER = webbook.read_template(footerFile)

        log.info('Updating info...')

    # Функция для информации с сайта и о сайте
    def get_info_about_site(self):
        info = self.info
        history = self.history
        org = self.org

        sort_by = self.sort_by
        subdiv = self.subdiv

        return info, history, org, subdiv, sort_by

    # Функция для фильтрации страницы
    def phone_table_filtered(self, terms):
        new_cache = list()
        for term in terms:
            if term == 'all' or term is None:
                terms[terms.index(term)] = ''
        if all(term == '' for term in terms):
            return self.cache
        for phone, name, email, server, role in self.cache:
            person = [phone.lower(), name.lower(), email.lower(), server.lower(), role.lower()]
            for term in terms:
                if term == '':
                    continue
                if any(term.lower() in field for field in person):
                    new_cache.append((phone, name, email, server, role))
        if any(a != '' for a in terms):
            self.cache = new_cache

        return

        # Вероятно можно оптимизировать

    # Функция обновления данных для сайта
    def update_site_from_database(self):
        self.cache = list()
        for pers in Person.objects.all():
            self.cache.append(tuple([
                str(pers.Inside),
                pers.Name,
                pers.Email,
                pers.Corporation,
                pers.Role
            ]))
        # return self.cache

    # Обновление кеша приложения с разных БД
    def update_site_from_different_servers(self):
        log.info('Creating xml book...')
        self.cache = []
        for i in range(len(self.urls)):
            # xmlbook = create_xml_book(self.urls[i], i, len(self.urls))
            xml_book = create_xml_book(self.urls[i])
            log.info(f'XML-book created {i + 1} times...')
            self.cache += webbook.create_book_cache(self.names[i], xml_book)

        # self.delete_unusable_phones()
        self.update_site_from_database()

    # Для функции удаления номеров телефонов
    def create_field_inside_phones(self):
        self.phones = [item['Inside'] for item in Person.objects.values('Inside')]

    def get_cache(self):
        return self.cache

    # def clear_cache(self):
    #     self.cache = []

    # DEBUG part
    def get_history(self):
        return self.history

    def update_server_data(self, history=None, org=None, subdiv=None, sort_by=None):
        self.history = self.history if history is None else history
        self.org = self.org if org is None else org
        self.sort_by = self.sort_by if sort_by is None else sort_by
        self.subdiv = self.subdiv if subdiv is None else subdiv

    # Информация об отделах компании. Бухгалтерия, грузчики и т.д.
    @staticmethod
    def get_list_of_organizations():
        menu = set(item['Corporation'] for item in Person.objects.values('Corporation'))
        return menu

    # Функция очистки пользователей, которые уволились или были уволены.

    def delete_unusable_phones(self):
        self.create_field_inside_phones()
        delete_list = []
        for person in Person.objects.all():
            if person.Inside not in self.phones:
                delete_list.append(person)
        for person in delete_list:
            person.delete()

        self.phones = None

    # phone - Inside
    # Name
    # email
    # server - Corporation
    # Role

    # Сортировка данных в БД, чтобы удобно вытаскивать данные с неё
    def quick_sort(self, order_by):
        self.cache = list()
        for pers in Person.objects.order_by(order_by).all():
            self.cache.append(tuple([
                str(pers.Inside),
                pers.Name,
                pers.Email,
                pers.Corporation,
                pers.Role
            ]))
        self.phone_table_filtered([self.history, self.org, self.subdiv])


def create_xml_book(uri: "Url address"):
    xmlbook = webbook.download_book(uri)
    return xmlbook.decode("utf-8")


class DatabaseWorker:
    def __init__(self):
        pass
