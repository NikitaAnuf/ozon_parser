from argparse import ArgumentParser, Namespace
import re
import time

# Парсер на основе Chrome
from undetected_chromedriver import Chrome

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from fake_useragent import UserAgent


BASE_URL = 'https://www.ozon.ru/'
# Стандартная пауза для имитирования человека
MIMIC_PAUSE = 1 # sec
# Стандартная пауза для ожидания появления элемента
DRIVER_PATIENCE = 10 # sec


# Инициализация парсера аргументов командной строки
def init_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(description='Парсинг Ozon')

    # Оба аргумента позиционные. Сначала поисковой запрос, потом артикул товара
    parser.add_argument('query', help='Поисковой запрос')
    parser.add_argument('article', help='Артикул товара')

    return parser


# Проверка аргументов на правильность
def check_arguments(args: Namespace) -> tuple[str | None, str | None, str | None]:
    try:
        # Если одного из аргументов нет, возвращаю ошибку
        query, article = args.query, args.article
    except Exception as ex:
        return None, None, f'Ошибка в извлечении значений аргументов скрипта - {ex.args}'

    # Проверка аргумента query на правильность
    # Если в поисковом запросе есть только пробелы, возвращаю ошибку, такой запрос не имеет смысла
    if len(query.strip()) == 0:
        return None, None, 'Поисковый запрос составлен неверно, в нём должен быть хотя бы один непробельный символ'

    # Проверка аргумента article на правильность. Артикул состоит из 10 чисел
    # Решил использовать регулярное выражение, чтобы не делать сложные условия
    if not re.match(r'^[0-9]{10}$', article):
        return None, None, 'Введённый артикул неверный, он должен состоять из 10 числовых символов'

    # Если всё правильно, возвращаем query и article без ошибок
    return query, article, None


def init_web_driver() -> Chrome:
    ua = UserAgent()
    # Рандомный user agent. Нужен, чтобы парсер было сложнее вычислить
    user_agent = ua.random

    options = Options()

    # options.add_argument('--headless')
    options.add_argument('--disable-gpu') # Отключаю GPU для стабильности работы
    options.add_argument('--window-size=1920,1080') # Стандартный размер окна, чтобы вёрстка не изменялась
    options.add_argument(f'user-agent={user_agent}')

    # При закрытии драйвера в логах возвращалась проигнорированная ошибка дескриптора
    # Параметр enable_cdp_events в драйвере позволяет её предотвратить
    driver = Chrome(options=options, enable_cdp_events=True)

    return driver


# Общая функция для поиска товара
def find_product(query: str, article: str) -> tuple[dict | str | None, str | None]:
    try:
        driver = init_web_driver()
    except Exception as ex:
        return None, f'Ошибка в инициализации веб-драйвера - {ex.__str__()}'

    # Открытие главной страницы
    driver.get(BASE_URL)
    # Ожидание проверки антибот защиты
    time.sleep(MIMIC_PAUSE)

    driver.quit()


if __name__ == '__main__':
    parser = init_arg_parser()

    # Чтение аргументов
    try:
        args = parser.parse_args()
    except Exception as ex:
        print(f'Ошибка в получении аргументов скрипта: {ex.__str__()}')
        exit()

    query, article, error = check_arguments(args)
    if error is not None:
        print(error)
        exit()

    find_product(query, article)
