from argparse import ArgumentParser, Namespace
import re
import time
import random

# Парсер на основе Chrome
from undetected_chromedriver import Chrome

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common import TimeoutException

from fake_useragent import UserAgent


BASE_URL = 'https://www.ozon.ru/'
# Стандартная пауза для имитирования человека
MIMIC_PAUSE = 1 # sec
# Стандартная пауза для ожидания появления элемента
DRIVER_PATIENCE = 10 # sec
# Placeholder в поисковой строке. Вынесен в отдельную переменную для возможности быстрой замены
SEARCH_INPUT_PLACEHOLDER = 'Искать на Ozon'


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


def input_search_query(driver: Chrome, query: str) -> str | None:
    try:
        # Ждём пока появится строка поиска
        input = WebDriverWait(driver, DRIVER_PATIENCE).until(
            expected_conditions.element_to_be_clickable((By.XPATH, f'//input[@placeholder="{SEARCH_INPUT_PLACEHOLDER}"]'))
        )
        time.sleep(MIMIC_PAUSE)
    except Exception as ex:
        return f'Поисковая строка не была найдена = {ex.__str__()}'

    try:
        input.clear()

        # Посылаю буквы по одной со случайной паузой, имитирую действия человека
        for char in query:
            input.send_keys(char)
            time.sleep(random.uniform(.05, .2))

        # После ввода запроса отправляю нажатие на Enter
        input.send_keys(Keys.RETURN)
    except Exception as ex:
        return f'Не удалось ввести запрос в поисковую строку = {ex.__str__()}'

    return None


# Общая функция для поиска товара
def find_product(query: str, article: str) -> tuple[dict | str | None, str | None]:
    driver = None
    try:
        try:
            driver = init_web_driver()
        except Exception as ex:
            return None, f'Ошибка в инициализации веб-драйвера - {ex.__str__()}'

        # Открытие главной страницы
        driver.get(BASE_URL)
        # Ожидание проверки антибот защиты
        time.sleep(MIMIC_PAUSE)

        error = input_search_query(driver, query)
        if error is not None:
            return None, error
    finally:
        time.sleep(MIMIC_PAUSE)
        if driver:
            driver.quit()

        return {}, None


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

    result, error = find_product(query, article)
    if error is not None:
        print(error)
