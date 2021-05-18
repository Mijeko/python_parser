# -*- coding: utf-8 -*-
import re
import sqlite3
import sys
import io
import time
import traceback
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime

from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

import pandas as pd

def get_detail_page(url,driver):
    driver.get(url)
    return driver.find_elements_by_class_name("p-offer__offer-container")

def get_start_action(url,driver):
    print(url)
    detail = get_detail_page(url,driver)

    try:
        datesString=detail.find_element_by_class_name('p-offer__dates').text
    except:
        datesString=""

    dates = datesString.split('по')

    return dates[0]

def getSection(en_sect):
    # {'beer-cider', 'beverages', 'kvass', 'cold-tea', 'water', 'sparkling-water'}
    if(en_sect=='beer-cider'): return 'Пиво-Сидр';
    if(en_sect=='kvass'): return 'Квас';
    if(en_sect=='cold-tea'): return 'Холодный чай';
    if(en_sect=='water'): return 'Вода';
    if(en_sect=='sparkling-water'): return 'Газированнная вода';
    if(en_sect=='beverages'): return 'Напитки';

def translit(city):
    slovar = {'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
              'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'i', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
              'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h',
              'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e',
              'ю': 'u', 'я': 'ya', 'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'YO',
              'Ж': 'ZH', 'З': 'Z', 'И': 'I', 'Й': 'I', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
              'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'H',
              'Ц': 'C', 'Ч': 'CH', 'Ш': 'SH', 'Щ': 'SCH', 'Ъ': '', 'Ы': 'y', 'Ь': '', 'Э': 'E',
              'Ю': 'U', 'Я': 'YA'}
    for key in slovar:
        city = city.replace(key, slovar[key]).lower()
    return city


dataToExcel = {
    'Сеть': [],
    'Вид продукта': [],
    'Продукция': [],
    'Размер тары': [],
    'Тара': [],
    'Начало акции': [],
    'Окончание акции': [],
    'Цена до акции': [],
    'Цена во время акции': [],
    '% скидки': [],
}

def parce_start():
    option = webdriver.ChromeOptions()
    option.add_argument('headless')
    # city = translit(input("Введите город в котором хотите парсить скидки: "))
    city = translit('Барнаул')
    if city == '':
        city = translit("Барнаул")
        print("Город не выбран. По умолчанию парсим Барнаул")

    # for segment in {'beer-cider','beverages','kvass','cold-tea','water','sparkling-water'}:
    # for segment in {'beer-cider', 'beverages'}:
    for segment in {'beer-cider'}:

        url = "https://edadeal.ru/"+city+"/offers"
        bigParams="retailer=5ka&retailer=aniks&retailer=auchan&retailer=bristol&retailer=lenta-giper&retailer=magnit-univer&retailer=maria-ra&retailer=myfasol&segment="+segment
        url_start_page = url+"?"+bigParams


        driver = webdriver.Chrome(ChromeDriverManager().install())
        driver.maximize_window()
        driver.get(url_start_page)
        time.sleep(5)
        last_page=1

        for e in driver.find_elements_by_class_name('b-button.b-button_disabled_false.b-button_theme_blank.b-button_shape_square.b-button_size_m.b-button_justify_center.b-button_selected_false.b-pagination__n'):
            last_page = int(e.text)

        page_num = 1
        last_page=3
        while page_num <= last_page:
            url_start = url + "?page=" + str(page_num)+"&"+bigParams

            # driver = webdriver.Chrome(ChromeDriverManager().install())
            # driver.maximize_window()
            driver.get(url_start)
            time.sleep(5)
            driver.implicitly_wait(5)
            items=0
            print(url_start)
            goods_card = driver.find_elements_by_class_name("p-offers__offer")
            for gcard in goods_card:
                net = gcard.find_element_by_class_name("b-image.b-image_disabled_false.b-image_cap_f.b-image_img_vert.b-image_loaded_true.b-offer__retailer-icon").get_attribute('title')
                gname = gcard.find_element_by_class_name("b-offer__description").text

                items+=1
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


                dataToExcel['Сеть'].append(net)
                dataToExcel['Вид продукта'].append(getSection(segment))
                dataToExcel['Продукция'].append(gname)
                dataToExcel['Размер тары'].append(packData[0])
                dataToExcel['Окончание акции'].append(date)
                dataToExcel['Цена до акции'].append(gprice_old)
                dataToExcel['Цена во время акции'].append(gprice_dis)
                dataToExcel['% скидки'].append(percent)
                # dataToExcel['Начало акции'].append(get_start_action(gcard.get_attribute('href'),driver))

                with io.open('demo.txt', "a", encoding="utf-8") as f:
                    f.write(getSection(segment)+gname+'\n')

            print(page_num)
            print(items)
            page_num += 1
        driver.quit()


    # df = pd.DataFrame.from_dict(dataToExcel, orient='index')
    # df = df.transpose()
    # df.to_excel('./price.xlsx',sheet_name='price', index=False)


parce_start()