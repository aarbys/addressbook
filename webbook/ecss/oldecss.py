#!/usr/bin/env python3

from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
import urllib.parse
import os.path
import time

from .logger import log
from . import webbook
from confdb import config
from .errors import error_sender


class Server:
    def __init__(self, urls: list):
        self.path = r"C:\VSCODEaaa\father_work\trying_django\djsite\webbook\ecss"
        # Пустые значения, для полноты инициализации
        self.cache = None
        # Переброс в класс ссылки, которые дадут нам данные о пользователях
        self.urls = urls

        # Загрузка Головы сайта.
        log.info('Load header...')
        headerFile = self.path + r'\www\header.html'
        # os.path.join(config.get('www', 'static_location'), 'header.html')
        self.HEADER = webbook.read_template(headerFile)

        # Подгрузка ног сайта
        log.info('Load footer...')
        footerFile = self.path + r'\www\footer.html'
        # os.path.join(config.get('www', 'static_location'), 'footer.html')
        self.FOOTER = webbook.read_template(footerFile)

        # Время обновление сайта
        self.cache_expire_time = time.time() - 1
        # Обновление сайта
        self.update_site()

    # Функции для создания головы и ног сайта
    def page_header(self, errorinfo=None, info=None, history=None):
        fmt_params = dict()
        fmt_params['errorinfo'] = '' if errorinfo is None else errorinfo
        fmt_params['info'] = self.info if info is None else info
        fmt_params['history'] = '' if history is None else history
        return bytes(self.HEADER.format(**fmt_params), 'UTF-8')

    def page_footer(self):
        return bytes(self.FOOTER, 'UTF-8')

    # Функция для фильтрации страницы
    def phone_table_filtered(self, term, page):
        term = term.lower()
        newcache = list()
        for phone, name, email, server in self.cache:
            if phone.lower().find(term) >= 0 \
                    or name.lower().find(term) >= 0 \
                    or email.lower().find(term) >= 0 \
                    or server.lower().find(term) >= 0:
                newcache.append(tuple([phone, name, email, server]))
        nav = webbook.create_next_prev_links(newcache, term, page)
        webpage = nav + webbook.create_phone_table(newcache, page) + nav
        return bytes(webpage, 'UTF-8')

    # Функция обновления сайта
    def update_site(self):
        if self.cache_expire_time < time.time():

            # db = webbook.DataBaseWorker()
            # db.create_clear_table()
            # db.create_database_python(self.urls)
            # xmlbook = db.get_data_from_db()
            xmlbook = ''
            for i in range(len(self.urls)):
                xmlbook += create_xml_book(self.urls[i], i, len(self.urls))

            self.cache = xmlbook
            self.cache_expire_time = time.time()
            self.cache_expire_time += config.getint('book', 'cache_expire_sec')

    def get_cache(self):
        self.update_site()
        cache = self.HEADER + self.cache + self.FOOTER
        return cache

    def phone_table(self, page):
        nav = webbook.create_next_prev_links(self.cache, '', page)
        webpage = nav + webbook.create_phone_table(self.cache, page) + nav
        return bytes(webpage, 'UTF-8')


