import cProfile
import logging

from django.shortcuts import render
from .EcssWebBook import Server
from .confdb import config, urls, names
from .webbook import create_phone_table, create_next_prev_links
from django.views.decorators.csrf import csrf_exempt
from time import time
from .models import Person
from django.http import JsonResponse
import os
DEBUG = True

# Create your views here.
server = Server(urls, names)

# Просто посмотреть какие у нас ссылки есть, попробовать их самостоятельно использовать
for p in urls:
    print(p)
info, history, org, subdiv, sort_by = None, None, None, None, 'fio'
last_update = time()

role = config.get("www", "role")
menu = server.get_list_of_organizations()


@csrf_exempt
def page(request, pagenum: int):
    print("Заход на страницу тута\n\n\n\n\n\n")
    global server, info, history, org, subdiv, sort_by, last_update, role, menu

    # 86400 - сутки
    if DEBUG or (time() - last_update) < 0:
        server.update_site_from_database()
    else:
        server.update_site_from_different_servers()
        last_update = time()

    # Сортировка по фамилиям и т.д. на странице
    # if split_request(request, pagenum) == 1:
    #     pagenum = 1

    if sort_by:
        sort_page_data(sort_by)
    # Сбор данных с БД и серверов
    cache = server.get_cache()
    nextpage, page_amount = create_next_prev_links(cache=cache, page=pagenum)

    # Создание таблицы пользователей
    persons = create_phone_table(page=pagenum, cache=cache)

    # Болванка простая
    html_page = os.path.join(os.path.dirname(os.path.abspath(__file__)), "www", "header.html")
    return render(request, html_page, {
        "Role": role,
        "menu": menu,
        "persons": persons,
        "info": info,
        "history": '' if history is None else history,
        "page": pagenum,
        "nextpage": nextpage,
        "page_amount": page_amount,
        "selected": '' if org is None else org,
        "sort_by": sort_by,
        "subdiv": subdiv,
        "elements_amount": int(config.get("book", "show_lines")),
        "elements_variable": [5, 10, 15, 20, 25, 30, 35],
    })


# Функция для обновления сайта, в ней идет распределение запроса от пользователя
# Сбор данных с БД на разных устройствах и обновление на главном аппарате.
def split_request(request, pagenum):
    global server, info, history, org, subdiv, sort_by
    if request.POST.get("Find"):
        handle_post_find_request(request)
        pagenum = 1

    elif request.POST.get("clear"):
        pagenum = 1
        server.update_server_data()
        info, history, org, subdiv, sort_by = server.get_info_about_site()
        server.update_site_from_database()

    else:
        if pagenum != 1:
            info, history, org, subdiv, sort_by = server.get_info_about_site()
        data = [history, org, subdiv]
        if any(pr_var is not None for pr_var in data):
            server.phone_table_filtered(data)

        else:
            server.update_site_from_database()

    return pagenum


# Быстрая сортировка данных на странице, сортировка происходит на стороне БД
# Уже не оптимизировать!!!
def sort_page_data(sort_by):
    global server
    try:
        server.quick_sort(get_index_to_sort(sort_by))
    except Exception as e:
        print(f"server quick sort unreal!!! Error: {e}")


def get_index_to_sort(sort_by):
    data = {
        "fio": "Name",
        "subdivision": "Subdivision",
        "inside": "Inside",
        "outside": "Outside",
        "corporation": "Corporation"
    }
    return data[sort_by.lower()]


# Обработка POST запроса с поиском каким-либо
# Функция создана для разбиения блоков кода.
def handle_post_find_request(request):
    global server, info, history, org, subdiv, sort_by
    sort_by = request.POST.get('sorting_type')
    history = request.POST.get('filter', '')
    subdiv = '' if request.POST.get('subdivision') == "all" else request.POST.get('subdivision')
    org = '' if request.POST.get('organizations') == "all" else request.POST.get('organizations')

    try:
        if (info, history, org, subdiv, sort_by) != server.get_info_about_site():
            server.update_server_data(history, org, subdiv, sort_by)

        if history != '' or org != '' or subdiv != '':
            server.phone_table_filtered([history, org, subdiv])

        else:
            server.update_site_from_database()
            server.quick_sort(get_index_to_sort(sort_by))

    except AttributeError as e:
        info, history, org, subdiv, sort_by = server.get_info_about_site()
        server.update_site_from_database()
        logging.error(str(e))


