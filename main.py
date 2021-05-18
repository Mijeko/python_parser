import re
import sqlite3
import sys
import traceback
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager

def db_rows_count():
    sqlite_connection = sqlite3.connect('XXX_db.db')
    con = sqlite_connection.cursor()
    con.execute("select * from XXX_GOODS LIMIT 1")
    results = con.fetchall()
    con.close()
    sqlite_connection.close()
    if len(results) > 0:
        return True


def db_output_all():
    sqlite_connection = sqlite3.connect('XXX_db.db')
    con = sqlite_connection.cursor()
    sqlite_select_query = "SELECT * from XXX_GOODS"
    con.execute(sqlite_select_query)
    records = con.fetchall()
    print("Вывод каждой строки \n")
    for row in records:
        print("ID:", row[0])
        print("Наименование:", row[1])
        print("Цена без скидки:", row[2])
        print("Цена со скидкой:", row[3])
        print("Магазин:", row[4])
        print("Дата добавления", row[5], end="\n\n")
    con.close()
    sqlite_connection.close()


def db_delete_table(table_name):
    sqlite_connection = sqlite3.connect('XXX_db.db')
    con = sqlite_connection.cursor()
    con.execute("DELETE from " + table_name)
    sqlite_connection.commit()
    con.close()
    sqlite_connection.close()
    print("ТАБЛИЦА", table_name, "ОЧИЩЕНА!")


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


def parce_start():
    city = translit("Барнаул")
    # city = translit(input("Введите город в котором хотите парсить скидки: "))
    # if city == '':
    #     city = translit("Барнаул")
    #     print("Город не выбран. По умолчанию парсим Томск")

    segment="beer-cider"
    url = "https://XXX.ru/" + city + "/offers"
    bigParams = "retailer=5ka&retailer=aniks&retailer=auchan&retailer=bristol&retailer=lenta-giper&retailer=magnit-univer&retailer=maria-ra&retailer=myfasol&segment=" + segment
    url_start_page = url + "?" + bigParams
    # url_start_page = "https://XXX.ru/"+city+"/offers"
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.maximize_window()
    print(url_start_page)
    driver.get(url_start_page)
    driver.implicitly_wait(5)
    last_page = 1
    for e in driver.find_elements_by_class_name(
            'b-button.b-button_disabled_false.b-button_theme_blank.b-button_shape_square.b-button_size_m.b-button_justify_center.b-button_selected_false.b-pagination__n'):
        last_page = int(e.text)
    page_num = 1
    sqlite_connection = sqlite3.connect('XXX_db.db')
    con = sqlite_connection.cursor()
    if db_rows_count():
        db_delete_table("XXX_GOODS")

    print(last_page)
    while page_num <= last_page:
        url_start = url + "?page=" + str(page_num)+"&"+bigParams
        driver.get(url_start)
        driver.implicitly_wait(5)
        goods_card = driver.find_elements_by_class_name("b-offer__root")
        for gcard in goods_card:
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
            gmarket = gcard.find_element_by_class_name(
                "b-image.b-image_disabled_false.b-image_cap_f.b-image_img_vert.b-image_loaded_true.b-offer__retailer-icon").get_attribute(
                "title")
            g_add_date = datetime.now().date()
            try:
                con.execute('INSERT INTO XXX_GOODS (name,price_old,price_dis,market,add_date,city)'
                            'VALUES (?,?,?,?,?,?)', (gname, gprice_old, gprice_dis, gmarket, g_add_date, city))
                sqlite_connection.commit()
                row_count = con.execute("SELECT COUNT(*) FROM XXX_GOODS").fetchone()[0]
                print("Строка", row_count, "добавлена")
            except sqlite3.Error as error:
                print("Класс исключения: ", error.__class__)
                print("Исключение", error.args)
                print("Печать подробноcтей исключения SQLite: ")
                exc_type, exc_value, exc_tb = sys.exc_info()
                print(traceback.format_exception(exc_type, exc_value, exc_tb))
        page_num += 1
    db_output_all()
    con.close()
    sqlite_connection.close()
    driver.quit()


parce_start()