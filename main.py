# -*- coding: utf-8 -*-
#compile to exe run command in console: pyinstaller --onefile main.py
import re
import sqlite3
import sys
import io
import time

from collections import Counter
import traceback
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from threading import Thread
import pandas as pd

# retailers={'5ka','auchan','bristol','lenta-giper','magnit-univer','maria-ra'}
selected_retailers=[]
retailers=['5ka','auchan','aniks','bristol','lenta-giper','magnit-univer','maria-ra','myfasol']
city = 'barnaul'
url = "https://edadeal.ru/" + city + "/offers"
# query_params = "retailer=5ka&retailer=auchan&retailer=bristol&retailer=lenta-giper&retailer=magnit-univer&retailer=maria-ra&segment="
dataToExcel = {
    'Сеть': [],
    'Вид продукта': [],
    'Подкатегория': [],
    'Доп_категория': [],
    'Продукция': [],
    'Размер тары': [],
    'Тара': [],
    # 'Начало акции': [],
    'Окончание акции': [],
    'Цена до акции': [],
    'Цена во время акции': [],
    '% скидки': [],
    'Ссылка': [],
}
def get_sub_cat(driver):
    subcat=""
    for e in driver.find_elements_by_class_name('p-offer__segment-path'):
        subcat = e.text
    return subcat
def get_concret_section(driver):
    concret = ''
    try:
        name= driver.find_element_by_class_name('p-offer__description').text
    except:
        name='Не удалось получить'
    if isBeer(name):
        concret = 'Б/А пиво'
    elif isEnergyDrink(name):
        concret = 'Энергетик'

    return concret
def isBeer(str):
    return check_by_tags(str,['пивной','Пиво безалкогол'])
def isEnergyDrink(str):
    return check_by_tags(str,['энергет','кофеин','таурин'])
def check_by_tags(str,tags):
    isBool = False
    for e in tags:
        if str.lower().find(e.lower()) > 0:
            isBool = True
    return isBool
def getSection(en_sect):
    # {'beer-cider', 'beverages', 'kvass', 'cold-tea', 'water', 'sparkling-water'}
    if(en_sect=='beer-cider'): return 'Пиво-Сидр';
    if(en_sect=='kvass'): return 'Квас';
    if(en_sect=='cold-tea'): return 'Холодный чай';
    if(en_sect=='water'): return 'Вода';
    if(en_sect=='sparkling-water'): return 'Газированнная вода';
    if(en_sect=='beverages'): return 'Напитки';