def create_table_ajax(persons):
    table = ['<tr>'
             '<th class="table-head-left">ФИО</th>'
             '<th class="table-head">Подразделение</th>'
             '<th class="table-head">Внутренний</th>'
             '<th class="table-head">Внешний</th>'
             '<th class="table-head-right">Корпоративный</th>'
             '</tr>']
    for phone, name, email, ss, role in persons:
        table.append('<tr>'
                     f'<td class="fill">{name}</td>'
                     f'<td class="fill">{ss}</td>'
                     f'<td class="fill">{phone}</td>'
                     '<td class="fill">i dont know</td>'
                     '<td class="fill">i dont know</td>'
                     '</tr>')
    st = ''.join(table)
    return st


def reload_page(request):
    global server
    if request.method == 'POST':
        server.update_site_from_database()
        history, sort_by, subdiv, org, elem_amount = post_data_receive(request)

        terms = [history, subdiv, org]
        print(f"sort_by={sort_by}")
        server.quick_sort(get_index_to_sort(sort_by))
        server.phone_table_filtered(terms)

        cache = server.get_cache()
        persons = create_phone_table(page=1, cache=cache, line_counter=int(elem_amount))
        st = create_table_ajax(persons)

        next_page, page_amount = create_next_prev_links(cache, 1)

        print(elem_amount)
        data = {
            "Users": st,
            "countpage": str(page_amount),
            "nextpage1": "./next_table",
            "elements_amount": elem_amount,
        }
        return JsonResponse(data, safe=False)


# надо сделать вторую функцию на переход между страницами
def next_table(request):
    global server
    if request.method == 'POST':
        server.update_site_from_database()
        history, sort_by, subdiv, org, elem_amount = post_data_receive(request)

        terms = [history, subdiv, org]
        server.quick_sort(get_index_to_sort(sort_by))
        server.phone_table_filtered(terms)
        cache = server.get_cache()

        pagenum = int(request.POST.get('countpage1')) + 1
        next_page, page_amount = create_next_prev_links(cache, pagenum)
        pagenum = page_amount if (pagenum % page_amount == 0) else pagenum % page_amount
        persons = create_phone_table(page=pagenum, cache=cache, line_counter=elem_amount)
        st = create_table_ajax(persons)

        next_page, page_amount = create_next_prev_links(cache, pagenum)

        data = {
            "Users": st,
            "countpage": str(page_amount),
            "nextpage1": "./next_table",
            "prevpage1": "./prev_table",
            "pagenum": pagenum,
            "elements_amount":elem_amount,
        }
        return JsonResponse(data, safe=False)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def prev_table(request):
    global server
    if request.method == 'POST':
        server.update_site_from_database()

        history, sort_by, subdiv, org, elem_amount = post_data_receive(request)
        terms = [history, subdiv, org]
        print(f"terms = {terms}")
        server.quick_sort(get_index_to_sort(sort_by))
        server.phone_table_filtered(terms)

        cache = server.get_cache()
        pagenum = int(request.POST.get('countpage1')) - 1
        pagenum, page_amount = create_next_prev_links(cache, pagenum)

        persons = create_phone_table(page=int(pagenum), cache=cache, line_counter=elem_amount)
        st = create_table_ajax(persons)

        data = {
            "Users": st,
            "countpage": str(page_amount),
            "nextpage1": "./next_table",
            "prevpage1": "./prev_table",
            "pagenum": pagenum,
            "elements_amount":elem_amount,
        }
        return JsonResponse(data, safe=False)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def post_data_receive(request):
    history = request.POST.get('history')
    sort_by = request.POST.get('sort_by')
    subdiv = request.POST.get('subdiv')
    org = request.POST.get('org')
    elem_amount = int(request.POST.get('elements_amount'))
    if elem_amount > 45:
        elem_amount = 45
    elif elem_amount < 1:
        elem_amount = 1

    return history, sort_by, subdiv, org, elem_amount

#  r"C:\VSCODEaaa\father_work\trying_django\djsite\webbook\ecss\wb.ini"
# Исправить пути
