import math

import xml.etree.ElementTree as ET

from .logger import log
from .confdb import config
import sys
import urllib.error as urlerror
import urllib.request as urlrequest
from .errors import error_sender
import codecs
from .models import Person


def phone_as_human(phone=None):
    phone_length = len(phone)
    if phone is None:
        return ''

    if phone_length < 5:
        return phone

    if 5 <= phone_length < 10:
        pairs = list()
        while len(phone) > 0:
            pairs.append(phone[-3:])
            phone = phone[:-3]

    if phone_length >= 10:
        pairs = list()
        pairs.append(phone[-4:])
        phone = phone[:-4]
        while len(phone) > 0:
            pairs.append(phone[-3:])
            phone = phone[:-3]

    return '-'.join(reversed(pairs)).strip('-')


# ~ tnumber = '123456789012345678910'
# ~ tnumber = '1234567890abcdefghijk'
# ~ for i in range(len(tnumber)+1):
# ~ element = str(tnumber)[0:i]
# ~ print(f'{element:24s} {phone_as_human(element)}')


def download_book(bookURI):
    try:
        response = urlrequest.urlopen(bookURI)
    except urlerror.HTTPError as e:
        error_sender(str(e))
        # log.error("Cannot download book, HTML error code %d: '%s'", e.code, e.msg)
        # ~ sys.stderr.write(f'{e.code} {e.msg}\n')
        sys.exit(1)

    return response.read()


def read_template(fname):
    try:
        with codecs.open(fname, 'r', "utf-8") as fp:
            template = fp.read()
    except OSError as e:
        log.error(e)
        raise

    return ' '.join(template.split())  # squeeze spaces and remove newlines


def create_phone_table(cache=None, page=1, line_counter=20):
    persons = list()

    offset = (page - 1) * line_counter

    for person in cache[offset:]:
        persons.append(person)
        line_counter -= 1
        if line_counter == 0:
            break
    return persons


def create_next_prev_links(cache, page):
    line_counter = config.getint('book', 'show_lines')
    page_amount = math.ceil(len(cache) / line_counter)
    if page % page_amount == 0:
        page = page_amount
    else:
        page = page % page_amount

    return page, page_amount


def create_book_cache(data_base: str, xmlbook=None):
    book = ET.fromstring(xmlbook)
    book_cache = list()
    MAGIC_TAG = 'EcssWebBookContactList'
    if book.tag == MAGIC_TAG:
        CONTACT_ENTRY_TAG = 'Contact'
        PHONE_ENTRY_XPATH = './Phone'
        NAME_ENTRY_XPATH = './Name'
        EMAIL_ENTRY_XPATH = './Email'
        SERVER_ENTRY_XPATH = './Server'
    else:
        CONTACT_ENTRY_TAG = 'DirectoryEntry'
        PHONE_ENTRY_XPATH = './Telephone'
        NAME_ENTRY_XPATH = './Name'
        EMAIL_ENTRY_XPATH = './Mail'
        SERVER_ENTRY_XPATH = './Server'

    from time import time
    abs_time = 0
    # Надо оптимизировать этот цикл, 4 секунды для 1 БД занимает
    for entry in book:
        if entry.tag != CONTACT_ENTRY_TAG:
            continue

        name = entry.find(NAME_ENTRY_XPATH)
        phone = entry.find(PHONE_ENTRY_XPATH)
        email = entry.find(EMAIL_ENTRY_XPATH)
        if name is None or phone is None:  # or server is None
            # skip broken entries
            continue

        if email is None:
            # email may not be present in common template so make fake element
            email = ET.Element('email')

        user = [str(phone.text or ''),  # Внутренний номер
                str(name.text or ''),  # Имя
                str(email.text or 'none'),  # Эл.почта
                f"{data_base}",  # Корпорация
                "none",  # Роль в орге
                "none",  # Подразделение
                "0"]  # Внешний номер
        # ,str(server.text or ''), str(role or "")
        t = time()
        save_for_db(user)
        abs_time += time() - t
        book_cache.append(tuple(user))

    print(f"abs time is {abs_time}")
    return book_cache


def cast(val, conv_type, default=None):
    try:
        return conv_type(val)
    except (ValueError, TypeError):
        return default


#
def save_for_db(user):
    data = {
        "Inside": int(user[0]),
        "Name": user[1],
        "Email": user[2],
        "Corporation": user[3],
        "Role": user[4],
        "Subdivision": user[5],
        "Outside": int(user[6])}
    try:
        Person.objects.update_or_create(Inside=int(user[0]), Corporation=data["Corporation"], defaults=data)
    except Exception as e:
        print(f"Some problems. Error: {e}")