class ABServer(HTTPServer):
    def __init__(self, *args):
        super().__init__(*args)
        self.info = config.get('www', 'info')

        log.info('Load header...')
        headerFile = os.path.join(config.get('www', 'static_location'), 'header.html')
        self.HEADER = webbook.read_template(headerFile)

        log.info('Load footer...')
        footerFile = os.path.join(config.get('www', 'static_location'), 'footer.html')
        self.FOOTER = webbook.read_template(footerFile)

        log.info('Make address book cache...')
        # -1 on next line for guarantee first time update cache
        self.cache_expire_time = time.time() - 1
        self.update_cache_if_need()

    def page_header(self, errorinfo=None, info=None, history=None):
        fmt_params = dict()
        fmt_params['errorinfo'] = '' if errorinfo is None else errorinfo
        fmt_params['info'] = self.info if info is None else info
        fmt_params['history'] = '' if history is None else history
        return bytes(self.HEADER.format(**fmt_params), 'UTF-8')

    def page_footer(self):
        return bytes(self.FOOTER, 'UTF-8')

    def phone_table(self, page):
        nav = webbook.create_next_prev_links(self.cache, '', page)
        webpage = nav + webbook.create_phone_table(self.cache, page) + nav
        return bytes(webpage, 'UTF-8')
        # ~ return bytes(webbook.create_phone_table(self.cache, page), 'UTF-8')

    def phone_table_filtered(self, term, page):
        term = term.lower()
        newcache = list()
        for phone, name, email, server in self.cache:
            if phone.lower().find(term) >= 0 \
                    or name.lower().find(term) >= 0 \
                    or email.lower().find(term) >= 0 \
                    or server.lower().find(term) >= 0:
                newcache.append(tuple([phone, name, email, server]))
        nav = webbook.create_next_prev_links(newcache, term, page)
        webpage = nav + webbook.create_phone_table(newcache, page) + nav
        return bytes(webpage, 'UTF-8')
        # ~ return bytes(webbook.create_phone_table(newcache, page), 'UTF-8')

    def update_cache_if_need(self):
        if self.cache_expire_time < time.time():
            data = config.get('book', 'uri').split("aboba")
            db = webbook.DataBaseWorker()
            db.create_clear_table()
            db.create_database_python(data)

            # for i in range(1, len(data)):
            #     xmlbook += create_xml_book(data[i], i, len(data))

            xmlbook = db.get_data_from_db()

            self.cache = webbook.create_book_cache(xmlbook)
            self.cache_expire_time = time.time()
            self.cache_expire_time += config.getint('book', 'cache_expire_sec')


class ABRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.server.update_cache_if_need()

        parameters = self.get_params()

        filter_param = parameters.get('filter')
        if filter_param is None:
            filter_param = ''
        else:
            filter_param = webbook.cast(filter_param[0], str, '')

        page_param = parameters.get('page')
        if page_param is None:
            page_param = 1
        else:
            page_param = webbook.cast(page_param[0], int, 1)
        if page_param == 0:
            page_param = 1

        if filter_param != '':
            self.send_filtered_table(filter_param, page_param)
        else:
            self.send_table(page_param)

    def send_200(self):
        # ~ self.send_response(200) # This also logging every request in console
        self.send_response_only(200)  # Do not logging every request
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def send_table(self, page=0):
        self.send_200()
        self.wfile.write(self.server.page_header())
        self.wfile.write(self.server.phone_table(page))
        self.wfile.write(self.server.page_footer())

    def send_filtered_table(self, term=None, page=0):
        self.send_200()
        self.wfile.write(self.server.page_header(history=term))
        self.wfile.write(self.server.phone_table_filtered(term, page))
        self.wfile.write(self.server.page_footer())

    def get_params(self):
        query = urllib.parse.urlparse(self.path).query
        return urllib.parse.parse_qs(query)


def create_xml_book(URI: "Url address", ind: int, max_len: int):
    xmlbook = webbook.download_book(URI)

    if ind == 0:
        xmlbook = xmlbook.decode("utf-8").replace("</EcssWebBookContactList>\n", "")
    elif ind == max_len - 1:
        xmlbook = xmlbook.decode("utf-8").replace("<EcssWebBookContactList>\n", "")
    else:
        xmlbook = xmlbook.decode("utf-8").replace("<EcssWebBookContactList>\n", "")
        xmlbook = xmlbook.replace("</EcssWebBookContactList>\n", "")

    return xmlbook

if __name__ == "__main__":
    hostport = (config.get('proxy', 'address'), config.getint('proxy', 'port'))
    webServer = ABServer(hostport, ABRequestHandler)
    log.info("Start server at http://%s:%s" % hostport)

    try:
        webServer.serve_forever()
    except Exception as e:
        webbook.error_sender(str(e))

    # try:
    #     webServer.serve_forever()
    # except KeyboardInterrupt:
    #     pass

    webServer.server_close()
    log.info("Server stopped.")