def foo(savedItems, result, index, url_start,segment):
    driver2 = webdriver.Chrome(ChromeDriverManager().install())
    driver2.maximize_window()
    driver2.get(url_start)
    driver2.implicitly_wait(2)

    try:
        WebDriverWait(driver2, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "b-offer__offer-info")))
    except:
        print('капибара')

    goods_card = driver2.find_elements_by_class_name("p-offers__offer")
    for gcard in goods_card:
        contain_doubles = False
        try:
            clearHref = re.findall(r'^[^?]*',gcard.get_attribute('href'))
        except:
            print('капибара')
        for containValue in result[index]['Ссылка']:
            if (containValue == clearHref[0]):
                contain_doubles = True

        if (contain_doubles):
            continue

        savedItems[index] += 1
        try:
            net = gcard.find_element_by_class_name("b-image.b-image_disabled_false.b-image_cap_f.b-image_img_vert.b-image_loaded_true.b-offer__retailer-icon").get_attribute('title')
        except:
            net = 'Не удалось получить'
        gname = gcard.find_element_by_class_name("b-offer__description").text

        try:
            gprice_dis = gcard.find_element_by_class_name("b-offer__price-new").text
            gprice_dis = re.search("\d+(,.)\d+", gprice_dis).group(0)
        except NoSuchElementException:
            gprice_dis = 0

        try:
            gprice_old = gcard.find_element_by_class_name("b-offer__price-old").text
            gprice_old = re.search("\d+(,.)\d+", gprice_old).group(0)
        except NoSuchElementException:
            gprice_old = 0

        try:
            percent = gcard.find_element_by_class_name("b-offer__badge").text
        except NoSuchElementException:
            percent = 0

        try:
            date = gcard.find_element_by_class_name("b-offer__dates").text
        except NoSuchElementException:
            date = 0

        try:
            pack = gcard.find_element_by_class_name("b-offer__quantity").text
            packData = pack.split('/')
        except NoSuchElementException:
            pack = 0
            packData = ['Не указано']

        driver_detail = webdriver.Chrome(ChromeDriverManager().install())
        driver_detail.maximize_window()
        driver_detail.get(clearHref[0])
        driver_detail.implicitly_wait(3)

        result[index]['Сеть'].append(net)
        result[index]['Вид продукта'].append(getSection(segment))
        result[index]['Продукция'].append(gname)
        result[index]['Размер тары'].append(packData[0])
        result[index]['Окончание акции'].append(date)
        result[index]['Цена до акции'].append(gprice_old)
        result[index]['Цена во время акции'].append(gprice_dis)
        result[index]['% скидки'].append(percent)
        # result[index]['Начало акции'].append(get_start_action(gcard.get_attribute('href'),driver))
        result[index]['Подкатегория'].append(get_sub_cat(driver_detail))
        result[index]['Доп_категория'].append(get_concret_section(driver_detail))
        result[index]['Ссылка'].append(clearHref[0])
        driver_detail.quit()

    driver2.quit()
def get_last_page(driver, url, query_params):

    lp = get_actual_last_page(driver)
    lp_tmp=1

    while(lp != lp_tmp):
        lp_tmp =check_last_page(url, query_params, lp)
        lp=lp_tmp

    return lp_tmp
def get_actual_last_page(driver):
    last_page = 1
    for e in driver.find_elements_by_class_name( 'b-pagination__n'):
        last_page = int(e.text)
    return last_page
def check_last_page(url, query_params, lp):
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.maximize_window()
    driver.get(url + "?page=" + str(lp)+"&"+query_params)
    driver.implicitly_wait(2)
    lp = get_actual_last_page(driver)
    driver.quit()
    return lp
def save_to_file(data):
    df = pd.DataFrame.from_dict(data, orient='index')
    df = df.transpose()
    df.to_excel('./price.xlsx', sheet_name='price', index=False)
def print_select():
    on=0
    for i in filter(lambda x : x not in selected_retailers, retailers):
        print(i)
        # print(on,' - ',i)
        on+=1
def build_query(key,data):
    out=''
    for row in data:
        out+=key+'='+row+'&'
    return out[:-1]
def start():
    while(True):
        print_select()
        value = input('Введите название магазина для парсинга (Пустой Enter для продолжения): ')
        if not value:
            break
        selected_retailers.append(value)
    query_params = build_query('retailer',selected_retailers)

    start_time = time.time()
    for segment in {'beer-cider', 'beverages'}:
        params =query_params+'&segment='+segment
        url_start_page = url + "?" + params
        print(url_start_page)
        driver = webdriver.Chrome(ChromeDriverManager().install())
        driver.maximize_window()
        driver.get(url_start_page)
        driver.implicitly_wait(2)
        last_page = get_last_page(driver, url, params)
        # last_page = 1
        threads = [None] * last_page
        results = [dataToExcel] * last_page
        saved_items = [0] * last_page
        for page_num in range(last_page):
            pagenation =page_num+1
            url_start = url + "?page=" + str(pagenation) + "&" + params
            threads[page_num] = Thread(target=foo, args=(saved_items, results, page_num,url_start,segment))
            threads[page_num].start()
    for i in range(len(threads)):
        threads[i].join()
    list(map(save_to_file, results))
    print('complete for secs: ', time.time()-start_time)

start()